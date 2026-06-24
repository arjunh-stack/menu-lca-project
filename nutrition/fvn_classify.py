"""fvn_classify.py — Classify each FDC food (and any bare ingredient
string) into the Nutri-Score "fruits, vegetables, legumes, nuts & oils"
(FVN) percentage component.

Why this exists
---------------
Six of the seven Nutri-Score nutrients are direct nutrient rows we can
read from FDC (energy, sugars, sat-fat, sodium, protein, fibre). The
seventh — the *fruit / vegetable / legume / nut / qualifying-oil
percentage of the product by mass* — has no nutrient row. Clark et al.
(2022) estimated it from each product's sorted food categories; we do the
analogous thing one level down, classifying each *ingredient* and then
summing the qualifying ingredients' mass share per dish (done in
`compute_nutriscore.py`).

What qualifies (official FSAm-NPS / Santé publique France 2017 rule)
-------------------------------------------------------------------
  fruits, vegetables, pulses (legumes), nuts & seeds, and oils sourced
  from OLIVES, WALNUTS, and RAPESEED (canola) only.

Explicitly NOT counted:
  * starchy roots & tubers — potato, sweet potato, cassava, yam,
    plantain, tapioca (Nutri-Score excludes these from the veg share)
  * any other oil (sunflower, vegetable/NFS, sesame, palm, soybean, …)
  * salty/sugary derivatives that are mostly water+salt+sugar — soy
    sauce, plant-based milks, fruit-juice *drinks* — small mass anyway
  * spices & herbs are immaterial by mass and left uncounted

Method
------
A hybrid of (a) FDC food-category prior — works across both the SR-Legacy
coarse scheme ("Vegetables and Vegetable Products") and the FNDDS WWEIA
fine scheme ("Tomatoes", "Beans, peas, legumes") — and (b) a curated
description-keyword fallback for foods whose category is unset or generic.
Exclusions are applied first so they always win.

Outputs nutrition/data/ingredient_fvn.csv (fdc_id, fvn_class) for every
food in fdc_micronutrient_table.csv. `classify_name()` is exported for
the ~1% of dish ingredients with no FDC match (string-only fallback).

Usage:
  python3 nutrition/fvn_classify.py            # build table + self-test
"""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
MICRO = DATA_DIR / "fdc_micronutrient_table.csv"
OUT = DATA_DIR / "ingredient_fvn.csv"

QUALIFYING = {"fruit", "vegetable", "legume", "nut", "oil"}

# --- exclusion terms (checked against description first; always win) ----
STARCHY = ("potato", "french fr", "frites", "hash brown", "tater",
           "cassava", "yam", "plantain", "tapioca", "starchy")
QUAL_OIL_TERMS = ("olive oil", "rapeseed", "canola", "colza", "walnut oil")
# foods that look FVN by category/keyword but are mostly water/salt/sugar
EXCLUDE_TERMS = ("soy sauce", "plant-based milk", "plant based milk",
                 "juice drink", "juice cocktail", "-ade", "soda",
                 "fruit drink", "tamari")

# --- category priors (substring match on the FDC category, lowercased) --
FRUIT_CAT = ("fruit", "apple", "banana", "berr", "citrus", "melon",
             "peach", "nectarine", "pear", "grape", "pineapple", "mango",
             "cherr", "plum", "apricot", "kiwi", "pomegran")
VEG_CAT = ("vegetable", "tomato", "onion", "spinach", "lettuce", "carrot",
           "broccoli", "pepper", "cucumber", "mushroom", "cabbage",
           "squash", "greens", "green beans", "cauliflower", "celery",
           "asparagus", "eggplant", "zucchini", "beet", "dark-green",
           "red and orange", "okra", "artichoke", "kale", "brussels",
           "string bean")
LEGUME_CAT = ("legume", "beans, peas")
NUT_CAT = ("nut and seed", "nuts and seeds")

# --- description keywords (fallback when category is generic/unset) -----
FRUIT_KW = ("apple", "banana", "orange", "lemon", "lime", "grape",
            "berry", "berries", "strawberr", "blueberr", "raspberr",
            "mango", "pineapple", "peach", "pear", "plum", "cherry",
            "melon", "watermelon", "kiwi", "apricot", "fig", "pomegran",
            "cranberr", "papaya", "guava", "passion fruit", "fruit",
            "avocado", "coconut", "raisin", "currant", "date")
VEG_KW = ("tomato", "onion", "garlic", "ginger", "spinach", "lettuce",
          "carrot", "broccoli", "bell pepper", "jalapeno", "jalapeño",
          "chili pepper", "cucumber", "mushroom", "cabbage", "squash",
          "zucchini", "eggplant", "cauliflower", "celery", "asparagus",
          "beet", "kale", "okra", "artichoke", "brussels", "pumpkin",
          "leek", "shallot", "scallion", "green bean", "snap pea",
          "snow pea", "bok choy", "radish", "turnip", "parsnip",
          "fennel", "watercress", "arugula", "chard", "collard",
          "corn", "sweetcorn", "pea,", "peas,")
LEGUME_KW = ("bean", "lentil", "chickpea", "garbanzo", "edamame", "tofu",
             "tempeh", "soybean", "hummus", "split pea", "black-eyed",
             "pinto", "kidney bean", "cannellini", "mung")
NUT_KW = ("almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut",
          "peanut", "macadamia", "pine nut", "brazil nut", "sesame",
          "sunflower seed", "pumpkin seed", "tahini", "nut butter",
          "chia", "flaxseed", "flax seed", "hemp seed", "poppy seed")


def _has(text: str, terms) -> bool:
    return any(t in text for t in terms)


def classify(description: str, category: str = "") -> str:
    """Return one of fruit/vegetable/legume/nut/oil/none for an FDC food.

    Exclusions win first, then specific classes (nut→legume→fruit→veg) so
    e.g. a "nut and seed" food is never reclassified as veg by a stray
    keyword."""
    d = (description or "").lower()
    c = (category or "").lower()

    # 1) exclusions — always win
    if _has(d, STARCHY) or _has(c, ("starchy", "white potato")):
        return "none"
    if _has(d, EXCLUDE_TERMS):
        return "none"
    # spices/herbs and plant-based milks: immaterial or non-qualifying,
    # excluded by category (catches "Spices, pepper, black" etc.)
    if _has(c, ("spices and herbs", "plant-based milk", "plant based milk")):
        return "none"
    if d.startswith("spices,"):
        return "none"

    # 2) oils — only olive / rapeseed / walnut qualify; all other oils out
    if "oil" in d and "boil" not in d:
        return "oil" if _has(d, QUAL_OIL_TERMS) else "none"

    # 3) nuts & seeds
    if _has(c, NUT_CAT) or _has(d, NUT_KW):
        return "nut"

    # 4) legumes / pulses
    if _has(c, LEGUME_CAT) or _has(d, LEGUME_KW):
        return "legume"

    # 5) fruit
    if _has(c, FRUIT_CAT) or _has(d, FRUIT_KW):
        return "fruit"

    # 6) vegetables (potato/starchy already excluded above)
    if _has(c, VEG_CAT) or _has(d, VEG_KW):
        return "vegetable"

    return "none"


def classify_name(name: str) -> str:
    """String-only fallback for an ingredient with no FDC match."""
    return classify(name, "")


def build_table() -> None:
    n = 0
    counts: dict[str, int] = {}
    with open(MICRO) as fin, open(OUT, "w", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["fdc_id", "fvn_class"])
        for r in csv.DictReader(fin):
            cls = classify(r["description"], r["fdc_category"])
            w.writerow([r["fdc_id"], cls])
            counts[cls] = counts.get(cls, 0) + 1
            n += 1
    print(f"wrote {OUT}  ({n:,} foods)")
    fvn = sum(v for k, v in counts.items() if k != "none")
    print(f"  FVN-qualifying: {fvn:,} ({fvn/n:.1%}); by class:")
    for k in ["fruit", "vegetable", "legume", "nut", "oil", "none"]:
        print(f"    {k:10} {counts.get(k, 0):,}")


# Cases the classifier MUST get right — guards against keyword regressions.
SELFTEST = [
    ("Garlic, raw", "Vegetables and Vegetable Products", "vegetable"),
    ("Ginger root, raw", "Vegetables and Vegetable Products", "vegetable"),
    ("Tomatoes, raw", "Tomatoes", "vegetable"),
    ("Tomato products, canned, sauce", "Vegetables and Vegetable Products", "vegetable"),
    ("Avocado, raw", "Other vegetables and combinations", "fruit"),
    ("Mushrooms, raw", "Other vegetables and combinations", "vegetable"),
    ("Lime juice, raw", "Fruits and Fruit Juices", "fruit"),
    ("Banana, raw", "Bananas", "fruit"),
    ("Beans, black, mature seeds, raw", "Legumes and Legume Products", "legume"),
    ("Chickpeas (garbanzo beans)", "Legumes and Legume Products", "legume"),
    ("Tofu, raw, firm", "Legumes and Legume Products", "legume"),
    ("Peanut butter", "Nuts and seeds", "nut"),
    ("Nuts, almonds", "Nut and Seed Products", "nut"),
    ("Seeds, sesame seeds, whole, dried", "Nut and Seed Products", "nut"),
    ("Olive oil", "Salad dressings and vegetable oils", "oil"),
    ("Vegetable oil, NFS", "Salad dressings and vegetable oils", "none"),
    ("Sesame oil", "Salad dressings and vegetable oils", "none"),
    ("Potato, NFS", "White potatoes, baked or boiled", "none"),
    ("Sweet potato, NFS", "Other red and orange vegetables", "none"),
    ("Plantain, raw", "Other starchy vegetables", "none"),
    ("Soy sauce", "Soy-based condiments", "none"),
    ("Coconut milk", "Plant-based milk", "none"),
    ("Salt, table", "Spices and Herbs", "none"),
    ("Spices, pepper, black", "Spices and Herbs", "none"),
    ("Chicken, breast, raw", "Poultry Products", "none"),
    ("Sugars, granulated", "Sweets", "none"),
    ("Flour, wheat, all-purpose", "Cereal Grains and Pasta", "none"),
    ("Rice, white, cooked", "Cereal Grains and Pasta", "none"),
]


def selftest() -> bool:
    ok = True
    for desc, cat, expect in SELFTEST:
        got = classify(desc, cat)
        flag = "ok " if got == expect else "FAIL"
        if got != expect:
            ok = False
        if got != expect:
            print(f"  [{flag}] {desc[:38]:38} cat={cat[:26]:26} -> {got} (expected {expect})")
    print("self-test:", "ALL PASS" if ok else "FAILURES ABOVE")
    return ok


if __name__ == "__main__":
    if selftest():
        build_table()
