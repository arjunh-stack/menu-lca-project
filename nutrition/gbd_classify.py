"""gbd_classify.py — Classify each FDC food (and any bare ingredient
string) into one of the seven GBD dietary risk-factor food groups used by
Koen van Greevenbroek's `mealhealth` package, or `other`.

Why this exists
---------------
`mealhealth.assess_meal()` describes a meal as grams of each of seven GBD
risk-factor groups plus the meal's total calories. Everything outside the
seven groups (poultry, fish, eggs, oils, refined grains, dairy, sugar,
potatoes, …) enters the model *only* through the calorie total, by
displacing the baseline diet. So to feed mealhealth we need, per
ingredient, which (if any) of the seven groups it belongs to. This is the
mealhealth analogue of `fvn_classify.py` (which serves Nutri-Score).

The seven groups (mealhealth keys)
----------------------------------
  fruits, vegetables, whole_grains, legumes, nuts_seeds,
  red_meat (unprocessed beef/pork/lamb/goat),
  processed_meat (bacon/ham/sausage/deli/cured).
Anything else -> "other" (counts toward kcal only).

Method
------
Four of the seven groups (fruits, vegetables, legumes, nuts_seeds) are
exactly the Nutri-Score FVN classes minus the non-GBD "oil" class, so we
delegate those to `fvn_classify.classify()` and rename. The two GBD groups
NutriScore never modelled — meat (split unprocessed/processed) and whole
grains (split from refined) — get dedicated rules here, checked *first*:

  * processed_meat is checked before red_meat (a cured pork product is
    processed, not unprocessed red meat).
  * whole_grains requires an explicit whole-grain marker in the
    description; refined grains (white bread, white rice, all-purpose
    flour, regular pasta) fall through to "other" — they are NOT a GBD
    risk group and act through calories only.

Outputs nutrition/data/ingredient_gbd.csv (fdc_id, gbd_group) for every
food in fdc_micronutrient_table.csv. `classify_name()` is exported for the
~1 % of dish ingredients with no FDC match (string-only fallback).

Usage:
  python3 nutrition/gbd_classify.py            # build table + self-test
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fvn_classify import classify as fvn_classify

DATA_DIR = Path(__file__).resolve().parent / "data"
MICRO = DATA_DIR / "fdc_micronutrient_table.csv"
OUT = DATA_DIR / "ingredient_gbd.csv"

GBD_GROUPS = ("fruits", "vegetables", "whole_grains", "legumes",
              "nuts_seeds", "red_meat", "processed_meat")

# FVN class -> GBD group (the four shared groups; "oil"/"none" -> other).
_FVN_TO_GBD = {
    "fruit": "fruits",
    "vegetable": "vegetables",
    "legume": "legumes",
    "nut": "nuts_seeds",
    "oil": "other",
    "none": "other",
}

# --- meat-alternative veto (checked before any meat rule) ----------------
# Soy/plant "meat" products look meaty by keyword but are not GBD red/
# processed meat. Route soy-based ones to legumes, the rest to other.
MEATALT_TERMS = ("meat-alternative", "meat alternative", "meatless",
                 "plant-based", "plant based", "vegetarian", "vegan",
                 "meat substitute", "imitation", "tofu", "tempeh", "seitan",
                 "soy-based", "veggie burger", "beyond ", "impossible ")

# --- processed meat (checked before red meat) ---------------------------
PROCESSED_CAT = ("bacon", "sausage", "frankfurter", "cold cuts and cured",
                 "luncheon meat", "cured meat", "deli and cured")
PROCESSED_KW = ("bacon", "ham,", " ham", "sausage", "salami", "pepperoni",
                "chorizo", "prosciutto", "hot dog", "frankfurter", "bologna",
                "pastrami", "corned beef", "luncheon", "bratwurst", "kielbasa",
                "deli ", "cured", "smoked sausage", "pancetta", "mortadella",
                "capicola", "soppressata", "andouille", "linguica",
                "spam", "pepperette", "jerky", "summer sausage", "liverwurst",
                "blood sausage", "chorizo", "nduja", "guanciale")

# --- unprocessed red meat (checked after processed) ---------------------
RED_CAT = ("beef products", "beef, excludes ground", "ground beef", "pork",
           "pork products", "lamb, veal", "lamb, goat", "liver and organ")
RED_KW = ("beef", "pork", "lamb", "veal", "goat meat", "venison", "bison",
          "mutton", "ground beef", "steak", "tenderloin", "sirloin", "ribeye",
          "brisket", "oxtail", "tripe", "liver", "kidney")
# tokens that, if present, veto a red-meat match (poultry/fish/etc.)
NOT_RED = ("chicken", "turkey", "duck", "poultry", "fish", "salmon", "tuna",
           "shrimp", "egg", "broth", "bouillon", "stock,", "gravy")

# --- whole grains (refined grains deliberately excluded -> "other") -----
WHOLE_GRAIN_KW = ("whole wheat", "whole-wheat", "whole grain", "whole-grain",
                  "wholegrain", "wholemeal", "brown rice", "wild rice",
                  "oatmeal", "rolled oats", "steel-cut", "oat bran",
                  "oats", "barley", "quinoa", "bulgur", "buckwheat",
                  "rye ", "rye,", "rye bread", "millet", "farro", "spelt",
                  "sorghum", "freekeh", "amaranth", "teff", "whole rye",
                  "whole oat", "popcorn", "cracked wheat")


def _has(text, terms):
    return any(t in text for t in terms)


def classify(description: str, category: str = "") -> str:
    """Return one of the seven GBD group names or "other" for an FDC food.

    Order matters: meat-alternative veto, then processed_meat, then
    red_meat, then whole_grains, then fall back to the FVN classes
    (fruits/vegetables/legumes/nuts_seeds)."""
    d = (description or "").lower()
    c = (category or "").lower()

    # 0) meat-alternative veto — never let these become red/processed meat
    if _has(d, MEATALT_TERMS):
        # soy/bean-based alternatives are GBD legumes; others act via kcal
        if _has(d, ("soy", "tofu", "tempeh", "bean", "lentil", "pea protein")):
            return "legumes"
        return "other"

    # 1) processed meat (before red meat)
    if _has(c, PROCESSED_CAT) or _has(d, PROCESSED_KW):
        return "processed_meat"

    # 2) unprocessed red meat (poultry/fish/egg/broth veto)
    if not _has(d, NOT_RED):
        if _has(c, RED_CAT) or _has(d, RED_KW):
            return "red_meat"

    # 3) whole grains (refined grains fall through to "other")
    #    guard "oats" against "goat" (already meat-vetoed above, but be safe)
    if _has(d, WHOLE_GRAIN_KW) and "goat" not in d:
        return "whole_grains"
    # brown/wild rice written with reversed word order ("Rice, brown, ...")
    if "rice" in d and ("brown" in d or "wild" in d):
        return "whole_grains"

    # 4) the four shared groups via the Nutri-Score FVN classifier
    return _FVN_TO_GBD[fvn_classify(description, category)]


def classify_name(name: str) -> str:
    """String-only fallback for an ingredient with no FDC match."""
    return classify(name, "")


def build_table() -> None:
    n = 0
    counts: dict[str, int] = {}
    with open(MICRO) as fin, open(OUT, "w", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["fdc_id", "gbd_group"])
        for r in csv.DictReader(fin):
            g = classify(r["description"], r["fdc_category"])
            w.writerow([r["fdc_id"], g])
            counts[g] = counts.get(g, 0) + 1
            n += 1
    print(f"wrote {OUT}  ({n:,} foods)")
    risk = sum(v for k, v in counts.items() if k != "other")
    print(f"  in a risk group: {risk:,} ({risk/n:.1%}); by group:")
    for k in (*GBD_GROUPS, "other"):
        print(f"    {k:14} {counts.get(k, 0):,}")


# Cases the classifier MUST get right — guards against keyword regressions.
SELFTEST = [
    # processed meat
    ("Bacon, cooked", "Bacon", "processed_meat"),
    ("Sausage, pork", "Sausages and Luncheon Meats", "processed_meat"),
    ("Ham, sliced, prepackaged, deli", "Cold cuts and cured meats", "processed_meat"),
    ("Pepperoni", "Sausages and Luncheon Meats", "processed_meat"),
    ("Frankfurter, beef", "Frankfurters", "processed_meat"),
    ("Salami, dry or hard, pork", "Sausages and Luncheon Meats", "processed_meat"),
    ("Chorizo, pork and beef", "Sausages", "processed_meat"),
    # unprocessed red meat
    ("Beef, ground, raw", "Ground beef", "red_meat"),
    ("Beef, tenderloin, raw", "Beef Products", "red_meat"),
    ("Pork, fresh, loin, raw", "Pork Products", "red_meat"),
    ("Lamb, leg, raw", "Lamb, Veal, and Game Products", "red_meat"),
    ("Beef liver, raw", "Liver and organ meats", "red_meat"),
    # NOT red meat
    ("Chicken, breast, raw", "Poultry Products", "other"),
    ("Fish, salmon, raw", "Finfish and Shellfish Products", "other"),
    ("Egg, whole, raw", "Dairy and Egg Products", "other"),
    ("Beef broth", "Soups, Sauces, and Gravies", "other"),
    # meat alternatives
    ("Tofu, raw, firm", "Legumes and Legume Products", "legumes"),
    ("Soy-based meatless patty", "Soy and meat-alternative products", "legumes"),
    ("Plant-based patty, no marker", "Soy and meat-alternative products", "other"),
    # whole vs refined grains
    ("Bread, whole-wheat", "Yeast breads", "whole_grains"),
    ("Rice, brown, long-grain, cooked", "Rice", "whole_grains"),
    ("Oatmeal, cooked", "Grits and other cooked cereals", "whole_grains"),
    ("Quinoa, cooked", "Pasta, noodles, cooked grains", "whole_grains"),
    ("Bread, white", "Yeast breads", "other"),
    ("Rice, white, cooked", "Rice", "other"),
    ("Flour, wheat, all-purpose", "Cereal Grains and Pasta", "other"),
    ("Pasta, cooked", "Pasta, noodles, cooked grains", "other"),
    # shared FVN groups still work
    ("Tomatoes, raw", "Tomatoes", "vegetables"),
    ("Banana, raw", "Bananas", "fruits"),
    ("Beans, black, mature seeds, raw", "Legumes and Legume Products", "legumes"),
    ("Nuts, almonds", "Nut and Seed Products", "nuts_seeds"),
    ("Olive oil", "Salad dressings and vegetable oils", "other"),
    ("Potato, NFS", "White potatoes, baked or boiled", "other"),
    ("Cheese, cheddar", "Cheese", "other"),
    ("Salt, table", "Spices and Herbs", "other"),
]


def selftest() -> bool:
    ok = True
    for desc, cat, expect in SELFTEST:
        got = classify(desc, cat)
        if got != expect:
            ok = False
            print(f"  [FAIL] {desc[:40]:40} cat={cat[:24]:24} -> {got} "
                  f"(expected {expect})")
    print("self-test:", "ALL PASS" if ok else "FAILURES ABOVE")
    return ok


if __name__ == "__main__":
    if selftest():
        build_table()
