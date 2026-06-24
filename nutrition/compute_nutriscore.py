"""compute_nutriscore.py — Per-dish Nutri-Score for every canonical dish,
following Clark et al. (2022). (Stage 2b, NutriScore step.)

Pipeline
--------
For each dish in `nutrition/dish_macros.jsonl` (one row per cluster_id,
with a per-ingredient breakdown carrying fdc_id + grams + the four
macros), we:

  1. Re-derive per-100 g energy / protein / fat / carb from the matched
     ingredient contributions and the recipe's total mass.
  2. Add the four Nutri-Score nutrients missing from the macro pipeline —
     saturated fat, total sugars, fibre, sodium — by joining each
     ingredient's fdc_id to `data/fdc_micronutrient_table.csv` and
     summing (per_100g x grams / 100), again expressed per 100 g of dish.
  3. Estimate the fruit/veg/legume/nut/qualifying-oil mass percentage
     (the FVN positive component) from `data/ingredient_fvn.csv`
     (fdc_id -> class), falling back to a string classifier for the ~1 %
     of ingredients with no FDC match.
  4. Detect the Nutri-Score food-type variant (general / beverage /
     cheese / fat) — almost all prepared dishes are "general".
  5. Run `nutriscore.nutri_score()` to get the -15..40 score, the A-E
     grade, Clark's 1-5 scale, and the 0-100 scaled nutrition-impact
     score.

Basis note: per-100 g values use the recipe's *total* mass as the
denominator while sums run over *matched* ingredients only, so a dish
with unmatched ingredients has those treated as nutrient-free. We record
`fdc_match_rate_mass` per dish so low-coverage dishes can be filtered.

Outputs
-------
  nutrition/dish_nutriscore.jsonl        every dish (full detail)
  nutrition/dish_nutriscore_manifold.csv the 39,166-dish phylogeny
                                         manifold (joined to dish_meta;
                                         idx-aligned to umap.json), the
                                         requested deliverable.

Usage:
  python3 nutrition/compute_nutriscore.py
  python3 nutrition/compute_nutriscore.py --macros <path> --no-manifold
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nutriscore as ns
from fvn_classify import classify_name

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"

DEFAULT_MACROS = HERE / "dish_macros.jsonl"
MICRO_TABLE = DATA / "fdc_micronutrient_table.csv"
FVN_TABLE = DATA / "ingredient_fvn.csv"
DISH_META = ROOT / "phylogeny" / "data" / "dish_meta.csv"

OUT_JSONL = HERE / "dish_nutriscore.jsonl"
OUT_MANIFOLD = HERE / "dish_nutriscore_manifold.csv"

# --- food-type detection ------------------------------------------------
# Matched as whole words (\b) so "platter" != latte and "shaken" != shake.
# Deliberately conservative & NON-ALCOHOLIC only: Clark et al. excluded
# alcoholic beverages, and ambiguous drink/cocktail names (margarita,
# americano, cocktail, mojito…) collide with food dishes (margarita pizza,
# americano taco, shrimp cocktail), so they are left out — misflagging a
# solid as a beverage applies the much harsher beverage grid.
BEVERAGE_TERMS = (
    "smoothie", "smoothies", "milkshake", "milkshakes", "milk shake",
    "shake", "shakes", "latte", "lattes", "cappuccino", "espresso",
    "macchiato", "frappuccino", "frappe", "frappes", "lemonade",
    "soda", "cola", "juice", "boba", "horchata", "milk tea", "iced coffee",
    "iced tea", "hot chocolate", "hot cocoa", "bubble tea", "agua fresca",
    "protein shake", "chai latte", "matcha latte",
)
# solid-food anchors that veto a beverage match (e.g. "coffee cake",
# "juice-glazed ribs", "milkshake cake", "shrimp cocktail").
SOLID_GUARD = (
    "cake", "cheesecake", "bread", "muffin", "cookie", "pie", "tart",
    "donut", "doughnut", "sandwich", "brownie", "pancake", "waffle",
    "soup", "ice cream", "popsicle", "sorbet", "parfait", "bowl",
    "oatmeal", "porridge", "pudding", "bake", "glazed", "ribs", "wing",
    "rice", "noodle", "salad", "bar", "pizza", "taco", "burrito",
    "chicken", "beef", "pork", "steak", "shrimp", "fish", "burger",
    "wrap", "platter", "plate", "sauce", "glaze",
)
WATER_TERMS = ("sparkling water", "mineral water", "still water",
               "bottled water")
_BEV_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in BEVERAGE_TERMS)
                     + r")\b")


def detect_food_type(name: str, dominant_class: str | None,
                     dominant_share: float) -> tuple[str, bool]:
    """Return (food_type, is_water). Conservative: general unless a clear
    beverage by name, or a dish dominated (>50% mass) by cheese or by
    added fat/oil."""
    n = (name or "").lower()
    if any(t in n for t in WATER_TERMS) or n.strip() == "water":
        return "beverage", True
    if _BEV_RE.search(n) and not any(g in n for g in SOLID_GUARD):
        return "beverage", False
    if dominant_share > 0.5:
        if dominant_class == "cheese":
            return "cheese", False
        if dominant_class == "fat":
            return "fat", False
    return "general", False


def load_micros(path: Path) -> dict[str, dict]:
    table = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            table[r["fdc_id"]] = {
                "sat_fat_g": float(r["sat_fat_g"]),
                "sugars_g": float(r["sugars_g"]),
                "fiber_g": float(r["fiber_g"]),
                "sodium_mg": float(r["sodium_mg"]),
                "category": r["fdc_category"],
                "description": r["description"],
            }
    return table


def load_fvn(path: Path) -> dict[str, str]:
    with open(path) as f:
        return {r["fdc_id"]: r["fvn_class"] for r in csv.DictReader(f)}


def _dominant_dish_class(desc: str, category: str) -> str | None:
    """Coarse class of the dominant ingredient for food-type detection:
    'cheese', 'fat', or None."""
    d, c = desc.lower(), category.lower()
    if "cheese" in d and ("dairy" in c or "cheese" in c):
        return "cheese"
    if (("butter" in d and "peanut" not in d and "nut" not in d)
            or "margarine" in d or "fats and oils" in c
            or "lard" in d or "shortening" in d):
        return "fat"
    return None


def compute_dish(d: dict, micros: dict, fvn: dict) -> dict | None:
    mass = float(d.get("recipe_mass_g") or 0.0)
    if mass <= 0:
        return None

    tot = {"energy_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carb_g": 0.0,
           "sat_fat_g": 0.0, "sugars_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0}
    fvn_mass = 0.0
    matched_mass = 0.0
    dom_class, dom_share = None, 0.0

    for ing in d.get("ingredients", []):
        grams = float(ing.get("grams") or 0.0)
        fid = ing.get("fdc_id")
        # macros already scaled per ingredient in dish_macros
        for m in ("energy_kcal", "protein_g", "fat_g", "carb_g"):
            v = ing.get(m)
            if v is not None:
                tot[m] += float(v)

        cls = None
        if fid and fid in micros:
            matched_mass += grams
            mr = micros[fid]
            scale = grams / 100.0
            tot["sat_fat_g"] += mr["sat_fat_g"] * scale
            tot["sugars_g"] += mr["sugars_g"] * scale
            tot["fiber_g"] += mr["fiber_g"] * scale
            tot["sodium_mg"] += mr["sodium_mg"] * scale
            cls = fvn.get(fid)
            # track the single largest-mass ingredient for food-type sniffing
            if grams > dom_share * mass:
                dom_share = grams / mass
                dom_class = _dominant_dish_class(mr["description"], mr["category"])
        else:
            # no FDC micronutrient row — fall back to string FVN class only
            cls = classify_name(ing.get("ingredient", ""))

        if cls and cls != "none":
            fvn_mass += grams

    per100 = lambda x: round(tot[x] / mass * 100, 3)
    energy_100 = per100("energy_kcal")
    sugars_100 = per100("sugars_g")
    satfat_100 = per100("sat_fat_g")
    sodium_100 = per100("sodium_mg")
    protein_100 = per100("protein_g")
    fat_100 = per100("fat_g")
    carb_100 = per100("carb_g")
    fiber_100 = per100("fiber_g")
    fvn_pct = round(fvn_mass / mass * 100, 2)

    food_type, is_water = detect_food_type(d.get("canonical_name", ""),
                                           dom_class, dom_share)

    profile = ns.nutri_score(
        energy_kcal=energy_100, sugars_g=sugars_100, sat_fat_g=satfat_100,
        sodium_mg=sodium_100, protein_g=protein_100, fiber_g=fiber_100,
        fvn_pct=fvn_pct, fat_g=fat_100, food_type=food_type, is_water=is_water)

    return {
        "cluster_id": d.get("cluster_id"),
        "canonical_name": d.get("canonical_name"),
        "cuisine_bucket": d.get("cuisine_bucket"),
        "recipe_mass_g": round(mass, 1),
        "fdc_match_rate_mass": round(matched_mass / mass, 4),
        "food_type": food_type,
        "is_water": is_water,
        "per_100g": {
            "energy_kcal": energy_100, "protein_g": protein_100,
            "fat_g": fat_100, "carb_g": carb_100,
            "sat_fat_g": satfat_100, "sugars_g": sugars_100,
            "fiber_g": fiber_100, "sodium_mg": sodium_100,
            "salt_g": round(sodium_100 * 2.5 / 1000, 3),
        },
        "fvn_pct": fvn_pct,
        "nutriscore": profile,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--macros", default=str(DEFAULT_MACROS))
    ap.add_argument("--out", default=str(OUT_JSONL))
    ap.add_argument("--no-manifold", action="store_true",
                    help="skip the manifold CSV join")
    args = ap.parse_args()

    if not MICRO_TABLE.exists():
        sys.exit(f"ERROR: {MICRO_TABLE} missing — run port_fdc_micronutrients.py")
    if not FVN_TABLE.exists():
        sys.exit(f"ERROR: {FVN_TABLE} missing — run fvn_classify.py")

    micros = load_micros(MICRO_TABLE)
    fvn = load_fvn(FVN_TABLE)
    print(f"loaded {len(micros):,} micronutrient rows, {len(fvn):,} FVN classes")

    results: dict[int, dict] = {}
    grade_counts: dict[str, int] = {}
    ftype_counts: dict[str, int] = {}
    n = n_skip = 0
    with open(args.macros) as fin, open(args.out, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out = compute_dish(d, micros, fvn)
            if out is None:
                n_skip += 1
                continue
            fout.write(json.dumps(out) + "\n")
            results[out["cluster_id"]] = out
            g = out["nutriscore"]["grade"]
            grade_counts[g] = grade_counts.get(g, 0) + 1
            ftype_counts[out["food_type"]] = ftype_counts.get(out["food_type"], 0) + 1
            n += 1
    print(f"wrote {args.out}  ({n:,} dishes; {n_skip} skipped: no mass)")
    print("  grade distribution:")
    for g in "ABCDE":
        c = grade_counts.get(g, 0)
        print(f"    {g}: {c:6,} ({c/n:.1%})")
    print("  food-type:", {k: v for k, v in sorted(ftype_counts.items())})

    if args.no_manifold:
        return
    if not DISH_META.exists():
        print(f"  WARN: {DISH_META} not found — skipping manifold CSV")
        return

    # --- manifold join: dish_meta drives membership + idx ordering ------
    with open(DISH_META) as f:
        meta_rows = list(csv.DictReader(f))
    cols = ["idx", "cluster_id", "canonical_name", "cuisine_bucket",
            "food_type", "energy_kcal_100g", "protein_g_100g", "fat_g_100g",
            "carb_g_100g", "sat_fat_g_100g", "sugars_g_100g", "fiber_g_100g",
            "sodium_mg_100g", "salt_g_100g", "fvn_pct", "negative_points",
            "positive_points", "nutriscore_points", "grade",
            "nutriscore_1to5", "nutriscore_0to100", "fdc_match_rate_mass"]
    n_join = n_miss = 0
    with open(OUT_MANIFOLD, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in meta_rows:
            cid = int(r["cluster_id"])
            o = results.get(cid)
            if o is None:
                n_miss += 1
                continue
            p, q = o["per_100g"], o["nutriscore"]
            w.writerow([
                r["idx"], cid, o["canonical_name"], o["cuisine_bucket"],
                o["food_type"], p["energy_kcal"], p["protein_g"], p["fat_g"],
                p["carb_g"], p["sat_fat_g"], p["sugars_g"], p["fiber_g"],
                p["sodium_mg"], p["salt_g"], o["fvn_pct"],
                q["negative_points"], q["positive_points"], q["score"],
                q["grade"], q["score_1to5"], q["score_0to100"],
                o["fdc_match_rate_mass"],
            ])
            n_join += 1
    print(f"wrote {OUT_MANIFOLD}  ({n_join:,} manifold dishes; "
          f"{n_miss} in dish_meta without a macro row)")


if __name__ == "__main__":
    main()
