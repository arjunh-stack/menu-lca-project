"""Structural few-shot references for the grams-first ingredient prompt.

Ported verbatim from ../menu-project/ingredient_pipeline.py (production
design from METHODOLOGY.md Phase 4). Ingredient names are deliberately
replaced with generic labels ([protein], [starch/carb], etc) to give the
LLM proportion calibration without anchoring it to specific ingredients.

CATEGORY_MAP routes a restaurant-category tag (e.g. "burgers", "sushi") to
the structural reference bucket whose grams distribution most resembles
that cuisine.
"""

STRUCTURAL_REFERENCES = {
    "chicken": """Recipe type: "Chicken Fajita Mac and Cheese" (total weight: 1808g)
  - [starch/carb]: 450g (24.9%)
  - [dairy]: 400g (22.1%)
  - [protein]: 300g (16.6%)
  - [dairy]: 240g (13.3%)
  - [vegetable]: 150g (8.3%)
  - [vegetable]: 150g (8.3%)
  - [seasoning/spice]: 45g (2.5%)
  - [liquid/stock]: 30g (1.7%)
  - [seasoning/spice]: 15g (0.8%)
  - [seasoning/spice]: 5g (0.3%)

Recipe type: "Pad See Ew" (total weight: 970g)
  - [starch/carb]: 300g (30.9%)
  - [protein]: 250g (25.8%)
  - [vegetable]: 150g (15.5%)
  - [sauce/condiment]: 90g (9.3%)
  - [seasoning/spice]: 50g (5.2%)
  - [protein]: 50g (5.2%)
  - [liquid/stock]: 45g (4.6%)
  - [sugar/sweet]: 30g (3.1%)
  - [seasoning/spice]: 5g (0.5%)""",

    "beef": """Recipe type: "Beef Stroganoff" (total weight: 1535g)
  - [protein]: 500g (32.6%)
  - [dairy]: 300g (19.5%)
  - [vegetable]: 250g (16.3%)
  - [liquid/stock]: 200g (13.0%)
  - [vegetable]: 150g (9.8%)
  - [starch/carb]: 75g (4.9%)
  - [liquid/stock]: 30g (2.0%)
  - [seasoning/spice]: 15g (1.0%)
  - [seasoning/spice]: 10g (0.7%)
  - [seasoning/spice]: 5g (0.3%)

Recipe type: "Beef and Oyster pie" (total weight: 1245g)
  - [protein]: 400g (32.1%)
  - [starch/carb]: 350g (28.1%)
  - [liquid/stock]: 250g (20.1%)
  - [vegetable]: 150g (12.0%)
  - [dairy]: 50g (4.0%)
  - [seasoning/spice]: 15g (1.2%)
  - [starch/carb]: 15g (1.2%)
  - [seasoning/spice]: 10g (0.8%)
  - [seasoning/spice]: 5g (0.4%)""",

    "seafood": """Recipe type: "Fish pie" (total weight: 1850g)
  - [dairy]: 500g (27.0%)
  - [protein]: 400g (21.6%)
  - [vegetable]: 400g (21.6%)
  - [protein]: 200g (10.8%)
  - [dairy]: 150g (8.1%)
  - [starch/carb]: 100g (5.4%)
  - [dairy]: 50g (2.7%)
  - [seasoning/spice]: 30g (1.6%)
  - [seasoning/spice]: 15g (0.8%)
  - [seasoning/spice]: 5g (0.3%)

Recipe type: "Shrimp stir fry" (total weight: 820g)
  - [protein]: 300g (36.6%)
  - [vegetable]: 200g (24.4%)
  - [vegetable]: 100g (12.2%)
  - [sauce/condiment]: 60g (7.3%)
  - [liquid/stock]: 45g (5.5%)
  - [seasoning/spice]: 45g (5.5%)
  - [starch/carb]: 30g (3.7%)
  - [seasoning/spice]: 20g (2.4%)
  - [seasoning/spice]: 15g (1.8%)
  - [seasoning/spice]: 5g (0.6%)""",

    "vegetarian": """Recipe type: "Dal fry" (total weight: 690g)
  - [starch/carb]: 200g (29.0%)
  - [vegetable]: 150g (21.7%)
  - [vegetable]: 150g (21.7%)
  - [liquid/stock]: 100g (14.5%)
  - [seasoning/spice]: 30g (4.3%)
  - [liquid/stock]: 15g (2.2%)
  - [seasoning/spice]: 15g (2.2%)
  - [seasoning/spice]: 10g (1.4%)
  - [seasoning/spice]: 5g (0.7%)
  - [seasoning/spice]: 5g (0.7%)

Recipe type: "Mushroom risotto" (total weight: 1050g)
  - [liquid/stock]: 500g (47.6%)
  - [vegetable]: 200g (19.0%)
  - [starch/carb]: 150g (14.3%)
  - [dairy]: 100g (9.5%)
  - [liquid/stock]: 50g (4.8%)
  - [dairy]: 30g (2.9%)
  - [seasoning/spice]: 10g (1.0%)
  - [seasoning/spice]: 5g (0.5%)""",

    "dessert": """Recipe type: "Chocolate Gateau" (total weight: 875g)
  - [sugar/sweet]: 250g (28.6%)
  - [starch/carb]: 200g (22.9%)
  - [dairy]: 175g (20.0%)
  - [sugar/sweet]: 100g (11.4%)
  - [protein]: 100g (11.4%)
  - [dairy]: 30g (3.4%)
  - [sugar/sweet]: 10g (1.1%)
  - [seasoning/spice]: 5g (0.6%)

Recipe type: "Rock Cakes" (total weight: 655g)
  - [starch/carb]: 225g (34.4%)
  - [fruit]: 150g (22.9%)
  - [dairy]: 125g (19.1%)
  - [sugar/sweet]: 75g (11.5%)
  - [protein]: 50g (7.6%)
  - [dairy]: 15g (2.3%)
  - [sugar/sweet]: 10g (1.5%)
  - [seasoning/spice]: 5g (0.8%)""",

    "pasta": """Recipe type: "Lasagne" (total weight: 1680g)
  - [protein]: 500g (29.8%)
  - [sauce/condiment]: 400g (23.8%)
  - [starch/carb]: 250g (14.9%)
  - [dairy]: 200g (11.9%)
  - [vegetable]: 150g (8.9%)
  - [vegetable]: 80g (4.8%)
  - [liquid/stock]: 45g (2.7%)
  - [seasoning/spice]: 30g (1.8%)
  - [seasoning/spice]: 15g (0.9%)
  - [seasoning/spice]: 10g (0.6%)

Recipe type: "Spaghetti Bolognese" (total weight: 1350g)
  - [protein]: 400g (29.6%)
  - [starch/carb]: 350g (25.9%)
  - [sauce/condiment]: 250g (18.5%)
  - [vegetable]: 150g (11.1%)
  - [vegetable]: 80g (5.9%)
  - [liquid/stock]: 50g (3.7%)
  - [seasoning/spice]: 30g (2.2%)
  - [liquid/stock]: 15g (1.1%)
  - [seasoning/spice]: 15g (1.1%)
  - [seasoning/spice]: 10g (0.7%)""",

    "default": """Recipe type: "Mixed dish" (total weight: 1200g)
  - [protein]: 350g (29.2%)
  - [starch/carb]: 250g (20.8%)
  - [vegetable]: 200g (16.7%)
  - [liquid/stock]: 150g (12.5%)
  - [vegetable]: 100g (8.3%)
  - [dairy]: 75g (6.3%)
  - [sauce/condiment]: 30g (2.5%)
  - [seasoning/spice]: 20g (1.7%)
  - [liquid/stock]: 15g (1.3%)
  - [seasoning/spice]: 10g (0.8%)

Recipe type: "Simple meal" (total weight: 900g)
  - [protein]: 300g (33.3%)
  - [starch/carb]: 200g (22.2%)
  - [vegetable]: 150g (16.7%)
  - [liquid/stock]: 100g (11.1%)
  - [dairy]: 50g (5.6%)
  - [sauce/condiment]: 45g (5.0%)
  - [seasoning/spice]: 30g (3.3%)
  - [seasoning/spice]: 15g (1.7%)
  - [seasoning/spice]: 10g (1.1%)""",
}


# Tag → bucket routing with priority tiers.
#
# Bucket shape recap (see STRUCTURAL_REFERENCES above):
#   chicken    = Chicken Fajita Mac + Pad See Ew — high-carb (25-30%), medium
#                protein, lots of seasonings. Fits Asian noodle/rice dishes.
#   beef       = Beef Stroganoff + Beef and Oyster pie — high protein (32%),
#                dairy/stock heavy. Fits stews, casseroles, burgers, steak.
#   seafood    = Fish pie + Shrimp stir fry — high protein (20-37%) with
#                vegetable or dairy. Fits sushi/fish/shrimp dishes.
#   pasta      = Lasagne + Spaghetti Bolognese — high protein + sauce + starch
#                + dairy. Fits pasta and pizza.
#   vegetarian = Dal fry + Mushroom risotto — starch/veg/liquid heavy, ~0%
#                protein. ONLY good for genuinely meat-free dishes.
#   dessert    = Chocolate Gateau + Rock Cakes — sugar/starch/dairy heavy.
#   default    = Mixed dish + Simple meal — balanced (29% protein, 21%
#                starch, 17% veg). Safe fallback when cuisine is unclear or
#                spans proteins.
#
# Priority tiers — `bucket_for_tags` scans all tags on a restaurant and
# returns the highest-priority match. Tier 1 (ingredient) beats Tier 2
# (cuisine) beats Tier 3 (dietary restriction) beats Tier 4 (dessert).
# This fixes cases like "Pizza, Wings, American" where pizza→pasta would
# win first-match but wings→chicken is the real signal.
#
# Changes from the menu-project original (documented for FILTERING_LOG):
#   DROPPED — these mapped to wrong buckets; tags now fall through to "default":
#     healthy, salad, salads     (were→vegetarian; meal-salads have protein)
#     mexican, tacos, burritos   (were→beef; span beef/chicken/pork/bean/fish)
#     indian                     (was→vegetarian; US Indian is mostly meat curries)
#     vegetarian friendly        (was→vegetarian; means "we have veg options", not "veg-only")
#     vegetarian                 (was→vegetarian; too noisy — restaurant could be
#                                 "Indian, Vegetarian" while still serving meat curries.
#                                 Vegan is the cleaner signal for fully meat-free.)
#   CHANGED:
#     thai                       (seafood → chicken; the chicken template *is* Pad See Ew)
#   ADDED:
#     noodles, vietnamese, korean, caribbean, fried chicken → chicken
#     bbq → beef

TIER_1_INGREDIENT = {  # direct protein/dish-type signal
    "chicken":        "chicken",
    "fried chicken":  "chicken",
    "wings":          "chicken",
    "poultry":        "chicken",
    "beef":           "beef",
    "steak":          "beef",
    "burger":         "beef",
    "burgers":        "beef",
    "bbq":            "beef",
    "seafood":        "seafood",
    "fish":           "seafood",
    "sushi":          "seafood",
    "poke":           "seafood",
    "noodles":        "chicken",
    "pasta":          "pasta",
}

TIER_2_CUISINE = {  # cuisine style → shape of typical dish
    "asian":          "chicken",
    "chinese":        "chicken",
    "thai":           "chicken",
    "vietnamese":     "chicken",
    "korean":         "chicken",
    "caribbean":      "chicken",
    "japanese":       "seafood",
    "italian":        "pasta",
    "pizza":          "pasta",
}

TIER_3_DIET = {  # only fully restricted restaurants
    "vegan":          "vegetarian",
}

TIER_4_DESSERT = {
    "dessert":        "dessert",
    "desserts":       "dessert",
    "ice cream":      "dessert",
    "bakery":         "dessert",
}

_TIERS = (TIER_1_INGREDIENT, TIER_2_CUISINE, TIER_3_DIET, TIER_4_DESSERT)

# Flat union, exposed for callers that want a single-shot lookup. Tier 1
# wins on collisions (since dicts merge later-keys-win, we merge in reverse).
CATEGORY_MAP: dict[str, str] = {}
for _t in reversed(_TIERS):
    CATEGORY_MAP.update(_t)


def bucket_from_category(restaurant_category: str | None) -> str:
    """Match a restaurant's comma-separated category tags to a structural bucket key.

    Scans ALL tags by tier priority — tier 1 (ingredient) beats tier 2 (cuisine)
    beats tier 3 (diet) beats tier 4 (dessert). Within a tier, first match wins.
    Returns the bucket key ("chicken", "beef", ..., or "default").
    """
    if not restaurant_category:
        return "default"
    tags = [t.strip().lower() for t in restaurant_category.split(",")]
    for tier in _TIERS:
        for tag in tags:
            if tag in tier:
                return tier[tag]
    return "default"


def get_structural_reference(bucket: str) -> str:
    """Return the structural reference text for a given bucket key."""
    return STRUCTURAL_REFERENCES.get(bucket, STRUCTURAL_REFERENCES["default"])
