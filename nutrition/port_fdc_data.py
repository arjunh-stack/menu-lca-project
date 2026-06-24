"""port_fdc_data.py — Extract per-100 g macros from the USDA FoodData
Central bulk CSVs into a single flat lookup table. (Stage 2b, step 1.)

Reads three FDC data sources (SR Legacy, FNDDS/Survey, Foundation Foods),
joins each food to its nutrient rows, and pulls four nutrients — all
reported per 100 g edible portion, the FDC standard basis:

    energy (kcal), protein (g), total lipid/fat (g), carbohydrate (g)

Outputs, under nutrition/data/:
  fdc_macro_table.csv   fdc_id, source, description,
                        energy_kcal, protein_g, fat_g, carb_g
  fdc_descriptions.csv  fdc_id, source, description   (input to embedding)

Two source-specific quirks handled here:

1. Nutrient-id scheme differs by source. SR Legacy and Foundation key
   `food_nutrient.nutrient_id` on the standard nutrient `id`
   (1008/1003/1004/1005). FNDDS keys it on the legacy `nutrient_nbr`
   (208/203/204/205). Verified against each source's nutrient.csv.

2. Foundation caveat (PLAN D1). The Foundation bulk CSV's food.csv mixes
   ~87 k forensic chain-of-custody rows (sample_food, sub_sample_food,
   market_acquisition, agricultural_acquisition) in with the 469 real
   foundation foods. We filter to data_type == 'foundation_food'.

Energy preference: true Energy (kcal) first, then Atwater Specific, then
Atwater General — so a food reporting only Atwater energy still lands a
value rather than being dropped.

Idempotent: re-running overwrites the two output CSVs.
"""
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

SR_DIR = DATA_DIR / "sr_legacy" / "FoodData_Central_sr_legacy_food_csv_2018-04"
FNDDS_DIR = DATA_DIR / "fndds" / "FoodData_Central_survey_food_csv_2024-10-31"
FND_DIR = DATA_DIR / "foundation" / "FoodData_Central_foundation_food_csv_2026-04-30"

# Nutrient ids per source. Lists are energy-fallback priority order.
# SR Legacy + Foundation use the standard nutrient `id`; FNDDS uses
# `nutrient_nbr` (confirmed against each source's nutrient.csv).
STANDARD_IDS = {
    "energy_kcal": ["1008", "2048", "2047"],  # Energy, Atwater specific, general
    "protein_g": ["1003"],
    "fat_g": ["1004"],
    "carb_g": ["1005"],
}
FNDDS_IDS = {
    "energy_kcal": ["208", "958", "957"],
    "protein_g": ["203"],
    "fat_g": ["204"],
    "carb_g": ["205"],
}

MACROS = ["energy_kcal", "protein_g", "fat_g", "carb_g"]


def _pick(have: dict, priority: list[str]):
    """First nutrient amount present, walking the fallback priority list."""
    for nid in priority:
        amt = have.get(nid)
        if amt is not None and pd.notna(amt):
            return float(amt)
    return None


def port_source(source: str, food_csv: Path, food_nutrient_csv: Path,
                id_scheme: dict, foundation_only: bool = False) -> list[dict]:
    """Join one FDC source's food + food_nutrient CSVs into macro rows."""
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

    rows, n_no_energy = [], 0
    for fdc_id, desc in desc_by_id.items():
        nut = have.get(fdc_id, {})
        vals = {m: _pick(nut, id_scheme[m]) for m in MACROS}
        if vals["energy_kcal"] is None:
            # No usable energy value — useless for a macro lookup. Drop it.
            n_no_energy += 1
            continue
        rows.append({
            "fdc_id": fdc_id,
            "source": source,
            "description": desc.strip(),
            # protein/fat/carb default to 0.0 when a food genuinely
            # reports none (e.g. salt, water); energy is always present.
            "energy_kcal": round(vals["energy_kcal"], 2),
            "protein_g": round(vals["protein_g"] or 0.0, 2),
            "fat_g": round(vals["fat_g"] or 0.0, 2),
            "carb_g": round(vals["carb_g"] or 0.0, 2),
        })
    print(f"     -> {len(rows):,} with macros  ({n_no_energy:,} dropped: no energy value)")
    return rows


def main() -> None:
    print("Porting USDA FoodData Central bulk CSVs -> per-100g macro table")
    rows: list[dict] = []
    rows += port_source("sr_legacy",
                        SR_DIR / "food.csv", SR_DIR / "food_nutrient.csv",
                        STANDARD_IDS)
    rows += port_source("fndds",
                        FNDDS_DIR / "food.csv", FNDDS_DIR / "food_nutrient.csv",
                        FNDDS_IDS)
    rows += port_source("foundation",
                        FND_DIR / "food.csv", FND_DIR / "food_nutrient.csv",
                        STANDARD_IDS, foundation_only=True)

    if not rows:
        sys.exit("ERROR: no FDC rows extracted — check data/ paths.")

    df = pd.DataFrame(rows)[
        ["fdc_id", "source", "description",
         "energy_kcal", "protein_g", "fat_g", "carb_g"]
    ]
    macro_path = DATA_DIR / "fdc_macro_table.csv"
    desc_path = DATA_DIR / "fdc_descriptions.csv"
    df.to_csv(macro_path, index=False)
    df[["fdc_id", "source", "description"]].to_csv(desc_path, index=False)

    print(f"\nwrote {macro_path}  ({len(df):,} foods)")
    print(f"wrote {desc_path}")
    print("\nper-source counts:")
    print(df["source"].value_counts().to_string())


if __name__ == "__main__":
    main()
