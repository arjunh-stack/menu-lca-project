#!/usr/bin/env python3
"""STRICT classification of chunk_04.csv (v2).

Recipe test: would a chef Google "how to make ___" and find a real, recognizable
main dish someone would order for breakfast/lunch/dinner?
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

INPUT = dpath("chunks_v2/chunk_04.csv")
OUTPUT = dpath("chunks_classified_v2/chunk_04_classified.csv")

# ============================================================================
# DROP categories
# ============================================================================

# Drink tokens — drop if present unless paired with strong main protein dish
DRINK_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappe", "frappuccino",
    "frap", "americano", "macchiato", "cortado", "ristretto",
    "soda", "cola", "coke", "pepsi", "sprite", "fanta", "drpepper",
    "lemonade", "limeade", "smoothie", "smoothies", "milkshake", "shake", "shakes",
    "beer", "wine", "cocktail", "margarita", "mimosa", "sangria", "martini",
    "mojito", "vodka", "rum", "whiskey", "whisky", "tequila", "gin",
    "scotch", "brandy", "champagne", "prosecco", "lassi", "boba",
    "snapple", "gatorade", "powerade", "redbull", "monster",
    "horchata", "kombucha", "cider",
    "frescas", "fresca",
    "slushie", "slushy", "slush", "icee", "slurpee",
    "matcha",
    "smoothy",
    "float", "frosty",
    "milktea", "ade",
    "spritzer",
    "blast",
    "freeze", "freezes",
    "refresher", "refreshers",
}

# Dessert tokens
DESSERT_TOKENS = {
    "cookie", "cookies", "brownie", "brownies", "cupcake", "cupcakes",
    "cinnabon", "donut", "donuts", "doughnut", "doughnuts",
    "icecream", "gelato", "sundae", "sundaes", "sorbet",
    "cheesecake", "custard", "churro", "churros", "tiramisu",
    "cannoli", "pudding", "mousse", "macaron", "macarons", "macaroon",
    "macaroons", "tart", "tarts", "eclair", "eclairs", "baklava",
    "biscotti", "fudge", "praline", "pralines",
    "popsicle", "popsicles", "flan", "cobbler", "crumble", "strudel",
    "beignet", "beignets",
    # NOTE: kolache removed — sausage kolache is real breakfast main
    "blizzard", "mcflurry",
    "kulfi",
    "rasmalai", "gulab", "jamun", "jalebi",
}
# "cake" handled separately due to crab cake / fish cake

# Side tokens
SIDE_TOKENS = {
    "fries", "fry", "frie",
    "tots",
    "puppies",
    "breadstick", "breadsticks",
    "poppers",
    "coleslaw", "slaw",
    "applesauce",
    "cornbread",
    "hashbrown", "hashbrowns",
    "tater",
    "grits",
    "edamame",
}

# Sauce tokens (pure sauces alone)
SAUCE_BARE = {
    "ranch", "mayo", "mayonnaise", "ketchup", "mustard",
    "salsa", "guacamole", "queso", "hummus", "tahini",
    "tartar", "tarter", "remoulade", "gravy",
    "syrup", "jam", "jelly", "preserves", "honey",
    "aioli", "vinaigrette", "chimichurri", "chutney",
    "pesto",
}

# Bare ingredients (drop alone or in pure ingredient combos)
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
    "salmon", "tilapia",
    "duck", "veal", "venison",
    "asparagus", "eggplant",
    "anchovy", "anchovies",
    "snapper",
    "scallops", "scallop",
    "calamari",
    "oyster", "oysters", "mussels", "clams",
    "octopus",
    "crawfish",
    "catfish",
    "yellowtail",
    "mahi", "swordfish", "halibut", "trout",
    "spinach",
}

# Marketing fluff (alone or fully composed)
MARKETING_TOKENS = {
    "happy", "delight", "delights", "supreme", "deluxe", "premium",
    "favorite", "favorites", "classic", "classics", "original", "originals",
    "signature", "signatures", "special", "specials", "today", "todays",
    "featured", "fresh", "best", "popular", "famous",
    "new", "limited",
    "kids", "kid", "adult",
    "mini", "regular", "jumbo",
    "house", "chef", "chefs", "homestyle", "homemade",
    "extra", "extras",
    "togo", "takeout", "takeaway",
    "any",
    "side", "sides",
}

# Fragment generic tokens (non-dish words)
FRAGMENT_GENERIC = {
    "item", "items", "stuff", "thing", "things",
    "menu", "list", "section",
    "and", "or", "the", "a", "of", "in", "on", "with", "for", "by",
    "is", "are", "was", "were",
    "u", "n", "d", "s", "t", "y", "x", "p", "z", "f",
    "your", "own", "build", "make", "create", "pick", "choose", "design",
    "to", "go", "out", "take",
    "small", "medium", "large",
}

# Generic vessel/category words — alone are FRAGMENT, but with identifier are OK
GENERIC_VESSELS_FRAGMENT_ALONE = {
    "pizza", "pizzas", "burger", "burgers", "wrap", "wraps", "bowl", "bowls",
    "sandwich", "sandwiches", "sub", "subs", "pasta", "salad", "salads",
    "soup", "soups", "stew", "stews", "chili",
    "platter", "platters", "plate", "plates", "combo", "combos",
    "meal", "meals", "dinner", "lunch", "breakfast", "brunch",
    "tray", "trays", "bucket", "buckets",
    "wing", "wings", "tender", "tenders", "nugget", "nuggets",
    "rib", "ribs", "steak", "steaks",
    "drumstick", "drumsticks",
    "chop", "chops",
    "fillet", "fillets", "filet", "filets",
    "skewer", "skewers", "kebab", "kebabs", "kabob", "kabobs",
    "roll", "rolls",
    "pita", "pitas",
    "naan",
    "bagel", "bagels",
    "toast", "toasts",
    "pancake", "pancakes",
    "waffle", "waffles",
    "crepe", "crepes",
    "biscuit", "biscuits",
    "muffin", "muffins",
    "scramble",
    "omelet", "omelette",
    "sushi",
    "noodle", "noodles",
    "fries",
    "appetizer", "appetizers", "starter", "starters",
    "entree", "entrees", "main", "mains",
    "bread", "breads",
    "drink", "drinks", "beverage", "beverages",
    "dessert", "desserts",
    "veggie", "veggies", "vegetable", "vegetables", "vegan", "vegetarian",
    "meat", "meats",
    "sweet", "savory",
}

# Cooking-style descriptors — not specific enough alone but valid in dish names
COOKING_STYLE = {
    "fried", "grilled", "baked", "roasted", "broiled",
    "boiled", "steamed", "smoked", "blackened", "breaded", "crispy",
    "spicy", "mild", "hot", "cold", "sour", "salty",
    "lean", "season", "seasoned", "marinated",
    "raw",
    "stuffed", "loaded", "topped",
    "double", "triple",
    "mixed",
    "deep",  # deep-fried
    "crunchy", "crunch",
    "soft", "hard",
    "open", "closed",
    "wet", "dry",
    "battered", "buttered", "buttered",
    "sauteed", "saute",
    "braised", "poached",
    "charred", "charbroiled", "chargrilled",
    "smashed",
    "shredded",
    "pulled",
    "ground",
    "minced",
    "chopped",
    "sliced",
    "whole",
    "boneless", "skinless",
    "bone-in", "bonein",
    "rotisserie",
}

# Specific cuisine / flavor / sauce descriptors — paired with anchor/protein → keep
SPECIFIC_DESCRIPTORS = {
    "broccoli", "mushroom", "mushrooms", "garlic", "ginger",
    "orange", "lemon", "lime", "pineapple", "mango",
    "almond", "cashew", "walnut", "peanut", "sesame",
    "alfredo", "marinara", "pesto", "carbonara", "bolognese",
    "florentine", "milanese", "piccata", "picata", "marsala", "francese",
    "tikka", "korma", "vindaloo", "biryani", "curry", "masala",
    "tandoori", "saag", "palak", "makhani", "kadai", "karahi", "karahai",
    "manchurian", "schezwan", "hakka",
    "teriyaki", "katsu", "tempura", "yakitori",
    "bulgogi", "kalbi", "galbi",
    "pad", "satay",
    "barbacoa", "carnitas", "pastor", "asada", "tinga", "milanesa",
    "ranchero", "rancheros", "verde", "rojo", "roja", "verdes", "rojos",
    "buffalo", "bbq", "honey",
    "jerk", "creole", "cajun",
    "schnitzel", "wellington", "stroganoff",
    "scampi",
    "parmesan", "parm", "parmigiana",
    "kiev", "cordon", "bleu",
    "hunan", "szechuan", "sichuan", "mongolian",
    "katsudon",
    "pao", "tso",
    "hawaiian",
    "philly",
    "rueben", "reuben",
    "monte", "cristo",
    "shawarma",
    "gyro", "souvlaki",
    "kafta", "kofta", "kibbeh",
    "fajita", "fajitas",
    "enchilada", "enchiladas",
    "burrito", "burritos",
    "quesadilla", "quesadillas",
    "taco", "tacos",
    "tostada", "tostadas",
    "tamale", "tamales",
    "molcajete",
    "chateaubriand",
    "haleem", "nihari",
    "do", "piazza", "methi", "kathmandu", "fraizee",
    "vijayawada", "hyderabadi", "lucknowi", "chettinad", "mughlai",
    "bihari", "lahori", "desi",
    "chapli", "boti", "sheek", "seekh",
    "kabab", "kebab",
    "scarpariello", "scarparela",
    "souvlaki", "doner",
    "puttanesca", "amatriciana", "primavera",
    "vodka", "arrabbiata",
    "katsu",
    "fricassee", "cacciatore",
    "vongole",
    "saltimbocca", "ossobuco",
    "scallop", "scallops",  # specific shellfish (when used as descriptor)
    "kabob",
    "chowder", "bisque", "gumbo", "jambalaya", "etouffee",
    "albondigas",
    "pozole", "menudo", "birria", "quesabirria",
    "lengua", "tripa", "cabeza", "cabrito", "lechon",
    "ceviche", "aguachile",
    "torta", "tortas", "huarache", "huaraches", "tlayuda",
    "nachos",
    "chimichanga", "chimichangas",
    "flautas", "flauta", "taquitos", "taquito",
    "sopes", "sope", "gorditas", "gordita",
    "milanesa",
    "elote", "esquites",
    "salsa", "verde", "roja",
    "pollo", "puerco", "res",  # spanish
    "asado", "parrillada", "parillada", "parrilada", "discada",
    "chilaquiles", "rancheros", "huevos", "migas",
    "frittata", "shakshuka",
    "benedict", "florentine",
    "denver", "western",
    "matar", "shahi", "rogan", "josh", "chettinad",
    "dum", "biryani", "haleem", "nihari",
    "vindaloo", "korma", "tikka", "tandoori",
    "kashmiri",
    "punjabi", "gujarati", "south", "north", "andhra",
    "calabrese",
    "puntas",
    "vapor",  # al vapor (steamed)
    "molcajete",
    "everest", "kathmandu",  # Nepali specials
    "yucatan", "oaxaca", "veracruz",
    "diablo",
    "mojo",
    "jalfrezi", "jalfrazie",
    "pasanda",
    "bombay", "bengali", "amritsari",
    "frankie", "kati", "kathi", "frankie",
    "doner", "iskender", "adana",
    "habanero", "chipotle", "ancho", "pasilla", "guajillo",
    "poblano", "serrano", "morita",
    "jalapeno",
    "saigon",
    "singapore",
    "thai", "vietnamese", "korean", "japanese", "indian",
    "tex", "mex",
    "florentine", "florentina",
    "michoacana", "norteno", "regio",
    "ahogada", "cubana",
    "ranchero",
    "yakiniku", "sukiyaki", "shabu",
    "tonkotsu", "shoyu", "miso", "shio",
    "tom", "yum", "kha",
    "som", "tum", "larb",
    "khao", "soi",
    "rendang",
    "laksa",
    "hainanese",
    "char", "siu",
    "peking",
    "lemongrass",
    "banh", "mi", "bun", "ga", "bo", "cha",
    "boudin", "andouille",
    "muffuletta",
    "vapor",
    "puttanesca",
    "fritto",
    "scaloppine",
    "boscaiola", "diavola",
    "calzone",
    "primavera",
    "paesana",
    "siberia",  # could be a regional name
    "trompo",  # Mexican vertical spit
    "lao",
    "country",  # country fried steak
    "diner",
    "bombay", "punjabi",
    "bengali",
    "kerala",
    "goa", "goan",
    "afghan", "afghani",
    "turkish",
    "ethiopian",
    "moroccan",
    "lebanese",
    "iranian", "persian",
    "armenian",
    "burmese", "myanmar",
    "filipino",
    "hawaiian", "kalua",
    "cuban", "cubano",
    "puerto", "puertorican",
    "dominican",
    "jamaican", "jerk",
    "haitian",
    "salvadoran",
    "salvadore", "salvador",
    "honduran",
    "guatemalan",
    "venezuelan",
    "peruvian",
    "argentine", "argentinian", "argentinean",
    "brazilian",
    "colombian",
    "ecuadorian",
    "kashmiri", "punjabi", "gujarati",
    "trinidadian",
    "barbadian",
    "ackee",
    "saltfish",
    "doubles",
    # Indian potato/etc
    "aloo", "gobi", "matar", "chana", "paneer", "palak", "saag",
    "rajma", "chole",
    # Japanese specific
    "hamachi", "uni", "ikura", "unagi", "anago", "tako", "ebi",
    "saba", "tai", "hirame", "amaebi", "toro",
    "crudo",
    "wagyu",
    # Korean
    "kalbi", "galbi", "bulgogi", "soondubu",
    # Other
    "pibil", "cochinita",  # cochinita pibil
    "valenciana",
    "shanghai",
    "hyderabadi",
    "jalfrezi", "jalfrazie",
    "pasanda",
    # cooking words that imply real dish
    "smokey", "smoky",
    # asian
    "moo", "shu",  # moo shu / mo shu
    "mo",
    # Spanish dishes
    "ahogada", "campechano",
    "diavola", "boscaiola", "paesana",
    # vietnamese
    "vermicelli",
    # nigerian
    "egusi", "ogbono", "edikang", "afang", "banga", "amala",
    # european
    "scaloppine", "scallopini",
    # spanish meats
    "machaca",
    "barbacoa", "carnitas",
    # other ethnic identifiers
    "moilee",  # Indian fish curry
    "lomito",  # Argentine
    "cachapas",  # Venezuelan
    "mezze", "mezza",
    "souvlaki", "yufka",
    # specific cuts
    "porterhouse", "ribeye", "sirloin", "tenderloin",
    "flank", "skirt", "tomahawk",
    "tbone", "t-bone",
    # bbq
    "andouille", "boudin",
    "kielbasa",
    "burnt",  # burnt ends
    # po boy
    "boy", "po",  # alphabetized
    # other
    "aglio",  # olio aglio
    "olio",
    "scotch",  # scotch eggs
    # Cuisine descriptors — paired with anything → real dish category
    "italian", "mexican", "asian", "american", "chinese", "indian",
    "korean", "japanese", "thai", "greek", "french", "spanish",
    "vietnamese", "filipino", "russian", "german", "ethiopian",
    "moroccan", "lebanese", "afghan", "afghani", "iranian", "persian",
    "armenian", "turkish", "burmese", "irish", "british", "english",
    "polish", "portuguese", "brazilian", "argentine", "argentinian",
    "peruvian", "colombian", "venezuelan", "cuban", "puertorican",
    "dominican", "haitian", "jamaican", "caribbean",
    "salvadoran", "guatemalan", "honduran", "nicaraguan",
    "tex-mex", "texmex",
    "cantonese", "szechuan", "sichuan", "hunan", "shanghai", "taiwanese",
    "georgian",  # chicken tabaka
    "nepalese", "nepali",
    "lao", "laotian",
    # Region descriptors
    "bangkok", "saigon", "hanoi", "tokyo", "seoul",
    "punjab", "punjabi", "kerala", "goan", "andhra", "tamil",
    "bengali", "kashmiri", "rajasthani", "marathi", "gujarati",
    "manchurian",
    "yucatan", "oaxaca", "veracruz", "michoacan", "puebla",
    "alabama", "carolina", "memphis", "kansas", "texas", "kentucky",
    "buffalo", "nashville", "philly", "philadelphia",
    "manhattan", "brooklyn", "boston", "chicago", "florentine",
    "tuscan", "sicilian", "neapolitan", "roman", "milanese",
    "navratan",  # navratan korma
    "tabaka", "kushiage", "kushikatsu",
    "panang",
    "pulao", "pulav", "polou", "polo",
    "cholay", "cholaay", "chole",
    "bokkeum", "jeyuk",
    "chaat", "bhalla", "dahi",
    "achar",
    # cuts/styles
    "charbroiled", "char-broiled",
    # sauce / cooking
    "hot pot", "claypot",
    "korean bbq", "kbbq",
    "kimchi",  # generic but specific dish
}

# Single-word standalone main dishes (uniquely identify a dish)
SINGLE_WORD_MAINS = {
    "cheeseburger", "hamburger", "whopper", "bigmac", "mcrib",
    "carbonara", "lasagna", "lasagne", "spaghetti", "linguine",
    "ravioli", "gnocchi", "fettuccine", "rigatoni",
    "ramen", "udon", "soba", "pho",
    "biryani", "tandoori",
    "shawarma",
    "souvlaki",
    "falafel", "stroganoff",
    "bibimbap", "bulgogi", "japchae", "tteokbokki",
    "moussaka",
    "shakshuka",
    "kibbeh",
    "tagine", "tajine",
    "feijoada",
    "borscht", "goulash",
    "haggis",
    "bratwurst", "currywurst", "sauerbraten",
    "couscous",
    "jollof", "fufu", "injera",
    "poutine", "tourtiere",
    "cassoulet", "ratatouille", "bouillabaisse",
    "ossobuco", "saltimbocca",
    "rendang", "satay",
    "tonkatsu", "katsudon", "oyakodon", "gyudon", "unadon", "tendon",
    "okonomiyaki", "takoyaki",
    "schnitzel",
    "menudo", "pozole", "posole", "birria", "milanesa",
    "carnitas", "barbacoa", "chilaquiles", "chimichanga",
    "huarache", "tlayuda", "quesabirria",
    "spanakopita",
    "kushari",
    "naengmyeon", "samgyeopsal", "buldak", "kimbap",
    "vindaloo", "korma", "saag",
    "dosa", "uttapam", "idli", "thali", "manchurian",
    "paneer",
    "paella", "risotto",
    "lengua", "cabrito", "lechon",
    "katsu",
    "frittata",
    "rancheros",
    "cheesesteak",
    "minestrone",
    "gumbo", "jambalaya", "etouffee",
    "tabbouleh", "fattoush",
    "porchetta",
    "wellington",
    "ceviche",
    "tamales",
    "samosa", "samosas", "pakora", "pakoras",
    "pierogi", "pierogies",
    "empanada", "empanadas",
    "arepa", "arepas",
    "pupusa", "pupusas",
    "dumplings",
    "potstickers", "wontons", "gyoza",
    "lumpia",
    "calzone", "calzones", "stromboli",
    "sashimi", "tempura",
    "donburi",
    "philly",
    "muffuletta",
    "reuben",
    "blt",
    "tortellini",
    "casserole",
    "meatloaf", "meatballs",
    "haleem",
    "broast", "broasted",
    "asun",
    "ewedu",
    "dorilocos",
    "discada",
    "parrillada", "parillada", "parrilada",
    "chateaubriand",
    "cioppino",
    "khichdi", "khichri",
    "appam",
    "nihari",
    "kothu",
    "bhel",
    "torta", "tortas",
    "gordita", "gorditas",
    "flauta", "flautas",
    "sope", "sopes",
    "taquito", "taquitos",
    "chimichangas",
    "tostada", "tostadas",
    "enchilada", "enchiladas",
    "fajitas", "fajita",
    "quesadilla", "quesadillas",
    "burrito", "burritos",
    "taco", "tacos",
    "nachos",
    "chilaquiles",
    "carnitas",
    "barbacoa",
    "molcajete",
    "milanesa",
    "huevos",
    "asado",
    "albondigas",
    "ropa",
    "feijoada",
    "moussaka",
    "doubles",
    "ackee",
    "kushari",
    "kibbeh", "kafta", "kofta",
    "shish",
    "tahdig", "fesenjan",
    "manakish", "manaqish",
    "biryani", "haleem", "nihari", "korma",
    "vindaloo", "tikka", "tandoori",
    "saag", "palak", "rajma", "chole",
    "samosa", "pakora",
    "rendang",
    "laksa",
    "hainanese",
    "tonkotsu",
    "ramen", "udon", "soba",
    "okonomiyaki",
    "takoyaki",
    "tonkatsu",
    "bulgogi",
    "japchae",
    "tteokbokki",
    "samgyeopsal",
    "kimbap",
    "naengmyeon",
}

# Compound dish phrases — substring match → KEEP
COMPOUND_PHRASES = {
    "kung pao", "general tso", "moo shu", "moo goo",
    "butter chicken", "tikka masala", "chicken tikka",
    "chana masala", "saag paneer", "palak paneer", "matar paneer",
    "biscuits gravy", "biscuits and gravy",
    "fish chips", "fish and chips",
    "chicken waffles", "chicken and waffles",
    "mac cheese", "mac and cheese", "macaroni cheese",
    "pad thai", "pad see ew", "drunken noodles",
    "salisbury steak", "swedish meatballs",
    "frito pie",
    "pot pie", "shepherd pie", "shepherds pie", "cottage pie", "fish pie",
    "meat pie", "savory pie", "hand pie", "chicken pie",
    "pulled pork", "pulled chicken",
    "egg roll", "egg rolls", "spring roll", "spring rolls",
    "summer roll", "summer rolls",
    "lobster roll",
    "california roll",
    "philly cheesesteak", "cheese steak",
    "patty melt", "tuna melt",
    "buffalo chicken", "buffalo wings",
    "club sandwich",
    "rib eye", "new york strip", "ny strip", "prime rib",
    "fried chicken", "roast chicken", "baked chicken", "grilled chicken",
    "rotisserie chicken",
    "egg foo young", "foo young",
    "lo mein", "chow mein", "chow fun", "mei fun", "ho fun",
    "tso chicken", "pao chicken",
    "country fried steak", "chicken fried steak", "chicken fried",
    "italian beef", "italian sub",
    "meatball sub", "meatball sandwich",
    "egg sandwich", "breakfast sandwich",
    "monte cristo", "croque monsieur", "croque madame",
    "bourbon chicken",
    "garlic noodles",
    "stir fry", "fry stir",
    "mongolian beef", "mongolian chicken",
    "honey walnut shrimp",
    "fish taco", "shrimp taco", "carne asada", "al pastor",
    "carne asada taco",
    "lengua taco", "tripa taco", "asada taco",
    "albondigas",
    "beef broccoli", "broccoli beef",
    "cashew chicken",
    "orange chicken", "lemon chicken",
    "chicken parmesan", "veal parmesan", "eggplant parmesan", "eggplant parm",
    "chicken alfredo", "shrimp alfredo",
    "fettuccine alfredo",
    "chicken marsala", "chicken piccata", "chicken francese",
    "chicken cacciatore",
    "chicken katsu", "pork katsu",
    "beef bulgogi", "pork bulgogi",
    "fried rice", "rice fried",
    "lo mein", "chow mein",
    "honey chicken", "honey shrimp",
    "garlic chicken", "garlic shrimp",
    "sesame chicken", "sesame shrimp",
    "ginger chicken", "ginger beef",
    "pepper steak", "pepper chicken",
    "salt pepper", "salt and pepper",
    "ma po", "mapo tofu",
    "kung pao chicken", "kung pao shrimp", "kung pao beef", "kung pao tofu",
    "sweet sour", "sweet and sour",
    "moo goo gai pan",
    "happy family",
    "char siu",
    "peking duck", "roast duck", "crispy duck",
    "lemongrass chicken", "lemongrass beef",
    "banh mi",
    "bun bo", "bun cha",
    "tom yum", "tom kha",
    "green curry", "red curry", "yellow curry", "massaman curry", "panang curry",
    "pad see ew", "pad kee mao", "pad thai",
    "khao soi",
    "som tum",
    "larb gai", "larb moo",
    "nasi goreng", "mie goreng",
    "satay chicken", "chicken satay", "beef satay",
    "rendang beef",
    "kimchi jjigae", "kimchi stew",
    "sundubu", "soondubu",
    "tonkotsu ramen", "miso ramen", "shoyu ramen", "shio ramen",
    "shrimp tempura", "vegetable tempura",
    "chicken katsu", "pork katsu", "katsu curry",
    "katsu don", "oyako don", "gyu don", "una don", "ten don",
    "spicy tuna roll", "spicy salmon roll",
    "rainbow roll", "dragon roll", "philadelphia roll",
    "dynamite roll", "volcano roll",
    "uni nigiri", "salmon nigiri", "tuna nigiri",
    "pulled pork sandwich", "brisket sandwich",
    "philly cheesesteak", "cheesesteak hoagie",
    "italian sub", "italian hoagie", "italian hero",
    "chicken parm sub", "meatball sub", "eggplant parm sub",
    "bbq pulled pork",
    "bbq ribs", "baby back ribs", "st louis ribs",
    "rack of lamb", "lamb shank",
    "beef wellington",
    "duck confit",
    "coq au vin",
    "beef bourguignon",
    "boeuf bourguignon",
    "chicken cordon bleu",
    "chicken kiev",
    "chicken fricassee",
    "veal parmigiana",
    "eggplant parmigiana",
    "spaghetti carbonara", "spaghetti bolognese", "spaghetti meatballs",
    "spaghetti and meatballs",
    "lasagna bolognese",
    "shrimp scampi",
    "linguine clam",
    "linguine alle vongole",
    "penne arrabbiata", "penne vodka",
    "rigatoni bolognese",
    "ravioli ricotta", "lobster ravioli",
    "gnocchi pesto",
    "risotto mushroom", "mushroom risotto",
    "paella valenciana", "seafood paella",
    "ossobuco",
    "saltimbocca",
    "veal scaloppine",
    "carne asada",
    "al pastor",
    "carnitas tacos",
    "barbacoa tacos",
    "lengua tacos",
    "fish tacos", "shrimp tacos",
    "chicken enchiladas", "cheese enchiladas", "beef enchiladas",
    "chicken quesadilla", "steak quesadilla", "shrimp quesadilla",
    "huevos rancheros", "huevos divorciados",
    "chilaquiles rojos", "chilaquiles verdes",
    "chiles rellenos", "chile relleno",
    "menudo rojo",
    "pozole rojo", "pozole verde",
    "birria tacos", "quesabirria",
    "torta ahogada", "torta cubana",
    "molcajete",
    "fajita beef", "beef fajita", "chicken fajita", "shrimp fajita",
    "fajita mixta", "mixed fajita",
    "burrito chicken", "chicken burrito", "beef burrito", "bean burrito",
    "breakfast burrito", "california burrito", "burrito bowl",
    "wet burrito", "smothered burrito",
    "nachos supreme", "loaded nachos",
    "tostada chicken", "chicken tostada",
    "ceviche shrimp", "shrimp ceviche", "fish ceviche",
    "aguachile",
    "elote",
    "esquites",
    "tlayuda",
    "sopa azteca", "sopa de tortilla", "tortilla soup",
    "frijoles charros",
    "rice and beans", "beans and rice",
    "gallo pinto",
    "ropa vieja",
    "moros y cristianos",
    "lechon asado",
    "arroz con pollo",
    "cubano",
    "media noche",
    "jerk chicken", "jerk pork",
    "oxtail stew",
    "curry goat", "goat curry", "curry chicken",
    "rice and peas", "peas and rice",
    "ackee saltfish", "ackee and saltfish",
    "doubles",
    "patty jamaican", "jamaican patty",
    "fried plantain",
    "tostones", "maduros",
    "yuca frita",
    "empanada beef", "empanada chicken",
    "arepa reina pepiada",
    "pupusa cheese", "pupusa pork",
    "pollo asado", "pollo a la brasa",
    "lomo saltado", "aji de gallina",
    "anticuchos",
    "feijoada",
    "moqueca",
    "churrasco",
    "picanha",
    "milanesa",
    "chimichurri steak",
    "fish gyro",
    "chicken gyro", "beef gyro", "lamb gyro", "pork gyro",
    "gyro plate",
    "souvlaki chicken", "chicken souvlaki",
    "souvlaki pork", "pork souvlaki",
    "moussaka",
    "spanakopita",
    "tiropita",
    "pastitsio",
    "dolma", "dolmades",
    "tabbouleh", "fattoush",
    "hummus plate",
    "baba ghanoush",
    "kibbeh",
    "kafta", "kofta",
    "shish kebab", "shish kabob", "shish tawook",
    "lamb shawarma", "chicken shawarma", "beef shawarma",
    "doner kebab",
    "manakish", "manaqish",
    "fattet",
    "kebab koobideh", "koobideh",
    "joojeh kabab",
    "barg kabab",
    "fesenjan",
    "ghormeh sabzi",
    "tahdig",
    "biryani lamb", "lamb biryani", "biryani goat", "goat biryani",
    "biryani vegetable", "vegetable biryani",
    "haleem chicken", "chicken haleem", "lamb haleem",
    "nihari beef", "beef nihari", "nihari lamb",
    "kheer",
    "samosa potato", "potato samosa", "samosa beef", "beef samosa",
    "naan garlic", "garlic naan", "butter naan", "cheese naan",
    "paratha aloo", "aloo paratha",
    "dosa masala", "masala dosa",
    "uttapam onion", "onion uttapam",
    "idli sambar",
    "vada pav", "pav bhaji",
    "chole bhature",
    "rajma chawal",
    "korma chicken", "chicken korma",
    "vindaloo lamb", "lamb vindaloo", "vindaloo pork", "pork vindaloo",
    "tikka chicken", "chicken tikka",
    "tandoori chicken", "tandoori shrimp", "tandoori fish",
    "rogan josh",
    "saag chicken", "chicken saag",
    "palak chicken", "chicken palak",
    "paneer butter masala",
    "paneer tikka",
    "paneer makhani",
    "shahi paneer",
    "kadai chicken", "chicken kadai", "karahi chicken", "karahai chicken",
    "chettinad chicken",
    "hyderabadi biryani",
    "lucknowi biryani",
    "vijayawada biryani",
    "mughlai chicken",
    "do piazza", "piazza do",
    "methi chicken",
    "boti kabab", "boti kebab",
    "sheek kebab", "seekh kebab",
    "chapli kabab", "chapli kebab",
    "bihari chicken", "bihari beef", "bihari kabab",
    "kathi roll", "kati roll", "kathi kabab roll",
    "frankie roll",
    "chicken 65", "65 chicken",
    "gobi manchurian", "chicken manchurian",
    "schezwan chicken",
    "hakka noodles",
    "veg fried rice",
    "fish curry", "fish masala",
    "prawn curry",
    "egg curry",
    "mutton curry", "mutton biryani", "mutton vindaloo", "mutton korma",
    "fried fish", "fried shrimp", "fried catfish",
    "fried calamari", "fried oyster",
    "fish sandwich",
    "blt sandwich",
    "club sandwich",
    "reuben sandwich",
    "patty melt",
    "tuna melt",
    "grilled cheese",
    "pancake stack", "pancakes stack",
    "french toast",
    "eggs benedict",
    "biscuits gravy",
    "huevos rancheros",
    "shrimp grits", "shrimp and grits",
    "country breakfast",
    "denver omelet", "western omelet", "veggie omelet", "ham omelet",
    "spanish omelet", "mexican omelet", "cheese omelet", "feta omelet",
    "egg scramble", "scrambled eggs",
    "burrito bowl", "rice bowl", "poke bowl",
    "buddha bowl", "acai bowl",
    "tuna roll", "salmon roll", "shrimp roll",
    "rainbow roll", "dragon roll", "volcano roll", "philadelphia roll",
    "dynamite roll", "crunch roll",
    "california roll",
    "tempura roll",
    "spider roll",
    "caterpillar roll",
    "lobster roll",
    "crab roll",
    "soft shell crab roll",
    "double cheeseburger", "bacon cheeseburger", "mushroom swiss",
    "smoked brisket", "smoked ribs", "smoked chicken", "smoked turkey",
    "burnt ends",
    "bbq ribs", "bbq chicken", "bbq pork", "bbq brisket",
    "rib tips",
    "drunken noodles",
    "khao soi",
    "tom yum", "tom kha",
    "green curry", "red curry", "yellow curry", "massaman curry", "panang curry",
    "som tum",
    "larb",
    "khao pad",
    "yum nua",
    "satay",
    "rendang",
    "nasi lemak", "nasi goreng",
    "mie goreng",
    "laksa",
    "char kway teow",
    "hainanese chicken",
    "wonton soup", "egg drop soup", "hot and sour soup",
    "miso soup",
    "char siu pork",
    "broasted chicken",
    "chicken broast", "broast chicken",
    "do piazza",
    "methi chicken",
    "kathmandu chicken", "chicken kathmandu",
    "fraizee lamb",
    "muffuletta",
    "italian beef",
    "frito pie",
    "shepherds pie", "shepherd pie",
    "cottage pie",
    "chicken pot pie", "beef pot pie", "turkey pot pie",
    "pot pie",
    # additions
    "chicken scarpariello", "chicken scarparela",
    "chicken vesuvio",
    "chicken francese",
    "chicken saltimbocca",
    "veal francese", "veal piccata", "veal marsala",
    "shrimp creole",
    "jambalaya",
    "etouffee",
    "po boy", "po boys", "boy po", "boys po",  # alphabetized po boy
    "po boy shrimp", "boy po shrimp", "po shrimp boy",
    "shrimp po boy",
    "fried catfish",
    "blackened catfish",
    "blackened fish",
    "blackened shrimp",
    "redfish",
    "crawfish boil", "shrimp boil",
    "crab boil",
    "lobster bisque",
    "she crab soup",
    "clam chowder", "corn chowder", "fish chowder",
    "tortilla soup",
    "pho beef", "pho chicken", "beef pho", "chicken pho",
    "bun bo hue",
    "bun bo nam bo",
    "bun cha",
    "vermicelli bowl",
    "vermicelli noodle",
    "bo luc lac",
    "ga lac lac",
    "salt baked",
    "soy sauce chicken",
    "five spice chicken",
    "three cup chicken",
    "general gau",
    "chicken combo plate",  # NOTE: combo+plate alone fragment, but with chicken let's pass thru as protein dish
    "chicken plate",
    "rice plate",  # actually fragment, ok
    # vermicelli
    "singapore noodle", "singapore noodles", "singapore vermicelli",
    "singapore style noodle", "singapore style vermicelli",
    # chinese
    "hunan beef", "hunan chicken", "hunan shrimp", "hunan pork",
    "szechuan beef", "szechuan chicken", "szechuan shrimp",
    "shredded beef", "shredded pork", "shredded chicken",
    "twice cooked pork",
    "ants on tree",
    "shanghai noodle", "shanghai noodles",
    "dan dan noodle", "dan dan noodles",
    # mexican more
    "carne asada plate", "asada plate",
    "asada burrito",
    "carnitas burrito", "carnitas plate",
    "barbacoa burrito", "barbacoa plate",
    "carnitas taco",
    "barbacoa taco",
    "lengua taco",
    "tripa taco",
    "cabeza taco",
    "al pastor taco", "pastor taco",
    "chorizo taco",
    "campechano taco",
    # breakfast
    "egg sandwich", "egg breakfast",
    "sausage egg", "egg sausage", "bacon egg", "egg bacon",
    "ham egg", "egg ham",
    "potato egg",
    "breakfast taco",
    "breakfast burrito",
    "machaca",
    "torta de huevo", "torta huevo",
    # other
    "cuban sandwich", "cubano sandwich",
    "ham swiss", "ham and swiss",
    "italian wedding soup",
    "wedding soup",
    "minestrone soup",
    "french onion soup",
    "split pea soup",
    "matzo ball soup",
    "lentil soup",
    "navy bean soup", "white bean soup",
    "ham and bean", "ham bean",
    "chicken noodle",
    "chicken tortilla",
    "chicken rice", "rice chicken",
    "beef stew", "lamb stew",
    "irish stew",
    "guinness stew",
    "brunswick stew",
    "burgoo",
    # more pasta
    "tortellini soup",
    "tortellini brodo", "brodo tortellini",
    "pasta primavera",
    "penne vodka",
    "linguine vongole",
    "carbonara spaghetti",
    "puttanesca spaghetti",
    "amatriciana", "amatriciana spaghetti",
    "fra diavolo",
    # more global
    "greek salad", "caesar salad", "cobb salad", "wedge salad",
    "garden salad",
    "chef salad",
    "antipasto salad",
    "caprese salad",
    "nicoise salad",
    "panzanella",
    "fattoush",
    "tabbouleh",
    # turkish
    "iskender kebab", "doner kebab", "adana kebab", "urfa kebab",
    "shish tawook",
    "lahmacun",
    "iman bayildi",
    "manti",
    # afghan/persian
    "kabuli pulao", "qabuli palaw", "afghan pulao",
    "mantu",
    "ashak",
    "bolani",
    # ethiopian
    "doro wat", "doro tibs", "tibs", "kitfo", "shiro",
    "injera",
    "wat",
    # caribbean
    "ackee and saltfish",
    "rice and peas",
    "callaloo",
    "curry chicken", "curry goat",
    "brown stew chicken",
    "escovitch fish",
    # latin
    "pernil",
    "mofongo",
    "mangu",
    "tres golpes",
    "bandeja paisa",
    "arepa de queso",
    # filipino
    "adobo chicken", "chicken adobo", "pork adobo", "adobo pork",
    "lumpia",
    "pancit",
    "kare kare",
    "sinigang",
    "lechon kawali",
    "sisig",
    "halo halo",
    # bbq
    "smoked sausage", "smoked turkey", "smoked brisket", "smoked ribs",
    "burnt ends",
    "pulled pork sandwich",
    "brisket sandwich",
    "rib tips",
    "hot link",
    # subs
    "italian sub", "italian hoagie", "italian beef", "italian sausage",
    "philly sub",
    "meatball sub",
    "chicken parm sub",
    "eggplant parm sub",
    "veggie sub",
    "tuna sub",
    "ham and cheese", "ham cheese",
    "turkey and cheese", "turkey cheese", "turkey sandwich",
    "roast beef", "roast beef sandwich",
    "corned beef", "pastrami",
    # asian misc
    "wonton noodle", "wonton noodles",
    "wonton soup",
    "dumpling soup",
    "noodle soup",
    "beef noodle soup",
    "chicken noodle soup",
    "duck noodle soup",
    "fish ball noodle",
    # poke
    "poke bowl", "tuna poke", "salmon poke",
    # ahi
    "ahi tuna", "ahi poke", "ahi tuna poke",
    "blackened ahi",
    # sushi extras
    "sashimi platter", "sushi platter",
    "chirashi bowl", "chirashi don",
    "katsudon",
    "oyakodon",
    "donburi",
    # more
    "bistec encebollado",
    "bistec a caballo",
    "bistec ranchero",
    "bistec de puerco",
    "bistec de pollo",
    "bistec de res",
    "bistec ranchero",
    "milanesa de pollo", "milanesa de res",
    "machaca con huevo",
    "huevos a la mexicana", "huevos mexicana",
    "chilaquiles",
    # peri peri
    "peri peri chicken", "peri chicken",
    # more wings
    "lemon pepper wings", "garlic parmesan wings", "honey hot wings",
    "boneless wings",
    "buffalo wings",
    "bbq wings",
    "teriyaki wings",
    # tex-mex / mexican
    "queso flameado",
    "fundido",
    "queso fundido",
    "guacamole",
    "chile verde",
    "chile colorado",
    "carne guisada",
    "ropa vieja",
    "vaca frita",
    "lechon asado",
    # more regional
    "loco moco",
    "kalua pork",
    "spam musubi",
    "saimin",
    "loco moco",
    # nigerian
    "jollof rice",
    "egusi soup",
    "okra soup",
    "ewedu", "gbegiri",
    "amala",
    "pounded yam",
    "fufu",
    "moin moin",
    "akara",
    "puff puff",
    "suya",
    "asun",
    "isi ewu",
    "nkwobi",
    "afang",
    "edikang ikong",
    "banga",
    # ghanaian
    "waakye",
    "kelewele",
    "kontomire",
    # somali
    "anjero",
    "muqmad",
    # ethiopian more
    "kitfo",
    "tibs",
    "doro wat",
    "shiro",
    "atkilt",
    "gomen",
    "misir",
    "kik wat",
    # singaporean
    "char kway teow",
    "chai tow kway",
    "chicken rice",
    "fish head curry",
    # vietnamese more
    "banh xeo", "banh khot",
    "nem nuong",
    "cha gio",
    "bo luc lac", "luc lac",
    "ca kho", "ca kho to",
    "thit kho",
    "canh chua",
    "bun rieu", "bun mam",
    # other
    "big mac",
    "quarter pounder",
    "double down",
    "filet o fish",
    # sliders / wraps
    "buffalo chicken wrap",
    "chicken caesar wrap",
    "veggie wrap",
    "spicy chicken sandwich",
    "fried chicken sandwich",
    "chicken parmesan sandwich",
    # add: po boy variants alphabetized
    "boy po", "po boy",
}

# Stuff to keep specially even if might trigger DROPs:
KEEP_OVERRIDES = {
    # alphabetized real dishes
    "asun",
    "ewedu",
    "doubles",
    "ackee",
    "menemen",
}

# ============================================================================
# Patterns
# ============================================================================
INSTRUCTION_PATTERNS = [
    re.compile(r"\bbuild\b.*\bown\b"),
    re.compile(r"\bcreate\b.*\bown\b"),
    re.compile(r"\bmake\b.*\bown\b"),
    re.compile(r"\bdesign\b.*\bown\b"),
    re.compile(r"\bpick\b.*\b(your|own)\b"),
    re.compile(r"\bchoose\b.*\b(your|own)\b"),
    re.compile(r"\bcustomize\b"),
    re.compile(r"\bbuild own\b"),
    re.compile(r"\bown your\b"),
    re.compile(r"\byour own\b"),
    re.compile(r"\bany burger\b"),
    re.compile(r"\bany pizza\b"),
    re.compile(r"\bany sandwich\b"),
    re.compile(r"\binto make\b"),  # "any burger into make salad"
]

DEAL_PATTERNS = [
    re.compile(r"\bbogo\b"),
    re.compile(r"\b\d+\s*for\s*\$?\d+"),
    re.compile(r"\bbuy\s*\d+\s*get\b"),
    re.compile(r"\b\$\d+\s*deal\b"),
    re.compile(r"\bsave\s*\$"),
    re.compile(r"%\s*off"),
    re.compile(r"\bpromo\b"),
    re.compile(r"\blimited\s+time\b"),
]

BULK_PATTERNS = [
    re.compile(r"\bdozen\b"),
    re.compile(r"\bbucket\b"),
    re.compile(r"\bfamily\s+(meal|pack|box|pak|size|feast|dinner|bucket|platter|tray|bundle)\b"),
    re.compile(r"\bparty\s+(pack|tray|platter|box|size|bucket|bundle|wings|nuggets)\b"),
    re.compile(r"\bmeal\s+kit\b"),
    re.compile(r"\bvariety\s+pack\b"),
    re.compile(r"\bbox\s+of\b"),
    re.compile(r"\bbulk\b"),
    re.compile(r"\bcatering\b"),
    re.compile(r"\bfeeds\b"),
    re.compile(r"\bbundle\b"),
    re.compile(r"\bcrew\s+pack\b"),
    re.compile(r"\bgallon\b"),
    re.compile(r"\bsharing\b"),
    re.compile(r"\bpack\s+of\b"),
    re.compile(r"\b\d+\s*piece\s+(bucket|family|tray|platter|pack|box)\b"),
]

PROTEINS = {"chicken", "beef", "pork", "shrimp", "fish", "lamb", "turkey",
            "duck", "tofu", "salmon", "tuna", "crab", "lobster", "mutton",
            "goat", "veal", "venison", "bison", "ham", "bacon", "sausage",
            "chorizo", "carnitas", "barbacoa", "asada", "pastor",
            "lengua", "tripa", "cabeza",
            "snapper", "tilapia", "halibut", "trout", "catfish", "mahi",
            "swordfish", "yellowtail", "cod",
            "scallops", "scallop", "calamari", "octopus", "crawfish",
            "oyster", "oysters", "mussels", "clams",
            "paneer", "tempeh", "seitan",
            "egg", "eggs",
            "prawn", "prawns",
            "ahi", "hamachi",
            "ribeye", "sirloin", "porterhouse",
            "brisket",
            "milanesa",
            "puerco",  # spanish: pork
            "pollo",   # spanish: chicken
            "res",     # spanish: beef
            "carne",   # generic meat (pairs with asada/guisada)
            "pescado",  # spanish fish
            "camaron", "camarones",  # spanish shrimp
            "albondigas",  # meatballs
            "machaca",
            "pechuga", "muslo",  # chicken parts in spanish
            "ribeye", "sirloin", "tenderloin", "porterhouse",
            "tomahawk", "tbone",
            "wagyu",  # treat as protein anchor
            "kalbi", "galbi",
            "chuleta", "chuletas",  # spanish pork chop
            "milanesas",
            "pollos",
            "patty", "patties",
            "lardons", "pancetta", "guanciale",
            "kielbasa", "andouille", "boudin",
            "anchovy", "anchovies",
            "pepperoni",
            "salami",
            "uni", "ikura", "unagi", "ebi", "saba",
            "scallop",
            "rabbit",
            "quail",
            "frog",
            "perch", "bass", "pike", "walleye", "pollock",
            "redfish", "sea bass", "branzino",
            "marlin", "hake",
            "uni", "ikura", "unagi", "ebi", "saba", "tako",
            "hamachi",
            "lardons", "pancetta", "guanciale",
            "kielbasa", "andouille", "boudin",
            "bratwurst", "knockwurst",
            "elote",  # corn — sometimes a main, but typically appetizer
            }

ALL_ANCHORS = {
    "burger", "burgers", "cheeseburger", "cheeseburgers", "hamburger", "hamburgers",
    "sandwich", "sandwiches", "sub", "subs", "hoagie", "hoagies",
    "wrap", "wraps", "panini", "paninis",
    "burrito", "burritos", "taco", "tacos", "quesadilla", "quesadillas",
    "enchilada", "enchiladas", "tamale", "tamales", "fajita", "fajitas",
    "nachos", "tostada", "tostadas", "chimichanga", "chimichangas",
    "torta", "tortas", "pizza", "pizzas",
    "calzone", "calzones", "stromboli",
    "pasta", "spaghetti", "linguine", "fettuccine", "penne", "rigatoni",
    "ravioli", "lasagna", "lasagne", "gnocchi", "macaroni", "tortellini",
    "ramen", "udon", "soba", "pho", "noodles", "noodle",
    "biryani", "curry",
    "wings", "wing", "tenders", "tender", "nuggets", "nugget",
    "strips", "fingers", "drumstick", "drumsticks",
    "steak", "steaks", "ribeye", "sirloin", "filet", "filets", "fillet",
    "fillets", "porterhouse",
    "brisket", "ribs", "rib", "chops", "chop", "loin", "tenderloin",
    "schnitzel", "wellington",
    "salmon", "tuna", "tilapia", "cod", "halibut", "trout",
    "shrimp", "scampi", "lobster", "crab", "calamari", "scallops",
    "oysters", "mussels", "clams",
    "omelet", "omelette", "frittata", "quiche", "scramble", "scrambler",
    "benedict", "florentine",
    "bowl", "bowls", "plate", "plates", "platter", "platters", "combo",
    "stew", "stews", "chili", "soup", "bisque", "chowder", "gumbo",
    "jambalaya", "etouffee",
    "paella", "risotto",
    "kebab", "kebabs", "kabob", "kabobs", "shawarma",
    "gyro", "gyros", "souvlaki", "doner",
    "falafel", "casserole", "stroganoff", "kiev",
    "sushi", "sashimi", "tempura", "katsu",
    "donburi", "bibimbap", "bulgogi",
    "loaf", "meatloaf", "meatballs",
    "dumplings", "dumpling", "potstickers", "wontons", "gyoza",
    "samosa", "samosas", "pakora", "pakoras",
    "pierogi", "pierogies", "empanada", "empanadas",
    "arepa", "arepas", "pupusa", "pupusas",
    "pancake", "pancakes", "waffle", "waffles", "crepe", "crepes",
    "toast",
    "salad", "salads",
    "philly", "cheesesteak", "cheesesteaks",
    "blt", "club", "reuben",
    "whopper",
    "flautas", "flauta", "menudo", "sopes", "sope",
    "gorditas", "gordita", "carnitas", "barbacoa", "milanesa",
    "bao", "ceviche", "crawfish", "catfish",
    "huarache", "huaraches", "molcajete",
    "taquitos", "taquito",
    "saag", "palak", "dal", "daal",
    "yakitori", "yakisoba", "okonomiyaki", "takoyaki",
    "tonkatsu", "katsudon",
    "maki", "nigiri", "temaki", "uramaki", "futomaki", "chirashi",
    "rangoon", "rangoons",
    "spanakopita", "moussaka",
    "shakshuka", "kibbeh", "tagine", "tajine",
    "feijoada",
    "borscht", "goulash",
    "haggis", "boxty", "colcannon",
    "bratwurst", "currywurst", "sauerbraten",
    "couscous", "tabouli", "tabbouleh",
    "jollof", "fufu", "injera",
    "poutine", "tourtiere",
    "cassoulet", "ratatouille", "bouillabaisse", "coq", "confit",
    "ossobuco", "saltimbocca",
    "carbonara", "amatriciana", "puttanesca", "bolognese", "alfredo",
    "marinara", "primavera",
    "rendang", "satay", "nasi",
    "japchae", "tteokbokki", "kimbap", "buldak", "samgyeopsal",
    "salisbury",
    "minestrone", "pozole", "posole", "birria",
    "souffle",
    "quesabirria", "tlayuda",
    "tinga",
    "stack", "stacks", "melt", "melts",
    "chow", "lo", "fun", "mein",
    "roti", "naan", "paratha", "idli", "idly", "upma", "vada", "dosa",
    "uttapam", "uttappam", "sambhar", "sambar", "rasam", "thali", "biryanis", "kurma",
    "manchurian", "pakoda", "bhaji", "puri", "chole", "rajma",
    "paneer", "mole",
    "pita", "lavash", "sopa", "asado",
    "carnita", "lengua", "cabeza", "cabrito", "lechon",
    "kushari", "fattoush",
    "kebbeh", "larb",
    "jerk", "skillet", "skillets",
    "haleem", "nihari",
    "broast", "broasted",
    "asun", "ewedu",
    "discada", "parrillada", "parillada", "parrilada",
    "chateaubriand",
    "huevos", "rancheros", "chilaquiles", "migas",
    "muffuletta",
    "roll", "rolls",
    "banh", "mi", "bun", "ga", "bo",
    "pad",
    "manaqish", "manakish",
    "pho",
    "tendon",
    "moqueca",
    "feijoada", "churrasco", "picanha",
    "doubles",
    "ackee",
    "kibbeh", "kafta", "kofta",
    "shish",
    "tahdig", "fesenjan",
    # protein-style anchors
    "machaca",
    # spanish anchors
    "pollo", "puerco", "res", "carne", "pescado",
    "camaron", "camarones",
    "filete",
    "guisada", "guisado",
    "bistec",
    "mojarra",
    "pechuga",
    "ranchero", "rancheros",
    # po boy
    "boy", "po",
    # vermicelli
    "vermicelli",
    # adobo
    "adobo",
    # patty (jamaican, philly)
    "patty", "patties",
}

# ============================================================================
# Helpers
# ============================================================================
def has_word(name, word):
    return re.search(r"\b" + re.escape(word) + r"\b", name) is not None

def has_any_word(name, words):
    tokens = set(name.split())
    return any(w in tokens for w in words)

def has_phrase(name, phrases):
    for p in phrases:
        if " " in p:
            if p in name:
                return True
        else:
            if re.search(r"\b" + re.escape(p) + r"\b", name):
                return True
    return False

def matches_any_pattern(name, patterns):
    return any(p.search(name) for p in patterns)

# ============================================================================
# Classifier
# ============================================================================
def classify(name):
    n = name.strip().lower()
    if not n:
        return "drop", "fragment"

    tokens = n.split()
    token_set = set(tokens)

    # Pure numeric / single short
    if all(re.fullmatch(r"\d+|\w", t) for t in tokens):
        return "drop", "fragment"

    # Lots of single-char tokens => fragment
    short_tokens = sum(1 for t in tokens if len(t) <= 1)
    if short_tokens >= 3:
        return "drop", "fragment"
    if len(tokens) >= 3 and short_tokens >= len(tokens) * 0.5:
        return "drop", "fragment"

    # Strings of just numbers and single chars (e.g. "1 1 2 2 pizza")
    nonnoise = [t for t in tokens if not re.fullmatch(r"\d+", t) and len(t) > 1]
    if len(nonnoise) <= 1 and len(tokens) >= 3:
        # mostly numbers/single chars
        return "drop", "fragment"

    # 1. Instruction
    if matches_any_pattern(n, INSTRUCTION_PATTERNS):
        return "drop", "instruction"

    # 2. Deals
    if matches_any_pattern(n, DEAL_PATTERNS):
        return "drop", "deal"

    # 3. Bulk
    if matches_any_pattern(n, BULK_PATTERNS):
        return "drop", "bulk"

    # 4. Drink
    drink_hits = token_set & DRINK_TOKENS
    if drink_hits:
        # If protein + anchor or compound phrase, might be food (e.g. bourbon chicken)
        if any(t in PROTEINS for t in tokens) and (
                token_set & ALL_ANCHORS or has_phrase(n, COMPOUND_PHRASES)):
            pass
        # Special exceptions:
        # - vodka + pasta/pizza/rigatoni/penne → vodka sauce dish
        elif "vodka" in token_set and (
                token_set & {"pasta", "pizza", "penne", "rigatoni",
                             "spaghetti", "linguine", "fettuccine",
                             "tortellini", "ravioli", "lasagna", "lasagne",
                             "gnocchi", "noodle", "noodles", "sauce"}):
            pass
        # - margarita / margherita pizza
        elif "margarita" in token_set and (
                token_set & {"pizza", "pizzas", "pie", "pies", "sandwich",
                             "sandwiches", "calzone", "stromboli"}):
            pass
        elif "margherita" in token_set:
            pass
        # - monster burger / monster wings (size descriptor)
        elif "monster" in token_set and (
                token_set & {"burger", "burgers", "wings", "wing",
                             "sandwich", "sandwiches", "cheeseburger",
                             "hamburger", "pizza", "pizzas", "fries"}):
            pass
        # - whiskey/bourbon + protein dish
        elif (token_set & {"whisky", "whiskey", "bourbon"}) and (
                token_set & PROTEINS):
            pass
        # - scotch eggs (British dish)
        elif "scotch" in token_set and (token_set & {"egg", "eggs"}):
            pass
        # - beer-battered fish/etc
        elif "beer" in token_set and (
                token_set & PROTEINS or
                token_set & {"battered", "cheese"}):
            pass
        else:
            return "drop", "drink"

    # Specific drink phrases
    if has_phrase(n, ["cold brew", "iced tea", "iced coffee", "hot tea",
                      "sweet tea", "fountain drink", "soft drink",
                      "agua fresca", "aguas frescas",
                      "milk tea", "boba tea", "bubble tea", "thai tea",
                      "diet limeade", "diet lemonade",
                      "cherry limeade", "cranberry limeade",
                      "strawberry limeade", "strawberry lemonade",
                      "naturales aguas",
                      ]):
        return "drop", "drink"

    if "tea" in token_set and len(tokens) <= 3:
        if not (token_set & PROTEINS) and not (token_set & ALL_ANCHORS):
            return "drop", "drink"

    # 5. Dessert
    dessert_hits = token_set & DESSERT_TOKENS
    if dessert_hits:
        return "drop", "dessert"

    # cake handling
    if "cake" in token_set or "cakes" in token_set:
        savory_cake = any(s in token_set for s in
                          {"crab", "fish", "salmon", "tuna", "shrimp",
                           "rice", "potato", "corn", "johnny", "chicken",
                           "pancake", "pancakes"})
        if not savory_cake:
            return "drop", "dessert"

    # pie
    if "pie" in token_set and "pizza" not in n:
        savory_pie_kw = {"pot", "shepherd", "shepherds", "cottage", "meat",
                         "fish", "chicken", "beef", "pork", "turkey", "lamb",
                         "tuna", "salmon", "spinach", "broccoli", "frito",
                         "fritos", "tamale", "hand"}
        if not (token_set & savory_pie_kw):
            return "drop", "dessert"

    # muffin
    if "muffin" in token_set or "muffins" in token_set:
        if not (token_set & {"english", "egg", "eggs", "sausage", "bacon",
                              "ham", "breakfast", "mcmuffin"}):
            return "drop", "dessert"

    # parfait
    if "parfait" in token_set:
        return "drop", "snack"

    # 6. Sides
    side_hits = token_set & SIDE_TOKENS
    if side_hits:
        is_stir_fry = "stir" in token_set and ("fry" in token_set or "fried" in token_set)
        is_fish_fry = "fish" in token_set and ("fry" in token_set)
        has_anchor = bool(token_set & ALL_ANCHORS) or has_phrase(n, COMPOUND_PHRASES)
        if has_anchor or is_stir_fry or is_fish_fry:
            pass
        else:
            return "drop", "side"

    # biscuits
    if ("biscuit" in token_set or "biscuits" in token_set):
        if (token_set & {"gravy", "egg", "eggs", "sausage", "bacon",
                          "chicken", "ham", "breakfast", "country"}):
            return "keep", "main"  # biscuits + breakfast → real dish
        if not (token_set & ALL_ANCHORS):
            return "drop", "side"

    # 7. Sauce
    if len(tokens) <= 2:
        if all(t in SAUCE_BARE for t in tokens):
            return "drop", "sauce"
        if tokens[0] in SAUCE_BARE and tokens[-1] in {"dressing", "dip", "sauce",
                                                       "verde", "roja", "rojo",
                                                       "fresca", "blanca",
                                                       "brava"}:
            return "drop", "sauce"
        if tokens[-1] in SAUCE_BARE and tokens[0] in {"verde", "roja", "rojo",
                                                       "fresca", "blanca",
                                                       "brava", "extra"}:
            return "drop", "sauce"

    # bare "sauce" with one descriptor (no protein/anchor)
    if "sauce" in token_set and len(tokens) <= 3:
        if not (token_set & PROTEINS) and not (token_set & ALL_ANCHORS):
            return "drop", "sauce"

    # 8. Snacks
    if "snack" in token_set and len(tokens) <= 2:
        if not (token_set & PROTEINS) and not (token_set & ALL_ANCHORS):
            return "drop", "snack"

    if "olives" in token_set and len(tokens) <= 2:
        return "drop", "snack"

    # plain "chips" with sauce
    if "chips" in token_set and len(tokens) <= 3:
        if (token_set & {"salsa", "queso", "guacamole", "cheese", "nacho"} or
                len(tokens) == 1):
            if not (token_set & ALL_ANCHORS):
                return "drop", "snack"

    if len(tokens) <= 2 and (token_set & {"yogurt", "granola"}):
        return "drop", "snack"

    # Cuisine/region adjectives that are fragment alone (but specific in combo)
    CUISINE_ADJECTIVES_ALONE = {
        "italian", "mexican", "asian", "american", "chinese", "indian",
        "korean", "japanese", "thai", "greek", "french", "spanish",
        "vietnamese", "filipino", "russian", "german", "ethiopian",
        "moroccan", "lebanese", "afghan", "afghani", "iranian", "persian",
        "armenian", "turkish", "burmese", "irish", "british", "english",
        "polish", "portuguese", "brazilian", "argentine", "argentinian",
        "peruvian", "colombian", "venezuelan", "cuban", "puertorican",
        "dominican", "haitian", "jamaican", "caribbean",
        "salvadoran", "guatemalan", "honduran", "nicaraguan",
        "tex-mex", "texmex", "georgian", "nepalese", "nepali", "lao",
    }

    # ========================================================================
    # Single-token classification
    # ========================================================================
    if len(tokens) == 1:
        single = tokens[0]
        if single in SINGLE_WORD_MAINS or single in KEEP_OVERRIDES:
            return "keep", "main"
        if single in GENERIC_VESSELS_FRAGMENT_ALONE:
            return "drop", "fragment"
        if single in CUISINE_ADJECTIVES_ALONE:
            return "drop", "fragment"
        if single in INGREDIENT_BARE:
            return "drop", "ingredient"
        if single in MARKETING_TOKENS:
            return "drop", "marketing"
        if single in FRAGMENT_GENERIC:
            return "drop", "fragment"
        if single in COOKING_STYLE:
            return "drop", "fragment"
        if single in SAUCE_BARE:
            return "drop", "sauce"
        if single in DRINK_TOKENS:
            return "drop", "drink"
        if single in DESSERT_TOKENS:
            return "drop", "dessert"
        if single in SIDE_TOKENS:
            return "drop", "side"
        if len(single) <= 3:
            return "drop", "fragment"
        # Unknown long single — likely real ethnic dish (asun, ewedu, etc.)
        if len(single) >= 5 and re.fullmatch(r"[a-z]+", single):
            return "keep", "main"
        return "drop", "fragment"

    # ========================================================================
    # Multi-token classification
    # ========================================================================

    # 9. Compound dish phrases
    if has_phrase(n, COMPOUND_PHRASES):
        return "keep", "main"

    # 10. All marketing/fragment/vessel → drop
    nonspecific = MARKETING_TOKENS | GENERIC_VESSELS_FRAGMENT_ALONE | FRAGMENT_GENERIC | COOKING_STYLE
    if all(t in nonspecific for t in tokens):
        return "drop", "fragment"

    # 11. All marketing only → marketing
    if all(t in MARKETING_TOKENS for t in tokens):
        return "drop", "marketing"

    has_protein = bool(token_set & PROTEINS)
    has_anchor = bool(token_set & ALL_ANCHORS)
    has_specific = bool(token_set & SPECIFIC_DESCRIPTORS)
    has_ingredient = bool(token_set & INGREDIENT_BARE)
    has_cooking = bool(token_set & COOKING_STYLE)

    # 12. nonspecific + ingredients only — chicken combo, italian special, house plate
    # If all tokens are in (nonspecific ∪ INGREDIENT_BARE) and no specific descriptor
    if all(t in nonspecific or t in INGREDIENT_BARE for t in tokens) and not has_specific:
        # CONCRETE vessels (specific food forms) — pizza/burger/sandwich/burrito/etc
        # paired with ingredient → real dish (pepperoni pizza, cheese pizza, ham sandwich)
        CONCRETE_VESSELS = {
            "pizza", "pizzas", "burger", "burgers", "cheeseburger",
            "hamburger", "hamburgers", "cheeseburgers",
            "sandwich", "sandwiches", "sub", "subs",
            "burrito", "burritos", "taco", "tacos",
            "quesadilla", "quesadillas", "enchilada", "enchiladas",
            "tamale", "tamales", "fajita", "fajitas",
            "tostada", "tostadas", "torta", "tortas",
            "wrap", "wraps", "panini", "paninis",
            "calzone", "stromboli",
            "omelet", "omelette", "frittata", "quiche",
            "pancake", "pancakes", "waffle", "waffles", "crepe", "crepes",
            "ramen", "udon", "soba", "pho",
            "biryani", "curry",
            "soup", "stew", "chili", "chowder", "bisque", "gumbo",
            "kebab", "kebabs", "kabob", "kabobs",
            "gyro", "gyros", "shawarma", "souvlaki",
            "samosa", "samosas", "empanada", "empanadas",
            "dumplings", "potstickers",
            "lasagna", "lasagne", "spaghetti", "linguine", "fettuccine",
            "penne", "rigatoni", "ravioli", "gnocchi", "tortellini",
            "risotto", "paella",
            "salad",  # caesar salad, cobb salad — real
            "noodles", "noodle",
            "scramble", "scrambler",
            "benedict", "florentine",
            "casserole", "stroganoff",
            "meatloaf",
            "cheesesteak", "philly",
            # protein cuts/forms — concrete dish forms
            "fillet", "fillets", "filet", "filets",
            "steak", "steaks", "ribeye", "sirloin",
            "chop", "chops", "tenderloin",
            "ribs", "rib",
            "wings", "wing", "tenders", "tender", "nuggets", "nugget",
            "drumstick", "drumsticks", "fingers",
            "skewer", "skewers",
            "roll", "rolls",
            "bowl", "bowls",  # rice bowl, etc.
            "burrito", "burritos",
            # breakfast forms
            "toast",
            "stack", "stacks",
            "melt", "melts",
            # mexican/spanish forms
            "chimichanga", "chimichangas",
            "flautas", "flauta", "taquitos", "taquito",
            "sopes", "sope", "gorditas", "gordita",
            "huarache", "huaraches",
            "molcajete",
            "chilaquiles", "huevos", "rancheros",
            "ceviche",
            "tlayuda",
            # asian forms
            "sushi", "sashimi", "tempura", "katsu",
            "donburi", "bibimbap", "bulgogi",
            "maki", "nigiri", "temaki", "uramaki", "futomaki", "chirashi",
            "yakitori", "yakisoba", "okonomiyaki", "takoyaki",
            "tonkatsu", "katsudon",
            # other
            "shawarma", "doner",
            "spanakopita", "moussaka",
            "shakshuka", "kibbeh", "tagine", "tajine",
            "feijoada",
            "borscht", "goulash",
            "couscous",
            "jollof", "fufu", "injera",
            "poutine",
            "cassoulet", "ratatouille", "bouillabaisse",
            "ossobuco", "saltimbocca",
            "rendang", "satay", "nasi",
            "japchae", "tteokbokki", "kimbap",
            "minestrone", "pozole", "posole", "birria",
            "quesabirria",
            "haleem", "nihari",
            "discada", "parrillada", "parillada", "parrilada",
            "muffuletta",
            "asado",
            # roll types
            "rolls",
            # other
            "bao",
            "machaca",
            # spanish forms
            "milanesa", "carnitas", "barbacoa",
            "lengua", "tripa", "cabeza", "cabrito", "lechon",
            "menudo",
            # sandwich types
            "blt", "club", "reuben",
            "whopper",
            # patty melt etc
            "patty", "patties",
        }
        VAGUE_VESSELS = {
            "combo", "combos", "plate", "plates", "platter", "platters",
            "meal", "meals", "dinner", "lunch", "breakfast", "brunch",
            "tray", "trays", "bucket", "buckets",
            "special", "specials", "favorite", "favorites",
            "house",
        }
        # Pure protein/ingredient + concrete vessel → keep
        if has_ingredient and (token_set & CONCRETE_VESSELS):
            # protein + concrete vessel keeps even with vague vessel modifier
            # (e.g. "catfish dinner fillet" = catfish fillet for dinner)
            if has_protein:
                return "keep", "main"
            # non-protein ingredient + concrete vessel: drop if vague vessel mixed in
            other_vague = (token_set & VAGUE_VESSELS) - (token_set & CONCRETE_VESSELS)
            if not other_vague:
                non_marketing = [t for t in tokens
                                 if t not in MARKETING_TOKENS and t not in FRAGMENT_GENERIC]
                if len(non_marketing) >= 2 and any(
                        t in INGREDIENT_BARE and t not in PROTEINS for t in tokens):
                    return "keep", "main"
        # protein + cooking + anchor → keep
        if has_protein and has_anchor and has_cooking:
            return "keep", "main"
        # cooking + protein → real dish
        if has_protein and has_cooking and len(tokens) >= 2:
            return "keep", "main"
        # protein + non-protein ingredient → probable dish (e.g. "asparagus prawns",
        # "broccoli beef" already in compound)
        if has_protein and has_ingredient:
            non_protein_ingr = (token_set & INGREDIENT_BARE) - PROTEINS
            if non_protein_ingr:
                return "keep", "main"
        # 2 different proteins (e.g. "shrimp scallop") → real combo dish
        proteins_in = token_set & PROTEINS
        if len(proteins_in) >= 2:
            return "keep", "main"
        return "drop", "fragment"

    # 13. Has specific descriptor → likely real dish
    if has_specific:
        # if protein/anchor present alongside, definitely keep
        if has_protein or has_anchor or has_ingredient:
            return "keep", "main"
        # specific alone (e.g. "alfredo broccoli pasta" — has specific
        # but no protein) — keep if 2+ meaningful tokens
        meaningful = [t for t in tokens
                      if t not in MARKETING_TOKENS and t not in FRAGMENT_GENERIC]
        if len(meaningful) >= 2:
            return "keep", "main"

    # 14. Has anchor + non-marketing identifier → keep
    if has_anchor:
        # protein + anchor = real dish (cod sandwich, chicken pita, etc.)
        if has_protein:
            return "keep", "main"
        # Specific anchors that aren't generic vessels OR proteins/ingredients
        # — those identify a specific dish form (lasagna, gyro, biryani, etc.)
        specific_anchors = ((token_set & ALL_ANCHORS)
                            - GENERIC_VESSELS_FRAGMENT_ALONE
                            - PROTEINS
                            - INGREDIENT_BARE)
        # tokens beyond anchors that are descriptive (and not too short)
        non_anchor = [t for t in tokens
                      if t not in ALL_ANCHORS and t not in MARKETING_TOKENS
                      and t not in FRAGMENT_GENERIC
                      and t not in GENERIC_VESSELS_FRAGMENT_ALONE
                      and len(t) > 2]
        if non_anchor or specific_anchors:
            return "keep", "main"
        return "drop", "fragment"

    # 15. Has protein + cooking style → real dish
    if has_protein and has_cooking:
        return "keep", "main"

    # 16. Has protein + at least 2 other meaningful tokens
    meaningful = [t for t in tokens
                  if t not in MARKETING_TOKENS
                  and t not in FRAGMENT_GENERIC
                  and t not in GENERIC_VESSELS_FRAGMENT_ALONE]
    if has_protein and len(meaningful) >= 3:
        return "keep", "main"

    # Spanish protein words can be the entire dish
    if (token_set & {"pollo", "puerco", "res", "carne", "pescado",
                     "camaron", "camarones", "bistec", "milanesa", "machaca",
                     "pechuga", "filete"}) and len(tokens) >= 2:
        # likely Spanish dish like "bistec de puerco" or "pollo asado"
        # require at least one non-marketing word besides
        non_marketing = [t for t in tokens
                         if t not in MARKETING_TOKENS and t not in FRAGMENT_GENERIC]
        if len(non_marketing) >= 2:
            return "keep", "main"

    # 16b. Protein + ingredient (2 tokens) → likely real dish (alphabetized order)
    if len(tokens) == 2 and has_protein and has_ingredient:
        non_protein_ingr = (token_set & INGREDIENT_BARE) - PROTEINS
        if non_protein_ingr:
            return "keep", "main"

    # 16c. Protein + protein → real combo dish
    if len(token_set & PROTEINS) >= 2:
        return "keep", "main"

    # 17. Default — strict mode: when in doubt, drop
    if len(tokens) <= 2:
        return "drop", "fragment"

    # 3+ tokens with at least one specific or protein
    if has_protein or has_specific:
        return "keep", "main"

    return "drop", "fragment"


def main():
    rows_in = 0
    rows_out = 0
    counts = {"keep": 0, "drop": 0}
    reasons = {}
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
            counts[verdict] = counts.get(verdict, 0) + 1
            reasons[reason] = reasons.get(reason, 0) + 1
            rows_out += 1
    print(f"Input data rows : {rows_in}")
    print(f"Output data rows: {rows_out}")
    print(f"Verdicts : {counts}")
    print(f"Reasons  : {reasons}")


if __name__ == "__main__":
    main()
