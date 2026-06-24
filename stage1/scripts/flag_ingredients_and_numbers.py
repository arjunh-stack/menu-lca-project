"""Layer 11 pre-pass — flag two classes of canonicals for removal:

A) BARE INGREDIENTS: single-token (or 2-token compound like "red snapper",
   "mahi mahi") names that are just an ingredient/cut/fish, not a dish you
   can search a recipe for.

B) REDUNDANT NUMBER VARIANTS: names like "12 piece nuggets" / "10pc wings"
   where stripping the number+unit yields a name that already exists as
   another canonical. These are the same dish at different sizes — keep one.

C) BY-PREFIX FRAGMENTS: names starting with "by " ("by chicken piece",
   "by pork pound pulled") — leftover bulk-pricing copy ("by the pound").

Output: ingredients_and_numbers_review.csv
  cluster_id, canonical_name, total_count, verdict, reason

User reviews/edits this CSV, then run apply_ingredients_and_numbers.py to drop
the verdict='drop' rows.
"""

# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import csv
import re

IN  = dpath("dish_canonical_summary_v2.csv")
OUT = dpath("ingredients_and_numbers_review.csv")

# ----- Curated bare-ingredient list (DROP these single-tokens / 2-token compounds) -----
# Bare proteins/cuts/seafood/vegetables that are NOT dishes on their own.
# Cuts of meat: ribeye, filet — these are how you'd order a steak, but the
# "dish" is the steak prep. Bare cut name = not a dish.
BARE_INGREDIENTS = {
    # Fish/seafood (single-token)
    "salmon", "tuna", "cod", "tilapia", "halibut", "swordfish", "branzino",
    "snapper", "redfish", "trout", "mackerel", "sardine", "sardines",
    "anchovy", "anchovies", "haddock", "pollock", "flounder", "sole",
    "grouper", "mahi", "monkfish", "perch", "pike", "walleye", "bass",
    "catfish", "smelts", "smelt",
    # Shellfish
    "shrimp", "prawn", "prawns", "lobster", "crab", "scallop", "scallops",
    "mussel", "mussels", "clam", "clams", "oyster", "oysters", "crayfish",
    "crawfish", "octopus", "squid", "calamari", "abalone",
    # Meat cuts
    "ribeye", "sirloin", "tenderloin", "filet", "strip", "porterhouse",
    "tbone", "chuck", "brisket", "flank", "skirt", "shank", "shoulder",
    "rump", "round", "loin", "chop", "chops", "rib", "ribs",
    # Bare proteins (when alone)
    "beef", "chicken", "pork", "lamb", "veal", "duck", "turkey", "goat",
    "rabbit", "venison", "bison", "quail", "pheasant",
    # Vegetables (alone)
    "broccoli", "cauliflower", "asparagus", "spinach", "kale", "arugula",
    "carrot", "carrots", "potato", "potatoes", "onion", "onions", "tomato",
    "tomatoes", "pepper", "peppers", "mushroom", "mushrooms", "zucchini",
    "squash", "eggplant", "cucumber", "lettuce", "cabbage", "celery",
    "beet", "beets", "radish", "turnip", "leek", "leeks", "garlic", "shallot",
    "corn", "peas", "beans", "lentils", "chickpeas",
    # Fruits
    "apple", "orange", "lemon", "lime", "banana", "strawberry", "blueberry",
    "raspberry", "watermelon", "cantaloupe", "pineapple", "mango", "papaya",
    # Misc bare ingredients
    "rice", "pasta", "noodles", "bread", "tortilla", "tortillas", "cheese",
    "egg", "eggs", "tofu", "tempeh", "seitan",
}

# 2-token bare seafood names (compound names that are still just the fish)
BARE_INGREDIENTS_2TOK = {
    "red snapper", "mahi mahi", "sea bass", "chilean bass", "dover sole",
    "rainbow trout", "king crab", "snow crab", "soft shell crab",
    "sea scallops", "bay scallops", "tiger shrimp", "rock shrimp",
    "blue crab", "stone crab", "yellowtail tuna", "ahi tuna", "yellowfin tuna",
    "bigeye tuna", "bluefin tuna", "atlantic salmon", "king salmon",
    "sockeye salmon", "coho salmon", "chinook salmon",
    # Cuts
    "filet mignon", "ribeye steak", "ny strip", "new york strip",
    "porterhouse steak", "t bone", "skirt steak", "flank steak",
    "lamb chop", "lamb chops", "pork chop", "pork chops", "veal chop",
    "prime rib", "short rib", "short ribs", "baby back",
}

# Real dishes that happen to be 1 token — KEEP these even though they're 1 token
KEEP_SINGLE_TOKENS = {
    "burger", "cheeseburger", "pizza", "calzone", "stromboli", "pasta",
    "lasagna", "lasagne", "spaghetti", "ravioli", "gnocchi", "carbonara",
    "tiramisu",  # if not dropped earlier
    "enchiladas", "tacos", "taco", "burritos", "burrito", "quesadilla",
    "quesadillas", "tamales", "tostadas", "tostada", "sopes", "gorditas",
    "chimichanga", "chimichangas", "flautas", "flauta", "chilaquiles",
    "menudo", "pozole", "birria", "mole", "fajitas", "carnitas",
    "elote", "esquite", "horchata", "ceviche",
    "sushi", "sashimi", "tempura", "ramen", "udon", "soba", "yakitori",
    "yakisoba", "okonomiyaki", "takoyaki", "donburi", "katsu", "tonkatsu",
    "gyoza", "edamame",
    "pho", "banhmi", "bibimbap", "bulgogi", "japchae", "tteokbokki",
    "kimchi", "kimbap", "samgyeopsal",
    "biryani", "tikka", "vindaloo", "korma", "saag", "daal", "dal",
    "naan", "samosa", "samosas", "pakora", "pakoras", "dosa", "idli",
    "falafel", "shawarma", "kebab", "kebabs", "kofta", "tagine",
    "hummus", "baba", "tabbouleh", "fattoush", "kibbeh",
    "paella", "tortellini", "minestrone", "risotto", "bruschetta",
    "schnitzel", "wurst", "spaetzle", "sauerbraten", "goulash",
    "borscht", "pierogi", "pierogies",
    "bibingka", "lumpia", "adobo", "sinigang", "lechon",
    "mcnuggets", "wings", "tenders", "nuggets",  # already common shorthand
    "bbq", "blt", "philly", "reuben", "monte cristo", "po boy", "poboy",
    "club", "clubhouse", "patty melt", "patty",
    "pancakes", "pancake", "waffles", "waffle", "crepes", "crepe",
    "frenchtoast", "omelet", "omelette", "frittata", "quiche", "huevos",
    "eggsbenedict", "benedict",
    "meatloaf", "meatballs", "stew", "chili", "chowder", "gumbo", "jambalaya",
    "etouffee", "bouillabaisse", "cassoulet", "ratatouille", "coqauvin",
    "porchetta", "saltimbocca", "ossobuco", "scampi", "milanese",
    "pierogi", "spanakopita", "moussaka", "souvlaki", "dolma", "dolmas",
    "gyro", "gyros",
    "torta", "tortas", "wrap", "wraps", "sub", "subs", "hoagie", "sandwich",
    "panini",
    "cheesesteak", "philly cheesesteak",
    "rotisserie",
    "salad", "soup",
    "nachos", "fries",
}

# Number patterns. Names are token-sorted alphabetically, so "12pc nuggets" might
# appear as "12pc nuggets" but "8 piece dinner" appears as "8 dinner piece" etc.
NUM_PURE_TOKEN = re.compile(r"^\d+$")                # standalone digit token
NUM_PC_TOKEN   = re.compile(r"^\d+(pc|pcs)$", re.I)  # "12pc" as a single token
PIECE_TOKEN    = re.compile(r"^(pc|pcs|piece|pieces)$", re.I)
INCH_TOKEN     = re.compile(r"^(inch|in|inches)$", re.I)
NUM_PC_INFIX = re.compile(r"\b\d+\s*(pc|pcs|pieces?|piece)\b", re.I)
PURE_NUM_TOKEN = re.compile(r"^\d+$")

def strip_number_tokens(name):
    """Strip ALL number tokens (digit, Npc, piece/pieces/pc/pcs, inch/in/inches)
    from the name and return the remaining tokens re-sorted alphabetically.
    Returns None if no number tokens were stripped."""
    toks = name.split()
    new_toks = []
    stripped_any = False
    for t in toks:
        if (NUM_PURE_TOKEN.match(t) or NUM_PC_TOKEN.match(t) or
            PIECE_TOKEN.match(t) or INCH_TOKEN.match(t)):
            stripped_any = True
            continue
        new_toks.append(t)
    if not stripped_any:
        return None
    new_toks.sort()  # canonical form is alphabetized
    return " ".join(new_toks)

def has_digit(name):
    return any(c.isdigit() for c in name)

# ----- Load all canonical names -----
clusters = []
canonical_set = set()
with open(IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        canon = row["canonical_name"]
        clusters.append((cid, canon, cnt))
        canonical_set.add(canon)
print(f"loaded {len(clusters):,} clusters")

# ----- Classify each cluster -----
def classify(canon):
    toks = canon.split()
    n = len(toks)

    # Pass A: bare ingredients
    if n == 1 and toks[0] in BARE_INGREDIENTS and toks[0] not in KEEP_SINGLE_TOKENS:
        return "drop", f"bare_ingredient_1tok ({toks[0]})"
    if n == 1 and toks[0] not in KEEP_SINGLE_TOKENS:
        # Single token that's not in our keep list AND not in bare-ingredients
        # → ambiguous; flag for review (keep by default)
        return "review", "single_token_not_listed"
    if canon in BARE_INGREDIENTS_2TOK:
        return "drop", f"bare_ingredient_2tok"

    # Pass C: by-prefix fragments
    if toks and toks[0] == "by":
        return "drop", "by_prefix_fragment"

    # Pass B: redundant number variants
    if has_digit(canon):
        stripped = strip_number_tokens(canon)
        if stripped and stripped in canonical_set and stripped != canon:
            return "drop", f"redundant_with: {stripped}"
        # Stripped form is empty or only 1 token left → fragment after strip
        if stripped is not None and (not stripped or len(stripped.split()) <= 1):
            # If the residue is 1 token and is itself a known KEEP single, mark redundant with that
            if stripped and stripped in canonical_set:
                return "drop", f"redundant_with: {stripped}"
            return "drop", "fragment_after_number_strip"
        # No match — mark for review
        return "review", "has_digit_no_match"

    return "keep", "ok"

verdicts = []
for cid, canon, cnt in clusters:
    v, r = classify(canon)
    verdicts.append((cid, canon, cnt, v, r))

# ----- Stats -----
from collections import Counter
v_counts = Counter(v for _, _, _, v, _ in verdicts)
print(f"\nverdict counts:")
for v, n in v_counts.most_common():
    print(f"  {v:>8}: {n:>7,}")

reason_counts = Counter(r.split(":")[0].split("(")[0].strip() for _, _, _, v, r in verdicts if v != "keep")
print(f"\nreason counts (drop+review):")
for r, n in reason_counts.most_common():
    print(f"  {r:>30}: {n:>7,}")

# ----- Write review CSV -----
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "verdict", "reason"])
    # Sort: drops first (by count desc), then review (by count desc), then keeps
    order = {"drop": 0, "review": 1, "keep": 2}
    verdicts.sort(key=lambda r: (order[r[3]], -r[2]))
    for r in verdicts:
        w.writerow(r)
print(f"\nwrote {OUT}")
