#!/usr/bin/env python3
"""STRICT classification of menu items in chunks_v2/chunk_14.csv.

Bar: "Could a chef Google this exact name and find a recognizable dish recipe?"
WHEN IN DOUBT -> DROP.
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

INPUT = dpath("chunks_v2/chunk_14.csv")
OUTPUT = dpath("chunks_classified_v2/chunk_14_classified.csv")


# ---- Token sets ----

DRINK_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappe", "frappuccino",
    "frap", "frabbuccinos", "americano", "macchiato", "cortado", "ristretto",
    "soda", "smoothie", "milkshake", "shake", "shakes", "milktea",
    "cola", "coke", "pepsi", "sprite", "fanta", "drpepper",
    "redbull", "kombucha", "horchata", "agua", "aguas",
    "lemonade", "limeade", "limonade", "orangeade", "snapple",
    "gatorade", "powerade", "lassi", "boba",
    "beer", "wine", "cocktail", "margarita", "mimosa", "sangria",
    "martini", "mojito", "spritzer", "vodka", "rum", "whiskey",
    "whisky", "tequila", "gin", "bourbon", "scotch", "brandy", "champagne",
    "prosecco", "slushie", "slush", "slushy", "icee", "frosty",
    "milkshake", "float", "floats",
    "calypso", "lemonades", "calypso lemonades",
    "kefir", "fizz", "ombucha",
    "chico", "topo",  # topo chico
    "jarritos",
    "pelligrino", "pelligrino san", "san pelligrino",
    "modelo", "corona", "chardonnay", "noir",
    "kombucha", "frappucinos",
    "water",  # bottled water
    "milk",  # plain milk drink
    "drink",  # explicit drink label
    "tea", "iced tea",
    "juice",
    "milkshakes",
}

DESSERT_TOKENS = {
    "cake", "cakes", "cookie", "cookies", "brownie", "brownies", "cupcake",
    "cupcakes", "cinnabon", "donut", "donuts", "doughnut", "doughnuts",
    "icecream", "gelato", "sundae", "sundaes", "sorbet",
    "cheesecake", "tiramisu", "cannoli", "macaron", "macarons", "macaroon",
    "macaroons", "eclair", "eclairs", "baklava", "biscotti", "fudge",
    "candy", "candies", "praline", "pralines", "gummy", "gummies",
    "marshmallow", "marshmallows", "popsicle", "popsicles",
    "creme brulee", "flan", "churro", "churros", "cobbler", "strudel",
    "kolache", "kolaches", "beignet", "beignets", "halo halo",
    "shave ice", "shaved ice", "snow cone", "snow cones",
    "concrete", "blizzard", "mcflurry", "dilly bar", "dipped cone",
    "bismark", "bismarks", "cinnamon roll", "cinnamon rolls",
    "skittles", "nerds", "oreo",
    "mochi",  # the dessert
    "concha",
    "compote", "swirl",
    "patacon", "pisao",  # actually a Colombian dish — leave; remove
}

# Better dessert handling — more conservative
DESSERT_STRICT = {
    "cake", "cookie", "brownie", "cupcake", "cinnabon", "donut",
    "doughnut", "icecream", "ice cream", "gelato", "sundae", "sorbet",
    "cheesecake", "tiramisu", "cannoli", "macaron", "macaroon",
    "eclair", "baklava", "biscotti", "fudge", "praline", "gummy",
    "marshmallow", "popsicle", "creme brulee", "flan", "churro",
    "cobbler", "strudel", "kolache", "beignet",
    "skittles", "nerds", "oreo", "mochi", "concha", "compote",
    "fruta", "frosting",
}

SIDE_STRICT = {
    "fries", "frites", "tots", "puppies", "breadsticks",
}

PURE_FRAGMENT_PATTERNS = [
    re.compile(r"^[a-z0-9 ]{1,4}$"),
]

# Recognizable dish names that survive even tough scoring
DISH_TERMS = {
    # Italian
    "pizza", "calzone", "stromboli", "lasagna", "lasagne", "spaghetti", "linguine",
    "linguini", "fettuccine", "fettuccini", "penne", "rigatoni", "ravioli",
    "tortellini", "gnocchi", "macaroni", "carbonara", "bolognese", "alfredo",
    "marinara", "primavera", "pesto", "scampi", "piccata", "marsala", "parmigiana",
    "parmigiano", "parmesan", "saltimbocca", "osso buco", "risotto", "polenta",
    "panini", "focaccia", "bruschetta", "caprese", "minestrone", "cioppino",
    # Mexican
    "burrito", "taco", "tacos", "quesadilla", "enchilada", "enchiladas", "tamale",
    "tamales", "tostada", "tostadas", "tostado", "fajita", "fajitas", "nachos",
    "chimichanga", "chimichangas", "torta", "tortas", "chilaquiles", "huevos",
    "rancheros", "machaca", "carnitas", "barbacoa", "menudo", "pozole",
    "elote", "esquites", "sope", "sopes", "huarache", "huaraches", "memela",
    "tlayuda", "molotes", "panucho", "panuchos", "salbute", "salbutes",
    "picadita", "picaditas", "tetela", "mulita", "mulitas", "vampiro",
    "quesabirria", "quesabirrias", "birria", "tinga", "ceviche", "aguachile",
    "molcajete", "milanesa", "mole", "carne asada", "al pastor",
    "cochinita pibil", "chimichurri",
    # Asian
    "ramen", "udon", "soba", "pho", "banh mi", "banh", "bun", "vermicelli",
    "biryani", "tikka", "masala", "korma", "vindaloo", "tandoori", "naan",
    "samosa", "samosas", "pakora", "pakoras", "dosa", "idli", "uttapam",
    "bibimbap", "bulgogi", "kimchi", "japchae", "tteokbokki", "tteok",
    "donburi", "katsu", "tonkatsu", "chirashi", "okonomiyaki", "yakitori",
    "yakisoba", "tempura", "teriyaki", "sashimi", "sushi", "maki", "nigiri",
    "onigiri", "musubi", "gyoza", "potstickers", "wontons", "dumpling",
    "dumplings", "lo mein", "chow mein", "chow fun", "char siu", "kung pao",
    "general tso", "kung pao", "mapo tofu", "mongolian", "szechuan", "schezwan",
    "hunan", "cantonese", "shanghai", "peking", "hot pot", "dim sum",
    "har gow", "shumai", "siu mai", "xiaolongbao", "congee", "jook",
    "pad thai", "pad see ew", "pad kee mao", "pad krapow", "khao soi",
    "tom yum", "tom kha", "som tum", "larb", "satay", "rendang", "nasi goreng",
    "mee goreng", "laksa", "khao pad", "khao", "kao",
    "kebab", "kebabs", "kabob", "kabobs", "shawarma", "gyro", "gyros",
    "souvlaki", "doner", "falafel", "hummus", "tabouleh", "tabbouleh",
    "tzatziki", "moussaka", "spanakopita", "saganaki", "pastitsio",
    "kibbeh", "manakeesh", "lahmacun", "pide", "borek", "manti",
    "shish tawooq", "kofta", "kafta", "fattoush", "muhammara", "labneh",
    "machboos", "mansaf", "mujadara", "shakshuka", "harissa",
    "egusi", "jollof", "fufu", "injera", "wat", "wot", "tibs", "doro wat",
    "kitfo", "kifto", "miser wat", "berbere",
    # American
    "burger", "burgers", "cheeseburger", "cheeseburgers", "hamburger",
    "hamburgers", "sandwich", "sandwiches", "sandwhich", "sandwich",
    "sub", "subs", "hoagie", "hero", "grinder", "wrap", "wraps",
    "philly", "cheesesteak", "reuben", "patty melt", "blt", "club",
    "po boy", "poboy", "cuban", "cubano",
    "wings", "wing", "tenders", "tender", "nuggets", "nugget", "strips",
    "drumsticks", "drumstick", "thigh", "thighs", "drumette",
    "popcorn chicken", "fried chicken", "buffalo wings",
    "steak", "ribeye", "sirloin", "filet mignon", "tbone", "t-bone",
    "porterhouse", "brisket", "ribs", "rib tips", "tri tip", "tritip",
    "chops", "chop", "porkchop", "porkchops", "loin", "tenderloin",
    "schnitzel", "wellington", "stroganoff", "kiev", "stew",
    "salmon", "tuna", "tilapia", "cod", "halibut", "trout", "shrimp",
    "lobster", "crab", "calamari", "scallops", "oysters", "mussels", "clams",
    "omelet", "omelette", "frittata", "quiche", "scramble",
    "benedict", "florentine", "pancakes", "pancake", "waffle", "waffles",
    "crepe", "crepes", "french toast",
    "chowder", "bisque", "gumbo", "jambalaya", "etouffee",
    "meatloaf", "meatballs", "pot roast", "pot pie", "shepherds pie",
    "chicken fried steak", "country fried", "biscuits and gravy",
    "bbq", "barbecue", "barbeque", "pulled pork", "pulled chicken",
    "loco moco", "saimin", "spam musubi", "kalua",
    "salad",  # often "caesar salad", "cobb salad" etc — context matters
    "soup",  # usually combined
    # Misc
    "paella", "tagine", "tajine", "couscous", "schnitzel",
    "pierogi", "pierogies", "borscht", "vareniki",
    "empanada", "empanadas", "arepa", "arepas", "pupusa", "pupusas",
    "saltado", "lomo saltado", "tres leches",
    "baleada", "baleadas", "catracho", "catrachos",
    "moqueca", "feijoada", "asado",
}

# Things that, when standing alone (1-2 token), are not specific dishes
TOO_GENERIC_ALONE = {
    "bowl", "plate", "platter", "combo", "special", "deluxe", "supreme",
    "house", "favorite", "mix", "mixed", "regular", "small", "large",
    "kid", "kids", "side", "sides", "extra", "topping", "toppings",
    "meal", "meals", "dinner", "lunch", "breakfast", "appetizer",
    "entree", "starter", "main", "set", "menu",
    "salad",  # alone, must be specified
    "soup",
    "pasta",
    "rice",
    "noodles", "noodle",
    "wrap", "wraps",
    "pizza", "pizzas",
    "burger", "burgers",
    "sandwich", "sandwiches",
    "taco", "tacos",
    "burrito", "burritos",
    "wings", "wing",
    "roll", "rolls",
    "sushi",
    "curry", "curries",
    "ramen", "udon", "soba", "pho",
    "kebab", "kabob", "gyro",
    "stir", "fry", "stir fry", "fried",
    "chicken", "beef", "pork", "lamb", "fish", "shrimp", "tofu", "vegan",
    "tuna", "salmon", "veggie", "vegetable", "vegetables",
    "spicy", "hot", "cold", "fresh", "garlic", "honey",
    "italian", "mexican", "french", "thai", "chinese", "japanese", "korean",
    "indian", "mediterranean", "greek", "vietnamese",
    "tip", "tips", "tipping",
}


# Patterns to drop instantly
INSTRUCTION_PAT = re.compile(r"\b(build|create|make|pick|choose|design|customize|byo)\b.*\b(your|own)\b|\byour\s+own\b|\bbyo\b")
DEAL_PAT = re.compile(r"\b(\d+)\s*for\s*\$?\d|\bbogo\b|\bbuy\s*\d+\s*get\b|\b\$\d+\s*deal\b|\bdiscount\b|\bpromo\b")
TIP_PAT = re.compile(r"\btip\b|\bgratuity\b|\bstaff\b.*\btip\b|\btip\b.*\bstaff\b|\btips\b")
UTENSIL_PAT = re.compile(r"\butensils?\b|\bnapkin\b|\bbag\b|\bcompostable\b|\bplease\s+include\b|\bi\s+need\b")
THANK_PAT = re.compile(r"\bthank\b|\bthanks\b|\bwow\b|\blove\b\s+(staff|us|you)|\bbest\b\s+ever|\bthank\s+you\b")
INSTRUCTIONAL_ADD_PAT = re.compile(r"\badd\s+(extra|egg|to)\b|\bextra\s+\w+\s+to\s+your\b|\b(meat|veggies|item)\s+ordered\s+to\b|\bordered\s+to\s+your\b")
ALPHANUM_CODE_PAT = re.compile(r"^[a-z0-9 ]+$")
RESTAURANT_TIP_PAT = re.compile(r"\b\d+\s+(restaurant|staff|crew|team|hgs|smile|all|the)\s+tip\b|\btip\s+\d+|\bfor\s+\w+\s+love\b|\b\d+\s+love\b")
LOTSA_DIGITS_PAT = re.compile(r"\b00\b|\$\d+\b\s+\b\d+\b")
MENU_SECTION_PAT = re.compile(r"^(item|order|each|side|sides|meal|dinner|lunch|breakfast|appetizer|entree|starter|main|set|menu|combo|combinations?|combo plate|family|kids|adult)\s*\d*$")


def is_pure_alphanum_fragment(name: str) -> bool:
    """Check if name is mostly random char fragments / single letters."""
    tokens = name.split()
    if not tokens:
        return True
    # Count single-letter or 2-letter tokens (excluding allowed dish words)
    short_count = sum(1 for t in tokens if len(t) <= 2 and t not in {"po", "ny", "la", "el", "su", "go", "no", "mi", "uc", "mt", "st", "k", "n", "m", "bbq"})
    # If half or more tokens are very short fragments, it's broken
    if short_count >= max(2, len(tokens) // 2):
        # Check if any clear food token in there
        food_present = any(t in DISH_TERMS for t in tokens)
        if not food_present:
            return True
    # If 4+ single-letter tokens — almost certainly broken text
    single_letters = sum(1 for t in tokens if len(t) == 1)
    if single_letters >= 3:
        return True
    return False


def has_dish_term(name: str) -> str:
    """Return matched dish term if present, else empty."""
    tokens = set(name.split())
    for t in tokens:
        if t in DISH_TERMS:
            return t
    # Multi-word
    for term in DISH_TERMS:
        if " " in term and term in name:
            return term
    return ""


def has_drink_token(name: str) -> bool:
    tokens = set(name.split())
    for d in DRINK_TOKENS:
        if " " in d:
            if d in name:
                return True
        elif d in tokens:
            return True
    return False


def has_dessert_token(name: str) -> bool:
    tokens = set(name.split())
    for d in DESSERT_STRICT:
        if " " in d:
            if d in name:
                return True
        elif d in tokens:
            return True
    return False


def classify(name: str) -> tuple[str, str]:
    n = name.strip().lower()
    if not n:
        return "drop", "fragment"
    tokens = n.split()
    n_tokens = len(tokens)

    # 1) Tip / gratuity / utensils / thank-you etc - marketing/fragment
    if TIP_PAT.search(n) or RESTAURANT_TIP_PAT.search(n):
        return "drop", "marketing"
    if UTENSIL_PAT.search(n):
        return "drop", "fragment"
    if THANK_PAT.search(n) and not has_dish_term(n):
        return "drop", "marketing"
    if INSTRUCTION_PAT.search(n):
        return "drop", "instruction"
    if INSTRUCTIONAL_ADD_PAT.search(n):
        return "drop", "instruction"
    if DEAL_PAT.search(n):
        return "drop", "deal"

    # 2) Pure short fragment
    if n_tokens == 1:
        single = tokens[0]
        if single in DISH_TERMS and single not in TOO_GENERIC_ALONE:
            # specific named dish like "spaghetti" — but spaghetti alone isn't a recipe
            return "drop", "fragment"
        # known multi-token dishes saved as 1 word
        if single in {"hoagie", "pho", "ramen", "udon", "biryani", "shawarma", "moqueca",
                      "feijoada", "saimin", "menudo", "pozole", "soursop", "durian",
                      "spageti", "lasagna", "carbonara", "bolognese", "samosa",
                      "pakora", "souvlaki", "schnitzel", "stroganoff",
                      "ceviche", "wellington",
                      "kabocha", "barramundi"}:
            # still fragment unless dish-specific recipe; conservative drop
            return "drop", "fragment"
        return "drop", "fragment"

    # 3) Random alphanumeric fragments / mostly broken text
    if is_pure_alphanum_fragment(n):
        return "drop", "fragment"

    # 4) Drinks
    dish = has_dish_term(n)
    if has_drink_token(n) and not dish:
        return "drop", "drink"
    # Pure drink with size word
    if has_drink_token(n) and n_tokens <= 4 and not dish:
        return "drop", "drink"

    # 5) Dessert
    if has_dessert_token(n) and not dish:
        # Allow savory pies / pancakes (pancake/waffle/crepe handled elsewhere)
        # Just drop dessert
        return "drop", "dessert"

    # 6) Side: "fries" alone-ish
    side_hit = any(t in SIDE_STRICT for t in tokens)
    if side_hit and not dish:
        return "drop", "side"

    # 7) Sauces (bare)
    if n_tokens <= 3 and ("sauce" in tokens or "dip" in tokens or "dressing" in tokens) and not dish:
        return "drop", "sauce"

    # 8) Bulk
    if any(t in {"bucket", "dozen", "bulk", "platter", "tray", "case", "kit", "pack", "tote"} for t in tokens):
        return "drop", "bulk"

    # 9) Generic-only: if all tokens are too-generic and no specific dish term beyond them
    non_generic = [t for t in tokens if t not in TOO_GENERIC_ALONE]
    if not non_generic:
        return "drop", "fragment"

    # 10) Section / meal labels: "combo plate", "lunch special", "today special"
    bad_short = {
        "combination", "combinations", "combo", "special", "specials",
        "deluxe", "supreme", "ultimate", "house",
        "lunch", "dinner", "breakfast", "appetizer", "entree",
    }
    if n_tokens <= 3 and all(t in bad_short or t in TOO_GENERIC_ALONE for t in tokens):
        return "drop", "fragment"

    # 11) "X meal", "X plate", "X combo" with no specific identifier
    if n_tokens == 2:
        a, b = tokens
        if (a in TOO_GENERIC_ALONE and b in TOO_GENERIC_ALONE):
            return "drop", "fragment"
        # E.g. "chicken combo", "italian special", "house plate"
        generic = {"combo", "plate", "platter", "special", "meal", "dinner", "lunch",
                   "breakfast", "bowl", "wrap", "set", "deluxe", "supreme", "house",
                   "favorite", "regular", "kit", "menu", "side"}
        proteins = {"chicken", "beef", "pork", "lamb", "tofu", "fish", "shrimp",
                    "salmon", "tuna", "veggie", "vegan", "vegetable", "mixed",
                    "italian", "mexican", "thai", "chinese", "japanese", "korean",
                    "indian", "greek", "mediterranean", "vietnamese", "french"}
        if (a in generic and b in proteins) or (b in generic and a in proteins):
            return "drop", "fragment"
        if (a in generic and b in generic):
            return "drop", "fragment"

    # 12) Numbers as tokens — combo numbers like "2 chicken" or "b1 burger"
    # If the dominant content is alphanumeric IDs, drop
    code_tokens = sum(1 for t in tokens if re.fullmatch(r"[a-z]?\d+[a-z]?|\d+[a-z]?", t))
    if code_tokens >= 1 and n_tokens <= 4 and not dish:
        # short with ID and no real dish
        return "drop", "fragment"

    # 13) Final: must have a recognizable dish term OR be sufficiently descriptive
    # If we have a dish term, keep
    if dish:
        return "keep", "main"

    # Without a dish term but with multiple food-ingredient tokens, conservative drop
    # because "broccoli chicken pork rice" without dish-name is just ingredients
    food_words = {"chicken", "beef", "pork", "lamb", "tofu", "fish", "shrimp",
                  "salmon", "tuna", "rice", "noodles", "noodle", "veggie",
                  "vegetable", "vegetables"}
    has_food = any(t in food_words for t in tokens)
    if has_food and n_tokens >= 3:
        # Look for a "structural" dish word
        structural = {"sandwich", "sandwiches", "wrap", "burger", "taco", "burrito",
                      "pizza", "pasta", "ramen", "udon", "pho", "salad",
                      "platter", "plate", "stew", "soup", "chowder", "gumbo",
                      "curry", "biryani", "tikka", "masala", "tandoori",
                      "kebab", "kabob", "gyro", "shawarma", "falafel",
                      "katsu", "tempura", "yakisoba", "donburi", "bibimbap",
                      "bulgogi", "kimchi", "sushi", "roll", "rolls",
                      "casserole", "lasagna", "spaghetti", "fettuccine",
                      "linguine", "linguini", "penne", "fettuccini",
                      "rigatoni", "ravioli", "tortellini", "gnocchi",
                      "macaroni", "noodles", "noodle", "pancake", "pancakes",
                      "waffle", "waffles", "crepe", "crepes", "omelet",
                      "omelette", "scramble", "fajita", "fajitas",
                      "enchilada", "enchiladas", "tamale", "tamales",
                      "quesadilla", "tostada", "tostadas", "torta", "tortas",
                      "chimichanga", "nachos", "calzone", "stromboli",
                      "panini", "hoagie", "sub", "hero", "philly",
                      "cheesesteak", "reuben", "club", "patty", "melt",
                      "wings", "tenders", "nuggets", "strips", "drumsticks",
                      "ribs", "brisket", "loin", "tenderloin", "steak",
                      "schnitzel", "wellington", "stroganoff",
                      "scampi", "piccata", "marsala", "alfredo", "carbonara",
                      "marinara", "pesto", "primavera", "parmesan", "parmigiana",
                      "parmigiano", "bolognese",
                      "kabob", "kabobs", "souvlaki", "doner",
                      "moqueca", "tagine", "tajine", "paella", "risotto",
                      "polenta", "feijoada", "asado", "saltado", "milanesa",
                      "ceviche", "aguachile", "molcajete", "carnitas",
                      "barbacoa", "machaca", "chilaquiles", "huevos",
                      "rancheros", "menudo", "pozole", "elote", "esquites",
                      "sope", "sopes", "huarache", "huaraches", "tlayuda",
                      "panucho", "panuchos", "salbute", "salbutes",
                      "picadita", "picaditas", "tetela", "mulita", "mulitas",
                      "vampiro", "quesabirria", "quesabirrias", "birria",
                      "tinga", "vermicelli", "biriyani", "biryani",
                      "bulgolgi", "japchae", "jjamppong", "jajangmyeon",
                      "samosa", "samosas", "pakora", "pakoras", "naan",
                      "dosa", "idli", "uttapam", "tandoori", "tikka",
                      "korma", "vindaloo", "rogan josh", "saag", "palak",
                      "chana", "channa", "dal", "chaat", "thali",
                      "pad thai", "tom yum", "tom kha", "som tum", "larb",
                      "satay", "rendang", "nasi", "mee goreng", "laksa",
                      "khao soi", "khao", "kao", "pad", "drunken",
                      "yakitori", "yakiniku", "okonomiyaki",
                      "konbu", "miso", "kimbap", "tteok",
                      "dumplings", "dumpling", "potstickers", "wontons",
                      "gyoza", "shumai", "har gow", "xiaolongbao",
                      "congee", "jook", "bao", "baozi",
                      "kebab", "kabob",
                      "mansaf", "kibbeh", "manakeesh", "lahmacun", "pide",
                      "borek", "manti", "shish tawooq", "kofta", "kafta",
                      "moussaka", "spanakopita", "saganaki", "pastitsio",
                      "fattoush", "tabouleh", "tabbouleh", "tzatziki",
                      "muhammara", "labneh", "shakshuka", "shakshouka",
                      "harissa", "harira",
                      "egusi", "jollof", "fufu", "injera", "wat", "wot",
                      "tibs", "doro wat", "kitfo", "miser wat",
                      "loco moco", "saimin", "spam musubi", "kalua",
                      "katsu", "tonkatsu", "donburi", "chirashi",
                      "fishtaco", "saj", "sando",
                      "khaprow", "kraprow", "kraprao", "khaprao",
                      "stroganoff",
                      "mafe", "yassa", "thieboudienne", "thiou",
                      "borscht", "vareniki", "pierogi", "pierogies",
                      "empanada", "empanadas", "arepa", "arepas",
                      "pupusa", "pupusas", "baleada", "baleadas",
                      "catracho", "catrachos",
                      "biscuit", "biscuits", "biscuit and gravy",
                      "pot pie", "potpie", "shepherd",
                      "meatloaf", "meatballs",
                      "saucebox",  # specific brand item often
                      "okra", "gumbo", "etouffee", "jambalaya",
                      "bisque", "chowder",
                      "saji",
                      "musubi", "loco", "moco",
                      "kuli kuli",
                      "po boy", "poboy",
                      "katsu sando",
                      "bahn mi", "banh mi",
                      "pancit",
                      "adobo",
                      "bistec",
                      "rellenas", "rellenos", "relleno",
                      "milanessa",
                      "salbute", "tlayuda",
                      "gyoza",
                      "raman",
                      }
        if any(t in structural for t in tokens):
            return "keep", "main"

    # If nothing matched, drop as fragment (when in doubt, drop)
    return "drop", "fragment"


def main():
    rows_in = 0
    rows_out = 0
    keeps = 0
    with open(INPUT, "r", newline="", encoding="utf-8") as fin, \
         open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        header = next(reader)
        writer.writerow(["verdict", "reason", "normalized_name", "count"])
        for row in reader:
            rows_in += 1
            if not row:
                writer.writerow(["drop", "fragment", "", ""])
                rows_out += 1
                continue
            if len(row) < 2:
                name = row[0] if row else ""
                count = ""
            else:
                name = ",".join(row[:-1])
                count = row[-1]
            verdict, reason = classify(name)
            if verdict == "keep":
                keeps += 1
            writer.writerow([verdict, reason, name, count])
            rows_out += 1
    print(f"Input data rows: {rows_in}")
    print(f"Output data rows: {rows_out}")
    print(f"Kept: {keeps} ({100.0*keeps/max(rows_out,1):.1f}%)")


if __name__ == "__main__":
    main()
