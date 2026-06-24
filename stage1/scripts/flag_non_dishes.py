"""
Heuristically flag rows in unique_dishes_mains_only.csv that don't look like
actual unique dish names — pure format tokens ("bowl"), marketing fluff ("happy",
"special"), menu instructions ("your choice", "build your own"), deal patterns
("2 for meal"), leaked sides (fries), drinks (coffee/soda), bulk-format
(pack/bundle/kit/bucket/box), time-of-day labels, etc.

Output: unique_dishes_flagged.csv with a "proposed_exclude" column:
   "x"   = high confidence: not a dish
   "?"   = ambiguous (single format/protein word)
   ""    = looks like a real dish — keep
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

IN  = dpath("unique_dishes_mains_only.csv")
OUT = dpath("unique_dishes_flagged.csv")


# ─── X: definitely not a dish (whole name = one of these) ───
DEFINITELY_NOT_A_DISH = {
    # Time / meal periods
    "lunch", "dinner", "breakfast", "brunch", "snack", "morning", "evening",
    "afternoon", "today", "daily", "weekly", "weekend", "anytime",
    # Marketing / quality words
    "new", "fresh", "premium", "deluxe", "gourmet", "supreme", "ultimate",
    "mega", "super", "special", "signature", "classic", "original", "featured",
    "popular", "favorite", "favourites", "favorites", "best", "top", "famous",
    "homestyle", "homemade", "authentic", "traditional", "house", "chef",
    "exclusive", "elite", "select", "selected", "choice",
    # Greetings / feelings / vibes
    "happy", "hello", "welcome", "enjoy", "good", "great", "awesome",
    "amazing", "delicious", "tasty", "yummy", "fantastic", "perfect",
    # Pure menu / operational words
    "menu", "item", "items", "order", "orders", "extras", "extra",
    "catering", "party", "family", "group", "individual", "single",
    "standard", "regular",
    # Action / instruction verbs
    "pick", "choose", "build", "create", "make", "mix", "add", "your", "own",
    "yours",
    # Promo / coupon
    "deal", "deals", "value", "save", "promo", "free", "sale", "bogo",
    "limited", "offer", "offers",
    # Quantity / vessel only
    "piece", "pieces", "pc", "pcs", "ounce", "ounces", "size", "small",
    "medium", "large", "platter", "platters", "tray", "trays", "box",
    "boxes", "pack", "packs",
    # Pure descriptors with no noun
    "spicy", "mild", "hot", "cold", "sweet", "savory", "crispy", "crunchy",
    "grilled", "fried", "baked", "roasted", "smoked", "stuffed", "loaded",
    "side",
    # Other obvious junk
    "thing", "stuff", "etc", "tbd", "x", "n", "a", "b", "c",
    "dish", "dishes", "plate", "plates", "meal", "meals", "combo", "combos",
    "set", "sets", "menu",
}

# ─── ?: ambiguous — single format tokens (could be a default dish or just a label) ───
AMBIGUOUS_SINGLE_TOKEN = {
    "bowl", "bowls", "wrap", "wraps", "sub", "subs", "sandwich", "sandwiches",
    "pizza", "pizzas", "calzone", "calzones", "sushi", "taco", "tacos",
    "burrito", "burritos", "quesadilla", "quesadillas", "fajita", "fajitas",
    "salad", "salads", "pasta", "pastas", "burger", "burgers",
    "wing", "wings", "rib", "ribs", "curry", "curries", "steak", "steaks",
    "soup", "soups", "noodle", "noodles", "roll", "rolls", "dumpling",
    "dumplings", "stew", "stir fry", "fry", "fries", "chowder", "bisque",
    "stir-fry",
    # Bare protein names (often legitimate but very generic)
    "chicken", "beef", "pork", "lamb", "turkey", "ham", "tuna", "salmon",
    "shrimp", "fish", "duck", "veal", "goat", "tofu", "veggie", "vegetable",
    "vegetables", "cheese", "egg", "eggs", "rice", "potato", "potatoes",
    "noodle", "noodles", "bean", "beans",
    # Cuisines / generic styles
    "italian", "mexican", "chinese", "thai", "indian", "japanese", "korean",
    "vietnamese", "mediterranean", "greek", "asian", "american", "southern",
    "cajun", "creole", "tex-mex", "tex mex",
    # Format alone in plural/variants we missed
    "bites", "skewers", "kebab", "kebabs", "kabob", "kabobs", "tray",
}

# ─── X: multi-word menu instructions / marketing phrases (full match only) ───
DEFINITELY_NOT_PHRASES = {
    "your choice", "build own your", "build own", "build your", "your own",
    "choice your", "make own your", "make own", "make your", "create own",
    "create own your", "create your", "design own your", "design your",
    "pick day", "pick lunch", "pick of", "pick own", "pick own your",
    "pick your", "pick your own",
    "happy hour", "today special", "daily special", "house special",
    "lunch special", "dinner special", "weekend special",
    "soup day", "soup of the day",
    "deal box", "value meal", "kids meal", "kids combo",
    "mix match", "mix and match",
    "limited offer time", "limited time", "limited time offer",
    "of day", "by pound the",
    "no bready bowls", "bready", "no bready",
    "ranch chicken sandwich", "spicy sandwich", "side and sauce seasonings",
}


# Single-token additions (only drop if WHOLE name is one of these — preserves
# "french toast", "popcorn chicken", etc.)
DEFINITELY_NOT_A_DISH |= {
    "toast", "popcorn", "oatmeal", "granola", "cereal", "yogurt", "parfait",
    "jerky", "crackers", "pretzel", "pretzels", "muffin", "donut", "donuts",
    "cookie", "cookies", "brownie", "brownies", "cupcake", "cupcakes",
    "bagel", "bagels", "scone", "scones", "danish", "croissant", "croissants",
    "pastry", "pastries", "fries", "chips", "tots",
    # fruits / single ingredients
    "apple", "banana", "orange", "grape", "grapes", "berry", "berries",
    "fruit", "fruits", "watermelon", "pineapple", "mango", "strawberry",
    # drinks
    "lemonade", "smoothie", "smoothies", "shake", "shakes", "milkshake",
    "milkshakes", "milk", "water", "tea", "soda", "sodas", "beverages",
    "beverage", "drinks", "drink", "coffee", "espresso", "latte", "cappuccino",
    "mocha", "frappuccino", "frappe", "macchiato", "chai", "matcha",
    # alcohol
    "beer", "wine", "champagne", "cocktail", "cocktails", "margarita", "mojito",
    # dessert
    "ice", "gelato", "sundae", "sorbet", "froyo", "custard", "fudge", "candy",
    "chocolate", "pie",
    # bulk
    "pack", "bundle", "kit", "variety", "tote", "bucket", "kcup", "k-cup",
    # other
    "tray",
}

# Any-match regex patterns. If any one matches → drop as 'x'. These are
# unambiguous junk regardless of where they appear.
ALWAYS_FLAG_REGEX = [
    # ─── Deal / promo patterns ───
    re.compile(r"^\d+\s+for\b", re.I),  # "2 for ...", "4 for ..."
    re.compile(r"\bfor\s+(meal|wings|tenders|sushi|pasta|drinks?|combo|burritos?|enchiladas?|tacos?|fajitas?|night|nights|lunch|picnic|margaritas?|chicken|beef|one|two|three|four|five|six|seven|eight|nine|ten)\b", re.I),
    re.compile(r"\bbuy\s+\d+\s+get\b", re.I),
    re.compile(r"\bbogo\b", re.I),

    # ─── Sides (sneaked through L2) ───
    re.compile(r"\bfries\b", re.I),
    re.compile(r"\bmozzarella\s+sticks\b", re.I),
    re.compile(r"\bonion\s+rings?\b", re.I),
    re.compile(r"\btater\s*tots?\b", re.I),
    re.compile(r"\bhush\s*puppies\b", re.I),
    re.compile(r"\bbread\s*sticks?\b", re.I),
    re.compile(r"\bbreadsticks?\b", re.I),
    re.compile(r"\bgarlic\s*bread\b", re.I),
    re.compile(r"\bjalapeno\s*poppers?\b", re.I),
    re.compile(r"\bpotato\s+chips\b", re.I),

    # ─── Drinks: coffee family ───
    re.compile(r"\bcoffee\b", re.I),
    re.compile(r"\blatte\b", re.I),
    re.compile(r"\bcappuccino\b", re.I),
    re.compile(r"\bespresso\b", re.I),
    re.compile(r"\bmacchiato\b", re.I),
    re.compile(r"\bmocha\b", re.I),
    re.compile(r"\bfrappuccino\b", re.I),
    re.compile(r"\bfrapp(?:e|es)?\b", re.I),
    re.compile(r"\bchai\b", re.I),
    re.compile(r"\bmatcha\b", re.I),
    re.compile(r"\bcold\s+brew\b", re.I),

    # ─── Drinks: sodas / brand drinks / juices ───
    re.compile(r"\bbeverages?\b", re.I),
    re.compile(r"\bsodas?\b", re.I),
    re.compile(r"\bpepsi\b", re.I),
    re.compile(r"\bcoke\b", re.I),
    re.compile(r"\bcoca[\s-]*cola\b", re.I),
    re.compile(r"\bsprite\b", re.I),
    re.compile(r"\bfanta\b", re.I),
    re.compile(r"\bdr\s*pepper\b", re.I),
    re.compile(r"\bmountain\s*dew\b", re.I),
    re.compile(r"\b(?:7[-\s]?up|root\s*beer|ginger\s*ale)\b", re.I),
    re.compile(r"\blemonade\b", re.I),
    re.compile(r"\b(?:iced|hot)\s+tea\b", re.I),
    re.compile(r"\bbottled?\s+water\b", re.I),
    re.compile(r"\bsmoothies?\b", re.I),
    re.compile(r"\bmilkshakes?\b", re.I),
    re.compile(r"\bjuices?\b", re.I),  # "juice apple", "fresh juice"

    # ─── Frozen drinks / shakes ───
    re.compile(r"\bfrosty\b", re.I),
    re.compile(r"\bslushy?\b", re.I),
    re.compile(r"\bslushies?\b", re.I),
    re.compile(r"\bslush\b", re.I),
    re.compile(r"\bicee?\b", re.I),
    re.compile(r"\bgranita\b", re.I),
    re.compile(r"\bfloat\b", re.I),  # root beer float etc.

    # ─── Desserts ───
    re.compile(r"\bcinnabon\b", re.I),
    re.compile(r"\bdelights?\b", re.I),
    re.compile(r"\bdonuts?\b", re.I),
    re.compile(r"\bdoughnuts?\b", re.I),
    re.compile(r"\bcookies?\b", re.I),
    re.compile(r"\bbrownies?\b", re.I),
    re.compile(r"\bcupcakes?\b", re.I),
    re.compile(r"\bcheesecakes?\b", re.I),
    re.compile(r"\bcannoli\b", re.I),
    re.compile(r"\btiramisu\b", re.I),
    re.compile(r"\bmacarons?\b", re.I),
    re.compile(r"\beclairs?\b", re.I),
    re.compile(r"\bbaklava\b", re.I),
    re.compile(r"\bice\s*cream\b", re.I),
    re.compile(r"\bgelato\b", re.I),
    re.compile(r"\bsundaes?\b", re.I),
    re.compile(r"\bsorbet\b", re.I),
    re.compile(r"\bfrozen\s+yogurt\b", re.I),
    re.compile(r"\bfroyo\b", re.I),
    re.compile(r"\bdanish\b", re.I),
    re.compile(r"\bscones?\b", re.I),
    re.compile(r"\bcroissants?\b", re.I),
    re.compile(r"\bchurros?\b", re.I),
    re.compile(r"\bcustard\s+frozen\b", re.I),  # frozen custard
    re.compile(r"\bfrozen\s+custard\b", re.I),
    re.compile(r"\bfudge\b", re.I),
    re.compile(r"\btruffles?\b", re.I),
    re.compile(r"\bbiscotti\b", re.I),
    # specific dessert pies
    re.compile(r"\bapple\s+pie\b", re.I),
    re.compile(r"\bcherry\s+pie\b", re.I),
    re.compile(r"\bpecan\s+pie\b", re.I),
    re.compile(r"\bpumpkin\s+pie\b", re.I),
    re.compile(r"\bkey\s+lime\s+pie\b", re.I),
    re.compile(r"\b(banana|chocolate|coconut|cream|lemon|lime)\s+(pie|cream)\b", re.I),

    # ─── Snack-bars / breakfast snacks ───
    re.compile(r"\bbagels?\b", re.I),
    re.compile(r"\bbar\s+(oatmeal|granola|protein|yogurt|cereal|cinnamon|chocolate|nut|fruit)\b", re.I),
    re.compile(r"\b(oatmeal|granola|protein|yogurt|cereal|cinnamon|chocolate|nut|fruit)\s+bar\b", re.I),
    re.compile(r"\bcinnamon\s+rolls?\b", re.I),
    re.compile(r"\bcinnamon\s+twist\b", re.I),

    # ─── Bulk / pack format ───
    re.compile(r"\bpacks?\b", re.I),
    re.compile(r"\bbundles?\b", re.I),
    re.compile(r"\bkits?\b", re.I),
    re.compile(r"\bvariety\b", re.I),
    re.compile(r"\btote\b", re.I),
    re.compile(r"\bbucket\b", re.I),
    re.compile(r"\bbox\b", re.I),
    re.compile(r"\bk[-\s]?cups?\b", re.I),
]


def classify(name: str) -> str:
    if not name:
        return "x"
    toks = name.split()
    # single-token check
    if len(toks) == 1:
        t = toks[0]
        if t in DEFINITELY_NOT_A_DISH:
            return "x"
        if t in AMBIGUOUS_SINGLE_TOKEN:
            return "?"
        if len(t) <= 2 and not t.isdigit():
            return "x"
        return ""
    # multi-word: phrase blacklist
    if name in DEFINITELY_NOT_PHRASES:
        return "x"
    # all tokens are non-dish words → still junk
    if all(t in DEFINITELY_NOT_A_DISH for t in toks):
        return "x"
    # "build/pick/make/create + your/own" instruction patterns
    s = " " + name + " "
    has_verb = any(v in s for v in (" pick ", " build ", " make ", " create ", " choose ", " design "))
    has_pron = any(p in s for p in (" your ", " own ", " yours "))
    if has_verb and has_pron:
        return "x"
    # any of the always-flag regexes match
    for pat in ALWAYS_FLAG_REGEX:
        if pat.search(name):
            return "x"
    return ""


def main():
    counts = {"x": 0, "?": 0, "": 0}
    rows = []
    with open(IN) as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if not row:
                continue
            name = row[0]
            cnt = row[1] if len(row) > 1 else ""
            flag = classify(name)
            counts[flag] += 1
            rows.append([flag, name, cnt])

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["proposed_exclude", "normalized_name", "count"])
        # Put flagged rows first (x then ?), then keepers — sorted within each by count desc
        rows.sort(key=lambda r: (
            {"x": 0, "?": 1, "": 2}[r[0]],
            -int(r[2]) if r[2].isdigit() else 0
        ))
        w.writerows(rows)

    total = sum(counts.values())
    print(f"total rows: {total:,}")
    print(f"  marked X (definitely not a dish) : {counts['x']:>7,}  ({100*counts['x']/total:.1f}%)")
    print(f"  marked ? (ambiguous)             : {counts['?']:>7,}  ({100*counts['?']/total:.1f}%)")
    print(f"  unmarked (looks like a dish)     : {counts['']:>7,}  ({100*counts['']/total:.1f}%)")
    print(f"\nwrote {OUT}")

    print("\n=== sample of X-flagged (top 30 by frequency) ===")
    n = 0
    for flag, name, cnt in rows:
        if flag == "x":
            print(f"  {cnt:>6}  {name}")
            n += 1
            if n >= 30: break
    print("\n=== sample of ?-flagged (top 30 by frequency) ===")
    n = 0
    for flag, name, cnt in rows:
        if flag == "?":
            print(f"  {cnt:>6}  {name}")
            n += 1
            if n >= 30: break


if __name__ == "__main__":
    main()
