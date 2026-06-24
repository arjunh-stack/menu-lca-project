#!/usr/bin/env python3
"""Strict classifier for chunks_v2/chunk_19.csv.

Recipe Test: Could a chef Google-search for a recipe matching this exact name
and find a real, recognizable main dish suitable for breakfast/lunch/dinner?

Tokens are alphabetized. Many rows are gibberish, marketing fluff, codes, or
fragments. When in doubt → DROP.
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

INPUT = dpath("chunks_v2/chunk_19.csv")
OUTPUT = dpath("chunks_classified_v2/chunk_19_classified.csv")


# -------------- Token sets --------------

# Drinks (any of these → drop unless paired with a clear protein in a known dish)
DRINK_TOKENS = {
    "coffee", "latte", "cappuccino", "mocha", "espresso", "frappe",
    "frappuccino", "americano", "macchiato", "cortado", "ristretto",
    "chai", "matcha", "soda", "cola", "coke", "pepsi", "sprite", "fanta",
    "lemonade", "limeade", "smoothie", "smoothies", "milkshake", "shake",
    "shakes", "beer", "wine", "cocktail", "margarita", "mimosa",
    "sangria", "martini", "mojito", "vodka", "rum", "whiskey", "whisky",
    "tequila", "gin", "scotch", "brandy", "champagne", "prosecco",
    "lassi", "boba", "snapple", "gatorade", "powerade", "redbull",
    "monster", "horchata", "agua", "aguas", "kombucha", "cider",
    "frescas", "slushie", "slushy", "slush", "icee", "frosty", "float",
    "juice", "drink", "drinks", "beverage", "beverages",
    "lemonades",
}

# Drinks but contextual (only drop if these specific phrases match)
TEA_DRINK_PHRASES = ["iced tea", "hot tea", "sweet tea", "unsweet tea",
                     "green tea", "black tea", "chai tea", "milk tea",
                     "thai tea", "boba tea", "bubble tea"]

WATER_DRINK_INDICATORS = {"bottled", "sparkling", "spring", "still",
                          "fiji", "evian", "perrier", "pellegrino"}

# Desserts (drop if any present, with limited carve-outs for cake)
DESSERT_TOKENS = {
    "cake", "cakes", "cookie", "cookies", "brownie", "brownies",
    "cupcake", "cupcakes", "cinnabon", "donut", "donuts", "doughnut",
    "doughnuts", "icecream", "gelato", "sundae", "sundaes", "sorbet",
    "cheesecake", "custard", "churro", "churros", "tiramisu",
    "cannoli", "pudding", "mousse", "macaron", "macarons", "macaroon",
    "macaroons", "tart", "tarts", "eclair", "eclairs", "baklava",
    "biscotti", "fudge", "praline", "pralines", "gummy", "gummies",
    "marshmallow", "marshmallows", "popsicle", "popsicles",
    "flan", "cobbler", "crumble", "strudel", "kolache", "kolaches",
    "beignet", "beignets", "blizzard", "mcflurry",
    "concrete",  # ice cream concrete
    "halo",  # halo halo (Filipino dessert)
    "bismark", "bismarks", "twinkie", "tres", "leches",
    "ladoo", "barfi", "burfi", "kulfi", "rasgulla", "rasmalai",
    "jalebi", "halwa", "gulab", "jamun", "kheer",
}

# Cake exceptions — these ARE main dishes
CAKE_KEEP_HINTS = {"crab", "fish", "salmon", "tuna", "shrimp", "rice",
                   "pancake", "pancakes", "potato", "corn", "johnny",
                   "pan", "hot"}

# Sides (drop unless paired with a main anchor)
SIDE_TOKENS = {
    "fries", "fry",  # bare; "stir fry"/"fish fry" handled
    "rings",  # onion rings
    "tots", "tater",
    "puppies",  # hush puppies
    "breadstick", "breadsticks", "garlic bread",
    "poppers",
    "coleslaw", "slaw",
    "applesauce",
    "cornbread",
    "hashbrown", "hashbrowns",
    "okra",
    "grits",
    "pilaf",
}

# Snacks
SNACK_TOKENS = {"parfait", "granola", "popcorn", "jerky", "crackers",
                "chips"}  # chips alone is snack
SNACK_PHRASES = ["chips salsa", "chips queso", "chips guacamole",
                 "chips dip", "chips cheese", "salsa chips",
                 "queso chips", "fire chips roasted salsa",
                 "chips fresh salsa"]

# Bare sauces (drop)
SAUCE_BARE_NAMES = {"guacamole", "queso", "salsa", "hummus", "ranch",
                    "chimichurri", "tahini", "tzatziki", "syrup",
                    "honey", "gravy", "ketchup", "mayo", "mayonnaise",
                    "aioli", "vinaigrette", "pesto", "tapenade",
                    "chutney", "relish", "tartar", "remoulade", "jam",
                    "jelly", "preserves", "marmalade"}

SAUCE_BARE_PATTERNS = [
    re.compile(r"^salsa\s+(roja|verde|fresca|picante|brava|bandera|negra)$"),
    re.compile(r"^(roja|verde|fresca|picante|brava|bandera|negra)\s+salsa$"),
    re.compile(r"^(bbq|honey|honey mustard|ranch|caesar|italian|garlic|hot|sweet|tangy|smoky)\s+sauce$"),
    re.compile(r"^sauce\s+(bbq|honey|ranch|caesar|italian|garlic|hot|sweet|tangy|smoky)$"),
    re.compile(r"\bdipping\s+sauce\b"),
    re.compile(r"^gravy\s+(brown|sawmill|country|white)$"),
    re.compile(r"^(brown|sawmill|country|white)\s+gravy$"),
]

# Bare ingredients (proteins/veggies alone are not dishes)
BARE_INGREDIENTS = {
    "cheese", "bacon", "mushroom", "mushrooms", "onion", "onions",
    "tofu", "tomato", "tomatoes", "lettuce", "spinach", "kale",
    "cucumber", "pickle", "pickles", "olive", "olives", "pepper",
    "peppers", "jalapeno", "jalapenos", "carrot", "carrots", "celery",
    "broccoli", "cauliflower", "potato", "potatoes", "rice", "beans",
    "bean", "corn", "egg", "eggs",
    "ham", "salami", "pepperoni", "sausage", "chorizo", "turkey",
    "chicken", "beef", "pork", "lamb", "fish", "shrimp", "crab",
    "lobster", "tuna", "salmon", "duck", "goat",
    "avocado", "cilantro", "parsley", "basil", "garlic",
    "lime", "lemon", "milk", "cream", "yogurt", "feta", "mozzarella",
    "cheddar", "parmesan", "swiss", "provolone", "gouda", "brie",
    "ricotta",
    "veggie", "vegetable", "vegetables", "vegtable", "vegetales",
    "vegan", "vegetarian",
}

PROTEINS = {"chicken", "beef", "pork", "shrimp", "fish", "lamb",
            "turkey", "duck", "tofu", "salmon", "tuna", "crab",
            "lobster", "scallop", "scallops", "oxtail", "goat",
            "veal", "rabbit", "venison", "bison"}

# Words considered "marketing only" - if all tokens are these, drop
MARKETING_TOKENS = {
    "happy", "delight", "delights", "supreme", "deluxe", "premium",
    "favorite", "favorites", "classic", "classics", "original",
    "signature", "signatures", "special", "specials", "today",
    "todays", "featured", "new", "limited", "fresh", "famous",
    "best", "popular", "ultimate",
    "kids", "kid", "adult", "small", "medium", "large", "lg", "xlg",
    "med", "lil", "big", "mini", "regular", "reg", "extra",
    "side", "sides", "addon", "addons", "togo", "takeout", "extras",
    "pak", "silverware",
    "house", "chef", "chefs", "s", "the",
    "your", "own", "build", "create", "make", "pick", "choose",
    "for", "from", "and", "or", "with", "to", "in", "of", "on",
    "a", "an",
    "combo", "meal", "platter", "plate", "dinner", "lunch",
    "breakfast", "brunch",
    "served", "serves", "served with",
    "comes", "with", "topped", "loaded",
    "mix", "mixed", "two", "three", "one", "four", "five",
    "ten", "twenty", "no", "x",
    "go", "out", "up", "down", "n", "g", "b", "c", "d", "e", "f",
    "h", "j", "k", "l", "m", "p", "q", "r", "t", "u", "v", "w", "y", "z",
}

# Dish anchor tokens — presence usually signals real dish
MAIN_ANCHORS = {
    "burger", "burgers", "cheeseburger", "cheeseburgers", "hamburger",
    "hamburgers", "sandwich", "sandwiches", "sub", "subs", "hoagie",
    "hoagies", "wrap", "wraps", "panini", "paninis", "burrito",
    "burritos", "taco", "tacos", "quesadilla", "quesadillas",
    "enchilada", "enchiladas", "tamale", "tamales", "fajita",
    "fajitas", "nachos", "tostada", "tostadas", "chimichanga",
    "chimichangas", "torta", "tortas", "pizza", "pizzas", "calzone",
    "calzones", "stromboli", "spaghetti", "linguine",
    "fettuccine", "penne", "rigatoni", "ravioli", "lasagna", "lasagne",
    "gnocchi", "macaroni", "ramen", "udon", "soba", "pho", "noodles",
    "noodle", "biryani", "curry", "tikka", "masala", "korma",
    "vindaloo", "tandoori", "naan", "wings", "wing", "tenders",
    "tender", "nuggets", "nugget", "strips", "fingers", "drumstick",
    "drumsticks", "steak", "steaks", "ribeye", "sirloin", "filet",
    "fillet", "porterhouse", "brisket", "ribs", "rib", "chops",
    "chop", "loin", "tenderloin", "schnitzel", "wellington",
    "scampi", "calamari",
    "omelet", "omelette", "frittata", "quiche", "scramble",
    "scrambler", "benedict", "benedicts", "florentine", "huevos",
    "rancheros", "chilaquiles", "migas", "menemen",
    "stew", "stews", "chili", "soup", "bisque", "chowder", "gumbo",
    "jambalaya", "etouffee", "paella", "risotto", "polenta",
    "kebab", "kebabs", "kabob", "kabobs", "shawarma", "gyro", "gyros",
    "souvlaki", "doner", "falafel", "casserole", "stroganoff", "kiev",
    "sushi", "roll", "rolls", "sashimi", "tempura", "katsu",
    "donburi", "bibimbap", "bulgogi",
    "meatloaf", "meatballs", "dumplings", "dumpling", "potstickers",
    "wontons", "gyoza", "samosa", "samosas", "pakora", "pakoras",
    "pierogi", "pierogies", "empanada", "empanadas", "arepa", "arepas",
    "pupusa", "pupusas", "pancake", "pancakes", "waffle", "waffles",
    "crepe", "crepes", "toast",
    "mcmuffin", "mcgriddle", "croissanwich",
    "croissant", "croissants",
    "philly", "cheesesteak", "cheesesteaks", "blt", "club", "reuben",
    "whopper", "mcnuggets", "mcrib", "bigmac",
    "flautas", "flauta", "menudo", "sopes", "sope", "hotcakes",
    "gorditas", "gordita", "carnitas", "barbacoa", "milanesa", "bao",
    "ceviche", "crawfish", "catfish", "huarache", "huaraches",
    "molcajete", "taquitos", "taquito", "rotisserie",
    "saag", "palak", "dal", "daal", "yakitori", "yakisoba",
    "okonomiyaki", "takoyaki", "onigiri", "tonkatsu", "katsudon",
    "oyakodon", "gyudon", "unadon", "tendon", "chirashi", "nigiri",
    "maki", "temaki", "uramaki", "futomaki", "edamame", "rangoon",
    "rangoons", "spanakopita", "moussaka", "shakshuka", "kibbeh",
    "tagine", "tajine", "feijoada", "ropa", "moros", "borscht",
    "goulash", "halushki", "haggis", "boxty", "colcannon",
    "bratwurst", "currywurst", "sauerbraten", "couscous", "tabouli",
    "tabbouleh", "jollof", "fufu", "injera", "doro", "poutine",
    "tourtiere", "cassoulet", "ratatouille", "bouillabaisse", "coq",
    "confit", "ossobuco", "saltimbocca", "carbonara", "amatriciana",
    "puttanesca", "bolognese", "alfredo", "marinara", "mussaman",
    "panang", "khao", "rendang", "satay", "nasi", "japchae",
    "tteokbokki", "kimbap", "buldak", "samgyeopsal", "naengmyeon",
    "salisbury", "swedish", "minestrone", "pozole", "posole", "birria",
    "souffle", "quesabirria", "tlayuda", "elote", "tinga",
    "fillet", "fillets",
    "stack", "stacks", "melt", "melts",
    "lo", "primavera",
    "roti", "paratha", "idli", "idly", "upma", "vada", "dosa",
    "uttapam", "sambhar", "rasam", "thali", "kurma",
    "manchurian", "pakoda", "bhaji", "puri", "chole", "rajma",
    "paneer", "mole",
    "pita", "lavash", "sopa", "asado",
    "carnita", "lengua", "cabeza", "cabrito", "lechon",
    "kushari", "fattoush", "kebbeh", "larb",
    "jerk", "slam", "skillet", "skillets",
    "boy",  # po boy — paired with "po"
    "po",
    "pie",  # but only savory pies (separate logic)
    "salad", "salads",
    "yat",  # cantonese "yat" dishes
    "pasta",  # often part of dish
    "fried",  # only with rice/protein
    "stir",  # stir fry
    "shumai", "siu", "mai",  # dim sum
    "spam",
    "pho", "bun", "com",  # vietnamese; com=rice, bun=noodles
    "banh", "bun",
    "kimchi",
    "habachi", "hibachi",
    "yakiudon",
    "chaingmai",
    "sushi",
    "boil",  # crab boil
}

# Compound dish phrases (substring matching, tokens may be alphabetized)
# Each phrase below is checked as substring in normalized name
COMPOUND_KEEP_PHRASES = {
    "kung pao", "general tso", "pad thai", "pad see ew", "drunken noodles",
    "egg foo young", "foo young", "lo mein", "chow mein", "chow fun",
    "chow mei", "mei fun", "ho fun", "house yat",
    "fried rice", "rice fried",
    "stir fry", "fry stir", "stir fried", "fried stir",
    "fish fry", "fry fish",
    "tikka masala", "butter chicken", "chana masala", "chicken curry",
    "chicken tikka", "saag paneer", "palak paneer", "matar paneer",
    "fish chips", "chicken waffles",
    "mac cheese", "macaroni cheese",
    "rice beans", "beans rice",
    "salisbury steak", "swedish meatballs", "frito pie",
    "pot pie", "shepherd pie", "shepherds pie", "cottage pie",
    "fish pie", "meat pie", "savory pie", "hand pie", "chicken pie",
    "egg roll", "spring roll", "summer roll", "lobster roll",
    "egg rolls", "spring rolls", "summer rolls", "lobster rolls",
    "california roll", "philly cheesesteak", "cheese steak",
    "patty melt", "tuna melt",
    "buffalo chicken", "fried chicken", "roast chicken",
    "baked chicken", "grilled chicken", "rotisserie chicken",
    "country fried steak", "chicken fried steak",
    "buffalo wings", "hot wings", "bbq wings",
    "italian beef", "italian sub",
    "meatball sub", "meatball sandwich",
    "egg sandwich", "breakfast sandwich",
    "monte cristo", "croque monsieur", "croque madame",
    "bourbon chicken",
    "garlic noodles", "rice bowl",
    "fish taco", "shrimp taco", "carne asada", "al pastor",
    "lengua taco", "tripa taco", "asada taco",
    "soft taco", "hard taco",
    "mongolian beef", "mongolian chicken",
    "honey walnut shrimp", "sesame chicken", "sesame shrimp",
    "orange chicken", "lemon chicken",
    "beef broccoli", "broccoli beef",
    "cashew chicken", "garlic chicken", "garlic shrimp",
    "garlic sauce",  # in chinese: chicken in garlic sauce
    "hunan chicken", "hunan beef", "hunan shrimp",
    "szechuan chicken", "szechuan beef", "szechuan shrimp",
    "kung pao chicken", "kung pao shrimp", "kung pao beef",
    "general tso chicken", "general tso s chicken", "tso chicken",
    "garlic sauce",
    "bbq beef", "bbq chicken", "bbq pork",
    "breaded chicken", "grilled chicken", "fried chicken",
    "spring rolls", "summer rolls", "egg rolls",
    "club sandwich", "tuna sandwich",
    "philly steak", "philly cheese", "philly sub",
    "po boy", "boy po",  # alphabetized
    "shrimp scampi",
    "chicken scampi",
    "shrimp alfredo", "chicken alfredo",
    "shrimp parmesan", "chicken parmesan", "chicken parm",
    "eggplant parmesan",
    "lasagna meat", "lasagna cheese",
    "pad thai", "pad see ew",
    "thai curry",
    "green curry", "red curry", "yellow curry", "panang curry",
    "mussaman curry",
    "drunken pad",  # "drunken pad noodles"
    "biryani chicken", "chicken biryani",
    "biryani lamb", "lamb biryani",
    "biryani mutton", "mutton biryani",
    "biryani shrimp", "shrimp biryani",
    "biryani veg", "veg biryani", "biryani vegetable",
    "korma chicken", "chicken korma",
    "korma lamb", "lamb korma",
    "vindaloo chicken", "chicken vindaloo",
    "vindaloo lamb", "lamb vindaloo",
    "tandoori chicken", "chicken tandoori",
    "naan garlic", "garlic naan",
    "naan plain",
    "tikka chicken", "chicken tikka",
    "samosa veggie", "veggie samosa", "samosa potato",
    "spinach pie",
    "kimchi fried", "kimchi stew", "kimchi soup",
    "ramen pork", "pork ramen", "ramen miso", "miso ramen",
    "ramen shoyu", "shoyu ramen", "ramen tonkotsu", "tonkotsu ramen",
    "udon noodle", "udon noodles", "noodle udon", "noodles udon",
    "soba noodle", "soba noodles", "noodle soba", "noodles soba",
    "pho beef", "beef pho", "pho chicken", "chicken pho",
    "pho seafood", "seafood pho", "pho shrimp", "shrimp pho",
    "pho vegetable", "vegetable pho", "pho veggie", "veggie pho",
    "pho tofu", "tofu pho",
    "banh mi",
    "bun bo", "bo bun", "bun cha", "cha bun",
    "com tam", "tam com",
    "com bi", "bi com",
    "rice broken",
    "shaking beef", "shaky beef", "beef shaking", "beef shaky",
    "luc lac",
    "salmon teriyaki", "teriyaki salmon",
    "chicken teriyaki", "teriyaki chicken",
    "beef teriyaki", "teriyaki beef",
    "shrimp teriyaki", "teriyaki shrimp",
    "steak teriyaki", "teriyaki steak",
    "katsu chicken", "chicken katsu", "katsu pork", "pork katsu",
    "donburi katsu", "katsu donburi",
    "tempura shrimp", "shrimp tempura", "tempura vegetable",
    "vegetable tempura",
    "yakisoba",
    "hibachi chicken", "chicken hibachi", "hibachi shrimp",
    "shrimp hibachi", "hibachi steak", "steak hibachi",
    "hibachi vegetable", "hibachi tofu",
    "bibimbap beef", "beef bibimbap", "bibimbap chicken",
    "bibimbap vegetable",
    "japchae",
    "bulgogi beef", "beef bulgogi", "bulgogi pork",
    "samgyeopsal", "korean bbq",
    "kimbap",
    "moussaka", "spanakopita", "souvlaki", "gyro chicken",
    "chicken gyro", "gyro lamb", "lamb gyro", "gyro beef",
    "shawarma chicken", "chicken shawarma", "shawarma beef",
    "beef shawarma", "shawarma lamb", "lamb shawarma",
    "kebab chicken", "chicken kebab", "kebab lamb", "lamb kebab",
    "kebab beef", "beef kebab", "kebab veggie", "kebab vegetable",
    "falafel sandwich", "falafel wrap", "falafel plate",
    "kofta lamb", "lamb kofta", "kofta beef", "beef kofta",
    "kofta chicken", "chicken kofta",
    "tabbouleh",
    "shakshuka",
    "tagine chicken", "chicken tagine", "tagine lamb", "lamb tagine",
    "couscous chicken", "chicken couscous",
    "jollof rice", "fufu",
    "huevos rancheros", "huevos divorciados", "huevos motulenos",
    "chilaquiles rojos", "chilaquiles verdes", "chilaquiles green",
    "menudo",
    "torta de", "torta cubana", "cubana torta",
    "elote",
    "pozole", "posole", "birria taco", "taco birria",
    "quesabirria", "tlayuda",
    "tinga chicken", "chicken tinga",
    "carnitas taco", "taco carnitas", "barbacoa taco", "taco barbacoa",
    "milanesa", "ceviche shrimp", "shrimp ceviche", "ceviche fish",
    "fish ceviche", "ceviche mixto", "mixto ceviche",
    "molcajete",
    "fajita chicken", "chicken fajita", "fajita steak", "steak fajita",
    "fajita shrimp", "shrimp fajita", "fajita combo", "combo fajita",
    "fajita mix", "mix fajita", "fajita mixed", "mixed fajita",
    "fajita veggie", "veggie fajita", "fajita vegetable",
    "tacos al pastor", "al pastor tacos", "asada tacos", "tacos asada",
    "carne asada", "carne asada taco", "tacos carne asada",
    "shrimp tacos", "tacos shrimp",
    "fish tacos", "tacos fish",
    "chicken tacos", "tacos chicken",
    "pork tacos", "tacos pork",
    "steak tacos", "tacos steak",
    "ground beef tacos", "tacos ground beef",
    "lengua tacos", "tacos lengua",
    "buffalo wings", "lemon pepper wings", "garlic parm wings",
    "honey bbq wings", "korean wings", "korean fried chicken",
    "boneless wings",
    "honey garlic", "garlic honey",
    "honey hot",
    "ribs bbq", "bbq ribs", "spare ribs", "ribs spare", "baby back ribs",
    "back baby ribs", "rib tips", "tips rib",
    "pulled pork", "pulled chicken",
    "smoked brisket", "brisket smoked",
    "brisket sandwich", "sandwich brisket",
    "rib eye", "ny strip", "new york strip", "prime rib",
    "filet mignon", "filet mignon",
    "ribeye steak", "steak ribeye", "sirloin steak", "steak sirloin",
    "delmonico",
    "chicken parmesan", "parmesan chicken", "veal parmesan",
    "parmesan veal", "eggplant parmesan",
    "chicken marsala", "marsala chicken",
    "chicken francese", "francese chicken",
    "chicken piccata", "piccata chicken",
    "veal marsala", "marsala veal", "veal piccata", "piccata veal",
    "veal francese", "francese veal",
    "shrimp scampi", "scampi shrimp",
    "linguine clams", "clams linguine",
    "spaghetti meatballs", "meatballs spaghetti",
    "spaghetti carbonara", "carbonara spaghetti",
    "fettuccine alfredo", "alfredo fettuccine",
    "penne vodka", "vodka penne",
    "lasagna",
    "ravioli cheese", "cheese ravioli", "ravioli meat", "meat ravioli",
    "ravioli spinach", "spinach ravioli",
    "gnocchi",
    "tortellini",
    "cannelloni",
    "manicotti",
    "stuffed shells", "shells stuffed",
    "salmon teriyaki", "salmon grilled", "grilled salmon",
    "salmon blackened", "blackened salmon",
    "salmon cajun", "cajun salmon",
    "tilapia grilled", "grilled tilapia",
    "shrimp scampi", "garlic shrimp", "coconut shrimp", "shrimp coconut",
    "popcorn shrimp",
    "lobster tail", "tail lobster", "lobster roll",
    "crab cake", "crab cakes", "cakes crab", "cake crab",
    "crab legs", "legs crab", "crab boil",
    "shrimp boil", "seafood boil",
    "fried calamari", "calamari fried",
    "fish chips", "fish and chips",
    "fish fry",
    "scallops grilled", "grilled scallops", "scallops seared",
    "seared scallops",
    "blackened",
    "club sandwich", "tuna salad sandwich", "egg salad sandwich",
    "chicken salad sandwich",
    "patty melt", "tuna melt", "ham melt", "turkey melt",
    "reuben",
    "blt sandwich", "blt", "italian sub", "italian hoagie",
    "italian sandwich", "philly cheesesteak", "cheesesteak sub",
    "chicken cheesesteak", "cheesesteak chicken",
    "meatball sub", "meatball sandwich", "meatball hoagie",
    "veggie sub", "vegetable sub",
    "ham sub", "ham hoagie", "turkey sub", "turkey hoagie",
    "turkey club", "club turkey",
    "buffalo chicken sub", "buffalo chicken wrap",
    "buffalo chicken sandwich",
    "chicken parm sandwich", "chicken parmesan sandwich",
    "spinach wrap",
    "caesar wrap", "wrap caesar",
    "burrito chicken", "chicken burrito", "burrito beef", "beef burrito",
    "burrito bean", "bean burrito", "burrito veggie", "veggie burrito",
    "burrito breakfast", "breakfast burrito",
    "burrito carne", "carne burrito", "burrito asada", "asada burrito",
    "burrito chorizo", "chorizo burrito", "burrito steak", "steak burrito",
    "burrito shrimp", "shrimp burrito", "burrito al pastor",
    "burrito carnitas", "carnitas burrito",
    "supreme burrito", "burrito supreme",
    "wet burrito", "burrito wet",
    "quesadilla chicken", "chicken quesadilla",
    "quesadilla beef", "beef quesadilla",
    "quesadilla shrimp", "shrimp quesadilla",
    "quesadilla cheese", "cheese quesadilla",
    "quesadilla steak", "steak quesadilla",
    "quesadilla veggie", "veggie quesadilla",
    "enchilada chicken", "chicken enchilada", "enchiladas chicken",
    "chicken enchiladas", "enchiladas beef", "beef enchiladas",
    "enchiladas cheese", "cheese enchiladas", "enchiladas shrimp",
    "shrimp enchiladas",
    "enchiladas verdes", "verdes enchiladas",
    "tamale chicken", "chicken tamale", "tamale pork", "pork tamale",
    "tamales chicken", "chicken tamales",
    "chimichanga chicken", "chicken chimichanga",
    "chimichanga beef", "beef chimichanga",
    "tostada chicken", "chicken tostada",
    "fish and chips", "chips and fish",
    "shepherd s pie", "shepherds pie", "shepherd pie",
    "cottage pie", "frito pie", "chicken pot pie", "pot pie",
    "biscuits gravy", "biscuits and gravy",
    "eggs benedict", "benedict eggs",
    "huevos rancheros", "rancheros huevos",
    "ny strip", "new york strip",
    "prime rib",
    "korean bbq", "bbq korean",
    "spicy tuna roll", "tuna spicy roll",
    "rainbow roll", "color rainbow roll",
    "dragon roll", "dragon musashi roll",
    "tempura roll",
    "philadelphia roll", "philly roll",
    "california roll",
    "salmon roll", "salmon teriyaki",
    "tuna roll", "tuna spicy roll",
    "spicy tuna",
    "shrimp tempura roll", "tempura shrimp roll",
    "yellowtail roll", "hamachi roll",
    "eel roll", "unagi roll",
    "sushi combo", "combo sushi", "sushi platter", "sushi boat",
    "sashimi platter", "sashimi combo",
    "sushi deluxe", "deluxe sushi",
    "sushi dinner", "dinner sushi",
    "vermicelli grilled", "grilled vermicelli",
    "vermicelli shrimp", "shrimp vermicelli",
    "vermicelli pork", "pork vermicelli",
    "vermicelli chicken", "chicken vermicelli",
    "vermicelli beef", "beef vermicelli",
    "vermicelli combo", "combo vermicelli",
    "vermicelli noodle", "noodle vermicelli",
    "rice plate", "plate rice",
    "rice combo", "combo rice",
    "rice broken", "broken rice",
    "rice grilled chicken", "rice grilled pork", "rice grilled beef",
    "rice grilled shrimp",
    "stir fry vegetable", "vegetable stir fry",
    "stir fry chicken", "chicken stir fry",
    "stir fry beef", "beef stir fry",
    "stir fry shrimp", "shrimp stir fry",
    "stir fry tofu", "tofu stir fry",
    "stir fry mixed", "mixed stir fry",
    "wonton soup", "soup wonton",
    "egg drop soup", "drop egg soup",
    "hot and sour soup", "hot sour soup",
    "miso soup", "soup miso",
    "tom yum",
    "tom kha",
    "tom yum soup",
    "tom kha soup",
    "ramen tonkotsu", "tonkotsu ramen",
    "udon soup", "soup udon",
    "soba soup", "soup soba",
    "ham eggs", "eggs ham", "bacon eggs", "eggs bacon",
    "sausage eggs", "eggs sausage",
    "fried egg", "fried eggs",
    "scrambled eggs", "eggs scrambled",
    "omelette ham", "ham omelette",
    "omelette cheese", "cheese omelette",
    "omelette mushroom", "mushroom omelette",
    "omelette spinach", "spinach omelette",
    "omelette western", "western omelette",
    "omelette greek", "greek omelette",
    "omelette veggie", "veggie omelette",
    "omelette mediterranean", "mediterranean omelette",
    "italian omelette", "denver omelette",
    "french toast",
    "belgian waffle",
    "blueberry pancakes", "pancakes blueberry",
    "buttermilk pancakes", "pancakes buttermilk",
    "chicken waffles", "chicken and waffles",
    "country fried steak", "chicken fried steak",
    "lemon pepper wings", "garlic parmesan wings",
    "buffalo wings", "honey bbq wings", "honey garlic wings",
    "korean fried chicken",
    "wings boneless", "boneless wings",
    "wings traditional", "traditional wings",
    "wings bone in", "bone in wings",
    "smoked ribs", "ribs smoked", "smoked brisket",
    "brisket smoked",
    "fried okra",  # actually a side, but sometimes a main southern item
    "boil crab", "crab boil", "shrimp boil", "boil shrimp",
    "boil seafood", "seafood boil",
    "rice congee", "congee rice", "porridge",
    "porridge chicken", "chicken porridge", "porridge beef",
    "beef porridge",
    "instant noodles",  # often listed as filler dish in asian menus
    "ham fried rice", "shrimp fried rice", "chicken fried rice",
    "beef fried rice", "pork fried rice", "vegetable fried rice",
    "veggie fried rice", "egg fried rice", "house fried rice",
    "yangzhou fried rice", "shanghai fried rice", "thai fried rice",
    "pineapple fried rice", "kimchi fried rice", "spicy fried rice",
    "garlic fried rice",
    "lo mein chicken", "chicken lo mein", "lo mein beef", "beef lo mein",
    "lo mein shrimp", "shrimp lo mein", "lo mein pork", "pork lo mein",
    "lo mein veggie", "veggie lo mein", "lo mein vegetable",
    "lo mein house", "house lo mein", "lo mein combination",
    "combination lo mein", "lo mein seafood", "seafood lo mein",
    "lo mein plain", "plain lo mein",
    "chow mein chicken", "chicken chow mein", "chow mein beef",
    "beef chow mein", "chow mein shrimp", "shrimp chow mein",
    "chow mein pork", "pork chow mein", "chow mein veggie",
    "veggie chow mein", "chow mein house", "house chow mein",
    "chow fun beef", "beef chow fun", "chow fun chicken",
    "chow fun shrimp", "chow fun pork", "chow fun house",
    "house chow fun", "chow fun seafood",
    "mei fun singapore", "singapore mei fun",
    "mei fun chicken", "chicken mei fun", "mei fun shrimp",
    "shrimp mei fun", "mei fun beef", "beef mei fun",
    "mei fun pork", "pork mei fun",
    "pad thai chicken", "chicken pad thai", "pad thai shrimp",
    "shrimp pad thai", "pad thai beef", "beef pad thai",
    "pad thai pork", "pork pad thai", "pad thai veggie",
    "veggie pad thai", "pad thai tofu", "tofu pad thai",
    "pad see ew",
    "drunken noodles",
    "basil chicken", "chicken basil", "basil beef", "beef basil",
    "basil shrimp", "shrimp basil",
    "basil pork", "pork basil",
    "spicy basil", "basil spicy",
    "thai curry", "curry thai", "green curry", "red curry",
    "yellow curry", "panang curry", "mussaman curry", "massaman curry",
    "curry chicken", "chicken curry", "curry beef", "beef curry",
    "curry shrimp", "shrimp curry", "curry vegetable", "vegetable curry",
    "curry tofu", "tofu curry",
    "garlic chicken", "garlic shrimp", "garlic pork",
    "ginger chicken", "ginger beef", "ginger shrimp",
    "honey shrimp", "honey chicken",
    "rice congee",
    "tofu broccoli", "broccoli tofu", "tofu garlic",
    "string beans", "beans string",
    "snow peas", "peas snow",
    "moo shu pork", "moo shu chicken", "moo shu shrimp",
    "moo shu beef", "moo shu vegetable",
    "moo goo gai pan",
    "egg foo young", "foo young egg",
    "shrimp foo young", "foo young shrimp",
    "chicken foo young", "foo young chicken",
    "pork foo young", "foo young pork",
    "beef foo young", "foo young beef",
    "veggie foo young", "vegetable foo young",
    "salt pepper", "pepper salt",
    "salt pepper shrimp", "salt pepper chicken", "salt pepper pork",
    "salt pepper calamari", "salt pepper squid",
    "honey walnut shrimp", "walnut shrimp",
    "kung pao chicken", "kung pao shrimp", "kung pao beef",
    "kung pao tofu",
    "general tso chicken", "tso s chicken", "general tso s chicken",
    "sesame chicken", "chicken sesame", "sesame shrimp",
    "shrimp sesame", "sesame beef", "beef sesame",
    "orange chicken", "chicken orange", "orange beef", "beef orange",
    "orange shrimp", "shrimp orange",
    "lemon chicken", "chicken lemon", "lemon shrimp", "shrimp lemon",
    "mongolian beef", "beef mongolian", "mongolian chicken",
    "chicken mongolian", "mongolian shrimp", "shrimp mongolian",
    "hunan beef", "beef hunan", "hunan chicken", "chicken hunan",
    "hunan shrimp", "shrimp hunan",
    "szechuan beef", "beef szechuan", "szechuan chicken",
    "chicken szechuan", "szechuan shrimp", "shrimp szechuan",
    "twice cooked pork", "twice cooked",
    "ma po tofu", "mapo tofu", "tofu mapo",
    "bean curd",  # tofu dish
    "curd bean",
    "homestyle tofu", "tofu homestyle",
    "kungpao", "kungpao chicken",
    "thai basil",
    "chicken broccoli", "broccoli chicken",
    "shrimp broccoli", "broccoli shrimp",
    "beef broccoli", "broccoli beef",
    "pork broccoli", "broccoli pork",
    "tofu broccoli", "broccoli tofu",
    "snow pea", "pea snow",
    "snow peas",
    "fried squid", "squid fried", "calamari fried", "fried calamari",
    "boneless ribs", "ribs boneless", "boneless spare ribs",
    "spare boneless ribs",
    "boneless spare", "spare boneless",
    "ribs spare", "spare ribs",
    "wonton",
    "dumpling chicken", "chicken dumpling", "dumpling pork",
    "pork dumpling", "dumpling beef", "beef dumpling",
    "dumpling shrimp", "shrimp dumpling", "dumpling veggie",
    "veggie dumpling", "dumpling vegetable", "vegetable dumpling",
    "momo",  # Tibetan/Nepali dumpling
    "momo chicken", "chicken momo", "momo beef", "beef momo",
    "momo veg", "veg momo", "momo veggie", "veggie momo",
    "potstickers chicken", "chicken potstickers",
    "thukpa",
    "thali",
    "biryani",
    "korma",
    "vindaloo",
    "tandoori",
    "naan",
    "samosa",
    "pakora",
    "saag paneer", "paneer saag", "palak paneer", "paneer palak",
    "matar paneer", "paneer matar", "shahi paneer", "paneer shahi",
    "paneer tikka", "tikka paneer",
    "paneer butter", "butter paneer",
    "kadhai chicken", "chicken kadhai", "kadhai paneer",
    "chana masala", "masala chana", "chole",
    "dal makhani", "makhani dal",
    "dal tadka",
    "rajma",
    "aloo gobi", "gobi aloo", "aloo paratha",
    "lamb biryani", "chicken biryani", "shrimp biryani",
    "veg biryani", "vegetable biryani", "mutton biryani",
    "lamb curry", "chicken curry", "shrimp curry",
    "beef curry", "goat curry", "fish curry",
    "lamb vindaloo", "chicken vindaloo", "vegetable vindaloo",
    "lamb korma", "chicken korma", "vegetable korma",
    "tandoori chicken",
    "chicken biryani",
    "lamb biryani",
    "lobster sauce shrimp", "shrimp lobster sauce",
    "lobster sauce chicken",
    "garlic sauce chicken", "garlic sauce beef",
    "garlic sauce shrimp", "garlic sauce tofu",
    "garlic sauce pork",
    "oyster sauce beef", "beef oyster sauce",
    "oyster sauce chicken", "chicken oyster sauce",
    "curry sauce chicken", "chicken curry sauce",
    "curry sauce beef", "beef curry sauce",
}


# -------------- Patterns --------------

INSTRUCTION_PATTERNS = [
    re.compile(r"\bbuild\s+\w*\s*own\b"),
    re.compile(r"\bcreate\s+\w*\s*own\b"),
    re.compile(r"\bmake\s+\w*\s*own\b"),
    re.compile(r"\bpick\s+your\b"),
    re.compile(r"\bchoose\s+your\b"),
    re.compile(r"\bcustomize\b"),
    re.compile(r"\bdesign\s+your\b"),
    re.compile(r"\bown\s+your\b"),  # alphabetized
    re.compile(r"\byour\s+own\b"),
]

DEAL_PATTERNS = [
    re.compile(r"\bbogo\b"),
    re.compile(r"\b\d+\s*for\s*\$\d"),
    re.compile(r"\b\d+\s*for\s*\d+\b"),
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
    re.compile(r"\bk[\s-]*cups?\b"),
    re.compile(r"\bvariety\s+pack\b"),
    re.compile(r"\bbox\s+of\b"),
    re.compile(r"\bbulk\b"),
    re.compile(r"\bcatering\b"),
    re.compile(r"\bfeeds\b"),
    re.compile(r"\bfor\s+the\s+table\b"),
    re.compile(r"\bcrew\s+pack\b"),
    re.compile(r"\bgroup\s+order\b"),
    re.compile(r"\bsharer\b"),
    re.compile(r"\bgallon\b"),
    re.compile(r"\bsharing\b"),
    re.compile(r"\bpack\s+of\b"),
    re.compile(r"\b\d+\s*(piece|pc|pcs)\s+(bucket|family|tray|platter|pack|box|combo|meal)\b"),
    re.compile(r"\bcombo\s+meal\s+for\s+\d"),
    re.compile(r"\bpounds?\b"),
    re.compile(r"\blbs?\b"),
    re.compile(r"\bquart\b"),
    re.compile(r"\bgallons?\b"),
    re.compile(r"\bpints?\b"),
    re.compile(r"\b\d+\s*pcs?\b"),
    re.compile(r"\bx\d+\b"),  # x6, x12 etc — quantity
    re.compile(r"\b\d+pc\b"),
    re.compile(r"\b\d+\s*piece\b"),
]


# -------------- Helpers --------------

def has_word(name: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", name) is not None


def has_any_word(name: str, words: set) -> bool:
    tokens = name.split()
    return any(t in words for t in tokens)


def has_any_phrase(name: str, phrases) -> str | None:
    for p in phrases:
        if p in name:
            return p
    return None


def matches_any_pattern(name: str, patterns) -> bool:
    return any(p.search(name) for p in patterns)


def has_main_anchor(name: str) -> bool:
    tokens = name.split()
    for t in tokens:
        if t in MAIN_ANCHORS:
            return True
    return has_any_phrase(name, COMPOUND_KEEP_PHRASES) is not None


def is_short_code_or_letter_token(t: str) -> bool:
    """Check if token is a code-like fragment: e.g. c1, c12, n3, e7, m1, h1, v2, hs1."""
    if re.fullmatch(r"[a-z]{1,2}\d{1,3}", t):
        return True
    if re.fullmatch(r"\d{1,3}[a-z]{1,2}", t):
        return True
    if len(t) == 1 and t.isalpha():
        return True
    if len(t) <= 2 and not t.isalpha():
        return True
    return False


# -------------- Classifier --------------

def classify(name: str) -> tuple[str, str]:
    n = name.strip().lower()
    if not n:
        return "drop", "fragment"

    tokens = n.split()

    # 1. Instruction
    if matches_any_pattern(n, INSTRUCTION_PATTERNS):
        return "drop", "instruction"

    # 2. Deal
    if matches_any_pattern(n, DEAL_PATTERNS):
        return "drop", "deal"

    # 3. Bulk
    if matches_any_pattern(n, BULK_PATTERNS):
        return "drop", "bulk"

    has_anchor = has_main_anchor(n)

    # 4. Drink — strong drink token without main anchor
    if has_any_word(n, DRINK_TOKENS):
        if not has_anchor:
            # Allow if a real protein paired with drink word (e.g. "bourbon chicken")
            if has_any_word(n, PROTEINS):
                pass
            else:
                return "drop", "drink"

    # tea drink
    if has_word(n, "tea"):
        if not has_anchor:
            if any(p in n for p in TEA_DRINK_PHRASES) or n == "tea":
                return "drop", "drink"

    # juice/water alone
    if has_word(n, "juice") and not has_anchor:
        return "drop", "drink"
    if has_word(n, "water") and not has_anchor:
        if has_any_word(n, WATER_DRINK_INDICATORS):
            return "drop", "drink"

    # 5. Dessert
    if has_any_word(n, DESSERT_TOKENS):
        # cake exception
        if has_word(n, "cake") or has_word(n, "cakes"):
            if any(t in CAKE_KEEP_HINTS for t in tokens):
                pass  # not dessert
            else:
                return "drop", "dessert"
        elif has_word(n, "concrete"):
            # "concrete jungle pizza" is fine; but "concrete" alone or "concrete vanilla" is dessert
            if "pizza" in tokens or "jungle" in tokens:
                pass
            else:
                return "drop", "dessert"
        elif has_word(n, "tres") and has_word(n, "leches"):
            return "drop", "dessert"
        elif has_word(n, "tres") and has_word(n, "amigos"):
            pass  # "amigos enchiladas tres" — combo dish
        elif has_word(n, "halo"):
            if "halo" in tokens and tokens.count("halo") >= 2:
                return "drop", "dessert"
            pass  # "halal" was filtered? No: check
        else:
            return "drop", "dessert"

    # pie — drop only if dessert pie context (no savory keyword)
    if has_word(n, "pie") and "pizza" not in n:
        savory_keywords = {"pot", "shepherd", "shepherds", "cottage",
                           "meat", "fish", "chicken", "beef", "pork",
                           "turkey", "lamb", "tuna", "salmon", "spinach",
                           "broccoli", "frito", "fritos", "tamale",
                           "hand", "brooklyn"}
        if not any(t in savory_keywords for t in tokens):
            dessert_pie_words = {"apple", "pumpkin", "cherry", "pecan",
                                 "blueberry", "lemon", "chocolate",
                                 "strawberry", "lime", "cream", "berry",
                                 "banana", "coconut"}
            if any(t in dessert_pie_words for t in tokens) or len(tokens) <= 2:
                return "drop", "dessert"

    # muffin
    if has_word(n, "muffin") or has_word(n, "muffins"):
        if any(s in n for s in ["english muffin", "egg", "sausage",
                                 "bacon", "mcmuffin"]):
            pass
        else:
            return "drop", "dessert"

    # parfait
    if has_word(n, "parfait"):
        return "drop", "snack"

    # 6. Side — strong side token without anchor
    if has_any_word(n, SIDE_TOKENS):
        is_stir_fry = ("fry stir" in n or "stir fry" in n or "stir fried" in n
                       or "fried stir" in n)
        is_fish_fry = ("fish fry" in n or "fry fish" in n)
        if has_anchor or is_stir_fry or is_fish_fry:
            pass
        else:
            return "drop", "side"

    # 7. Snack
    if has_any_word(n, SNACK_TOKENS):
        if not has_anchor:
            if has_word(n, "chips"):
                # chips paired with sauce -> snack
                if any(s in n for s in SNACK_PHRASES):
                    return "drop", "snack"
                # chips alone or with non-anchor combo -> snack
                if not has_anchor:
                    return "drop", "snack"
            else:
                return "drop", "snack"

    # 8. Sauce
    for pat in SAUCE_BARE_PATTERNS:
        if pat.search(n):
            return "drop", "sauce"
    if n in SAUCE_BARE_NAMES:
        return "drop", "sauce"
    if n.startswith("extra ") and "sauce" in n and not has_anchor:
        return "drop", "sauce"

    # 9. Marketing-only
    if all(t in MARKETING_TOKENS for t in tokens):
        return "drop", "marketing"

    # 10. Fragment detection: too many short/code tokens
    short_or_code = sum(1 for t in tokens if is_short_code_or_letter_token(t))
    if short_or_code >= len(tokens) // 2 and short_or_code >= 2 and not has_anchor:
        return "drop", "fragment"

    # If majority of tokens are 1-character and there's no anchor -> fragment
    one_char = sum(1 for t in tokens if len(t) == 1)
    if one_char >= 2 and not has_anchor:
        return "drop", "fragment"

    # 11. Single-token rules
    if len(tokens) == 1:
        single = tokens[0]
        if single in MAIN_ANCHORS:
            # but generic anchors alone like "wrap", "sandwich", "bowl", "combo" -> fragment
            generic_alone = {"sandwich", "sub", "wrap", "panini", "bowl",
                             "plate", "platter", "combo", "burger",
                             "pizza", "pasta", "salad", "rice", "noodle",
                             "noodles", "soup", "tacos", "taco", "burrito",
                             "burritos", "pho", "fillet", "filet",
                             "calzone", "stromboli", "hoagie",
                             "lasagna", "ramen", "udon", "soba",
                             "naan", "biryani", "curry", "tikka",
                             "wings", "tenders", "nuggets",
                             "ribs", "rib", "chops", "chop",
                             "steak", "steaks", "stew", "chili",
                             "chowder", "kebab", "kabob", "shawarma",
                             "gyro", "souvlaki", "doner", "falafel",
                             "casserole", "sushi", "roll", "rolls",
                             "sashimi", "tempura", "katsu", "donburi",
                             "bibimbap", "bulgogi", "meatloaf",
                             "meatballs", "dumplings", "dumpling",
                             "pancake", "pancakes", "waffle", "waffles",
                             "crepe", "crepes", "toast", "salad",
                             "salads", "pita", "boy", "po", "stack",
                             "melt", "skillet", "kimchi",
                             "pasta", "spaghetti", "macaroni"}
            if single in generic_alone:
                return "drop", "fragment"
            return "keep", "main"
        if single in BARE_INGREDIENTS:
            return "drop", "ingredient"
        if single in MARKETING_TOKENS:
            return "drop", "marketing"
        if len(single) <= 4:
            return "drop", "fragment"
        # Unknown single word — DROP (strict)
        return "drop", "fragment"

    # 12. Two-token classification
    if len(tokens) == 2:
        # Both tokens marketing -> marketing
        if all(t in MARKETING_TOKENS for t in tokens):
            return "drop", "marketing"
        # Both tokens bare ingredients only -> ingredient
        if all(t in BARE_INGREDIENTS for t in tokens):
            # protein + protein could be sandwich combo
            num_proteins = sum(1 for t in tokens if t in PROTEINS)
            if num_proteins >= 2:
                return "keep", "main"
            return "drop", "ingredient"
        # Both very short / code-like
        if all(len(t) <= 3 for t in tokens):
            return "drop", "fragment"
        # No anchor and no protein -> fragment
        if not has_anchor and not has_any_word(n, PROTEINS):
            # both short or generic
            if all(len(t) <= 5 for t in tokens):
                return "drop", "fragment"
            # if one is marketing and the other is generic
            if any(t in MARKETING_TOKENS for t in tokens):
                # check if other token clearly identifies a dish
                other = [t for t in tokens if t not in MARKETING_TOKENS]
                if other and other[0] not in MAIN_ANCHORS:
                    return "drop", "fragment"

    # 13. Check compound dish phrase
    if has_any_phrase(n, COMPOUND_KEEP_PHRASES):
        return "keep", "main"

    # 14. Strong fragment: many tokens, none are anchors, none are proteins
    if not has_anchor and not has_any_word(n, PROTEINS):
        # If all tokens are marketing/ingredient/short -> fragment
        meaningful = [t for t in tokens
                      if t not in MARKETING_TOKENS
                      and t not in BARE_INGREDIENTS
                      and not is_short_code_or_letter_token(t)
                      and len(t) > 3]
        if len(meaningful) <= 1:
            return "drop", "fragment"

    # 15. Has anchor or has protein → likely main; KEEP
    if has_anchor or has_any_word(n, PROTEINS):
        return "keep", "main"

    # 16. Default: when in doubt → DROP (strict)
    return "drop", "fragment"


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
