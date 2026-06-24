#!/usr/bin/env python3
"""Classify menu items in chunk_01.csv as keep/drop with reason."""

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

INPUT = dpath("chunks/chunk_01.csv")
OUTPUT = dpath("chunks_classified/chunk_01_classified.csv")

# === Single-word dishes that should KEEP even when alone ===
SINGLE_WORD_MAINS = {
    "burrito", "burritos", "taco", "tacos", "pizza", "pizzas", "burger",
    "burgers", "cheeseburger", "cheeseburgers", "hamburger", "hamburgers",
    "sandwich", "sandwiches", "sub", "hoagie", "wrap", "wraps", "panini",
    "paninis", "calzone", "calzones", "stromboli", "quesadilla", "quesadillas",
    "enchilada", "enchiladas", "tamale", "tamales", "fajita", "fajitas",
    "nachos", "tostada", "tostadas", "chimichanga", "chimichangas",
    "torta", "tortas", "pasta", "spaghetti", "linguine", "fettuccine",
    "penne", "rigatoni", "ravioli", "lasagna", "lasagne", "gnocchi",
    "macaroni", "ramen", "udon", "soba", "pho", "biryani", "curry",
    "tikka", "korma", "vindaloo", "tandoori", "wings", "tenders",
    "nuggets", "drumsticks", "popcorn", "ribs", "steak", "steaks",
    "ribeye", "sirloin", "filet", "porterhouse", "brisket", "schnitzel",
    "wellington", "salmon", "tilapia", "halibut", "trout", "shrimp",
    "lobster", "crab", "calamari", "scallops", "oysters", "mussels",
    "clams", "scampi", "omelet", "omelette", "frittata", "quiche",
    "scramble", "benedict", "florentine", "huevos", "rancheros",
    "chilaquiles", "migas", "menemen", "bowl", "bowls", "plate", "plates",
    "platter", "combo", "stew", "chili", "soup", "bisque", "chowder",
    "gumbo", "jambalaya", "etouffee", "paella", "risotto", "polenta",
    "kebab", "kebabs", "kabob", "kabobs", "shawarma", "gyro", "gyros",
    "souvlaki", "doner", "falafel", "casserole", "stroganoff", "kiev",
    "sushi", "sashimi", "tempura", "katsu", "donburi", "bibimbap",
    "bulgogi", "meatloaf", "meatballs", "dumplings", "potstickers",
    "wontons", "gyoza", "samosa", "samosas", "pakora", "pakoras",
    "pierogi", "pierogies", "empanada", "empanadas", "arepa", "arepas",
    "pupusa", "pupusas", "pancake", "pancakes", "waffle", "waffles",
    "crepe", "crepes", "mcmuffin", "mcgriddle", "croissanwich",
    "croissant", "croissants", "salad", "salads",
    # less obvious mains worth keeping
    "blt", "club", "reuben", "whopper", "mcnuggets", "mcrib", "bigmac",
    "flautas", "flauta", "menudo", "sopes", "sope", "hotcakes", "gorditas",
    "gordita", "carnitas", "barbacoa", "milanesa", "bao", "ceviche",
    "crawfish", "catfish", "filets", "huarache", "huaraches", "molcajete",
    "taquitos", "taquito", "feast", "rotisserie", "tikka", "vindaloo",
    "biryani", "saag", "palak", "dal", "daal", "pho", "udon", "ramen",
    "soba", "yakitori", "yakisoba", "okonomiyaki", "takoyaki", "onigiri",
    "tonkatsu", "katsudon", "oyakodon", "gyudon", "unadon", "tendon",
    "chirashi", "nigiri", "maki", "temaki", "uramaki", "futomaki",
    "edamame", "rangoon", "rangoons",
    "spanakopita", "moussaka", "tzatziki",
    "shakshuka", "kibbeh", "tagine", "tajine",
    "feijoada", "ropa", "moros",
    "borscht", "goulash", "halushki",
    "haggis", "boxty", "colcannon",
    "bratwurst", "currywurst", "sauerbraten",
    "couscous", "tabouli", "tabbouleh",
    "jollof", "fufu", "injera", "doro",
    "poutine", "tourtiere",
    "cassoulet", "ratatouille", "bouillabaisse", "coq", "confit",
    "ossobuco", "saltimbocca", "carbonara", "amatriciana", "puttanesca",
    "bolognese", "alfredo", "marinara",
    "mussaman", "panang", "khao", "tom",
    "rendang", "satay", "nasi",
    "bibimbap", "japchae", "tteokbokki", "kimbap", "kimchi",
    "buldak", "samgyeopsal", "naengmyeon",
    "salisbury", "swedish", "stromboli",
    "stack", "stacks",  # pancake stacks
    "wrap", "fajita", "fajitas",
    "minestrone", "pozole", "posole", "menudo", "birria",
    "philly", "cheesesteak", "cheesesteaks",
    "souffle", "ratatouille",
    "quesabirria", "tlayuda", "elote",
    # Indian mains
    "roti", "naan", "paratha", "idli", "idly", "upma", "vada", "dosa",
    "uttapam", "sambhar", "rasam", "thali", "biryanis", "kurma",
    "manchurian", "pakoda", "bhaji", "puri", "chole", "rajma",
    "paneer", "mole",
    # Other
    "pita", "lavash", "sopa", "asado", "pozole", "posole", "birria",
    "carnita", "lengua", "cabeza", "cabrito", "lechon",
    "kushari", "fattoush", "kibbeh", "kebbeh",
    "khao", "som tum", "larb",
    "mochi",  # a dessert but...
    "jerk",  # jerk chicken category
    "slam",  # denny's grand slam
    "skillet", "skillets",
    "wellington",
    "lengua",
    "tinga",
}

# Compound dish names — multi-word phrases we should always keep
COMPOUND_MAIN_PHRASES = {
    "beef broccoli", "broccoli beef", "cashew chicken", "chicken cashew",
    "orange chicken", "chicken orange", "lemon chicken", "chicken lemon",
    "chicken parmesan", "parmesan chicken", "almond chicken", "chicken almond",
    "mushroom chicken", "chicken mushroom", "garlic chicken", "chicken garlic",
    "pineapple chicken", "chicken pineapple", "mango chicken", "chicken mango",
    "pepper chicken", "chicken pepper", "jalapeno chicken", "chicken jalapeno",
    "kung pao", "general tso", "moo shu", "moo goo", "hunan", "szechuan",
    "mongolian", "teriyaki", "honey walnut", "sweet sour",
    "butter chicken", "chicken curry", "chicken tikka", "tikka masala",
    "chana masala", "saag paneer", "palak paneer", "matar paneer",
    "biscuits gravy", "biscuits and gravy", "biscuit gravy",
    "bangers mash", "bangers and mash",
    "fish chips", "fish and chips",
    "chicken waffles", "chicken and waffles",
    "macaroni cheese", "mac cheese", "mac and cheese", "macaroni and cheese",
    "rice beans", "beans rice",
    "ham eggs", "eggs ham", "bacon eggs", "eggs bacon",
    "sausage eggs", "eggs sausage",
    "beef mushroom", "mushroom beef", "beef mushrooms", "mushrooms beef",
    "broccoli pork", "pork broccoli",
    "cheese ham", "ham cheese",  # common breakfast/sandwich combo
    "fried rice", "rice fried",
    "pad thai", "drunken noodles", "pad see ew",
    "salisbury steak", "swedish meatballs",
    "frito pie",  # a real dish
    "pot pie", "shepherd pie", "shepherds pie", "cottage pie", "fish pie",
    "meat pie", "savory pie", "hand pie", "chicken pie",
    "loaded fries",  # though this is fries, in some contexts a main
    "chicken fingers",
    "pulled pork", "pulled chicken",
    "egg roll", "spring roll", "summer roll", "lobster roll", "spring rolls",
    "egg rolls", "lobster rolls", "summer rolls", "california roll",
    "philly cheesesteak", "cheese steak",
    "patty melt", "tuna melt", "patty melts",
    "buffalo chicken",
    "blt", "club sandwich",
    "rib eye", "new york strip", "ny strip", "prime rib",
    "fried chicken", "roast chicken", "baked chicken", "grilled chicken",
    "rotisserie chicken",
    "honey butter", "honey hot",
    "egg foo young", "foo young",
    "lo mein", "chow mein", "chow fun", "mei fun", "ho fun",
    "general tso", "tso chicken", "kung pao", "pao chicken",
    "country fried steak", "chicken fried steak",
    "buffalo wings", "hot wings", "bbq wings",
    "ranch chicken",
    "philly", "cheesesteak",
    "italian beef", "italian sub",
    "meatball sub", "meatball sandwich",
    "egg sandwich", "breakfast sandwich",
    "monte cristo", "croque monsieur", "croque madame",
    "bourbon chicken",  # real Cajun dish, not bourbon drink
    "chicken honey",
    "garlic noodles", "drunken noodles",
    "rice bowl",
    "stir fry",  # common dish reference
    "chow fun house mei", "house special", "chef special", "chef s special",
    "house special chow mein", "house special fried rice",
    "egg foo young",
    "italian special",  # often an italian sub
    "deluxe pepperoni",  # deluxe pizza style
    "asiago club",  # club sandwich style
    "mongolian beef", "mongolian chicken",
    "honey walnut shrimp",
    "soft taco", "hard taco", "spicy taco",
    "fish taco", "shrimp taco", "carne asada", "al pastor",
    "carne asada taco", "shrimp taco",
    "lengua taco", "tripa taco", "asada taco",
    "albondigas", "tacos",
}

# Tokens that imply multi-ingredient main dish category
MAIN_ANCHORS = {
    "burger", "burgers", "cheeseburger", "cheeseburgers", "hamburger",
    "hamburgers", "sandwich", "sandwiches", "sub", "subs", "hoagie", "hoagies",
    "wrap", "wraps", "panini", "paninis", "burrito", "burritos", "taco",
    "tacos", "quesadilla", "quesadillas", "enchilada", "enchiladas",
    "tamale", "tamales", "fajita", "fajitas", "nachos", "tostada", "tostadas",
    "chimichanga", "chimichangas", "torta", "tortas", "pizza", "pizzas",
    "calzone", "calzones", "stromboli", "pasta", "spaghetti", "linguine",
    "fettuccine", "penne", "rigatoni", "ravioli", "lasagna", "lasagne",
    "gnocchi", "macaroni", "ramen", "udon", "soba", "pho", "noodles",
    "noodle", "biryani", "curry", "tikka", "masala", "korma", "vindaloo",
    "tandoori", "naan", "wings", "wing", "tenders", "tender", "nuggets",
    "nugget", "strips", "fingers", "drumstick", "drumsticks", "steak",
    "steaks", "ribeye", "sirloin", "filet", "porterhouse", "brisket", "ribs",
    "rib", "chops", "chop", "loin", "tenderloin", "schnitzel", "wellington",
    "salmon", "tuna", "tilapia", "cod", "halibut", "trout", "shrimp",
    "scampi", "lobster", "crab", "calamari", "scallops", "oysters", "mussels",
    "clams", "omelet", "omelette", "frittata", "quiche", "scramble",
    "scrambler", "benedict", "benedicts", "florentine", "huevos", "rancheros",
    "chilaquiles", "migas", "menemen", "bowl", "bowls", "plate", "plates",
    "combo", "stew", "stews", "chili", "soup", "bisque", "chowder", "gumbo",
    "jambalaya", "etouffee", "paella", "risotto", "polenta", "kebab", "kebabs",
    "kabob", "kabobs", "shawarma", "gyro", "gyros", "souvlaki", "doner",
    "falafel", "casserole", "stroganoff", "kiev", "sushi", "roll", "rolls",
    "sashimi", "tempura", "katsu", "donburi", "bibimbap", "bulgogi", "kimchi",
    "loaf", "meatloaf", "meatballs", "dumplings", "dumpling", "potstickers",
    "wontons", "gyoza", "samosa", "samosas", "pakora", "pakoras", "pierogi",
    "pierogies", "empanada", "empanadas", "arepa", "arepas", "pupusa",
    "pupusas", "pancake", "pancakes", "waffle", "waffles", "crepe", "crepes",
    "toast", "bagel", "bagels", "mcmuffin", "mcgriddle", "croissanwich",
    "croissant", "croissants", "salad", "salads",
    # additional anchors
    "philly", "cheesesteak", "cheesesteaks", "blt", "club", "reuben",
    "whopper", "mcnuggets", "mcnugget", "mcrib", "bigmac",
    "flautas", "flauta", "menudo", "sopes", "sope", "hotcakes",
    "gorditas", "gordita", "carnitas", "barbacoa", "milanesa", "bao",
    "ceviche", "crawfish", "catfish", "filets", "huarache", "huaraches",
    "molcajete", "taquitos", "taquito", "feast", "rotisserie",
    "saag", "palak", "dal", "daal", "yakitori", "yakisoba",
    "okonomiyaki", "takoyaki", "onigiri", "tonkatsu", "katsudon",
    "oyakodon", "gyudon", "unadon", "tendon", "chirashi", "nigiri",
    "maki", "temaki", "uramaki", "futomaki", "edamame", "rangoon",
    "rangoons", "spanakopita", "moussaka", "shakshuka", "kibbeh",
    "tagine", "tajine", "feijoada", "ropa", "moros", "borscht",
    "goulash", "halushki", "haggis", "boxty", "colcannon", "bratwurst",
    "currywurst", "sauerbraten", "couscous", "tabouli", "tabbouleh",
    "jollof", "fufu", "injera", "doro", "poutine", "tourtiere",
    "cassoulet", "ratatouille", "bouillabaisse", "coq", "confit",
    "ossobuco", "saltimbocca", "carbonara", "amatriciana", "puttanesca",
    "bolognese", "alfredo", "mussaman", "panang", "khao", "tom", "rendang",
    "satay", "nasi", "japchae", "tteokbokki", "kimbap", "buldak",
    "samgyeopsal", "naengmyeon", "salisbury", "swedish", "minestrone",
    "pozole", "posole", "birria", "souffle", "quesabirria", "tlayuda",
    "elote", "chimichanga", "tinga",
    # breakfast/brunch
    "frittata", "shakshuka", "scramble",
    # general
    "fillet", "fillets", "chuck", "round",
    "stack", "stacks", "melt", "melts",
    # Asian
    "chow", "lo", "fried rice",
    # other
    "alfredo", "marinara", "carbonara", "primavera",
    # Indian
    "roti", "naan", "paratha", "idli", "idly", "upma", "vada", "dosa",
    "uttapam", "sambhar", "rasam", "thali", "biryanis", "kurma",
    "manchurian", "pakoda", "bhaji", "puri", "chole", "rajma",
    "paneer", "mole",
    # Other ethnic
    "pita", "lavash", "sopa", "asado",
    "carnita", "lengua", "cabeza", "cabrito", "lechon",
    "kushari", "fattoush", "kibbeh", "kebbeh",
    "khao", "larb",
    "jerk", "slam", "skillet", "skillets",
    "tinga",
    # protein-style descriptor
    "wings", "wing",
}

DRINK_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappe", "frappuccino",
    "frap", "chai latte", "soda", "juice", "smoothie", "milkshake", "shake", "shakes",
    "beer", "wine", "cocktail", "lemonade", "iced tea", "bottled water", "slushie", "slush",
    "slushy", "icee", "americano", "macchiato", "cortado", "drink", "drinks",
    "beverage", "beverages", "cola", "coke", "pepsi", "sprite", "fanta",
    "dr pepper", "mountain dew", "redbull", "energy drink", "mocktail",
    "horchata", "agua", "aguas", "kombucha", "cider", "margarita", "mimosa",
    "sangria", "martini", "mojito", "sangria", "punch", "refresher", "refreshers",
    "spritzer", "vodka", "rum", "whiskey", "whisky", "tequila", "gin", "bourbon",
    "scotch", "brandy", "champagne", "prosecco", "lassi", "boba",
    "milktea", "ade", "limeade", "snapple", "gatorade", "powerade",
    "ristretto", "matcha latte", "iced coffee", "iced latte",
    "fountain drink", "fountain", "soft drink", "sweet tea", "unsweet tea",
    "iced", "hot tea",  # only paired with tea
    "milkshake", "smoothies", "cappuccinos",
    "frescas", "horchata", "agua fresca",
    "root beer", "ginger beer", "ginger ale",
    "redbull", "monster",
}

# tokens we treat as "drink-strong" — drop if ANY appears
DRINK_STRONG_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappuccino",
    "americano", "macchiato", "cortado", "ristretto",
    "soda", "cola", "coke", "pepsi", "sprite", "fanta",
    "lemonade", "limeade", "smoothie", "smoothies", "milkshake", "shake", "shakes",
    "beer", "wine", "cocktail", "margarita", "mimosa", "sangria", "martini",
    "mojito", "vodka", "rum", "whiskey", "whisky", "tequila", "gin",
    "scotch", "brandy", "champagne", "prosecco", "lassi", "boba",
    "snapple", "gatorade", "powerade", "redbull", "monster",
    "horchata", "agua", "aguas", "kombucha", "cider",
    "americano", "frappe", "matcha",
    "fanta", "fresca", "frescas",
    "slushie", "slushy", "slush", "icee",
}

DESSERT_STRONG_TOKENS = {
    "cake", "cakes", "cookie", "cookies", "brownie", "brownies", "cupcake",
    "cupcakes", "cinnabon", "donut", "donuts", "doughnut", "doughnuts",
    "icecream", "gelato", "sundae", "sundaes", "sorbet",
    "cheesecake", "custard", "churro", "churros", "tiramisu",
    "cannoli", "pudding", "mousse", "macaron", "macarons", "macaroon",
    "macaroons", "tart", "tarts", "eclair", "eclairs", "baklava",
    "biscotti", "fudge", "praline", "pralines", "gummy", "gummies",
    "marshmallow", "marshmallows",
    "popsicle", "popsicles", "flan", "cobbler", "crumble", "strudel",
    "kolache", "kolaches", "beignet", "beignets",
    "halo halo", "shave ice", "shaved ice", "snow cone", "snow cones",
    "rolled ice", "concrete", "blizzard", "mcflurry", "dilly bar",
    "dipped cone", "bismark", "bismarks", "cinnamon roll", "cinnamon rolls",
    "cinnabon",
    "ice cream",
    "apple pie", "pumpkin pie", "key lime pie", "pecan pie", "cherry pie",
    "blueberry pie", "lemon pie", "chocolate pie", "cream pie",
    "pumpkin spice cake",
    "cheesecake",
}

# pie words: drop only if dessert-pie context
DESSERT_PIE_INDICATORS = {
    "apple", "pumpkin", "cherry", "pecan", "blueberry", "key lime",
    "lemon meringue", "banana cream", "coconut cream", "chocolate",
    "strawberry", "lime", "fruit", "cream", "berry", "ice cream",
}

# muffin/biscuit are dessert/breakfast contextually
DESSERT_MUFFIN_INDICATORS = {
    "blueberry", "chocolate", "banana", "pumpkin", "cranberry", "lemon",
    "poppy", "corn", "bran", "apple", "cinnamon", "double chocolate",
}

SIDE_STRONG_TOKENS = {
    "fries", "fry", "frie",
    "rings",  # only "onion rings"
    "tots", "tater tots",
    "puppies",  # hush puppies
    "breadstick", "breadsticks", "garlic bread",
    "poppers",
    "side salad",
    "coleslaw", "slaw", "cole slaw",
    "applesauce",
    "mashed potatoes", "mashed potato",
    "cornbread", "corn bread",
    "hash brown", "hash browns", "hashbrown", "hashbrowns",
    "tater",
    "onion rings",
    "mozzarella sticks",
    "cheese sticks",
    "jalapeno poppers",
    "fried okra", "okra",
    "green beans",
    "grits",
    "rice pilaf", "pilaf",
    "salad small", "small salad",
}

# fries by themselves, but a "burger and fries" combo would still be a side dish on its own
# so any item where "fries" is the LAST/MAIN noun and there's no main anchor → side

SAUCE_STRONG_TOKENS = {
    "marinara sauce", "ranch dressing", "honey mustard sauce",
    "bbq sauce", "ketchup", "mayo", "mayonnaise",
    "aioli", "vinaigrette", "salsa", "guacamole", "queso", "hummus", "tahini",
    "pesto sauce", "tapenade", "chutney", "relish", "tartar", "remoulade", "gravy",
    "syrup", "jam", "jelly", "preserves",
}

# Sauce is tricky — only drop if "sauce" alone or known pure sauce; "garlic sauce" with chicken is a Chinese main
SAUCE_BARE_PATTERNS = [
    re.compile(r"^salsa$"),
    re.compile(r"^salsa\s+(roja|verde|fresca|picante|brava)$"),
    re.compile(r"^(roja|verde|fresca)\s+salsa$"),
    re.compile(r"^guacamole$"),
    re.compile(r"^queso$"),
    re.compile(r"^hummus$"),
    re.compile(r"^chips\s+(salsa|queso|guacamole|nacho|cheese)$"),
    re.compile(r"^(ranch|mayo|ketchup|mustard|aioli|vinaigrette)$"),
    re.compile(r"^(bbq|honey mustard|ranch|caesar|italian)\s+sauce$"),
    re.compile(r"\bdipping\s+sauce\b"),
    re.compile(r"^syrup$"),
    re.compile(r"^honey$"),
    re.compile(r"^gravy$"),
    re.compile(r"^gravy\s+(brown|sawmill|country|white)$"),
    re.compile(r"^(brown|sawmill|country|white)\s+gravy$"),
]

INGREDIENT_BARE = {
    "cheese", "bacon", "mushroom", "mushrooms", "onion", "onions", "tofu",
    "tomato", "tomatoes", "lettuce", "spinach", "kale", "cucumber", "pickle",
    "pickles", "olive", "olives", "pepper", "peppers", "jalapeno", "jalapenos",
    "carrot", "carrots", "celery", "broccoli", "cauliflower", "potato",
    "potatoes", "rice", "beans", "bean", "corn", "egg", "eggs",
    "ham", "salami", "pepperoni", "sausage", "chorizo", "turkey", "chicken",
    "beef", "pork", "lamb", "fish", "shrimp", "crab", "lobster", "tuna",
    "avocado", "cilantro", "parsley", "basil", "garlic",
    "lime", "lemon",
    "milk", "cream", "yogurt", "feta", "mozzarella", "cheddar",
    "parmesan", "swiss", "provolone", "gouda", "brie", "ricotta",
}

DEAL_PATTERNS = [
    re.compile(r"\bbogo\b"),
    re.compile(r"\b\d+\s*for\s*\$\d"),
    re.compile(r"\b\d+\s*for\s*\d+\b"),  # "2 for 5"
    re.compile(r"^\d+\s+\w+\s+for\b"),    # "2 dinner for"
    re.compile(r"^\d+\s+for\b"),
    re.compile(r"\bbuy\s*\d+\s*get\b"),
    re.compile(r"\b\$\d+\s*deal\b"),
    re.compile(r"\bsave\s*\$"),
    re.compile(r"%\s*off"),
    re.compile(r"\bpromo\b"),
    re.compile(r"\blimited\s+time\b"),
    re.compile(r"\bn\s*pour\s*\$\d"),
]

INSTRUCTION_PATTERNS = [
    re.compile(r"\bbuild\s+your\s+own\b"),
    re.compile(r"\bcreate\s+your\s+own\b"),
    re.compile(r"\bmake\s+your\s+own\b"),
    re.compile(r"\bpick\s+your\s+\w+\b"),
    re.compile(r"\bchoose\s+your\s+\w+\b"),
    re.compile(r"\bcustomize\b"),
    re.compile(r"\bdesign\s+your\s+own\b"),
    re.compile(r"\byour\s+own\s+(pizza|burger|bowl|sandwich|salad|wrap|burrito|taco|pasta)\b"),
]

BULK_PATTERNS = [
    re.compile(r"\bdozen\b"),
    re.compile(r"\bbucket\b"),
    re.compile(r"\bfamily\s+(meal|pack|box|pak|size|feast|dinner|bucket|platter|tray|bundle)\b"),
    re.compile(r"\bparty\s+(pack|tray|platter|box|size|bucket|bundle|wings|nuggets)\b"),
    re.compile(r"\bmeal\s+kit\b"),
    re.compile(r"\bk[\s-]*cups?\b"),
    re.compile(r"\bvariety\s+pack\b"),
    re.compile(r"\bbox\s+of\b"),
    re.compile(r"\bbulk\b"),
    re.compile(r"\bcatering\b"),
    re.compile(r"\bfeeds\b"),
    re.compile(r"\bfor\s+the\s+table\b"),
    re.compile(r"\bbundle\b"),
    re.compile(r"\bcrew\s+pack\b"),
    re.compile(r"\bgroup\s+order\b"),
    re.compile(r"\bsharer\b"),
    re.compile(r"\bgallon\b"),
    re.compile(r"\bsharing\b"),
    re.compile(r"\bpack\s+of\b"),
    re.compile(r"\b\d+\s*piece\s+(bucket|family|tray|platter|pack|box|combo|meal)\b"),
    re.compile(r"\bcombo\s+meal\s+for\s+\d"),
]

# pure marketing / non-dish strings
MARKETING_TOKENS_PURE = {
    "happy", "today special", "premium", "deluxe", "supreme", "ultimate",
    "new", "limited", "featured", "favorite", "popular", "best",
    "signature", "famous", "original", "fresh",
    "kids", "kid", "adult", "small", "medium", "large",
}

# Words that, alone or in tiny combinations, are marketing fluff
MARKETING_ONLY_NAMES = {
    "happy", "delight", "delights", "supreme", "deluxe", "premium",
    "favorite", "favorites", "classic", "classics", "original",
    "signature", "signatures", "special", "specials", "today",
    "featured", "featured today", "todays special",
    "new arrival", "new", "limited",
    "pak", "silverware", "extras", "add ons", "addon", "addons",
    "sides", "side", "extra", "extras", "drinks", "beverage",
    "to go", "togo", "take out", "takeout",
}

# A dish is clearly a "fries combo with main anchor" — keep
# bag-of-words detection helpers


def has_substring_phrase(name: str, phrases: set) -> str | None:
    for p in phrases:
        if p in name:
            return p
    return None


def has_word(name: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", name) is not None


def has_any_word(name: str, words: set) -> bool:
    for w in words:
        if " " in w:
            if w in name:
                return True
        else:
            if re.search(r"\b" + re.escape(w) + r"\b", name):
                return True
    return False


def matches_any_pattern(name: str, patterns: list) -> bool:
    return any(p.search(name) for p in patterns)


def has_main_anchor(name: str) -> bool:
    # Check tokens for any anchor
    for t in name.split():
        if t in MAIN_ANCHORS:
            return True
    # Multi-word anchors
    for phrase in COMPOUND_MAIN_PHRASES:
        if phrase in name:
            return True
    # check single-word mains
    for t in name.split():
        if t in SINGLE_WORD_MAINS:
            return True
    return False


def classify(name: str) -> tuple[str, str]:
    n = name.strip().lower()
    if not n:
        return "drop", "fragment"

    tokens = n.split()

    # 1. Instruction patterns
    if matches_any_pattern(n, INSTRUCTION_PATTERNS):
        return "drop", "instruction"

    # 2. Deal patterns (only true deal language; "special" alone not enough)
    if matches_any_pattern(n, DEAL_PATTERNS):
        return "drop", "deal"

    # 3. Bulk patterns (strong bulk signals)
    if matches_any_pattern(n, BULK_PATTERNS):
        return "drop", "bulk"

    has_anchor = has_main_anchor(n)

    # 4. Drink — strong drink token AND no main anchor
    if has_any_word(n, DRINK_STRONG_TOKENS):
        if not has_anchor:
            # If a real protein is present, treat as main (e.g. "bourbon chicken",
            # "chicken margarita", "beer battered fish")
            proteins_check = {"chicken", "beef", "pork", "shrimp", "fish", "lamb",
                              "turkey", "duck", "tofu", "salmon", "tuna", "crab",
                              "lobster"}
            if any(p in n.split() for p in proteins_check):
                pass
            else:
                return "drop", "drink"

    # "tea" specifically: only drink if "iced tea", "hot tea", "sweet tea", "green tea", "tea bag", or single word "tea"
    if has_word(n, "tea"):
        if not has_anchor:
            tea_drink_indicators = ["iced", "hot", "sweet", "unsweet", "green tea",
                                    "black tea", "chai tea", "milk tea", "fountain",
                                    "bottled", "brewed"]
            if any(ind in n for ind in tea_drink_indicators) or n.strip() == "tea":
                return "drop", "drink"

    # juice — only drink if clearly juice
    if has_word(n, "juice"):
        if not has_anchor:
            return "drop", "drink"

    # water — only drink if "bottled water", "sparkling water", "spring water"
    if has_word(n, "water"):
        if not has_anchor and any(w in n for w in ["bottled", "sparkling", "spring",
                                                     "still", "fiji", "evian",
                                                     "san pellegrino", "perrier"]):
            return "drop", "drink"

    # 5. Dessert
    if has_any_word(n, DESSERT_STRONG_TOKENS):
        # exclusions: pancake/cheesecake confusion not present (cheesecake is dessert)
        # crab cake, salmon cake, fish cake, rice cake, pancake -- "cake" alone is dessert
        if has_word(n, "cake") or has_word(n, "cakes"):
            if any(savory in n for savory in ["crab", "fish", "salmon", "tuna",
                                                "shrimp", "rice cake", "pancake",
                                                "pancakes", "cake batter shake",
                                                "potato cake", "corn cake", "johnny cake",
                                                "chicken"]):
                pass  # not dessert
            else:
                return "drop", "dessert"
        else:
            return "drop", "dessert"

    # pie — drop only if dessert-pie context
    if has_word(n, "pie") and "pizza" not in n:
        # savory pie indicators -> keep (account for alphabetized tokens)
        token_set = set(tokens)
        savory_keywords_in_tokens = {"pot", "shepherd", "shepherds", "cottage",
                                      "meat", "fish", "chicken", "beef", "pork",
                                      "turkey", "lamb", "tuna", "salmon", "spinach",
                                      "broccoli", "frito", "fritos", "tamale",
                                      "hand"}
        savory_pie = any(t in savory_keywords_in_tokens for t in tokens) or \
                     any(s in n for s in ["pot pie", "potpie", "savory pie"])
        if not savory_pie:
            # dessert pie indicators
            dessert_pie = any(s in n for s in DESSERT_PIE_INDICATORS) or \
                          any(s in n for s in ["pumpkin", "apple", "pecan", "cherry"])
            if dessert_pie or len(tokens) <= 3:
                return "drop", "dessert"

    # muffin — drop if blueberry/banana/chocolate/etc; keep if english muffin sandwich
    if has_word(n, "muffin") or has_word(n, "muffins"):
        if "english muffin" in n or "egg" in n or "sausage" in n or "bacon" in n \
                or "mcmuffin" in n:
            pass
        else:
            return "drop", "dessert"

    # parfait, granola, oatmeal -> snack/dessert
    if has_word(n, "parfait"):
        return "drop", "snack"

    # 6. Side
    if has_any_word(n, SIDE_STRONG_TOKENS):
        # Stir fry is a main dish (tokens "fry stir" appears alphabetized)
        is_stir_fry = ("fry stir" in n or "stir fry" in n or "stir fried" in n)
        # Fish fry is a main
        is_fish_fry = ("fish fry" in n or "fry fish" in n)
        if has_anchor or is_stir_fry or is_fish_fry:
            pass  # combo with main, keep
        else:
            return "drop", "side"

    # biscuits gravy is a southern main but my rule may treat biscuits as side
    # If "biscuit" present and combined with gravy (Southern main), keep
    if has_word(n, "biscuits") or has_word(n, "biscuit"):
        if "gravy" in n or "egg" in n or "sausage" in n or "bacon" in n or \
                "chicken" in n or "ham" in n or "breakfast" in n:
            pass  # keep
        elif not has_anchor:
            # biscuit + butter / biscuit + honey = side bread
            return "drop", "side"

    # 7. Sauce — only drop pure sauces
    for pat in SAUCE_BARE_PATTERNS:
        if pat.search(n):
            return "drop", "sauce"
    # "chips queso", "chips salsa" are snacks per rules
    if re.search(r"^chips\s+(queso|salsa|guacamole|nacho|cheese|fire roasted salsa|with [\w\s]+)$", n) or \
       re.search(r"^chips\s+\w+\s+(queso|salsa|guacamole)$", n):
        return "drop", "sauce"
    if n in {"guacamole", "queso", "salsa", "hummus", "ranch", "chimichurri"}:
        return "drop", "sauce"
    # "extra <something> sauce" with no anchor -> sauce
    if n.startswith("extra ") and "sauce" in n and not has_anchor:
        return "drop", "sauce"

    # 8. Single-token classification
    if len(tokens) == 1:
        single = tokens[0]
        if single in SINGLE_WORD_MAINS or single in MAIN_ANCHORS:
            return "keep", "main"
        if single in INGREDIENT_BARE:
            return "drop", "ingredient"
        if single in MARKETING_ONLY_NAMES:
            return "drop", "marketing"
        if len(single) <= 3:
            return "drop", "fragment"
        # Unknown single word — when in doubt, KEEP if not too short
        if len(single) >= 5:
            return "keep", "main"
        return "drop", "fragment"

    # 9. Marketing-only multi-word
    if all(t in MARKETING_ONLY_NAMES or t in MARKETING_TOKENS_PURE for t in tokens):
        return "drop", "marketing"

    # 10. Compound dish phrases (even if all-ingredient) -> KEEP
    if has_substring_phrase(n, COMPOUND_MAIN_PHRASES):
        return "keep", "main"

    # 11. All-ingredient short combos — be lenient: "beef broccoli" is a dish.
    # If 2 ingredients and one is a protein and other is a veggie/sauce-mainable, KEEP
    proteins = {"chicken", "beef", "pork", "shrimp", "fish", "lamb", "turkey",
                "duck", "tofu", "salmon", "tuna", "crab", "lobster"}
    veggies_or_pair = {"broccoli", "mushroom", "mushrooms", "garlic", "ginger",
                        "orange", "lemon", "lime", "pineapple", "mango",
                        "almond", "cashew", "walnut", "peanut", "pepper",
                        "peppers", "jalapeno", "spinach", "asparagus",
                        "eggplant", "cauliflower", "carrot", "carrots",
                        "honey", "sesame", "teriyaki", "bourbon", "bbq",
                        "buffalo", "ranch", "parmesan", "alfredo", "marinara",
                        "pesto", "florentine", "milanese", "piccata",
                        "marsala", "francese", "cordon bleu", "kiev",
                        "katsu", "tikka", "korma", "vindaloo", "biryani",
                        "curry", "masala"}

    has_protein = any(t in proteins for t in tokens)
    has_pair = any(t in veggies_or_pair for t in tokens)

    if has_protein and has_pair:
        # Likely a real dish like "chicken broccoli", "beef garlic"
        return "keep", "main"

    # 12. Two ingredient bare combo with no anchor — drop as ingredient
    if not has_anchor:
        # If all tokens are bare ingredients/marketing
        non_meaningful = INGREDIENT_BARE | MARKETING_ONLY_NAMES | MARKETING_TOKENS_PURE
        if all(t in non_meaningful for t in tokens):
            # exception: 2+ proteins or protein+protein combo — sandwich style — KEEP
            num_proteins = sum(1 for t in tokens if t in proteins)
            # exception: combination of protein + cheese + bread-component is fine
            if num_proteins >= 2:
                return "keep", "main"
            # If contains a real protein (chicken, beef, etc) treat as a real dish
            if num_proteins >= 1 and len(tokens) >= 2:
                return "keep", "main"
            if len(tokens) <= 2:
                return "drop", "ingredient"
            # 3+ ingredients with no protein and no anchor -> ingredient combo
            if len(tokens) <= 3:
                return "drop", "ingredient"

    # 13. Default: KEEP
    return "keep", "main"


def main():
    rows_in = 0
    rows_out = 0
    with open(INPUT, "r", newline="", encoding="utf-8") as fin, \
         open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        next(reader)  # header
        writer.writerow(["verdict", "reason", "normalized_name", "count"])
        for row in reader:
            rows_in += 1
            if not row:
                continue
            if len(row) < 2:
                name = row[0] if row else ""
                count = ""
            else:
                name = ",".join(row[:-1])
                count = row[-1]
            verdict, reason = classify(name)
            writer.writerow([verdict, reason, name, count])
            rows_out += 1
    print(f"Input data rows: {rows_in}")
    print(f"Output data rows: {rows_out}")


if __name__ == "__main__":
    main()
