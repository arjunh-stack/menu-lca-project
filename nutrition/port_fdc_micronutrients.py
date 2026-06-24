"""port_fdc_micronutrients.py — Extract the per-100 g nutrients that the
Nutri-Score algorithm needs but that `port_fdc_data.py` does not carry.
(Stage 2b sibling, NutriScore prerequisite.)

`port_fdc_data.py` pulls only the four headline macros (energy, protein,
total fat, carbohydrate). The Nutri-Score nutrient profile (Clark et al.
2022, PNAS, "Calculating the Nutrition Impact Score") additionally needs:

    saturated fat (g)   — negative component
    total sugars (g)    — negative component
    sodium (mg)         — negative component  (salt = sodium x 2.5)
    fibre (g)           — positive component

and a food-category tag, which we re-use downstream to (a) estimate the
fruit/veg/nut/legume/oil percentage (the one positive component with no
direct nutrient row) and (b) detect the Nutri-Score food-type variants
(beverage / cheese / added-fat).

Reads the same three FDC bulk sources as `port_fdc_data.py` and joins
each food to its nutrient rows. Output, under nutrition/data/:

  fdc_micronutrient_table.csv
      fdc_id, source, description, fdc_category,
      sat_fat_g, sugars_g, fiber_g, sodium_mg

Nutrient-id scheme differs by source exactly as in `port_fdc_data.py`:
SR Legacy + Foundation key `food_nutrient.nutrient_id` on the standard
nutrient `id`; FNDDS keys it on the legacy `nutrient_nbr`. Verified
against each source's nutrient.csv:

    nutrient              standard id     FNDDS nbr
    saturated fat         1258            606
    total sugars          2000 (or 1063)  269
    fibre, total dietary  1079            291
    sodium                1093            307

A missing nutrient row defaults to 0.0 (a food that genuinely reports no
fibre / sugars / sat-fat contributes none) — this matches the Nutri-Score
convention of scoring an absent positive component as 0 points and is
conservative for the negative components.

fdc_category resolution:
  SR Legacy / Foundation : food.food_category_id -> food_category.description
  FNDDS                  : survey_fndds_food.wweia_food_category
                           -> wweia_food_category.wweia_food_category_description

Idempotent: re-running overwrites the output CSV.

Usage:
  python3 nutrition/port_fdc_micronutrients.py
"""
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

SR_DIR = DATA_DIR / "sr_legacy" / "FoodData_Central_sr_legacy_food_csv_2018-04"
FNDDS_DIR = DATA_DIR / "fndds" / "FoodData_Central_survey_food_csv_2024-10-31"
FND_DIR = DATA_DIR / "foundation" / "FoodData_Central_foundation_food_csv_2026-04-30"

# Nutrient ids per source. Each is a fallback-priority list (first present
# wins) so a food that reports only an older sugars row still lands a value.
STANDARD_IDS = {
    "sat_fat_g": ["1258"],
    "sugars_g": ["2000", "1063"],   # Total Sugars, then Sugars Total NLEA
    "fiber_g": ["1079"],
    "sodium_mg": ["1093"],
}
FNDDS_IDS = {
    "sat_fat_g": ["606"],
    "sugars_g": ["269"],
    "fiber_g": ["291"],
    "sodium_mg": ["307"],
}

NUTRIENTS = ["sat_fat_g", "sugars_g", "fiber_g", "sodium_mg"]


def _pick(have: dict, priority: list[str]):
    """First nutrient amount present, walking the fallback priority list."""
    for nid in priority:
        amt = have.get(nid)
        if amt is not None and pd.notna(amt):
            return float(amt)
    return None


def _category_map_standard(food_csv: Path) -> dict[str, str]:
    """fdc_id -> category description for SR Legacy / Foundation, via
    food.food_category_id -> food_category.description."""
    cat_csv = food_csv.parent / "food_category.csv"
    cats = pd.read_csv(cat_csv, dtype=str)
    id_to_name = dict(zip(cats["id"], cats["description"]))
    foods = pd.read_csv(food_csv, usecols=["fdc_id", "food_category_id"],
                        dtype=str)
    return {
        r.fdc_id: id_to_name.get(r.food_category_id, "")
        for r in foods.itertuples(index=False)
    }


def _category_map_fndds(survey_dir: Path) -> dict[str, str]:
    """fdc_id -> WWEIA category description for FNDDS."""
    sff = pd.read_csv(survey_dir / "survey_fndds_food.csv",
                      usecols=["fdc_id", "wweia_category_number"], dtype=str)
    wcat = pd.read_csv(survey_dir / "wweia_food_category.csv", dtype=str)
    code_to_name = dict(zip(wcat["wweia_food_category"],
                            wcat["wweia_food_category_description"]))
    return {
        r.fdc_id: code_to_name.get(r.wweia_category_number, "")
        for r in sff.itertuples(index=False)
    }


def port_source(source: str, food_csv: Path, food_nutrient_csv: Path,
                id_scheme: dict, category_map: dict[str, str],
                foundation_only: bool = False) -> list[dict]:
    """Join one FDC source's food + food_nutrient rows into nutrient rows."""
    foods = pd.read_csv(food_csv, usecols=["fdc_id", "data_type", "description"],
                        dtype=str)
    if foundation_only:
        foods = foods[foods["data_type"] == "foundation_food"]
    foods = foods.dropna(subset=["fdc_id", "description"])
    valid_ids = set(foods["fdc_id"])
    desc_by_id = dict(zip(foods["fdc_id"], foods["description"]))
    print(f"  {source}: {len(valid_ids):,} foods")

    wanted_ids = {nid for lst in id_scheme.values() for nid in lst}
    fn = pd.read_csv(food_nutrient_csv,
                     usecols=["fdc_id", "nutrient_id", "amount"],
                     dtype={"fdc_id": str, "nutrient_id": str, "amount": float})
    fn = fn[fn["nutrient_id"].isin(wanted_ids) & fn["fdc_id"].isin(valid_ids)]

    have: dict[str, dict[str, float]] = defaultdict(dict)
    for fdc_id, nid, amt in fn.itertuples(index=False):
        have[fdc_id][nid] = amt

    rows = []
    for fdc_id, desc in desc_by_id.items():
        nut = have.get(fdc_id, {})
        vals = {n: _pick(nut, id_scheme[n]) for n in NUTRIENTS}
        rows.append({
            "fdc_id": fdc_id,
            "source": source,
            "description": desc.strip(),
            "fdc_category": category_map.get(fdc_id, ""),
            # absent nutrient -> 0.0 (see module docstring)
            "sat_fat_g": round(vals["sat_fat_g"] or 0.0, 3),
            "sugars_g": round(vals["sugars_g"] or 0.0, 3),
            "fiber_g": round(vals["fiber_g"] or 0.0, 3),
            "sodium_mg": round(vals["sodium_mg"] or 0.0, 2),
        })
    return rows


def main() -> None:
    print("Porting USDA FDC bulk CSVs -> per-100g Nutri-Score nutrient table")
    rows: list[dict] = []
    rows += port_source(
        "sr_legacy", SR_DIR / "food.csv", SR_DIR / "food_nutrient.csv",
        STANDARD_IDS, _category_map_standard(SR_DIR / "food.csv"))
    rows += port_source(
        "fndds", FNDDS_DIR / "food.csv", FNDDS_DIR / "food_nutrient.csv",
        FNDDS_IDS, _category_map_fndds(FNDDS_DIR))
    rows += port_source(
        "foundation", FND_DIR / "food.csv", FND_DIR / "food_nutrient.csv",
        STANDARD_IDS, _category_map_standard(FND_DIR / "food.csv"),
        foundation_only=True)

    if not rows:
        sys.exit("ERROR: no FDC rows extracted — check data/ paths.")

    df = pd.DataFrame(rows)[
        ["fdc_id", "source", "description", "fdc_category",
         "sat_fat_g", "sugars_g", "fiber_g", "sodium_mg"]
    ]
    out = DATA_DIR / "fdc_micronutrient_table.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out}  ({len(df):,} foods)")
    print("per-source counts:")
    print(df["source"].value_counts().to_string())
    print("\nnutrient presence (non-zero):")
    for n in NUTRIENTS:
        nz = (df[n] > 0).mean()
        print(f"  {n:11s} non-zero in {nz:.1%} of rows")


if __name__ == "__main__":
    main()
