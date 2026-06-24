"""Layer 20 stage 1 — flag over-tokenized singletons (count=1, ≥5 tokens, no
recognizable dish noun) for LLM keep/drop review.

A singleton is a cluster with total_count=1 (one menu row only). The long tail
contains both real long-tail ethnic dishes (`enchiladas potosinas`, `chow mein
shrimp subgum`, etc.) and over-tokenized fragments from upstream processing
(menu codes, run-on alphabetized strings, multi-item catering listings).

Rule: if a singleton has ≥5 tokens AND none of its tokens is in the
DISH_NOUN_ALLOWLIST, flag it for LLM review. The allowlist keeps anything that
mentions a recognizable dish format/category — those are very likely real
long-tail dishes whose specifics we don't want to over-prune.

Real long-tail ethnic dishes are PROTECTED because:
  - Most are 1-3 tokens (`pongal`, `enchiladas potosinas`) → don't hit the ≥5
    threshold at all.
  - 5+ token ethnic dishes almost always include a recognizable dish noun
    (`chicken huli huli rice plate`, `boneless chicken karahi handi`).

Only the LLM is asked about the fragment-suspect set, with a strict
keep-the-real-dish rubric.

Inputs:  dish_canonical_summary_v12.csv
Outputs: long_singleton_flags.csv (singletons to send to LLM)
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

IN  = dpath("dish_canonical_summary_v12.csv")
OUT = dpath("long_singleton_flags.csv")

MIN_TOKENS = 5

DISH_NOUN_ALLOWLIST = {
    # formats / categories — if the canonical mentions any of these, it's
    # almost certainly a real composite dish, not a fragment.
    "pizza", "pizzas", "pasta", "pastas",
    "taco", "tacos", "burrito", "burritos", "quesadilla", "quesadillas",
    "tostada", "tostadas", "enchilada", "enchiladas", "fajita", "fajitas",
    "tamale", "tamales", "chimichanga", "chimichangas", "torta", "tortas",
    "sandwich", "sandwiches", "sub", "subs", "wrap", "wraps", "panini", "paninis",
    "burger", "burgers", "cheeseburger", "cheeseburgers",
    "bowl", "bowls", "plate", "plates", "platter", "platters",
    "salad", "salads", "soup", "soups", "stew", "stews", "chili",
    "curry", "curries", "tikka", "masala", "vindaloo", "korma", "biryani",
    "ramen", "udon", "soba", "pho", "lo", "mein", "chow",
    "noodle", "noodles",
    "rice", "fried", "steamed", "grilled", "roasted", "baked", "smoked",
    "wings", "tenders", "nuggets", "strips", "fingers",
    "ribs", "brisket", "steak", "chop", "chops", "loin",
    "kabob", "kebab", "skewer", "skewers", "shawarma", "gyro", "kebab",
    "sushi", "sashimi", "nigiri", "maki", "roll", "rolls",
    "dumpling", "dumplings", "potsticker", "potstickers", "wonton", "wontons",
    "spring", "egg",
    "calzone", "stromboli", "flatbread",
    "pancake", "pancakes", "waffle", "waffles", "crepe", "crepes",
    "omelet", "omelette", "frittata", "scramble",
    "bagel", "bagels", "biscuit", "biscuits", "muffin", "muffins",
    "casserole", "lasagna", "manicotti", "ravioli", "tortellini", "gnocchi",
    "risotto", "polenta", "paella",
    "dosa", "naan", "samosa", "samosas", "tandoori", "vindaloo",
    "halal", "kosher",
    "fish", "salmon", "tuna", "shrimp", "prawn", "lobster", "crab", "scallop",
    "chicken", "beef", "pork", "lamb", "turkey", "duck", "goat", "veal",
    "tofu", "vegetable", "vegetables", "veggie", "vegan", "vegetarian",
    "cheese", "mozzarella", "cheddar", "feta",
    "philly", "reuben", "cubano", "muffaletta", "po", "boy", "hoagie", "grinder",
    "fettuccine", "linguine", "spaghetti", "penne", "rigatoni", "ziti", "macaroni",
    "carbonara", "alfredo", "marinara", "pesto", "bolognese", "primavera",
    "pongal", "biryani", "korma", "paella", "moussaka", "souvlaki",
    "schnitzel", "wiener", "bratwurst", "kielbasa",
    "fajita", "carnitas", "barbacoa", "asada", "pastor", "lengua", "chorizo",
    "menudo", "pozole", "mole", "elote", "esquites",
    "huli", "loco", "moco", "spam", "musubi",
    "huevos", "rancheros", "chilaquiles", "molletes",
    "kimchi", "bibimbap", "bulgogi", "galbi", "tteokbokki",
    "pho", "banh", "nem", "goi", "bun", "com",
    "satay", "rendang", "nasi", "mie", "sambal",
    "falafel", "hummus", "shakshuka", "tagine", "couscous",
}

clusters = []
with open(IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        clusters.append((cid, row["canonical_name"], cnt))
print(f"loaded {len(clusters):,} clusters")

n_singletons = 0
n_long = 0
flagged = []
for cid, canon, cnt in clusters:
    if cnt != 1:
        continue
    n_singletons += 1
    toks = canon.split()
    if len(toks) < MIN_TOKENS:
        continue
    n_long += 1
    if any(t in DISH_NOUN_ALLOWLIST for t in toks):
        continue
    flagged.append((cid, canon, len(toks)))

print(f"singletons:                {n_singletons:,}")
print(f"  with >= {MIN_TOKENS} tokens:        {n_long:,}")
print(f"  no allowlist dish noun:  {len(flagged):,}  ← flagged for LLM")

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "n_tokens"])
    flagged.sort(key=lambda r: -r[2])
    for r in flagged:
        w.writerow(r)
print(f"\nwrote {OUT}")

print("\ntop flagged (longest first):")
for cid, canon, n in flagged[:20]:
    print(f"  [{n}] {canon}")
print("\nrandom sample:")
import random
for cid, canon, n in random.sample(flagged, min(20, len(flagged))):
    print(f"  [{n}] {canon}")
