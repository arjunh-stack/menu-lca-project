"""aggregate_macros.py — Recipe + per-ingredient macros -> per-dish macros.
(Stage 2b, step 4.)

Joins each recipe in a recipes JSONL file against ingredient_fdc_table.csv
(built by match_ingredients.py) and sums the four macros over the recipe's
ingredients, scaled by gram weight:

    contribution = per_100g_value * grams / 100

Writes nutrition/dish_macros.jsonl, one JSON object per recipe (cluster_id),
with per-recipe and per-serving totals, a per-ingredient breakdown, and the
list of any ingredients that failed to match.

Serving model (PLAN D4): the recipe step prompts for a "standard 4-serving
recipe", so per-serving = per-recipe / 4. The per-recipe totals are the
primitive; per-serving can be re-derived if a different normaliser lands.

Pure in-process arithmetic — no API calls, fast, idempotent.

Usage:
  python3 aggregate_macros.py                                   # recipes_validation.jsonl
  python3 aggregate_macros.py --recipes ../recipes/recipes.jsonl  # full ~75k run
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_RECIPES = ROOT / "recipes" / "recipes_validation.jsonl"
DEFAULT_TABLE = HERE / "ingredient_fdc_table.csv"
DEFAULT_OUT = HERE / "dish_macros.jsonl"

N_SERVINGS = 4  # PLAN D4
MACROS = ["energy_kcal", "protein_g", "fat_g", "carb_g"]


def load_ingredient_table(path: Path) -> dict[str, dict]:
    """ingredient_fdc_table.csv -> {lowercased ingredient: row dict}."""
    table: dict[str, dict] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            unmatched = str(row.get("unmatched", "")).strip().lower() == "true"
            rec = {
                "fdc_id": row.get("fdc_id") or None,
                "matched_description": row.get("matched_description") or None,
                "source": row.get("source") or None,
                "confidence": row.get("confidence") or None,
                "unmatched": unmatched,
            }
            for m in MACROS:
                v = row.get(m)
                rec[m] = float(v) if v not in (None, "", "None") else None
            table[(row["ingredient"] or "").strip().lower()] = rec
    return table


def aggregate_recipe(recipe: dict, table: dict[str, dict]) -> dict:
    """Sum macros over one recipe's ingredients, scaled by grams."""
    totals = {m: 0.0 for m in MACROS}
    ing_rows: list[dict] = []
    unmatched: list[str] = []
    total_mass = 0.0
    matched_mass = 0.0

    for ing in recipe.get("ingredients", []):
        name = (ing.get("ingredient") or "").strip()
        grams = float(ing.get("grams") or 0.0)
        total_mass += grams
        rec = table.get(name.lower())

        row = {"ingredient": name, "grams": round(grams, 2)}
        if rec is None or rec["unmatched"] or rec["energy_kcal"] is None:
            unmatched.append(name)
            row.update({
                "matched_fdc": None, "fdc_id": None, "source": None,
                "energy_kcal": None, "protein_g": None,
                "fat_g": None, "carb_g": None, "confidence": "none",
            })
        else:
            matched_mass += grams
            scale = grams / 100.0
            contrib = {m: round((rec[m] or 0.0) * scale, 2) for m in MACROS}
            for m in MACROS:
                totals[m] += contrib[m]
            row.update({
                "matched_fdc": rec["matched_description"],
                "fdc_id": rec["fdc_id"],
                "source": rec["source"],
                "confidence": rec["confidence"],
                **contrib,
            })
        ing_rows.append(row)

    per_recipe = {m: round(totals[m], 1) for m in MACROS}
    per_serving = {m: round(totals[m] / N_SERVINGS, 1) for m in MACROS}
    match_rate = round(matched_mass / total_mass, 4) if total_mass else 0.0

    return {
        "cluster_id": recipe.get("cluster_id"),
        "canonical_name": recipe.get("canonical_name"),
        "cuisine_bucket": recipe.get("cuisine_bucket"),
        "recipe_mass_g": round(total_mass, 1),
        "n_servings": N_SERVINGS,
        "energy_kcal_per_recipe": per_recipe["energy_kcal"],
        "protein_g_per_recipe": per_recipe["protein_g"],
        "fat_g_per_recipe": per_recipe["fat_g"],
        "carb_g_per_recipe": per_recipe["carb_g"],
        "energy_kcal_per_serving": per_serving["energy_kcal"],
        "protein_g_per_serving": per_serving["protein_g"],
        "fat_g_per_serving": per_serving["fat_g"],
        "carb_g_per_serving": per_serving["carb_g"],
        "match_rate": match_rate,
        "unmatched": unmatched,
        "ingredients": ing_rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipes", default=str(DEFAULT_RECIPES),
                   help=f"recipes JSONL (default: {DEFAULT_RECIPES.name})")
    p.add_argument("--table", default=str(DEFAULT_TABLE),
                   help="ingredient_fdc_table.csv from match_ingredients.py")
    p.add_argument("--out", default=str(DEFAULT_OUT),
                   help="output JSONL (default: dish_macros.jsonl)")
    args = p.parse_args()

    table_path = Path(args.table)
    if not table_path.exists():
        sys.exit(f"ERROR: {table_path} not found — run match_ingredients.py first.")
    table = load_ingredient_table(table_path)
    print(f"loaded {len(table):,} matched ingredients from {table_path.name}")

    n = n_skipped = 0
    sum_recipe = {m: 0.0 for m in MACROS}
    match_rates: list[float] = []
    full_match = 0
    with open(args.recipes) as fin, open(args.out, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            recipe = json.loads(line)
            if recipe.get("error"):
                n_skipped += 1
                continue
            out = aggregate_recipe(recipe, table)
            fout.write(json.dumps(out) + "\n")
            n += 1
            for m in MACROS:
                sum_recipe[m] += out[f"{m}_per_recipe"]
            match_rates.append(out["match_rate"])
            if out["match_rate"] >= 0.999:
                full_match += 1

    print(f"wrote {args.out}  ({n:,} dishes; {n_skipped} skipped error rows)")
    if n:
        avg_mr = sum(match_rates) / len(match_rates)
        print(f"  mean ingredient-mass match rate: {avg_mr:.1%}")
        print(f"  fully matched dishes (match_rate=1.0): {full_match:,}/{n:,}")
        print("  mean per-recipe macros (4 servings):")
        for m in MACROS:
            unit = "kcal" if m == "energy_kcal" else "g"
            print(f"    {m:14s} {sum_recipe[m] / n:8.1f} {unit}  "
                  f"({sum_recipe[m] / n / N_SERVINGS:.1f} {unit}/serving)")


if __name__ == "__main__":
    main()
