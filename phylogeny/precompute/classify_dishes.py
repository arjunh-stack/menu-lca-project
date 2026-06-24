"""Stage 5.6 — per-dish categorical attributes for the colour overlays.

Derives three labels per v1 dish, written to phylogeny/data/dish_classes.csv:

  cuisine        the restaurant cuisine the dish is most associated with
                 (American, Italian, Thai, …). Computed from the
                 `restaurant_category` tags of every restaurant serving
                 the dish in menu_dishes.sqlite, mapped through a curated
                 tag→cuisine table. Generic tags ("American", "Asian")
                 are down-weighted 0.5× so a specific cuisine wins a
                 modest contest; dishes with no cuisine signal → "Other".

  protein_type   the dish's primary protein — the protein category with
                 the most grams across its recipe ingredients
                 (chicken / beef / pork / fish / lamb / turkey / egg /
                 tofu / beans / cheese / none).

  carb_type      the dish's primary carbohydrate, same idea
                 (rice / wheat / corn / potato / none).

protein/carb use keyword rules over the recipe ingredient strings —
those strings are LLM-normalised and clean ("chicken breast", "white
rice"), so rules resolve the overwhelming majority. Broths, stocks and
sauces are excluded so "chicken stock" / "fish sauce" don't masquerade
as the protein.

Usage:  python3 classify_dishes.py
"""
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PHYLO_DIR = SCRIPT_DIR.parent
REPO = PHYLO_DIR.parent
DATA_DIR = PHYLO_DIR / "data"

DB = REPO / "menu_dishes.sqlite"
RECIPES = REPO / "recipes" / "recipes.jsonl"
DISH_META = DATA_DIR / "dish_meta.csv"
OUT = DATA_DIR / "dish_classes.csv"

# --- cuisine: restaurant-category tag -> cuisine label -----------------
GENERIC = {"American", "Asian"}        # down-weighted so specifics win
CUISINE_MAP = {t: c for c, tags in {
    "American": ["American", "Traditional American", "New American",
                 "Comfort Food", "Southern", "Soul Food", "Diner", "BBQ",
                 "Cajun", "Hawaiian", "Hot Dog", "Cheesesteak",
                 "Fish and Chips", "Fish & Chips"],
    "Mexican": ["Mexican", "New Mexican", "Tex Mex", "Burritos", "Tacos",
                "Quesadillas"],
    "Italian": ["Italian", "Pizza", "Pasta"],
    "Chinese": ["Chinese", "Chinese: Other", "Cantonese",
                "Chinese: Cantonese", "Chinese: Sichuan", "Dumpling House",
                "Taiwanese"],
    "Japanese": ["Japanese", "Sushi", "Japanese: Sushi", "Ramen",
                 "Japanese BBQ", "Poke"],
    "Thai": ["Thai", "Northern Thai"],
    "Vietnamese": ["Vietnamese", "Pho"],
    "Korean": ["Korean"],
    "Indian": ["Indian", "Indian Curry", "North Indian", "South Indian",
               "Biryani", "Rice & Curry", "Pakistani", "Nepalese",
               "Himalayan", "Bangladeshi", "Afghan", "South Asian"],
    "Mediterranean": ["Mediterranean", "Greek", "Middle Eastern", "Lebanese",
                      "Turkish", "Persian", "Arabian", "Falafel", "Kebab",
                      "Moroccan"],
    "Latin American": ["Latin American", "Latin Fusion", "Caribbean",
                       "Peruvian", "Salvadorian", "Colombian",
                       "Puerto Rican", "Venezuelan", "Brazilian",
                       "South American", "Cuban", "Latin American: Other"],
    "Asian": ["Asian", "Asian Fusion", "Noodles", "Asian: Other",
              "South East Asian", "Malaysian", "Mongolian", "Filipino",
              "Indonesian", "Singaporean"],
    "African": ["African", "Ethiopian"],
    "European": ["European", "Modern European", "French", "German",
                 "Spanish", "British", "Irish"],
}.items() for t in tags}

# --- protein / carb keyword rules (checked in order) -------------------
# (label, [substrings that select it])
PROTEIN_RULES = [
    ("fish",    ["fish", "shrimp", "prawn", "salmon", "tuna", "cod",
                 "tilapia", "crab", "lobster", "scallop", "calamari",
                 "squid", "clam", "mussel", "anchov", "halibut", "catfish",
                 "mahi", "snapper", "trout", "seafood", "octopus",
                 "crawfish", "haddock", "sardine", "eel"]),
    ("lamb",    ["lamb", "mutton", "goat"]),
    ("turkey",  ["turkey"]),
    ("chicken", ["chicken"]),
    ("beef",    ["beef", "steak", "brisket", "sirloin", "veal"]),
    ("pork",    ["pork", "bacon", "ham", "sausage", "prosciutt", "chorizo",
                 "pancetta", "pepperoni", "salami", "carnitas"]),
    ("egg",     ["egg"]),
    ("tofu",    ["tofu", "tempeh", "seitan", "edamame"]),
    ("beans",   ["bean", "chickpea", "garbanzo", "lentil"]),
    ("cheese",  ["cheese", "paneer", "feta", "mozzarella", "cheddar",
                 "parmesan", "ricotta", "queso", "gouda", "provolone"]),
]
PROTEIN_EXCLUDE = ("stock", "broth", "bouillon", "sauce", "powder",
                   "seasoning")
NOT_BEANS = ("green bean", "string bean", "bean sprout", "vanilla bean",
             "coffee bean", "cocoa bean")

CARB_RULES = [
    ("potato", ["potato", "fries", "hash brown", "tater", "yam", "cassava",
                "yuca", "plantain"]),
    ("corn",   ["corn", "masa", "polenta", "hominy", "grits", "cornmeal"]),
    ("rice",   ["rice"]),
    ("wheat",  ["bread", "pasta", "flour", "tortilla", "noodle", "spaghetti",
                "macaroni", "bun", "dough", "naan", "pita", "couscous",
                "bulgur", "crust", "wrap", "biscuit", "cracker", "orzo",
                "gnocchi", "udon", "ramen", "vermicelli"]),
]


def protein_of(name: str) -> str | None:
    n = name.lower()
    if any(x in n for x in PROTEIN_EXCLUDE):
        return None
    for label, keys in PROTEIN_RULES:
        if label == "egg" and ("eggplant" in n or "noodle" in n):
            continue
        if label == "beans" and any(x in n for x in NOT_BEANS):
            continue
        if any(k in n for k in keys):
            return label
    return None


def carb_of(name: str) -> str | None:
    n = name.lower()
    if "cornstarch" in n or "rice vinegar" in n or "rice wine" in n \
            or "rice paper" in n:
        return None
    for label, keys in CARB_RULES:
        if any(k in n for k in keys):
            return label
    return None


def primary(ingredients, classifier) -> str:
    """Category carrying the most grams across the recipe."""
    mass = defaultdict(float)
    for ing in ingredients:
        cat = classifier(str(ing.get("ingredient", "")))
        if cat:
            mass[cat] += float(ing.get("grams") or 0)
    return max(mass, key=mass.get) if mass else "none"


def load_v1() -> dict[str, int]:
    """canonical_name -> cluster_id for the v1 dish set."""
    with open(DISH_META) as f:
        return {r["canonical_name"]: int(r["cluster_id"])
                for r in csv.DictReader(f)}


def cuisine_by_cluster(name_to_cid: dict[str, int]) -> dict[int, str]:
    """Dominant cuisine per dish from restaurant_category tags."""
    votes: dict[int, Counter] = defaultdict(Counter)
    conn = sqlite3.connect(DB)
    q = ("SELECT canonical_dish, restaurant_category FROM menu_dishes "
         "WHERE canonical_dish IS NOT NULL")
    for canon, cats in conn.execute(q):
        cid = name_to_cid.get(canon)
        if cid is None or not cats:
            continue
        for tag in cats.split(","):
            cuisine = CUISINE_MAP.get(tag.strip())
            if cuisine:
                votes[cid][cuisine] += 1
    conn.close()

    out = {}
    for cid, c in votes.items():
        # down-weight generic cuisines so a specific one wins close calls
        scored = {k: (v * 0.5 if k in GENERIC else v) for k, v in c.items()}
        out[cid] = max(scored, key=scored.get)
    return out


def main():
    print("loading v1 dish set ...")
    name_to_cid = load_v1()
    print(f"  {len(name_to_cid):,} dishes")

    # cuisine needs menu_dishes.sqlite; protein/carb only need recipes.jsonl,
    # so a host without the DB still gets a usable (cuisine-less) output.
    if DB.exists():
        print("aggregating restaurant cuisines from menu_dishes.sqlite ...")
        cuisine = cuisine_by_cluster(name_to_cid)
        print(f"  {len(cuisine):,} dishes got a cuisine")
    else:
        print(f"  WARN: {DB} not found — cuisine set to 'Other' for all "
              f"dishes.\n        Run classify_dishes.py where "
              f"menu_dishes.sqlite lives to fill cuisine in.")
        cuisine = {}

    print("classifying primary protein / carb from recipes ...")
    v1_cids = set(name_to_cid.values())
    rows = {}
    with open(RECIPES) as f:
        for line in f:
            d = json.loads(line)
            cid = d.get("cluster_id")
            if cid not in v1_cids or d.get("error"):
                continue
            ings = d.get("ingredients") or []
            rows[cid] = (primary(ings, protein_of), primary(ings, carb_of))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id", "cuisine", "protein_type", "carb_type"])
        for cid in sorted(v1_cids):
            prot, carb = rows.get(cid, ("none", "none"))
            w.writerow([cid, cuisine.get(cid, "Other"), prot, carb])

    # quick distribution print for a sanity check
    for col in ("cuisine", "protein_type", "carb_type"):
        c = Counter()
        with open(OUT) as f:
            for r in csv.DictReader(f):
                c[r[col]] += 1
        top = ", ".join(f"{k} {v:,}" for k, v in c.most_common(8))
        print(f"  {col:13s}: {top}")
    print(f"DONE — {OUT}")


if __name__ == "__main__":
    main()
