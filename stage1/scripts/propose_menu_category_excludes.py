"""
Propose menu categories to EXCLUDE for a "main dishes only" view.

Inputs: cleaned db (after C1-C5), Layer 1 filter applied.
Output:
  - proposed_menu_category_excludes.csv  (categories to drop, with reason + row count)
  - proposed_menu_category_ambiguous.csv (need user judgment)
Summary printed: how many menu rows each bucket affects.
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

import sqlite3
import csv
import html
import re
from collections import defaultdict

DB = dpath("mydb.sqlite")
EXCLUDE_FILE = dpath("unique_categories_to_exclude.csv")
OUT_EXCL = dpath("proposed_menu_category_excludes.csv")
OUT_AMB  = dpath("proposed_menu_category_ambiguous.csv")


# ─── EXCLUDE keywords (clearly NOT a main dish) ───
# Each entry: (regex pattern, label). Use word-boundary patterns to avoid false matches.
# Tested against lowercased category strings.
EXCLUDE_PATTERNS = [
    # Beverages
    (r"\b(beverage|beverages|drink|drinks|drinkable|liquids?)\b", "drinks"),
    (r"\b(coffee|tea|espresso|latte|mocha|cappuccino|americano|macchiato|chai|matcha)\b", "coffee/tea"),
    (r"\b(soda|pop|cola|soft\s*drink|fountain|bubbly|sparkling)\b", "soda"),
    (r"\b(juice|juices|lemonade|limeade|punch|slushie|slushies|slush|aguas?\s*frescas?|horchata)\b", "juice"),
    (r"\b(smoothie|smoothies|shake|shakes|milkshake|milkshakes|frappe|frappes?|frappuccino)\b", "smoothie/shake"),
    (r"\b(water|waters|bottled\s*water|sparkling\s*water|spring\s*water|seltzer)\b", "water"),
    (r"\b(beer|wine|liquor|cocktail|cocktails|spirits|sake|champagne|mimosa|margarita|mojito|sangria|whiskey|vodka|tequila|rum|bourbon|scotch|gin|aperitif|digestif|brewery|alcohol|alcoholic|booze|hard\s*seltzer|spritzer|lager|ale|ipa|stout|pilsner|porter|cider|prosecco|martini)\b", "alcohol"),
    (r"\b(boba|bubble\s*tea|tapioca\s*tea|milk\s*tea)\b", "bubble tea"),
    (r"\b(hot\s*chocolate|cocoa|hot\s*cocoa|chocolate\s*milk)\b", "hot chocolate"),
    (r"\b(slushy|icee|frozen\s*drink|granita|granitas?)\b", "frozen drink"),

    # Desserts / sweets
    (r"\b(dessert|desserts|sweets?|sweet\s*treats?|treats?)\b", "dessert"),
    (r"\b(ice\s*cream|frozen\s*yogurt|fro[-\s]?yo|gelato|sorbet|sherbet|soft\s*serve|sundae|sundaes)\b", "ice cream"),
    (r"\b(cake|cakes|cupcake|cupcakes|brownie|brownies|cookie|cookies|pie|pies|donut|donuts|doughnut|doughnuts|pastry|pastries|muffin|muffins|tart|tarts|cannoli|tiramisu|cheesecake|baklava|churros?|funnel\s*cake|gulab\s*jamun|mochi)\b", "baked sweet"),
    (r"\b(candy|candies|chocolate(?!\s*chip)|fudge|truffle|truffles|gummy|gummies|jelly\s*beans?|lollipop)\b", "candy"),
    (r"\b(croissant|croissants|scone|scones|danish|biscotti|macaron|macarons|eclair|eclairs|profiterole)\b", "pastry"),

    # Sides
    (r"\b(side|sides|side\s*order|side\s*orders|side\s*dish|side\s*dishes|on\s*the\s*side)\b", "side"),
    (r"\b(fries|french\s*fries|tater\s*tots?|onion\s*rings)\b", "fries (often side)"),

    # Appetizers / starters / snacks
    (r"\b(appetizer|appetizers|app|apps|starter|starters|first\s*course|small\s*plate|small\s*plates|tapas|antipasti|antipasto|amuse\s*bouche|nibbles?|finger\s*foods?)\b", "appetizer/starter"),
    (r"\b(snack|snacks|chips|chip|crackers?|popcorn|trail\s*mix|nuts|jerky|granola\s*bar)\b", "snack"),

    # Add-ons / sauces / modifiers
    (r"\b(sauce|sauces|dressing|dressings|dipping|dip|dips|topping|toppings|condiment|condiments|spread|spreads|garnish|garnishes)\b", "sauce/condiment"),
    (r"\b(add[-\s]?on|add[-\s]?ons|extras?|modifier|modifiers|customize|customise|customization|build\s*your\s*own\s*topping|additional)\b", "addon/modifier"),
    # bread: tightened — don't match "sushi rolls", "spring rolls", "lobster rolls"
    (r"\b(breads?|bagels?|pretzels?|breadsticks?|garlic\s*bread|dinner\s*rolls?|bread\s*rolls?|hawaiian\s*rolls?|hot\s*dog\s*buns?|hamburger\s*buns?|burger\s*buns?|loaf|loaves|baguette|focaccia)\b", "bread"),

    # Kids
    (r"\b(kids?|kid's|children|children's|junior(?!\s*size)|jr\.?|lil'?|little\s*ones?|tots?\s*menu)\b", "kids menu"),

    # App / delivery surfaced (not a real category)
    (r"\b(picked\s*for\s*you|featured|popular|most\s*popular|trending|recommended|top\s*picks?|best\s*sellers?|fan\s*favorites?|new\s*items?|new\s*menu|customer\s*favorites?|chefs?\s*picks?|staff\s*picks?|seasonal)\b", "delivery-app surfaced"),

    # Catering / bulk (not a single-person main dish)
    (r"\b(catering|party\s*pack|party\s*tray|party\s*platter|trays?|family\s*meal|family\s*pack|family\s*size|family\s*style|bulk|by\s*the\s*pound|by\s*the\s*tray|group\s*order|groups?\s*meal|hot\s*tray|cold\s*tray|whole\s*tray|half\s*tray)\b", "catering/family pack"),

    # Non-restaurant retail leakage (in case Layer 1 missed any)
    (r"\b(grocery|groceries|convenience|household|personal\s*care|beauty|cosmetics|baby|pet|pets|tobacco|vape|cigarettes?|cigars?|magazines?|gift\s*cards?|stamps?|lottery|atm|stationery|hardware|flowers|floral)\b", "non-food retail"),
    (r"\b(pharmacy|otc|over[-\s]?the[-\s]?counter|first\s*aid|vitamins?|supplements?|medicine|medication|allergy|cold\s*and\s*flu)\b", "pharmacy"),

    # Other clearly-not-mains
    (r"\b(jam|jams|jelly|jellies|preserves|honey|syrup|syrups|butter|butters|spread)\b", "spread/preserves"),
    (r"\b(merchandise|merch|apparel|t[-\s]?shirts?|hats|mugs|swag|gear)\b", "merchandise"),
    (r"\b(gift\s*card|giftcard|gift\s*certificate)\b", "gift card"),
]

# ─── AMBIGUOUS keywords (could be a main or not — needs user judgment) ───
AMBIGUOUS_PATTERNS = [
    (r"\b(combo|combos|combo\s*meal|combo\s*meals|meal\s*deal|meal\s*deals|value\s*meal|set\s*meal|set\s*menu)\b", "combo (incl. main)"),
    (r"\b(soup|soups|broth|chowder|bisque|stew|stews|gumbo|pho|ramen)\b", "soup (sometimes main)"),
    (r"\b(salad|salads)\b", "salad (sometimes main)"),
    (r"\b(special|specials|daily\s*special|today's\s*special|chef's?\s*special)\b", "specials"),
    (r"\b(a\s*la\s*carte|a-la-carte|alacarte)\b", "a la carte"),
    (r"\b(build\s*your\s*own|byo|create\s*your\s*own|design\s*your\s*own)\b", "build your own"),
    (r"\b(deal|deals|promotion|promotions|promo|promos|special\s*offer|limited\s*time)\b", "deals"),
    (r"\b(brunch)\b", "brunch (mains+sides)"),
    (r"\b(individual\s*items?|individual)\b", "individual items"),
    (r"\b(sushi\s*roll|maki|nigiri|sashimi|temaki|hand\s*roll)\b", "sushi pieces (often shared)"),
]


def load_exclude_tags():
    tags = set()
    with open(EXCLUDE_FILE) as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) >= 2 and row[1].strip().lower() == "x":
                tags.add(html.unescape(row[0]).strip())
    return tags


def excluded_ids(con, exclude):
    cur = con.cursor()
    cur.execute("SELECT id, category FROM restaurants WHERE category IS NOT NULL AND category != ''")
    bad = set()
    for rid, cat in cur:
        tags = {t.strip() for t in cat.split(",")}
        if tags & exclude:
            bad.add(rid)
    return bad


def classify(cat: str):
    low = cat.lower()
    for pat, label in EXCLUDE_PATTERNS:
        if re.search(pat, low):
            return ("exclude", label)
    for pat, label in AMBIGUOUS_PATTERNS:
        if re.search(pat, low):
            return ("ambiguous", label)
    return ("keep", "")


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    bad = excluded_ids(con, load_exclude_tags())
    cur.execute("DROP TABLE IF EXISTS _bad")
    cur.execute("CREATE TEMP TABLE _bad (id INTEGER PRIMARY KEY)")
    cur.executemany("INSERT INTO _bad VALUES (?)", ((i,) for i in bad))

    cur.execute("""
        SELECT category, COUNT(*) AS n
        FROM menus
        WHERE category IS NOT NULL AND category != ''
          AND restaurant_id NOT IN (SELECT id FROM _bad)
        GROUP BY category
    """)
    rows = cur.fetchall()

    buckets = defaultdict(list)  # bucket → [(category, n, label)]
    bucket_total_rows = defaultdict(int)
    for cat, n in rows:
        bucket, label = classify(cat)
        buckets[bucket].append((cat, n, label))
        bucket_total_rows[bucket] += n

    # write outputs
    with open(OUT_EXCL, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["proposed_exclude", "menu_category", "menu_rows", "matched_reason"])
        for cat, n, label in sorted(buckets["exclude"], key=lambda x: -x[1]):
            w.writerow(["x", cat, n, label])

    with open(OUT_AMB, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["should_exclude_(x_or_blank)", "menu_category", "menu_rows", "matched_reason"])
        for cat, n, label in sorted(buckets["ambiguous"], key=lambda x: -x[1]):
            w.writerow(["", cat, n, label])

    print(f"\n=== summary (Layer-1 filtered set: {sum(n for _,n in rows):,} menu rows, {len(rows):,} distinct categories) ===")
    for b in ("exclude", "ambiguous", "keep"):
        print(f"  {b:>10}: {len(buckets[b]):>6,} categories  →  {bucket_total_rows[b]:>10,} menu rows")
    print(f"\nwrote: {OUT_EXCL}")
    print(f"wrote: {OUT_AMB}")

    print("\n=== top 30 EXCLUDE proposals (by menu rows) ===")
    for cat, n, label in sorted(buckets["exclude"], key=lambda x: -x[1])[:30]:
        print(f"  {n:>8,}  [{label:<25s}]  {cat}")

    print("\n=== top 30 AMBIGUOUS (need your call) ===")
    for cat, n, label in sorted(buckets["ambiguous"], key=lambda x: -x[1])[:30]:
        print(f"  {n:>8,}  [{label:<28s}]  {cat}")


if __name__ == "__main__":
    main()
