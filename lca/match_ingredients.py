"""match_ingredients.py — Match the unique ingredient strings from a
recipes JSONL file to AGRIBALYSE/SU-EATABLE/Poore & Nemecek emission
factors, and join multi-impact (water, land, etc.) by matched LCI Name.

Output: lca/ingredient_ef_table.csv, one row per unique ingredient with:
  - matched_lci_name
  - ghg_kgco2e_per_kg (+ min, max from cross-source widening)
  - water_m3_per_kg, land_pt_per_kg, acidification_per_kg,
    eutrophication_freshwater_per_kg (from AGRIBALYSE; None if matched
    source was SU-EATABLE or P&N, since those don't carry multi-impact)
  - confidence, method, unmatched

Idempotent — re-running is free thanks to lca/data/ef_cache.json.

Usage:
  python3 match_ingredients.py                                    # uses recipes_validation.jsonl
  python3 match_ingredients.py --recipes ../recipes/recipes.jsonl # for full run
  python3 match_ingredients.py --concurrency 30
"""
import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matcher  # type: ignore  # noqa: E402
import multi_impact  # type: ignore  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RECIPES = ROOT / "recipes" / "recipes_validation.jsonl"
DEFAULT_OUT = Path(__file__).resolve().parent / "ingredient_ef_table.csv"
ENV_FILE = ROOT / ".env.openrouter"


def load_api_key() -> str:
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"OPENROUTER_API_KEY not found in {ENV_FILE}")


def collect_unique_ingredients(recipes_path: Path) -> list[tuple[str, int]]:
    """Return [(name, occurrence_count)] sorted by count desc.

    Preserves first-seen casing for the name (lowercased key is used
    only for deduplication).
    """
    seen: dict[str, tuple[str, int]] = {}
    n_recipes = 0
    with open(recipes_path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("error"):
                continue
            n_recipes += 1
            for ing in r.get("ingredients", []):
                raw = (ing.get("ingredient") or "").strip()
                if not raw:
                    continue
                key = raw.lower()
                if key in seen:
                    name, n = seen[key]
                    seen[key] = (name, n + 1)
                else:
                    seen[key] = (raw, 1)
    print(f"  {n_recipes:,} recipes -> {len(seen):,} unique ingredient strings")
    return sorted(seen.values(), key=lambda nc: -nc[1])


def match_one(name: str, api_key: str) -> dict:
    """Run matcher + multi-impact join. Wraps exceptions so a single
    failing ingredient doesn't kill the whole batch."""
    try:
        r = matcher.match_ingredient(name, api_key=api_key)
    except Exception as e:
        return {
            "ingredient": name, "unmatched": True,
            "method": f"exception:{type(e).__name__}",
            "error": str(e)[:200],
        }
    lci = r.get("matched_lci_name")
    impacts = multi_impact.get_multi_impact(lci) if lci else None
    if impacts:
        r["water_m3_per_kg"] = impacts.get("water_use")
        r["land_pt_per_kg"] = impacts.get("land_use")
        r["acidification_per_kg"] = impacts.get("acidification")
        r["eutrophication_fw_per_kg"] = impacts.get("eutrophication_freshwater")
    else:
        r["water_m3_per_kg"] = None
        r["land_pt_per_kg"] = None
        r["acidification_per_kg"] = None
        r["eutrophication_fw_per_kg"] = None
    return r


def write_csv(out_path: Path, ingredients: list[tuple[str, int]],
              results_by_name: dict[str, dict]) -> None:
    cols = [
        "ingredient", "occurrences",
        "matched_lci_name", "primary_source", "n_matches", "n_sources",
        "ghg_kgco2e_per_kg", "ghg_min", "ghg_max",
        "water_m3_per_kg", "land_pt_per_kg",
        "acidification_per_kg", "eutrophication_fw_per_kg",
        "confidence", "method", "unmatched",
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for name, occ in ingredients:
            r = results_by_name.get(name.lower(), {})
            matches = r.get("matches") or []
            primary_source = matches[0]["source"] if matches else None
            n_sources = len(set(m.get("source") for m in matches)) if matches else 0
            w.writerow({
                "ingredient": name,
                "occurrences": occ,
                "matched_lci_name": r.get("matched_lci_name"),
                "primary_source": primary_source,
                "n_matches": r.get("n_matches", 0),
                "n_sources": n_sources,
                "ghg_kgco2e_per_kg": r.get("recommended"),
                "ghg_min": r.get("min"),
                "ghg_max": r.get("max"),
                "water_m3_per_kg": r.get("water_m3_per_kg"),
                "land_pt_per_kg": r.get("land_pt_per_kg"),
                "acidification_per_kg": r.get("acidification_per_kg"),
                "eutrophication_fw_per_kg": r.get("eutrophication_fw_per_kg"),
                "confidence": r.get("confidence"),
                "method": r.get("method"),
                "unmatched": r.get("unmatched", False),
            })


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipes", default=str(DEFAULT_RECIPES),
                   help=f"Recipes JSONL (default: {DEFAULT_RECIPES.name})")
    p.add_argument("--out", default=str(DEFAULT_OUT),
                   help="Output CSV path (default: lca/ingredient_ef_table.csv)")
    p.add_argument("--concurrency", type=int, default=20,
                   help="Max concurrent LLM calls (default: 20)")
    args = p.parse_args()

    api_key = load_api_key()
    print(f"loading {args.recipes}...")
    ingredients = collect_unique_ingredients(Path(args.recipes))

    # Pre-warm lazy globals so threads don't race on first encode
    print("warming model + embedding index...")
    matcher._get_model()
    matcher._load_embedding_index()

    print(f"matching with concurrency={args.concurrency}...")
    results_by_name: dict[str, dict] = {}
    t0 = time.time()
    last_print = t0

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(match_one, name, api_key): name for name, _ in ingredients}
        n_done = 0
        n_ok = n_unmatched = 0
        for fut in as_completed(futs):
            name = futs[fut]
            r = fut.result()
            results_by_name[name.lower()] = r
            n_done += 1
            if r.get("unmatched"):
                n_unmatched += 1
            else:
                n_ok += 1
            if time.time() - last_print > 5:
                elapsed = time.time() - t0
                rate = n_done / elapsed
                eta = (len(futs) - n_done) / rate if rate > 0 else 0
                print(f"  {n_done:>4d}/{len(futs)}  ({n_ok} ok, {n_unmatched} unmatched)  "
                      f"rate={rate:.1f}/s  eta={eta:.0f}s", flush=True)
                last_print = time.time()

    elapsed = time.time() - t0
    print(f"\ndone in {elapsed:.0f}s ({n_ok} matched, {n_unmatched} unmatched)")

    out_path = Path(args.out)
    write_csv(out_path, ingredients, results_by_name)
    print(f"wrote {out_path}")

    # Print a few summary stats
    matched_with_multi = sum(1 for r in results_by_name.values()
                             if not r.get("unmatched") and r.get("water_m3_per_kg") is not None)
    print(f"  matched with AGRIBALYSE multi-impact: {matched_with_multi}/{len(ingredients)}")


if __name__ == "__main__":
    main()
