"""aggregate_lca.py — Per-recipe LCA aggregation.

Joins a recipes JSONL (from recipes/pipeline.py) against
ingredient_ef_table.csv and produces per-recipe totals plus Monte Carlo
uncertainty on the GHG headline number.

  recipes_validation.jsonl  ─┐
                              ├──►  dish_lca_validation.jsonl  (one row / cluster_id)
  ingredient_ef_table.csv  ──┘

Per recipe we report:
  - recipe_mass_g (sum of ingredient grams as written)
  - ghg_kgco2e_per_recipe, ghg_kgco2e_per_kg
  - water_m3_per_recipe, water_m3_per_kg
  - land_pt_per_recipe, land_pt_per_kg
  - acidification_per_recipe, eutrophication_fw_per_recipe
  - ghg_mc: {mean, median, std, p5, p25, p75, p95} from 10k-draw triangular
    Monte Carlo over (ghg_min, ghg_recommended, ghg_max) per ingredient,
    with normal(σ=15%) mass noise. Per-ingredient variance contribution
    surfaces the GHG hotspots.
  - n_ingredients, match_rate, unmatched (list of ingredient names that
    couldn't be matched — these are dropped from the totals)

Scope: cradle-to-farm-gate (D3). Headline GHG = AGRIBALYSE ag+processing
column where available, widened with P&N cross-source values for MC.

Headline GHG uncertainty: full triangular MC (D2).
Other impacts (water/land/acidification/eutrophication): deterministic
point-estimate aggregation. AGRIBALYSE doesn't publish ranges for these
and we don't synthesize them in v1.

Usage:
  python3 aggregate_lca.py                                       # default paths
  python3 aggregate_lca.py --recipes ../recipes/recipes.jsonl --out dish_lca.jsonl
  python3 aggregate_lca.py --mc-draws 5000 --seed 42
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monte_carlo import Ingredient, monte_carlo_propagation  # type: ignore  # noqa: E402
from pedigree import score_product  # type: ignore  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LCA_DIR = Path(__file__).resolve().parent
DEFAULT_RECIPES = ROOT / "recipes" / "recipes_validation.jsonl"
DEFAULT_EF_TABLE = LCA_DIR / "ingredient_ef_table.csv"
DEFAULT_CACHE = LCA_DIR / "data" / "ef_cache.json"
DEFAULT_OUT = LCA_DIR / "dish_lca_validation.jsonl"


def _to_float(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def load_ef_table(path: Path) -> dict[str, dict]:
    """Return dict keyed by lowercased ingredient string → EF row."""
    out: dict[str, dict] = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            key = r["ingredient"].strip().lower()
            out[key] = {
                "ingredient": r["ingredient"],
                "matched_lci_name": r["matched_lci_name"] or None,
                "primary_source": r["primary_source"] or None,
                "n_matches": int(r["n_matches"]) if r.get("n_matches") else 0,
                "ghg": _to_float(r["ghg_kgco2e_per_kg"]),
                "ghg_min": _to_float(r["ghg_min"]),
                "ghg_max": _to_float(r["ghg_max"]),
                "water": _to_float(r["water_m3_per_kg"]),
                "land": _to_float(r["land_pt_per_kg"]),
                "acidification": _to_float(r["acidification_per_kg"]),
                "eutrophication_fw": _to_float(r["eutrophication_fw_per_kg"]),
                "confidence": r["confidence"] or None,
                "method": r["method"] or None,
                "unmatched": r["unmatched"] == "True",
            }
    return out


def load_cache_sources(path: Path) -> dict[str, str]:
    """Map lowercased ingredient name → source_description from ef_cache.json.

    Source_description holds the DB-name-tagged string ("AGRIBALYSE v3.2: …; …")
    that the pedigree module needs for `_parse_sources`. The EF table itself
    only stores `primary_source = "Local cache"`, which is not enough.
    Returns empty dict if cache absent (pedigree degrades to "no sources").
    """
    if not path.exists():
        return {}
    with open(path) as f:
        cache = json.load(f)
    out: dict[str, str] = {}
    for name, entry in cache.get("entries", {}).items():
        out[name.strip().lower()] = entry.get("source_description") or ""
    return out


def aggregate_recipe(recipe: dict, ef_table: dict[str, dict],
                     cache_sources: dict[str, str],
                     mc_draws: int, seed: int | None) -> dict:
    """Compute per-recipe totals + MC + pedigree. Skips ingredients with no EF."""
    cluster_id = recipe.get("cluster_id")
    ingredients = recipe.get("ingredients", [])
    recipe_mass_g = sum(float(i.get("grams", 0) or 0) for i in ingredients)

    rows: list[dict] = []           # per-ingredient breakdown rows
    mc_inputs: list[Ingredient] = []  # MC inputs (matched only)
    pedigree_inputs: list[dict] = []  # pedigree inputs (matched only)
    unmatched: list[str] = []

    totals = {"ghg_g": 0.0, "water_m3": 0.0, "land_pt": 0.0,
              "acidification": 0.0, "eutrophication_fw": 0.0}
    mass_with_ef_g = 0.0  # mass that contributed to GHG (used for match_rate)

    for ing in ingredients:
        name = (ing.get("ingredient") or "").strip()
        grams = float(ing.get("grams", 0) or 0)
        if not name or grams <= 0:
            continue
        ef = ef_table.get(name.lower())
        if ef is None or ef["unmatched"] or ef["ghg"] is None:
            unmatched.append(name)
            rows.append({
                "ingredient": name,
                "grams": grams,
                "matched_lci": None,
                "ghg_g": None,
                "water_l": None,
                "land_pt": None,
                "source": None,
                "unmatched": True,
            })
            continue

        kg = grams / 1000.0
        ghg_g = kg * ef["ghg"] * 1000.0  # → grams CO2e for the recipe row
        water_m3 = kg * ef["water"] if ef["water"] is not None else None
        land_pt = kg * ef["land"] if ef["land"] is not None else None
        acid = kg * ef["acidification"] if ef["acidification"] is not None else None
        eutr = kg * ef["eutrophication_fw"] if ef["eutrophication_fw"] is not None else None

        totals["ghg_g"] += ghg_g
        if water_m3 is not None:
            totals["water_m3"] += water_m3
        if land_pt is not None:
            totals["land_pt"] += land_pt
        if acid is not None:
            totals["acidification"] += acid
        if eutr is not None:
            totals["eutrophication_fw"] += eutr
        mass_with_ef_g += grams

        mc_inputs.append(Ingredient(
            name=name,
            mass_g=grams,
            ef_recommended=ef["ghg"],
            ef_min=ef["ghg_min"] if ef["ghg_min"] is not None else ef["ghg"],
            ef_max=ef["ghg_max"] if ef["ghg_max"] is not None else ef["ghg"],
        ))

        pedigree_inputs.append({
            "name": name,
            "confidence": ef["confidence"],
            "method": ef["method"] or "",
            "n_matches": ef["n_matches"],
            "source": cache_sources.get(name.lower(), ""),
            "co2e": ghg_g,  # weight by recipe-row CO2e, not per-kg EF
        })

        rows.append({
            "ingredient": name,
            "grams": grams,
            "matched_lci": ef["matched_lci_name"],
            "source": ef["primary_source"],
            "ghg_g": round(ghg_g, 2),
            "water_l": round(water_m3 * 1000.0, 2) if water_m3 is not None else None,
            "land_pt": round(land_pt, 3) if land_pt is not None else None,
            "unmatched": False,
        })

    rows.sort(key=lambda r: -(r.get("ghg_g") or 0))

    # Monte Carlo on GHG (skip when nothing matched)
    if mc_inputs:
        mc = monte_carlo_propagation(mc_inputs, n_simulations=mc_draws, seed=seed)
        ghg_mc = {
            "mean": round(mc["mean"], 4),
            "median": round(mc["median"], 4),
            "std": round(mc["std"], 4),
            "p5": round(mc["p5"], 4),
            "p25": round(mc["p25"], 4),
            "p75": round(mc["p75"], 4),
            "p95": round(mc["p95"], 4),
        }
        # Top-5 variance contributors for hotspot analysis
        contrib = sorted(
            mc["per_ingredient_variance_contribution"].items(),
            key=lambda kv: -kv[1],
        )[:5]
        ghg_mc["top_variance_drivers"] = [
            {"ingredient": n, "variance_pct": round(100 * v, 2)} for n, v in contrib
        ]
    else:
        ghg_mc = None

    # Pedigree score across matched ingredients (weighted by CO2e share)
    pedigree = score_product(pedigree_inputs) if pedigree_inputs else None

    n_ing = sum(1 for r in rows if not r["unmatched"])
    n_total = len(rows)
    match_rate_count = n_ing / n_total if n_total else 0.0
    match_rate_mass = mass_with_ef_g / recipe_mass_g if recipe_mass_g > 0 else 0.0

    recipe_mass_kg = recipe_mass_g / 1000.0
    ghg_recipe_kg = totals["ghg_g"] / 1000.0

    return {
        "cluster_id": cluster_id,
        "canonical_name": recipe.get("canonical_name"),
        "top_raw_name": recipe.get("top_raw_name"),
        "cuisine_bucket": recipe.get("cuisine_bucket"),
        "total_count": recipe.get("total_count"),
        "model": recipe.get("model"),
        "recipe_mass_g": round(recipe_mass_g, 1),
        "n_ingredients": n_total,
        "n_matched": n_ing,
        "match_rate_count": round(match_rate_count, 3),
        "match_rate_mass": round(match_rate_mass, 3),
        "unmatched": unmatched,
        "ghg_kgco2e_per_recipe": round(ghg_recipe_kg, 4),
        "ghg_kgco2e_per_kg":     round(ghg_recipe_kg / recipe_mass_kg, 4) if recipe_mass_kg > 0 else None,
        "water_m3_per_recipe":   round(totals["water_m3"], 4),
        "water_m3_per_kg":       round(totals["water_m3"] / recipe_mass_kg, 4) if recipe_mass_kg > 0 else None,
        "land_pt_per_recipe":    round(totals["land_pt"], 3),
        "land_pt_per_kg":        round(totals["land_pt"] / recipe_mass_kg, 3) if recipe_mass_kg > 0 else None,
        "acidification_per_recipe":     round(totals["acidification"], 5),
        "eutrophication_fw_per_recipe": round(totals["eutrophication_fw"], 6),
        "ghg_mc": ghg_mc,
        "data_quality_grade": pedigree["overall_grade"] if pedigree else None,
        "data_quality_score": pedigree["overall_score"] if pedigree else None,
        "data_gaps": pedigree["data_gaps"] if pedigree else [],
        "ingredients": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipes", default=str(DEFAULT_RECIPES))
    p.add_argument("--ef-table", default=str(DEFAULT_EF_TABLE))
    p.add_argument("--cache", default=str(DEFAULT_CACHE),
                   help="ef_cache.json path (used to recover DB-source strings for pedigree)")
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--mc-draws", type=int, default=10_000,
                   help="Monte Carlo draws per recipe (default: 10,000)")
    p.add_argument("--seed", type=int, default=None,
                   help="Random seed for reproducibility (default: nondeterministic)")
    args = p.parse_args()

    ef_path = Path(args.ef_table)
    recipes_path = Path(args.recipes)
    out_path = Path(args.out)

    print(f"loading EF table from {ef_path.name}...")
    ef_table = load_ef_table(ef_path)
    print(f"  {len(ef_table):,} ingredient EFs loaded")

    cache_path = Path(args.cache)
    print(f"loading EF cache from {cache_path.name} (for pedigree sources)...")
    cache_sources = load_cache_sources(cache_path)
    print(f"  {len(cache_sources):,} cache entries loaded")

    print(f"loading recipes from {recipes_path.name}...")
    recipes = []
    with open(recipes_path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("error"):
                continue
            recipes.append(r)
    print(f"  {len(recipes):,} recipes (after dropping errors)")

    print(f"aggregating + MC ({args.mc_draws:,} draws/recipe)...")
    t0 = time.time()
    out_handle = open(out_path, "w")
    n_done = 0
    n_full_match = 0
    n_any_unmatched = 0
    for r in recipes:
        lca = aggregate_recipe(r, ef_table, cache_sources, args.mc_draws,
                               seed=args.seed + n_done if args.seed is not None else None)
        if lca["match_rate_count"] >= 1.0:
            n_full_match += 1
        else:
            n_any_unmatched += 1
        out_handle.write(json.dumps(lca) + "\n")
        n_done += 1
    out_handle.close()

    elapsed = time.time() - t0
    print(f"\ndone in {elapsed:.0f}s ({n_done / elapsed:.0f} recipes/s)")
    print(f"  full match: {n_full_match}/{n_done}")
    print(f"  with at least one unmatched ingredient: {n_any_unmatched}/{n_done}")
    print(f"  output: {out_path}")


if __name__ == "__main__":
    main()
