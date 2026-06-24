#!/usr/bin/env python3
"""Classify menu items in chunk_14.csv as keep/drop with reason."""

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

INPUT = dpath("chunks/chunk_14.csv")
OUTPUT = dpath("chunks_classified/chunk_14_classified.csv")

# === Keyword sets ===

DRINK_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappe", "frappuccino",
    "frap", "chai", "soda", "juice", "smoothie", "milkshake", "shake", "shakes",
    "beer", "wine", "cocktail", "lemonade", "tea", "water", "slushie", "slush",
    "slushy", "icee", "americano", "macchiato", "cortado", "drink", "drinks",
    "beverage", "beverages", "cola", "coke", "pepsi", "sprite", "fanta",
    "dr pepper", "mountain dew", "redbull", "energy", "mocktail", "milk",
    "horchata", "agua", "aguas", "kombucha", "cider", "margarita", "mimosa",
    "sangria", "martini", "mojito", "punch", "refresher", "refreshers",
    "spritzer", "highball", "lowball", "shot", "vodka", "rum", "whiskey",
    "whisky", "tequila", "gin", "bourbon", "scotch", "brandy", "champagne",
    "prosecco", "lassi", "boba", "bubble", "milktea", "ade", "limeade",
    "orangeade", "snapple", "gatorade", "powerade", "espresso", "ristretto",
    "lungo", "flat white", "matcha", "redbull",
}

DESSERT_TOKENS = {
    "cake", "cakes", "cookie", "cookies", "brownie", "brownies", "cupcake",
    "cupcakes", "cinnabon", "donut", "donuts", "doughnut", "doughnuts",
    "ice cream", "icecream", "gelato", "sundae", "sundaes", "sorbet",
    "cheesecake", "pie", "pies", "custard", "churro", "churros", "tiramisu",
    "cannoli", "pudding", "mousse", "macaron", "macarons", "macaroon",
    "macaroons", "tart", "tarts", "eclair", "eclairs", "baklava", "scone",
    "scones", "muffin", "muffins", "danish", "danishes", "pastry", "pastries",
    "biscotti", "fudge", "candy", "candies", "chocolate bar", "truffle",
    "truffles", "praline", "pralines", "gummy", "gummies", "lollipop",
    "lollipops", "marshmallow", "marshmallows", "frosting", "icing",
    "sprinkles", "whipped cream", "milkshake", "float", "floats", "parfait",
    "popsicle", "popsicles", "creme brulee", "flan", "rice pudding",
    "bread pudding", "cobbler", "crumble", "crisp", "strudel", "kolache",
    "kolaches", "beignet", "beignets", "fritter", "fritters", "halo halo",
    "shave ice", "shaved ice", "snow cone", "snow cones", "rolled ice",
    "concrete", "blizzard", "mcflurry", "dilly bar", "dipped cone",
    "bismark", "bismarks", "cinnamon roll", "cinnamon rolls", "cinnamon stick",
    "cinnamon sticks", "stickbun", "stickbuns",
}

SIDE_TOKENS = {
    "fries", "fry", "frie",  # any fries
    "rings",  # onion rings
    "sticks",  # mozzarella sticks, breadsticks, cheese sticks
    "tots",
    "puppies",  # hush puppies
    "breadstick", "breadsticks",
    "garlic bread",
    "poppers",  # jalapeno poppers
    "side salad",
    "coleslaw", "slaw",
    "applesauce",
    "mashed potatoes", "mash",
    "biscuit", "biscuits",
    "cornbread", "corn bread",
    "hash brown", "hash browns", "hashbrown", "hashbrowns",
}

SAUCE_TOKENS = {
    "sauce", "sauces", "dressing", "dressings", "dip", "dips", "marinara",
    "ranch", "honey mustard", "bbq sauce", "ketchup", "mayo", "mayonnaise",
    "aioli", "vinaigrette", "salsa", "guacamole", "queso", "hummus", "tahini",
    "pesto", "tapenade", "chutney", "relish", "tartar", "remoulade", "gravy",
    "syrup", "jam", "jelly", "preserves", "honey", "butter",
}

INGREDIENT_TOKENS = {
    "cheese", "bacon", "mushroom", "mushrooms", "onion", "onions", "tofu",
    "tomato", "tomatoes", "lettuce", "spinach", "kale", "cucumber", "pickle",
    "pickles", "olive", "olives", "pepper", "peppers", "jalapeno", "jalapenos",
    "carrot", "carrots", "celery", "broccoli", "cauliflower", "potato",
    "potatoes", "rice", "beans", "bean", "corn", "egg", "eggs", "ham", "salami",
    "pepperoni", "sausage", "chorizo", "turkey", "chicken", "beef", "pork",
    "lamb", "fish", "salmon", "tuna", "shrimp", "crab", "lobster", "avocado",
    "cilantro", "parsley", "basil", "oregano", "thyme", "garlic", "ginger",
    "lime", "lemon", "orange", "apple", "banana", "strawberry", "blueberry",
    "raspberry", "grape", "pineapple", "mango", "peach", "pear", "watermelon",
    "almond", "peanut", "walnut", "cashew", "pecan", "pistachio", "hazelnut",
    "milk", "cream", "yogurt", "sour cream", "feta", "mozzarella", "cheddar",
    "parmesan", "swiss", "provolone", "gouda", "brie", "ricotta", "blue cheese",
    "goat cheese",
}

DEAL_PATTERNS = [
    re.compile(r"\bbogo\b"),
    re.compile(r"\b\d+\s*for\s*\$?\d"),
    re.compile(r"\bbuy\s*\d+\s*get\b"),
    re.compile(r"\bcombo\s*\$?\d"),
    re.compile(r"\b\$\d+\s*deal\b"),
    re.compile(r"\bdeal\b"),
    re.compile(r"\bspecial\b"),
    re.compile(r"\bpromo\b"),
    re.compile(r"\bsave\s*\$"),
    re.compile(r"%\s*off"),
]

INSTRUCTION_PATTERNS = [
    re.compile(r"\bbuild\s+your\s+own\b"),
    re.compile(r"\bcreate\s+your\s+own\b"),
    re.compile(r"\bmake\s+your\s+own\b"),
    re.compile(r"\bpick\s+your\b"),
    re.compile(r"\bchoose\s+your\b"),
    re.compile(r"\bcustomize\b"),
    re.compile(r"\bdesign\s+your\s+own\b"),
    re.compile(r"\byour\s+own\s+(pizza|burger|bowl|sandwich|salad|wrap|burrito|taco)\b"),
]

BULK_PATTERNS = [
    re.compile(r"\bpack\b"),
    re.compile(r"\bdozen\b"),
    re.compile(r"\bbucket\b"),
    re.compile(r"\bplatter\b"),
    re.compile(r"\btray\b"),
    re.compile(r"\bfamily\b"),
    re.compile(r"\bparty\b"),
    re.compile(r"\bmeal\s+kit\b"),
    re.compile(r"\bk[\s-]*cups?\b"),
    re.compile(r"\bvariety\b"),
    re.compile(r"\bbox\s+of\b"),
    re.compile(r"\bbulk\b"),
    re.compile(r"\bcase\b"),
    re.compile(r"\bcatering\b"),
    re.compile(r"\bfeeds\b"),
    re.compile(r"\bfor\s+the\s+table\b"),
    re.compile(r"\b\d+\s*pc\b"),  # 12 pc, 20 pc -- often buckets
    re.compile(r"\b\d+\s*piece\s+(bucket|pack|family|tray|platter)\b"),
]

MARKETING_TOKENS = {
    "happy", "classic", "premium", "deluxe", "supreme", "ultimate", "special",
    "today", "new", "limited", "featured", "favorite", "popular", "best",
    "signature", "famous", "original", "fresh", "hot", "cold", "spicy",
    "mild", "extra", "double", "triple", "mega", "giant", "jumbo", "small",
    "medium", "large", "kids", "kid", "adult",
}

# Words that strongly indicate a real main dish — even if other drop tokens appear,
# if the item also has these structural anchors, lean keep.
MAIN_ANCHORS = {
    "burger", "burgers", "cheeseburger", "cheeseburgers", "hamburger",
    "hamburgers", "sandwich", "sandwiches", "sub", "subs", "hoagie", "wrap",
    "wraps", "panini", "paninis", "burrito", "burritos", "taco", "tacos",
    "quesadilla", "quesadillas", "enchilada", "enchiladas", "tamale", "tamales",
    "fajita", "fajitas", "nachos", "tostada", "tostadas", "chimichanga",
    "chimichangas", "torta", "tortas", "pizza", "pizzas", "calzone", "calzones",
    "stromboli", "pasta", "spaghetti", "linguine", "fettuccine", "penne",
    "rigatoni", "ravioli", "lasagna", "lasagne", "gnocchi", "macaroni",
    "ramen", "udon", "soba", "pho", "noodles", "noodle", "lo mein", "chow mein",
    "pad thai", "yakisoba", "biryani", "curry", "tikka", "masala", "korma",
    "vindaloo", "tandoori", "naan",
    "wings", "wing", "tenders", "tender", "nuggets", "nugget", "strips",
    "fingers", "popcorn chicken", "drumsticks", "drumstick",
    "steak", "steaks", "ribeye", "sirloin", "filet", "tbone", "t-bone",
    "porterhouse", "brisket", "ribs", "rib", "chops", "chop", "loin",
    "tenderloin", "schnitzel", "wellington",
    "salmon", "tuna", "tilapia", "cod", "halibut", "trout", "shrimp",
    "scampi", "lobster", "crab", "calamari", "scallops", "oysters", "mussels",
    "clams",
    "omelet", "omelette", "frittata", "quiche", "scramble", "scrambler",
    "benedict", "benedicts", "florentine", "huevos", "rancheros", "chilaquiles",
    "migas", "menemen",
    "bowl", "bowls", "plate", "plates", "platter", "combo",
    "stew", "stews", "chili", "soup", "bisque", "chowder", "gumbo",
    "jambalaya", "etouffee", "paella", "risotto", "polenta",
    "kebab", "kebabs", "kabob", "kabobs", "shawarma", "gyro", "gyros",
    "souvlaki", "doner", "falafel",
    "casserole", "pot pie", "potpie", "shepherd", "shepherds",
    "stroganoff", "wellington", "kiev",
    "sushi", "roll", "rolls", "sashimi", "tempura", "katsu", "donburi",
    "bibimbap", "bulgogi", "kimchi",
    "loaf", "meatloaf", "meatballs",
    "dumplings", "dumpling", "potstickers", "wontons", "gyoza",
    "samosa", "samosas", "pakora", "pakoras", "pierogi", "pierogies",
    "empanada", "empanadas", "arepa", "arepas", "pupusa", "pupusas",
    "pancake", "pancakes", "waffle", "waffles", "crepe", "crepes",
    "french toast", "toast", "bagel", "bagels", "muffin",  # contextual
    "biscuit",  # contextual when combined
    "mcmuffin", "mcgriddle", "croissanwich",
    "salad", "salads",  # often a real main if specified
}

# === Helpers ===

def has_token(name: str, tokens: set) -> bool:
    """Check if any token (multi-word or single word) appears as a whole word in name."""
    for t in tokens:
        if " " in t:
            if t in name:
                return True
        else:
            # whole word match
            if re.search(r"\b" + re.escape(t) + r"\b", name):
                return True
    return False


def first_matching(name: str, tokens: set) -> str | None:
    for t in tokens:
        if " " in t:
            if t in name:
                return t
        else:
            if re.search(r"\b" + re.escape(t) + r"\b", name):
                return t
    return None


def matches_any_pattern(name: str, patterns: list) -> bool:
    return any(p.search(name) for p in patterns)


def classify(name: str) -> tuple[str, str]:
    """Return (verdict, reason)."""
    n = name.strip().lower()

    if not n:
        return "drop", "fragment"

    tokens = n.split()
    has_anchor = has_token(n, MAIN_ANCHORS)

    # 1. Instruction patterns (build/create your own)
    if matches_any_pattern(n, INSTRUCTION_PATTERNS):
        return "drop", "instruction"

    # 2. Deal patterns
    if matches_any_pattern(n, DEAL_PATTERNS) and not has_anchor:
        # "combo" alone could be deal but combo is a main anchor; only drop if no anchor
        return "drop", "deal"

    # 3. Bulk patterns
    if matches_any_pattern(n, BULK_PATTERNS):
        # "pack", "dozen", etc. are strong bulk signals regardless of anchors
        return "drop", "bulk"

    # 4. Drink — if any drink token appears AND no main anchor
    if has_token(n, DRINK_TOKENS):
        # Exception: "chicken bowl" with "milk" wouldn't happen; just check no anchor
        if not has_anchor:
            return "drop", "drink"
        # If both an anchor and drink token, prefer keep (e.g., "chicken sandwich coffee" rare)
        # But we should still drop pure drinks like "iced coffee large"
        # Heuristic: if no clear food-token combo, it's drink
        # We'll only keep if there's a strong main anchor that isn't itself a drink-coincident word

    # 5. Dessert
    if has_token(n, DESSERT_TOKENS):
        # "pie" is in DESSERT but also "pot pie" / "shepherds pie" are mains
        # Check: if "pot pie" or "shepherd" or "chicken pie" or "meat pie" — keep
        if "pot pie" in n or "potpie" in n or "shepherd" in n or "cottage pie" in n or "meat pie" in n or "fish pie" in n or "hand pie" in n or "chicken pie" in n or "steak pie" in n or "savory pie" in n:
            pass  # don't drop
        elif "muffin" in n and ("egg" in n or "sausage" in n or "bacon" in n or "mcmuffin" in n or "english" in n):
            pass  # english muffin sandwich
        elif "cake" in n and ("crab" in n or "fish" in n or "salmon" in n or "rice cake" in n or "pancake" in n):
            pass
        else:
            return "drop", "dessert"

    # 6. Side — but "fries" is often part of combos like "burger fries" -> still side combo unclear
    if has_token(n, SIDE_TOKENS):
        # If has main anchor and side, it's a combo plate -- keep
        if has_anchor:
            pass
        else:
            return "drop", "side"

    # 7. Sauce — usually plain
    if has_token(n, SAUCE_TOKENS):
        # If has anchor (e.g., "chicken alfredo sauce" -> still a dish) keep it
        if has_anchor:
            pass
        else:
            # very short -> sauce
            if len(tokens) <= 4:
                return "drop", "sauce"
            # else might be a dish description; keep
            pass

    # 8. Single-word ingredient drop
    if len(tokens) == 1 and tokens[0] in INGREDIENT_TOKENS:
        return "drop", "ingredient"

    # 9. Fragment — single short token (not a known dish)
    if len(tokens) == 1:
        single = tokens[0]
        if len(single) <= 3:
            return "drop", "fragment"
        # If single word matches a main anchor, keep
        if single in MAIN_ANCHORS or single in {"burrito", "taco", "pizza", "burger", "sandwich", "wings", "tenders", "nuggets", "ramen", "pho", "sushi", "salad", "omelet", "omelette", "lasagna", "spaghetti", "pasta", "steak", "ribs", "calzone", "quesadilla", "enchilada", "tamale", "fajita", "shawarma", "gyro", "falafel", "biryani", "curry", "wellington", "stroganoff", "scampi", "katsu", "donburi", "bibimbap", "bulgogi", "samosa", "pierogi", "empanada", "pupusa", "arepa", "frittata", "quiche", "benedict", "chilaquiles", "menemen", "huevos", "rancheros", "tikka", "masala", "korma", "vindaloo", "tandoori", "schnitzel", "kebab", "kabob", "souvlaki", "shepherd", "meatloaf", "meatballs", "potstickers", "gyoza", "wontons", "dumplings", "pakora", "tempura", "sashimi", "calamari", "scampi", "jambalaya", "etouffee", "paella", "risotto", "polenta", "gumbo", "chowder", "bisque", "chili", "stew", "soup", "panini", "hoagie", "torta", "chimichanga", "tostada", "nachos", "burritos", "tacos", "pizzas", "burgers", "sandwiches", "wraps", "subs", "salads", "bowls", "plates", "wings", "noodles"}:
            return "keep", "main"
        return "drop", "fragment"

    # 10. Marketing-only (all tokens are marketing words)
    if all(t in MARKETING_TOKENS for t in tokens):
        return "drop", "marketing"

    # 11. All-ingredient short (2 ingredients alone, no main anchor)
    if not has_anchor and all(t in INGREDIENT_TOKENS or t in MARKETING_TOKENS for t in tokens):
        # e.g., "bacon cheese", "ham cheese" -- ambiguous; treat as ingredient
        if len(tokens) <= 2:
            return "drop", "ingredient"
        # More complex combos may be a real dish description; keep
        return "keep", "main"

    # Default: KEEP (when in doubt)
    return "keep", "main"


def main():
    rows_in = 0
    rows_out = 0
    with open(INPUT, "r", newline="", encoding="utf-8") as fin, \
         open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        header = next(reader)
        writer.writerow(["verdict", "reason", "normalized_name", "count"])
        for row in reader:
            rows_in += 1
            if not row:
                # preserve empty? skip
                continue
            # name might contain commas? Use csv reader; row may have 2+ fields.
            if len(row) < 2:
                name = row[0] if row else ""
                count = ""
            else:
                # join all but last as name to be safe (rare commas)
                name = ",".join(row[:-1])
                count = row[-1]
            verdict, reason = classify(name)
            writer.writerow([verdict, reason, name, count])
            rows_out += 1
    print(f"Input data rows: {rows_in}")
    print(f"Output data rows: {rows_out}")


if __name__ == "__main__":
    main()
