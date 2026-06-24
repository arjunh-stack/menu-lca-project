# Filtering & Cleaning Log

Tracks every transformation applied to the raw Kaggle SQLite db (`mydb.sqlite`) so we can reproduce / undo / audit each layer.

- **Cleaning layers (C1–C5)**: in-place modifications to fix data quality issues. Idempotent.
- **Filtering layers (Layer 1+)**: row-exclusion rules applied during analysis (do NOT modify db).

## Pipeline summary (top-down)

| Stage | What | Resulting count |
|---|---|---|
| Source `restaurants` | raw | 63,469 |
| Source `menus` | raw | 5,117,217 |
| C1–C5 | in-place db cleaning (price, HTML, USD column, category canonicalization) | (no row delta) |
| Layer 1 | drop non-restaurant categories (pharmacy, grocery, retail, dessert/coffee/bar shops) | 45,109 restaurants → 3,286,489 menu rows |
| Layer 2 | drop non-mains menu sections (drinks/desserts/sides/sauces/kids/catering/etc.) | 1,659,202 menu rows |
| Layer 3 | fuzzy dish-name normalization (case, html, sizes, qty, sort tokens) | 288,307 distinct names |
| Layer 4 | infer dish format from `menus.category` (`Tuna` + Wraps → `tuna wrap`) | 297,383 distinct |
| Layer 5 | heuristic flagger — drop pure marketing/instruction/single-token rows | 296,140 → 285,011 |
| Layer 6 | lenient per-row LLM classification (30 parallel agents) | 276,431 |
| Layer 7 | strict "recipe test" LLM re-classification (30 parallel agents, "when in doubt → DROP") | 195,949 |
| Layer 8 | mechanical drop of pathological long/repeat-token fragments | 195,551 |
| Layer 9 | hybrid alias clustering (fuzz.ratio bucketed by token count) | 165,655 canonical dishes (with ~30k alias links) |
| Layer 10 | curated-dictionary synonym merge (sub/hoagie/grinder, prawn/shrimp, etc.) | 164,823 canonical dishes |
| Layer 11A | heuristic drop of bare ingredients + redundant numbered variants | 163,211 |
| Layer 11B | LLM strict-pass on the digit-with-no-match review pile (3 parallel agents) | 153,007 |
| Layer 12 | token-based drop of side/snack/appetizer/combo/à-la-carte indicators | 149,244 |
| Layer 13 | strip floating single-letter tokens (apostrophe-s, BMT/BLT acronyms, w/) | 148,181 |
| Layer 14 | LLM-judged long-tail merges (token-overlap candidates → Gemini Flash YES/NO) | 124,800 canonical dishes |
| Layer 15 | strip Subway/chain marketing tokens (`footlong`, `pro`) | 124,712 |
| Layer 16 | drop canonicals containing `meal`/`meals`/`dinner`/`dinners` | 122,897 |
| Layer 17 | second LLM long-tail merge pass (post-15/16 candidates → Gemini Flash YES/NO) | 117,154 canonical dishes |
| Layer 18 | sub↔sandwich relaxed LLM pass (skeleton-equal pairs → relaxed prompt) | 115,348 |
| Layer 19 | drop bare-format canonicals (`sandwich sub`, `burger`, `plate taco`, etc.) | 115,320 |
| Layer 20 | LLM keep/drop on over-tokenized singleton fragments (≥5 tokens, no allowlist noun) | 114,920 canonical dishes |
| Layer 21 | drop add-on canonicals (`add chicken`, `add avocado burrito`, etc.) | 114,873 canonical dishes |
| Layer 22 | strip artifact doubled tokens (preserve `mahi mahi`, `bang bang`, etc.) | 114,865 canonical dishes |
| Layer 23 | targeted quesadilla cleanup (Spanish↔English, plural→singular, abbreviation) | 114,855 canonical dishes |
| Layer 24 | parallel-agent multi-category cleanup (11 categories, 1,130 high-confidence merges/renames applied) | **113,925 canonical dishes** |

## Source

- **File:** `mydb.sqlite`
- **Tables:** `restaurants` (63,469 rows), `menus` (5,117,217 rows)
- **Schema (post-cleaning):**
  - `restaurants`: id, position, name, score, ratings, category, price_range, full_address, zip_code, lat, lng
  - `menus`: restaurant_id, category, name, description, price, **price_usd** (added in C3)

## Cleaning Layers (in-place db modifications)

All implemented in `clean_db.py`. Idempotent — safe to re-run.

### C1 — Null bizarre price_range
**Issue:** one restaurant had `price_range = '$$$$$$$$$$$$$$$$$'` (17 dollar signs).
**Action:** set that one row's `price_range` to NULL.
**Affected:** `Schlotzsky's Deli` (id `45119`) at 8745 Memorial Blvd, Port Arthur, TX 77640. 1 row.

### C2 — HTML-unescape text columns
**Issue:** raw data has HTML entities (`&amp;`, `&lt;`, `&gt;`, `&Amp;`) and some are double-encoded (`&amp;amp;`).
**Action:** unescape `restaurants.category`, `menus.name`, `menus.description` until idempotent. Also handles wrong-cased entities (`&Amp;` → `&`) via case-insensitive regex.
**Affected:**
- `restaurants.category`: 3,592 rows
- `menus.name`: 242,463 rows
- `menus.description`: 282,120 rows
**Notes:** 47 malformed numeric entities (`&#amp;` — invalid syntax) in beauty-product descriptions are left alone. Strings containing literal `&...;` (e.g., "shrimp & egg; ...") are correctly not touched.

### C3 — Numeric price column (`menus.price_usd`)
**Issue:** `menus.price` is TEXT, formatted as `"9.99 USD"`. All 5.1M rows verified to be USD (no currency conversion needed).
**Action:** added `menus.price_usd REAL` column. Populated by stripping ` USD` suffix and casting via `CAST(REPLACE(price, ' USD', '') AS REAL)`.
**Affected:** 5,117,217 rows. 0 NULL after.
**Notes:**
- Original `menus.price` text column preserved.
- Range observed: min `-7.05`, max `1395.00`, mean `10.37`. Negative prices exist (likely discounts/credits) — left as-is.
- 174k rows have `price_usd = 0.0` (free items / placeholders / drink bundles).

### C4 — Canonicalize `restaurants.category`
**Issue:** comma-separated tag list contained typo/case/punctuation/singular-plural duplicates (e.g., `burger`/`Burger`/`Burgers`, `Coffee & Tea`/`Coffee and Tea`, `Sandwich`/`Sandwiches`, `Ice Cream`/`Ice cream`).
**Action (two passes per tag):**
- **Pass 1 (cluster key):** lowercase + html-unescape + replace `&`/`+` with `and` + collapse whitespace. Within each cluster, canonical = most common original spelling.
- **Pass 2 (singular/plural):** for canonicals from pass 1, apply `-ies → -y`, `-ches/-shes/-xes/-sses/-zes → drop -es`, `-oes → -o`, plain `-s → drop`. Within each singularized cluster, canonical = most common.
- For each restaurant, split category on `,`, map each tag, dedup, rejoin.
**Affected:**
- Tag count: 380 raw → **365 canonical**
- Restaurants updated: 7,296 across runs
- Full mapping written to `category_canonical_mapping.csv` (raw_tag → canonical_tag → raw_count)
**Notable merges:** `burger`→`Burgers`, `wings`→`Wings`, `Coffee & Tea`→`Coffee and Tea`, `pizza`→`Pizza`, `salad`→`Salads`, `Ice Cream & Frozen Yogurt`→`Ice Cream + Frozen Yogurt`, `Breakfast & Brunch`→`Breakfast and Brunch`, `PIzza`→`Pizza`, `pasta`→`Pasta`, `Juice & Smoothies`→`Juice and Smoothies`, `Ice cream`→`Ice Cream`, `Snack`→`Snacks`, `pet supplies`→`Pet Supplies`, `italian`→`Italian`, `Sandwich`→`Sandwiches`.

### C5 — Canonicalize `menus.category`
**Issue:** the menu-section field had massive case/whitespace duplication. E.g., "Breakfast" appeared as 12 variants (`BREAKFAST`, `Breakfast `, `breakfast`, `BreakFast`, etc.); "Beverages" also had 12 variants; "Sides" had 10.
**Action:** same two-pass canonicalization as C4 — but `menus.category` is a single label per row (no comma splitting). Mapping built from all 73,048 raw values across the whole db, applied in place.
**Affected:** 713,216 menu rows updated.
**Result:**
- Whole-db distinct categories: 73,048 → **62,394** (10,654 collapsed)
- Layer-1 filtered (real restaurants only): **49,746** distinct
**Output:** `menu_category_canonical_mapping.csv` (raw → canonical → row count)
**Why so many remain:** the long tail is per-restaurant custom sections (e.g., "12 Inch Subs", "Today's Specials", "$5 Lunch", chain-specific labels like `No Bready Bowls™`, `Fresh Melts®`, `McCafé`). True semantic dedup ("Sandwiches" ≈ "Sandwich Menu" ≈ "Sub Menu") would require fuzzy/embedding clustering — not done here.

## Layer 1 — Exclude restaurants by user-marked category tags

**Why:** raw `restaurants` table mixes real restaurants with pharmacies, grocery stores, convenience stores, liquor stores, beauty supply, retail, dessert/coffee/snack-only spots, bars, etc. The user reviewed `unique_categories.csv` (380 unique tags) and explicitly marked the ones to exclude in `unique_categories_to_exclude.csv` (column B = "x").

**Rule:**
1. Load all 380 unique category tags from the source file.
2. Treat the user's `unique_categories_to_exclude.csv` column B as the exclusion set (87 tags).
3. For each restaurant, split its `category` field on `,`, html-unescape, strip whitespace, and exact-match each token against the exclusion set.
4. If ANY token matches, exclude that restaurant.

**Excluded tags (87, from `unique_categories_to_exclude.csv`):**
Açaí, Adult, Alcohol, Appetizers, Assorted Stores, Baby, Bagels, Bakery, Bar / Pub Food, Bar Food, Barfood, Beauty Supply, Beer, BOGO, bookstore, Bubble Tea, ButcherShop, Cafe, Cakes, Candy, chocolatier, Chocolate, Coffee & Tea, Coffee and Tea, Convenience, Cupcakes, Deli, Desserts, Dessert: Other, Donuts, Dount, Drinks, Everyday Essentials, Farmacia, florist, Flowers, French tacos, Frozen Food, Frozen Yogurt, Fruit, Gifts, Gift Store, Grocery, Health & Nutrition Supplements, Heat and Eat, Home & Decor, Home & Personal Care, Ice cream, Ice Cream, Ice Cream & Frozen Yogurt, Ice Cream + Frozen Yogurt, Indoor Plants & Gifts, Japanese sweets, Juice, Juice & Smoothies, Juice and Smoothies, Juice Bars, Juice Bars & Smoothies, JuiceAndSmoothie, Liquor Stores, MarketingCampaign, Mercado Express, Other, Pastry, Personal Care, Pet Shop, Pet Supplies, pet supplies, Pharmacy, Plants, Premium, Pretzel, Pub, Regalos y flores, Retail, Rolls, Smoke Shop, Smoothies, Snack, SnackAppretizer, Snacks, Specialty Foods, Sports Bar, Stir​ Fried, Tea & Coffee, whatever, Wine

**Effect:**
- Restaurants: 63,469 → **45,109** (removed 18,360)
- Menu rows: 5,117,217 → **3,286,489** (removed 1,830,728)

**Implemented in:** `dedup.py` (`load_exclude_tags`, `excluded_restaurant_ids`) and `export_restaurants.py`

**Outputs:**
- `restaurants_filtered.csv` — 45,109 kept restaurants (id, name, category, address)
- `unique_dishes_restaurants_only.csv` — deduped dishes from kept restaurants

**History:**
- v1 (superseded): substring LIKE match on 17 hardcoded keywords (Pharmacy, Grocery, Liquor, Convenience, Everyday Essentials, Home & Personal Care, Beauty, Gift Store, Retail, Baby, Pet Store, Office Supplies, Hardware, Flowers, Tobacco, Vape) → kept 59,069 restaurants. Replaced 2026-05-02 by user's explicit per-tag list above.

## Layer 2 — Exclude non-main-dish menu sections

**Why:** the user only wants dishes that someone would order as a main for breakfast/lunch/dinner. Sides, drinks, desserts, appetizers, sauces, kids menus, delivery-app-surfaced sections ("Picked for you"), and catering bundles should all be dropped.

**Rule:** drop any menu row whose `category` is in EITHER of these user-approved lists:
- `proposed_menu_category_excludes.csv` (10,437 categories pre-marked as clear non-mains)
- `proposed_menu_category_ambiguous.csv` (6,772 categories — combos, salads, soups, sushi, specials, a la carte, build-your-own, individual items, brunch, deals)

Total: **17,209 distinct menu categories excluded** at this layer.

Categorization keywords used (in `propose_menu_category_excludes.py`):
- **Drinks:** beverage, drink, coffee, tea, soda, juice, smoothie, shake, water, alcohol/beer/wine/cocktail, bubble tea, hot chocolate, frozen drink
- **Desserts:** dessert, ice cream/frozen yogurt, cake/cupcake/brownie/cookie/pie/donut/pastry/muffin/tart, candy/chocolate, croissant/scone/danish/eclair
- **Sides:** side, side order, fries
- **Appetizers/snacks:** appetizer, starter, small plate, tapas, snack/chips/popcorn/jerky
- **Add-ons:** sauce/dressing/dipping/topping/condiment, extras/modifiers, bread/bagel/pretzel
- **Kids:** kids, children, junior
- **Delivery-app surfaced:** picked for you, featured, popular, most popular, trending, new items, customer favorites, chef's picks
- **Catering:** catering, party pack, family meal, trays, by the pound, bulk
- **Non-food retail / pharmacy** (in case any leaked through Layer 1)
- **Misc:** jam/honey/syrup, merchandise, gift cards
- **Ambiguous (also dropped this round):** combo, soup, salad, specials, a la carte, build your own, deals, brunch, individual items, sushi/sashimi/nigiri

**Effect (Layer 1 + Layer 2 combined):**
- Menu rows: 5,117,217 → **1,659,202** (dropped 3,458,015)
- Distinct restaurants represented: still 45,109 (Layer 2 doesn't drop restaurants, only sections)

**Implemented in:** `dedup.py` (`load_excluded_menu_categories`)

**Note:** ambiguous categories may be re-included later for specific analyses (e.g., if salads should count as mains).

## Layer 3 — Fuzzy dish-name normalization (string-level dedup)

**Why:** raw menu names duplicate the same dish many ways: case differences, HTML entities (`&amp;`), size prefixes ("Large/XL/Jumbo"), quantity descriptors ("5 pieces", "8 oz"), parenthetical notes, leading numbers ("1.", "A)"), and word-order variation ("Pizza Margherita" vs "Margherita Pizza").

**Pipeline (applied in order to each `menus.name`) — CONSERVATIVE version (post-rewrite):**
1. HTML-unescape (`&amp;` → `&`)
2. Lowercase
3. Strip leading **enumerations only** — `1.`, `1)`, `A.`, `A)`, `#13` (not bare numbers like `12`)
4. Remove parenthetical / bracketed content
5. Strip leading `<number> [optional pc/ct/pack]` — strips the count but **KEEPS the dish noun**. So `12 Tenders Bucket` → `tenders bucket`, `5 Wings` → `wings`, `8 pc. Family Bucket Meal` → `family bucket meal`. (Word boundary on QTY_WORDS so `ten` doesn't prefix-match `tenders`.)
6. Remove embedded `<number> <measurement_unit>` — `8 oz`, `11 inch`. Measurement units only: `oz`, `lb`, `inch`, `qt`, `gal`, `ml`. Dish nouns NOT included.
7. Remove size words: extra large, xl, xxl, jumbo, grande, large, medium, regular, reg, small, sm, md, lg, mini, kids, family, party, individual, single, double, triple, half, whole, full, personal, junior, jr, senior, sr, petite, tall, short, venti
8. Remove **only safe filler**: `new, w/, with, and, the, a, an, of, in, on`. (Articles, basic prepositions, conjunction, "new".)
9. Strip non-alphanumeric chars
10. Collapse whitespace
11. Sort tokens alphabetically (so word order doesn't matter)

**Notable changes vs the original (over-aggressive) normalizer:**
- **Removed dish nouns from the unit-strip list:** `wings`, `tenders`, `nuggets`, `rolls`, `slices` — they're dishes, not units. They're still stripped when paired with a leading count via step 5.
- **Removed flavor/quality differentiators from the noise list:** `spicy, hot, cold, sweet, mild, savory, fresh, homemade, house, chef's, signature, classic, traditional, original, premium, deluxe, gourmet` — these distinguish dishes (e.g., `Spicy Italian` ≠ `Italian`).
- **Removed meal-format words from the noise list:** `special, combo, meal, plate, platter, dish, order, menu, item` — these distinguish bundles from singles.

**Why this matters:** the old normalizer collapsed `Spicy Italian` and `Italian` into `italian`, `Boneless Wings` into `boneless`, `Cold Cut Combo` into `cut`, `Chicken Tenders` into `chicken`. The new normalizer keeps those distinct.

**Effect (after Layer 1 + Layer 2 applied — mains-only set, conservative normalizer):**
- Total menu rows after L1+L2: 1,659,202
- Empty after normalization: 837 (was 16,024 under old normalizer — fewer collapse to nothing)
- Normalized distinct names: **288,307**
  - 200,893 singletons (appear at exactly 1 restaurant)
  - 87,414 appearing at 2+ restaurants

**Comparison vs old over-aggressive normalizer:** count went UP from 258,180 → 288,307 because we stopped over-merging. Top dishes are now meaningfully distinct (`wings`, `cheeseburger`, `chicken`, `buffalo chicken`, `bacon cheeseburger`, `cheese steak`, `handcrafted tenders`, `italian spicy`, `cold combo cut`, `oven roasted turkey`) instead of one-word fragments (`boneless`, `bucket`, `cut`, `handcrafted`).

**Implemented in:** `dedup.py` (`normalize()`)

**Output:** `unique_dishes_restaurants_only.csv` (sorted by frequency desc)

## Layer 4 — Infer dish format from menu.category

**Why:** many restaurants name items minimally — Subway/Jersey Mike's list `Tuna`, `Roast Beef`, `Italian` as the dish name and rely on the menu section header (`Wraps`, `Subs`, `No Bready Bowls™`) to specify format. Other restaurants put format in the dish name (`Tuna Wrap`, `Tuna Sandwich`). Without folding the category in, "Tuna" the wrap, "Tuna" the bowl, and "Tuna" the sushi all collapse together — and the bare `Tuna` entry doesn't merge with `Tuna Wrap`.

**Rule:**
1. Match `menus.category` against a list of format-keyword regexes (`wrap`, `sub`, `sandwich`, `bowl`, `pizza`, `calzone`, `sushi`, `taco`, `burrito`, `quesadilla`, `fajita`, `salad`, `pasta`, `burger`, `wings`, `ribs`, `curry`, `steak`, `soup`).
2. If **exactly one** format token matches, take it. If 0 or 2+ (e.g., `Wraps & Sandwiches`, `Pizza & Stromboli`), skip — too ambiguous.
3. Singularize any plural-format-tokens already in the dish name (`Wraps` → `wrap`, `Sandwiches` → `sandwich`) so we don't get duplicate-token rows.
4. Append the format token to the dish name's tokens, dedup, sort.

**Examples:**
| Raw name | Category | Result |
|---|---|---|
| `Tuna` | Wraps | `tuna wrap` |
| `Tuna Wrap` | Wraps | `tuna wrap` |
| `Tuna Wraps` | Wraps | `tuna wrap` (plural singularized) |
| `Tuna` | No Bready Bowls™ | `bowl tuna` |
| `Tuna` | Sushi | `sushi tuna` |
| `Roast Beef` | No Bready Bowls™ | `beef bowl roast` |
| `Pepperoni` | Pizza | `pepperoni pizza` |
| `Pepperoni Pizza` | Pizza | `pepperoni pizza` |
| `Italian` | Subs | `italian sub` |
| `Italian` | Wraps & Sandwiches | `italian` (ambiguous, skip) |
| `Spicy Italian` | Subs | `italian spicy sub` |
| `Chicken` | Tacos | `chicken taco` |

**Effect:**
- 660,175 rows (40% of the L1+L2 filtered set) had a format token inferred and folded in
- Distinct unique dishes: 288,307 → **297,383**
- Slight INCREASE because we're now distinguishing same-protein-different-format (e.g., `Tuna` the wrap vs `Tuna` the bowl) where they previously collapsed together

**Implemented in:** `dedup.py` (`CATEGORY_FORMAT_PATTERNS`, `format_from_category`, `normalize_with_format`)

## Layer 5 — Drop non-dish entries (manual + heuristic flagging)

**Why:** even after L1–L4, the unique-dish list contained ~1,200 entries that aren't actual dish names — pure marketing/format/instruction text like `meal`, `pack`, `happy`, `plate`, `classic combo`, `combo plate`, `breakfast plate`, `breakfast good morning`, plus "build-your-own" instruction patterns (`build own pizza your`, `create own pancake your`, `bowl create own your`, `burrito create own your`).

**Rule:** flag each row in `unique_dishes_mains_only.csv` as one of:
- `x` (drop) — pure non-dish: single junk words from a curated DEFINITELY_NOT list (`meal, pack, happy, plate, classic, combo, box, dinner, traditional, mix, platter, build, your, own, lunch, today, special, signature, premium, deluxe, supreme, ...`); multi-word combos where every token is in that list (`classic combo`, `combo plate`); or build/pick/make/create + your/own instruction patterns.
- `?` (drop, but more arguable) — single-word format tokens (`bowl, wings, quesadilla, burrito, tacos, pizza, salad, burger, calzone, ...`) and bare protein names (`chicken, shrimp, beef, tuna, cheese, salmon, pork, turkey, ...`). These ARE real dishes at some restaurants but are too generic to be a useful "unique dish" entry on their own.
- blank — keep.

User chose to drop both `x` and `?`.

**Effect:**
- Unique normalized dishes: 297,383 → **296,140** (dropped 1,243)
  - 1,158 dropped as `x` (definitely not dishes)
  - 85 dropped as `?` (single-token ambiguous)
- Menu rows represented by dropped entries: 36,359

**Implemented in:** `flag_non_dishes.py` (heuristics) → `unique_dishes_flagged.csv` (review file) → `apply_dish_flags.py` (Layer 5 filter) → `unique_dishes_final.csv`

## Layer 6 — Per-row LLM classification (30 parallel sub-agents)

**Why:** the heuristic flagger (Layer 5) caught obvious junk via regex patterns but missed long-tail leaks — many drinks (`free iced latte sugar vanilla`), desserts (`12 cinnabon delights pack`), snacks (`bar oatmeal`), sides, sauces, deal text, and instruction phrases that didn't fit any pattern. To handle the long tail, classified each row with judgment instead of regex.

**Rule:**
1. Split `unique_dishes_final.csv` (285,011 rows) into 30 chunks of ~9,500 rows each.
2. Spawn 30 LLM sub-agents in parallel, each handling one chunk.
3. Each agent reads its chunk and writes a classified output with verdict (`keep`/`drop`) and reason (`main`, `drink`, `dessert`, `side`, `snack`, `sauce`, `bulk`, `deal`, `instruction`, `ingredient`, `fragment`, `marketing`).
4. Each agent uses the rubric "main dishes for breakfast/lunch/dinner only" with explicit drop criteria and "when in doubt → keep" tie-breaker.
5. Merge all 30 outputs into a single audit CSV + a keep-only mains CSV.

**Effect:**
- Classified 285,011 rows
- 276,431 kept (97.0%)
- 8,580 dropped (3.0%)
- Drop reasons: drink 1,565 / fragment 1,544 / sauce 1,355 / dessert 1,292 / bulk 1,138 / side 739 / deal 349 / snack 291 / ingredient 249 / instruction 49 / marketing 9

**Outputs:**
- `unique_dishes_classified.csv` — full 285k-row audit with verdict + reason for each row
- `unique_dishes_mains.csv` — final 276,431-row mains list (keep-only, sorted by frequency)
- `chunks/` and `chunks_classified/` — per-chunk inputs/outputs (kept for re-runs / spot-checks)

**Implemented in:** `split_for_agents.py` (chunker) → 30 parallel `Agent` calls → `merge_classified.py` (merger)

## Layer 7 — Strict LLM re-classification (v2 "recipe test")

**Why:** Layer 6 was too lenient (97% keep). Output still contained items like `brew cold`, `2 2 2 x x`, `n rise shine`, `big brunch` — strings that aren't real searchable dishes. User's bar: *"things I could specifically search for recipes for so they have to be a real dish."*

**Action:**
- Re-split `unique_dishes_mains.csv` (276,431 rows from Layer 6) into 30 chunks (`chunks_v2/chunk_NN.csv`, ~9,215 rows each).
- Spawned 30 parallel LLM sub-agents with a STRICT recipe-test rubric: keep only if a chef could Google-search the exact name and find a real, recognizable dish. Decision rule flipped from Layer 6: **"when in doubt → DROP"**.
- Drop categories: `fragment` (gibberish, code-like tokens, bare protein/format alone), `drink`, `dessert`, `side`, `snack`, `sauce`, `bulk`, `deal`, `instruction`, `ingredient`, `marketing`.
- Outputs merged via `merge_classified_v2.py` → `unique_dishes_classified_v2.csv` (full audit) + `unique_dishes_mains_v2.csv` (keepers).

**Affected:**
- Total processed: 274,772 (small loss from prior pass empty/short rows)
- Kept: **195,949** (71.3%)
- Dropped: 78,823 (28.7%) — overwhelmingly `fragment` (74,925), then `drink` 919, `side` 690, `dessert` 644, `bulk` 500, `sauce` 327, `marketing` 292, `ingredient` 179, `instruction` 155, `snack` 141, `deal` 51

**Notes:**
- Layer 6 LLM kept ~97% (lenient prompt). Layer 7 with the strict prompt drops an additional ~28%.
- Each agent built a deterministic rule-based classifier in Python (token sets for drinks/desserts/sauces/bulk + recognized dish lexicons across cuisines + protein+format heuristics) rather than judging line-by-line; given 9k rows per chunk this was the practical approach but means borderline calls vary by classifier.
- Output is the new "real dish" canonical list: **195,949 unique main dishes**.

## Layer 8 — Drop pathological long/repeat-token fragments

**Why:** Layer 7 missed a class of garbage that the rule-based agents kept as "main": rows that are an alphabetized concatenation of an entire menu section. Triggering example caught by user: `ball beef bihon binagoongan canton chicken crispy crispy egg fillet fillet fillet fillet fish fish fish fish fish fried fried fried fried grilled halo halo house kwek kwek malabon miki pansit pansit pansit pansit pinoy pinoy pork rice rice rice rice roll sauce shrimp soup sour spicy spicy style style sweet tofu vegetable vegetables`. These rows have either way too many tokens or many repeated tokens — fingerprints of the alphabetical-sort step in the normalizer running over a single row that originally listed many items in one cell.

**Rule (drop if ANY hits):**
- token count > 12, OR
- any single token appears ≥ 3 times, OR
- ≥ 2 distinct tokens each appear ≥ 2 times

**Effect:**
- 195,949 → **195,551** (dropped 398, sum-of-counts = 663 menu rows)
- Sample drops: `cheese cheese mac mac n wisconsin`, `taco taco taco tora tora tora`, `chicken chicken chicken fried fried or steak`, plus alphabetized full-menu strings like the Filipino-pansit example above and various long pizza/Tuscan-supper compounds.

**Implemented in:** `drop_long_fragments.py`

**Outputs:**
- `unique_dishes_mains_v3.csv` — final post-classification dish list (195,551 rows)
- `dropped_long_fragments.csv` — full audit of what was dropped (with token-count + repeat stats)

## Layer 9 — Alias clustering (collapse misspellings & variants)

**Why:** the 195,551-row v3 list still contains many entries that are the same dish under different spellings (`margherita pizza` ↔ `margharita pizza` ↔ `marguerita pizza` ↔ `magherita pizza`), trivial plural/singular variants (`torta` ↔ `tortas`, `boneless wings` ↔ `boneless wing`), and minor token differences (`bonelesss wings`, `bonless wings`). User wants a single canonical name per dish + the full list of aliases that map to it.

**Goal output:** `dish_aliases.csv` — one row per (canonical, alias, count, cluster_id, method) — usable as a join key against `menus` to count true dish frequency, and as a lookup ("all the names for this dish").

**Approach (designed as 2-step hybrid; settled on Step A only after Step B failed):**

### Step A — bucketed fuzzy clustering (the only step that ships)

1. Sort all 195,551 names by frequency desc — most-common spelling wins canonical.
2. Bucket names by **token count** (1-token names only compete with other 1-token names, etc.). This is critical: it prevents `torta` from absorbing `carnitas torta`, and `boneless wings` from absorbing `10 boneless wings`. 12 buckets total, largest is the 3-token bucket with 71k names.
3. Within each bucket, greedy clustering with `rapidfuzz.fuzz.ratio` (Levenshtein-indel similarity on the alphabetically-sorted name string).
4. Threshold = **90**. Picked empirically: at 85, `chicken pad thai` over-merged with `chicken pizza thai` (4-char diff in 34 chars = ratio 88); at 90, only 1-2 char typos survive. Catches `magherita`/`margherita`, `margaeita`/`margherita`, `phad`/`pad` thai while rejecting different-dish near-matches.
5. Each name joins the highest-count canonical it scores ≥ 90 against, or becomes its own canonical.

**Implemented in:** `cluster_aliases.py`. Runs in ~2.5 min on the full 195k.

### Step B — semantic synonym merge (built, ran, REJECTED)

Idea was: embed each Step-A canonical with `BAAI/bge-small-en-v1.5` (sentence-transformer, 384-dim, MPS GPU), bucket by first-letter, merge cluster pairs whose canonicals are cosine ≥ 0.86 via union-find. Goal: catch synonyms like `hoagie` ↔ `sub`, `flapjacks` ↔ `pancakes`.

**Why it failed:** union-find chained transitively across many marginal pair merges, producing absurd super-clusters. Concrete example from the actual run: cluster 1 (canonical `boneless wings`) absorbed `bacon burger cheeseburger`, `burger cheeseburger`, `bean burrito cheesy rice`, `burrito fiesta veggie`, `bean burrito`, `buffalo chicken pizza`, etc. — every B-word that had > 0.86 cosine to *anything* in its chain. With 116k pair merges over 69k clusters, transitive linkage explodes. Result: 33,819 clusters, but most large ones were nonsensical mixes.

**Disabled** (`RUN_STEP_B = False` in script). True synonym merging needs a different approach: nearest-neighbor + token-overlap constraint, or HDBSCAN with very strict density, or pairwise LLM judging on top-K candidates. Deferred.

**Effect of Step A only:**
- 195,551 normalized names → **165,655 canonical dishes**
- 29,896 aliases collapsed (15.3% reduction)
- Cluster size distribution: p50 = 1, p90 = 2, p99 = 4, max = 26. **87% of clusters are singletons** (no alias) — the v3 input was already clean enough that most names are unique.
- Largest legit cluster: `marinara meatball sandwich sub` with 26 fuzzy aliases (mostly Subway/sandwich-shop spelling drift)

**Sample clusters (validation):**

| Canonical | Aliases (count) |
|---|---|
| `margherita pizza` | margarita, margharita, marguerita, magherita, margaeita, margerita, margeritha, marggeritta, margheritta + 2 more (11 typos all merged) |
| `boneless wings` | boneless wing, bonelesss wings, bonless wings (only true typos — varieties NOT merged) |
| `torta` | tortas (singular/plural only — different-protein tortas stay separate) |
| `chicken pad thai` | chicken phad thai, chicken pai thai, choice pad thai (close typos only — `chicken pizza thai` correctly stays separate) |
| `enchiladas` | enchilada, enchaladas, enchaladas, enchilladas (only spelling variants) |

**Outputs:**
- **`dish_aliases.csv`** — long-format table: `canonical_name, alias_name, alias_count, cluster_id, method` (195,551 rows). `method=self` for the canonical itself, `method=fuzzy` for an aliased name. This is the "dish key" — join to `menus` via the normalized name to look up true canonical.
- **`dish_canonical_summary.csv`** — one row per cluster: `cluster_id, canonical_name, n_aliases, total_count` (165,655 rows). Sorted by total_count desc.

**Implemented in:** `cluster_aliases.py`

**Iteration history (3 runs):**
1. Run 1 — `token_set_ratio ≥ 92`, no bucketing → 69k clusters but `torta` had 1,049 aliases including every protein variant (`carnitas torta`, `barbacoa torta`, etc.). `token_set_ratio` returns 100 for any token-subset relationship — fundamental mismatch. Step B also produced bogus mega-clusters.
2. Run 2 — same scorer, Step B disabled → still bad subset over-merging.
3. Run 3 — switched to `fuzz.ratio` + token-count bucketing, threshold 85 → mostly clean, but `chicken pad thai` over-merged with `chicken pizza thai`. Bumped to **90** → final.

## Layer 10 — Curated synonym dictionary

**Why:** Layer 9 catches typos and trivial variants but cannot merge true synonyms — `hoagie` ↔ `sub`, `prawn` ↔ `shrimp`, `aubergine` ↔ `eggplant`, `flapjacks` ↔ `pancakes`. These are different words with the same meaning, and embedding-based approaches (the abandoned Step B) over-merged. Curated dictionary is precise and safe.

**Approach:**
1. Build `synonyms.csv` — a hand-curated list of `(alias_token, canonical_token, group, notes)`. Each row says "rewrite this token to that one when it appears in a dish name." Plurals listed alongside singulars (`hoagies → subs`).
2. Run `validate_synonyms.py` → `synonym_validation.csv` to **see what each rule would actually merge** before applying. For each entry: count of affected clusters, top-5 example canonicals, top-5 example rewrites.
3. Mark each entry `APPLY` or `SKIP` in the `notes` column based on review. Reject entries that would over-merge (see "Rejected entries" below).
4. Run `apply_synonyms.py` to:
   - Read APPLY-only entries.
   - For each L9 cluster's canonical, rewrite tokens via the synonym map (then dedup + sort, matching Layer 3 normalization).
   - Group L9 clusters whose rewritten canonicals are equal — those merge.
   - Within each merge group, the new canonical = rewrite of the highest-count L9 cluster's canonical.

**APPLY entries (26 total, 13 distinct semantic merges):**

| Group | Tokens (alias → canonical) |
|---|---|
| sub_family | `hoagie/hoagies → sub/subs`, `grinder/grinders → sub/subs`, `poboy → sub` |
| pancake_family | `flapjack/flapjacks → pancake/pancakes`, `hotcake/hotcakes → pancake/pancakes` |
| shrimp | `prawn/prawns → shrimp`, `gamba/gambas → shrimp` |
| burger | `hamburger/hamburgers → burger/burgers` |
| pasta_spelling | `fettuccini/fettucini → fettuccine`, `linguini → linguine`, `spagetti → spaghetti` |
| sandwich_spelling | `paninis/panino → panini` |
| greek | `gyros → gyro` |
| eggplant | `aubergine → eggplant` |
| squid | `calamari → squid` |
| snail | `escargot → snail` |
| fries | `frites → fries` |

**REJECTED entries (validation showed false positives):**

| Rejected | Reason |
|---|---|
| `wedge → sub` | actually salad wedges (`buffalo salad wedge`, 135 ct) and potato wedges |
| `wedges → subs` | potato wedges, french-toast wedges |
| `po → sub` | `ma po tofu` (307 ct, Chinese mapo tofu — completely different dish) |
| `boy → sub` | only meaningful in `po-boy` context; standalone token is dangerous |
| `hero → sub` | mixed false positives: `gyro hero pita sandwich`, `hero hometown pizza`, `crispy heroes wings` (the L9 canonical `firehouse hero sub` is already a sub) |
| `heroes → subs` | `heroes pizza`, `calzone heroes`, `crispy heroes wings` |
| `cheeseburger → burger` | cheeseburger is a *type* of burger, not a synonym — keeping varieties distinct preserves info |
| `griddlecake → pancake` | 0 affected clusters in the data |

**Effect:**
- L9 clusters → L10 clusters: **165,655 → 164,823** (832 collapsed, ~0.5%)
- Of 164,823 final clusters, 721 are merge-groups that combined ≥2 L9 clusters
- Many more canonicals were *renamed* without merging (e.g., a cluster whose canonical was `prawn teriyaki` became `shrimp teriyaki` even when no separate `shrimp teriyaki` cluster existed to merge with)

**Sample merges (validated):**

| Final canonical | Merged in (top hits) |
|---|---|
| `italian sub` | hoagie italian sub (42), hoagie italian (12), hoagies italian sub (5), grinder italian (1) |
| `pancakes` | hotcakes (333), pancake (91), flapjacks (4) |
| `shrimp teriyaki` | prawn teriyaki (73), shrimps teriyaki (2), shrimp tereyaki (1) |
| `burger` | hamburger (461) and other hamburger variants |
| `broccoli shrimp` | broccoli prawns (38) |

**Sanity checks (rejected entries stayed separate):**
- `ma po tofu` (282 ct) still its own cluster — `po → sub` was correctly rejected
- `buffalo salad wedge` (135 ct) still its own cluster — `wedge → sub` rejected
- `cheeseburger` (706 ct) still distinct from `burger` — `cheeseburger → burger` rejected

**Outputs:**
- `synonyms.csv` — the manual dictionary (mark `APPLY` or `SKIP` in `notes`)
- `validate_synonyms.py` → `synonym_validation.csv` — per-entry impact report
- `apply_synonyms.py` → final merge
- `dish_aliases_v2.csv` — **final alias key (195,551 rows)**: `canonical_name, alias_name, alias_count, cluster_id, method` where `method ∈ {self, fuzzy, synonym}`
- `dish_canonical_summary_v2.csv` — **final canonical list (164,823 rows)**: `cluster_id, canonical_name, n_aliases, total_count`
- `synonym_merges.csv` — audit of every Layer-10 merge: which L9 clusters got combined and what triggered it

## Layer 11 — Bare ingredients + redundant number variants

**Why:** the post-Layer-10 list still contained two classes of non-recipe entries:
- **Bare ingredients** that aren't a dish on their own (`red snapper`, `catfish`, `brisket`, `ribeye steak`, `prime rib` — these are "what protein you cooked with," not "the dish itself").
- **Redundant number variants** where the same dish appears with a count/size prefix (`12 cheese pizza` ≡ `cheese pizza`, `8pc chicken nuggets` ≡ `chicken nuggets`, `10 boneless wings` ≡ `boneless wings`).

User's bar (consistent across the pipeline): "things I could specifically search for recipes for so they have to be a real dish."

### Layer 11A — heuristic flagger + auto-apply (1,612 drops)

**Implemented in:** `flag_ingredients_and_numbers.py` → `ingredients_and_numbers_review.csv`, then `apply_ingredients_and_numbers.py` for the confident drops.

**Three rule families:**
1. **Bare ingredients** — curated lists of single-token (`catfish`, `brisket`, `tilapia`, `mackerel`, `grouper`, `shrimp`, `chickpeas`) and 2-token compounds (`red snapper`, `mahi mahi`, `ribeye steak`, `filet mignon`, `prime rib`, `flank steak`, `atlantic salmon`, etc.) that are pure ingredients/cuts. Single-token check is gated by a `KEEP_SINGLE_TOKENS` allow-list of well-known single-word dishes (`enchiladas`, `nachos`, `mcnuggets`, `paella`, `pho`, `biryani`, `lasagna`, etc.) so that real dishes spelled in one word don't get mistakenly dropped.
2. **Redundant number variants** — strip every digit token, `Npc`/`Npcs`, `pc`/`pcs`/`piece`/`pieces`, `inch`/`in`/`inches` from the canonical, re-sort the remaining tokens alphabetically (matching Layer 3 normalization), and check if the result is itself a canonical. If yes → `redundant_with: <result>`.
3. **By-prefix fragments** — names starting with `by ` (`by chicken piece`, `by pizza slice`, `by pork pound pulled`) are leftover bulk-pricing copy ("by the pound"). Always drop.

**Stats (auto-applied 1,612 drops):**
- redundant_with: 1,400 (e.g. `12 cheese pizza` → `cheese pizza`, `8pc chicken meal nuggets` → `chicken meal nuggets`, `5 layer beefy burrito` is KEPT — Layer 11B handled the trickier numbers)
- fragment_after_number_strip: 130
- by_prefix_fragment: 64
- bare_ingredient_2tok: 11 (`red snapper`, `ribeye steak`, `prime rib`, etc.)
- bare_ingredient_1tok: 7 (`catfish`, `brisket`, `tilapia`, `mackerel`, `grouper`, `shrimp`, `chickpeas`)

**Effect:** 164,823 → 163,211 (1,612 dropped, 9,459 menu rows worth)

**Outputs:**
- `ingredients_and_numbers_review.csv` — full per-row decision (`drop` / `review` / `keep`) with reasoning
- `dropped_ingredients_and_numbers.csv` — audit of the 1,612 confident drops
- `dish_aliases_v3.csv`, `dish_canonical_summary_v3.csv` — post-11A files

### Layer 11B — LLM strict-pass on the digit-with-no-match review pile (10,204 drops)

After 11A, **10,779 names remained flagged for review** because they contained a digit but stripping numbers didn't land on an existing canonical (so the heuristic couldn't decide). Sample: `12pc carte la nuggets` (alphabetized — original was probably "Nuggets a la Carte 12pc"), `8 chicken lovers meal pc sides` (Popeyes meal), `3 n piece strips whatachick whatameal` (Whataburger menu code), `chicken 65` (real Indian dish), `7 layer dip` (real dish).

**Approach (same playbook as Layer 7):**
- Split the 10,779 rows into 3 chunks of 3,593 each, sorted by count desc so high-impact items are reviewed first.
- Spawn 3 parallel LLM sub-agents with a strict rubric: "Could a chef Google this exact name and find a real recognizable dish?" — `keep` only if yes; `drop` with a reason (`redundant`, `fragment`, `bulk`, `marketing`, `ingredient`) otherwise. "When in doubt → drop."
- Each agent built a per-chunk Python rule classifier (curated keep-phrases like `chicken 65`, `7 layer`, `5 spice`, `3/4/5/6 cheese`, `5 layer beefy burrito`, Italian `formaggi N`; menu-code detection like `c1`/`b12`/`p38`; bulk-pack detection; size-prefix detection).
- Merge outputs and apply via `merge_and_apply_review.py`.

**Stats (10,779 reviewed → 10,204 dropped):**
| Verdict | Count |
|---|---|
| keep / main | 575 |
| drop / fragment | 7,358 (mostly alphabetized menu codes from chains: `b3`, `c95`, `h12`, `pnct4`, `vs8` etc.) |
| drop / redundant | 2,649 (all the `Npc X` and `N inch X` patterns the heuristic missed because of token re-sorting) |
| drop / marketing | 108 (`whole30`, `lunch special`, hours/calorie strings) |
| drop / bulk | 89 (`8 chicken lovers meal`, `family 12 pack`, catering quart sizes) |

**Effect:** 163,211 → **153,007** (10,204 dropped, 27,848 menu rows worth).

**Notable kept items (the agents correctly identified intrinsic-number dishes):**
- `chicken 65` and variants (Indian dish — the 65 is part of the name)
- `7 layer dip`
- `3 cheese ravioli`, `4 cheese pizza`, `5 cheese pasta`, `6 cheese stromboli`
- `5 spice chicken`
- `5 layer beefy burrito` (Taco Bell named item)

**Outputs:**
- `chunks_review/` and `chunks_review_classified/` — per-chunk inputs/outputs
- `review_classified_merged.csv` — full audit of all 10,779 verdicts
- `dropped_review.csv` — sorted list of the 10,204 drops
- `dish_aliases_v4.csv` — **final alias key (179,738 rows post-Layer-11)**
- `dish_canonical_summary_v4.csv` — **final canonical dish list (153,007 rows post-Layer-11)**

**Implemented in:** `split_review_for_agents.py` (chunker) → 3 parallel `Agent` calls → `merge_and_apply_review.py` (merger + applicator)

## Layer 12 — Token-based side/snack/combo/à-la-carte drop

**Why:** the post-Layer-11 list still contained section-indicator items that survived earlier passes — `plain rice` (side), `snack taco` (snack), `chicken combo` (meal deal), `caesar salad side`, `cold combo cut sandwich sub` (Subway combo), `carte la shrimp` (à-la-carte item, alphabetized).

**Approach:** token-level drop. If a canonical contains any token from this set, drop the cluster:

```
snack, snacks, side, sides,
appetizer, appetizers, starter, starters,
topping, toppings, garnish, garnishes, condiment, condiments,
combo, combos,
carte    (alphabetized "à la carte" → "carte ... la")
```

**Tokens deliberately NOT in the drop set (would over-merge):**
- `sauce`, `sauces` — many Chinese dishes name themselves by the sauce (`chicken garlic sauce`, `beef oyster sauce`, `eggplant garlic sauce` — 2,824 hits, mostly real dishes)
- `dip`, `dips` — dominated by `French Dip` sandwiches (`dip french sandwich`, `classic dip french swiss`), which are real menu items
- `plain` — mixed (real `plain naan`, `plain dosa` vs side `plain rice`)
- `add`, `extra`, `no`, `w` — too many legitimate uses (`extra cheese pizza`, `bacon w eggs`)

**Stats (3,763 clusters dropped):**

| Trigger token | Count |
|---|---|
| combo | 2,900 |
| side | 473 |
| carte | 140 |
| sides | 66 |
| topping | 63 |
| toppings | 30 |
| appetizer | 40 |
| snack | 24 |
| starter | 18 |
| appetizers | 3 |
| garnish | 2 |
| condiments | 2 |
| snacks | 2 |

**Effect:** 153,007 → **149,244 canonical dishes** (3,763 clusters, 28,008 menu rows).

**Implemented in:** `flag_sides_combos.py`

**Outputs:**
- `dropped_sides_combos.csv` — audit of every dropped cluster + trigger token
- `dish_aliases_v5.csv` — **final alias key (175,455 rows post-Layer-12)**
- `dish_canonical_summary_v5.csv` — **final canonical dish list (149,244 rows post-Layer-12)**

## Layer 13 — Strip floating single-letter tokens

**Why:** 8,982 canonicals contained a floating single-letter token (a 1-character token surrounded by spaces). These are parsing artifacts from upstream alphabetization + apostrophe/punctuation handling:

| Source pattern | Example canonical | Real dish |
|---|---|---|
| Apostrophe-s split | `burger dave s` | Dave's Burger |
| Apostrophe-s split | `chicken general s tso` | General Tso's Chicken |
| Apostrophe-n split | `beef cheddar n` | Beef 'n Cheddar |
| Acronym split (Subway B.M.T.) | `b footlong italian m pro sandwich t` | Footlong Italian B.M.T. |
| Acronym split (BLT) | `b l t wrap` | BLT Wrap |
| `w/` leftover | `bacon breakfast platter w` | Breakfast Platter w/ Bacon |
| Possessive in brand | `mike philly s sub` | Mike's Philly Sub |

**Approach:** for each canonical with one or more single-letter tokens, strip them and check the cleaned form:

1. **Cleaned form == an existing canonical** → MERGE this cluster into it (the bigger one wins). E.g. `b italian m sandwich sub t` (1,219 ct) merged into `italian sandwich sub` (26,270 ct).
2. **Cleaned form has ≥ 2 tokens but no match** → RENAME the canonical to the cleaner form. E.g. `b footlong italian m pro sandwich t` → `footlong italian pro sandwich`. Cluster keeps its alias rows; the noisy label becomes a tidier one.
3. **Cleaned form has < 2 tokens** → DROP (residue too thin to be a real dish on its own).

**Stats (8,982 cleaned):**

| Action | Count |
|---|---|
| rename | 7,919 |
| merge  | 959 |
| drop   | 104 |

**Effect:** 149,244 → **148,181 canonical dishes** (1,063 net reduction, all from merges; renames don't change the cluster count). Zero canonicals with single-letter tokens remain.

**Implemented in:** `clean_single_letters.py`

**Outputs:**
- `single_letter_changes.csv` — full audit (every cluster, action, cleaned form)
- `dish_aliases_v6.csv` — **final alias key (175,167 rows post-Layer-13)**
- `dish_canonical_summary_v6.csv` — **final canonical dish list (148,181 rows post-Layer-13)**

After Layer 13, `build_dish_index.py` was re-run against `dish_aliases_v6.csv` so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the cleaned canonicals (1,167,831 rows, 43,183 restaurants, **138,241 distinct canonical dishes** appearing in actual menu data, 2,688 zip codes).

## Layer 14 — LLM-judged long-tail merges (the redone "Step B")

**Why:** the Layer-13 list still had a heavy long tail — 91,518 singletons (61.8% of clusters but only 7.6% of menu instances). Many singletons were the same dish as a frequent canonical under a slightly different name that fuzz-ratio-by-token-count couldn't catch (different token counts, different word choices). Examples: `nigiri yellowtail` ≡ `nigiri sashimi yellowtail`, `mein vegetable` ≡ `lo mein vegetable`, `back ribs` ≡ `baby back ribs`. This is exactly the synonym-merge problem Layer 9's "Step B" tried to solve and failed at (over-merging via embedding+union-find chaining).

This time the redesign worked: **token-overlap candidate generation + LLM pairwise judging** with no chaining.

### Stage 1 — token-overlap candidate generation

**Implemented in:** `find_merge_candidates.py`. Inverted-token index over the 21,277 clusters with count ≥ 5 (the "merge target pool"). For each singleton with 2–6 tokens, look up candidate targets sharing ≥ 60% of its tokens, with target_token_count ≤ 2× singleton_token_count (prevents mismatched-length merges). Keep top-3 candidates per singleton, sorted by overlap_ratio desc, target_count desc.

Output: `merge_candidates.csv` — **128,388 candidate pairs** from 51,177 singletons.

### Stage 2 — LLM pairwise judging via OpenRouter

**Implemented in:** `judge_merge_candidates.py`. Async batched calls to OpenRouter:
- **Model:** `google/gemini-2.0-flash-001` (very fast, very cheap, plenty smart for binary classification)
- **Batch size:** 20 pairs per request
- **Concurrency:** 50 in-flight requests via `asyncio.Semaphore` + `httpx.AsyncClient`
- **Prompt:** food-expert classifier with strict rule "if one name adds a key topping/protein/sauce/style that distinguishes the dish, they are DIFFERENT"
- **Format:** model returns one line per pair: `N. YES|NO brief reason`
- **Resume support:** keyed by (singleton_cid, target_cid) so reruns skip already-judged pairs

**Throughput:** all 128,388 pairs judged in **3 min 19 sec** at ~660 pairs/sec sustained. Cost: ~$0.60 total (gemini-flash is cheap).

Output: `candidate_judgments.csv` — every pair with verdict and reason.

**Final tallies:**
| Verdict | Count | Notes |
|---|---|---|
| YES | 30,243 | merge candidates approved by LLM |
| NO  | 98,145 | rejected (~76% — most token-overlap candidates aren't true merges) |
| err | 0 | retried 532 PARSE_ERRORs in 8s second pass |

### Stage 3 — Apply merges

**Implemented in:** `apply_judged_merges.py`. For each singleton with ≥1 YES verdict, pick the highest-count YES target as merge destination. One-step merge only — no chaining (a singleton's target is not itself merged into anywhere even if the target is also a singleton in another row). Re-point the singleton's alias rows to the target cluster, rewrite canonical to target's canonical, mark `method='llm_merge'`.

**Effect:** 148,181 → **124,800 canonical dishes** (23,381 unique singletons absorbed). Singletons collapsed: 91,518 → 68,137 (25.5% drop). The remaining singletons are mostly truly unique long-tail items that no high-count cluster matches.

**Sample merges (validated):**

| Singleton | Absorbed into |
|---|---|
| `nigiri yellowtail` | `nigiri sashimi yellowtail` |
| `mein vegetable` | `lo mein vegetable` |
| `back ribs` | `baby back ribs` |
| `cheeseburger impossible` | `burger cheeseburger impossible` |
| `kee mao pasta pud udon` | `kee mao pad pasta` |
| `bowl don gyu rice` | `bowl don gyu` (rice implied) |
| `bbq chopped sub` | `bbq chopped sandwich` |
| `chimichanga classic` | `burrito chimichanga classic` |
| `beef general` | `beef general tso` |
| `cavatappi pesto` | `cavatappi pasta pesto` |

**Why this approach worked where Layer 9 Step B failed:**
- **Token-overlap pre-filter** keeps candidates lexically related (no `boneless wings` ↔ `bacon burger cheeseburger` from cosine-only search)
- **LLM judges each pair independently** — no union-find transitivity, no chaining
- **One-step merges** — a target absorbs singletons but doesn't itself merge further in this pass
- **Strict prompt** — "if one adds a distinguishing topping/protein/style, they are DIFFERENT" caught most false positives (76% NO rate)

**Outputs:**
- `find_merge_candidates.py` / `merge_candidates.csv` — 128,388 token-overlap candidate pairs
- `judge_merge_candidates.py` / `candidate_judgments.csv` — every pair with YES/NO + reason
- `apply_judged_merges.py` / `llm_merges_applied.csv` — audit of 23,381 applied merges
- `dish_aliases_v7.csv` — **final alias key (175,340 rows post-Layer-14)**
- `dish_canonical_summary_v7.csv` — **final canonical dish list (124,800 rows post-Layer-14)**

After Layer 14, `build_dish_index.py` was re-run against `dish_aliases_v7.csv` so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the further-merged canonicals (1,167,831 rows, 43,183 restaurants, **116,918 distinct canonical dishes** appearing in actual menu data, 2,688 zip codes).

## Layer 15 — Strip Subway/chain marketing tokens (`footlong`, `pro`)

**Why:** post-Layer-14 review surfaced ~120 canonicals containing chain-specific marketing tokens that don't describe the food itself:

- **`footlong`** — 115 canonicals. Subway's pure size descriptor (12-inch sandwich); the same sandwich also appears without `footlong`. Examples: `footlong italian pro sandwich` ≡ `italian pro sandwich`; `footlong meatball sandwich` ≡ `meatball sandwich`.
- **`pro`** — 30 canonicals. Subway's "Pro" double-meat upsell. Same dish under it.

These over-fragment the canonical list because the same recipe lives under multiple `<token-set with footlong>` ↔ `<token-set without footlong>` clusters that fuzz/LLM passes didn't merge (the missing/extra token is exactly 1, but it's a meaningful-looking word so the LLM rule "extra distinguishing word = DIFFERENT" was being applied even when the extra word is just packaging).

**Approach (same shape as Layer 13's single-letter cleanup):** for each canonical containing a strip-token, remove the strip-tokens, re-sort. Then:

1. **Stripped form == an existing canonical** → MERGE this cluster into it.
2. **Stripped form has ≥1 token but doesn't match an existing canonical** → RENAME this cluster's canonical to the cleaner form.
3. **Stripped form is empty** → DROP (none observed in this run).

**Tokens deliberately NOT stripped:**
- `style` — used in legit dish-naming contexts (`street style taco`, `kosher style`, `home style bean curd`, `chicago stuffed style pizza`). Mixed signal — stripping would damage real dishes.

**Stats (121 canonicals hit):**
| Action | Count |
|---|---|
| merge | 88 |
| rename | 33 |
| drop | 0 |

**Effect:** 124,800 → **124,712 canonical dishes** (88 merges, 33 in-place renames).

**Implemented in:** `clean_chain_marketing.py`

**Outputs:**
- `chain_marketing_changes.csv` — full audit (cluster_id, old_canonical, total_count, action, cleaned, merged_into_cid)
- `dish_aliases_v8.csv` — alias key post-Layer-15 (175,340 rows)
- `dish_canonical_summary_v8.csv` — canonical list post-Layer-15 (124,712 dishes)

## Layer 16 — Drop canonicals containing `meal` / `dinner`

**Why:** post-Layer-14/15 review surfaced ~1,800 canonicals that describe meal-deal / combo-format packaging of an underlying dish, not a distinct dish. Examples:

| Canonical | Why it should drop |
|---|---|
| `chicken meal mixed` (1,420 ct) | chain meal-deal of chicken with mixed sides |
| `meal whopper` (1,191 ct) | same as `whopper` |
| `burger meal whopper` (832 ct) | same as `whopper` |
| `chicken dinner` (989 ct) | chicken served as dinner, not a distinct recipe |
| `dinner handcrafted tenders` (600 ct) | same as `handcrafted tenders` |
| `dinner roasted turkey` (245 ct) | same as `roasted turkey` |

These mirror the Layer-12 sides/combos pattern: the trigger token is itself a strong signal that the row is a meal-deal alias rather than a recipe.

**Approach:** drop any canonical containing any of `{meal, meals, dinner, dinners}`. Same mechanic as Layer 12 (token-based drop, no rename).

**Tokens deliberately NOT in the drop set:**
- `lunch`, `breakfast` — could carry distinct meaning (`breakfast burrito`, `breakfast sandwich`, `lunch sandwich`).
- `platter` — real format word (`seafood platter`, `kabob platter`, `mixed grill platter`).
- `special` — too mixed (real `today's special` items vs. genuine recipes); too risky without per-cluster LLM judgment.

**Stats (1,815 clusters dropped):**
| Trigger token | Count |
|---|---|
| dinner | 1,134 |
| meal | 669 |
| meals | 7 |
| dinners | 5 |

**Effect:** 124,712 → **122,897 canonical dishes**.

**Implemented in:** `drop_meal_dinner.py`

**Outputs:**
- `dropped_meal_dinner.csv` — audit of every dropped cluster + trigger token
- `dish_aliases_v9.csv` — alias key post-Layer-16 (172,949 rows)
- `dish_canonical_summary_v9.csv` — canonical list post-Layer-16 (122,897 dishes)

## Layer 17 — Second LLM long-tail merge pass

**Why:** Layers 15 and 16 changed which clusters are singletons and which are now "fat enough" to be merge targets. Many ex-singletons that just absorbed footlong/pro variants in L15 are now slightly bigger; conversely, dropping ~1,800 meal/dinner clusters in L16 didn't itself reshape the long tail but means the candidate-generation pool is freshly different. Re-running the Layer-14 pipeline against v9 picks up merges that didn't exist on the first pass.

### Stage 1 — token-overlap candidate generation (against v9)

**Implemented in:** `find_merge_candidates_v2.py`. Identical algorithm to v1 (see Layer 14), reading `dish_canonical_summary_v9.csv`. Same parameters: `MIN_TARGET_COUNT=5`, `MIN_TOKENS=2`, `MAX_TOKENS=6`, `MIN_OVERLAP_RATIO=0.60`, `TOP_K=3`.

Output: `merge_candidates_v2.csv` — **69,346 candidate pairs** (vs 128,388 in the v1 pass; smaller because Layer 14 already absorbed the easy merges).

### Stage 2 — LLM pairwise judging (Gemini Flash via OpenRouter)

**Implemented in:** `judge_merge_candidates_v2.py`. Same model / batch_size / concurrency / prompt / resume support as Layer 14's v1.

**Throughput:** all 69,346 pairs judged in **2 min 37 sec** at ~440 pairs/sec sustained.

Output: `candidate_judgments_v2.csv` — every pair with verdict and reason.

**Final tallies:**
| Verdict | Count | Notes |
|---|---|---|
| YES | 6,404 | merge candidates approved by LLM (~9.2% — much lower YES-rate than v1's 23.6% because v1 already absorbed the easy merges) |
| NO  | 62,937 | rejected (~90.8%) |
| err | 5 | left in place; tiny enough to skip retry |

### Stage 3 — Apply merges

**Implemented in:** `apply_judged_merges_v2.py`. Reads v9 + `candidate_judgments_v2.csv`, picks highest-count YES target per singleton, one-step merge (no chaining), marks `method='llm_merge_v2'`.

**Effect:** 122,897 → **117,154 canonical dishes** (5,743 unique singletons absorbed). 6,404 YES verdicts collapsed because some singletons had multiple YES targets and only the highest-count one wins.

**Outputs:**
- `find_merge_candidates_v2.py` / `merge_candidates_v2.csv` — 69,346 token-overlap candidate pairs
- `judge_merge_candidates_v2.py` / `candidate_judgments_v2.csv` — every pair with YES/NO + reason
- `apply_judged_merges_v2.py` / `llm_merges_applied_v2.csv` — audit of 5,743 applied merges
- `dish_aliases_v10.csv` — **final alias key (172,776 rows post-Layer-17)**
- `dish_canonical_summary_v10.csv` — **final canonical dish list (117,154 unique dishes)**

After Layer 17, `build_dish_index.py` was re-pointed at `dish_aliases_v10.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the further-merged canonicals (1,129,862 rows, 42,560 restaurants, 109,809 distinct canonical dishes appearing in actual menu data, 2,678 zip codes).

## Layer 18 — sub↔sandwich relaxed LLM pass

**Why:** post-Layer-17 review of the top-100 canonicals showed many false-negatives where the strict L14/L17 LLM prompt ("any extra distinguishing word = DIFFERENT") rejected pairs that genuinely are the same dish under a different format word. Subway calls them `subs`, every other shop calls the same item a `sandwich`. Examples that survived as separate clusters:

| Cluster A | Cluster B | Same dish? |
|---|---|---|
| `italian sandwich sub` (2,550) | `italian sandwich` (2,448) | yes |
| `marinara meatball sandwich sub` (2,485) | `marinara meatball sandwich` (2,307) | yes |
| `cali fresh sandwich steak sub` (2,351) | `cali fresh sandwich steak` (2,307) | yes |
| `buffalo chicken sandwich sub` (2,282) | `buffalo chicken sandwich` (2,895) | yes |
| `blt` (622) | `blt sandwich` | yes |
| `italian sub` (533) | `italian sandwich sub` (2,550) | yes |

These pass-throughs were specifically caused by the strict prompt instruction in L14/L17 — fixing them requires a separate pass with a *relaxed* prompt, run only on the narrow case where pairs differ ONLY by sub/sandwich tokens.

### Stage 1 — skeleton-equal candidate generation

**Implemented in:** `find_sub_sandwich_pairs.py`. For each canonical, compute its "skeleton" = sorted tokens with all of `{sub, subs, sandwich, sandwiches}` stripped. Group canonicals by skeleton; any group with ≥2 distinct canonicals (where at least one member has a sub/sandwich token) yields candidate pairs (lower-count → higher-count target).

Output: `sub_sandwich_candidates.csv` — **2,411 candidate pairs** from 2,051 skeleton groups.

### Stage 2 — relaxed LLM judging

**Implemented in:** `judge_sub_sandwich_pairs.py`. Same OpenRouter / Gemini Flash machinery as L14/L17 but with a *relaxed* prompt:

> "Each pair below differs ONLY by the inclusion or exclusion of a format word ('sub' / 'sandwich'). These are usually the SAME dish — Subway calls them subs, other shops call the same item a sandwich. Default to SAME unless one of the names is clearly a different food (e.g. open-faced vs roll, ciabatta vs sub roll, wrap vs sandwich, pizza vs sandwich)."

**Throughput:** all 2,411 pairs judged in **4 seconds** at this scale.

**Final tallies:**
| Verdict | Count |
|---|---|
| YES | 1,806 (74.9%) |
| NO  | 605 (25.1%) — model correctly held the line on cross-format edge cases |
| err | 0 |

**Sample NO verdicts** (LLM correctly refused these):
| Pair | LLM reason |
|---|---|
| `burger` vs `burger sandwich` | "burger is not always a sandwich" |
| `cheese quesadilla` vs `cheese quesadilla sandwich` | "quesadilla is not a sandwich" |
| `bacon chicken ranch` vs `bacon chicken ranch sandwich sub` | "missing format word" — correctly identified as the bare-protein form |

### Stage 3 — Apply merges

**Implemented in:** `apply_sub_sandwich_merges.py`. Same applicator pattern as L14/L17.

**Effect:** 117,154 → **115,348 canonical dishes** (1,806 unique singletons absorbed).

**Sample merges (variations now collapsed under a single canonical):**

| Final canonical | Absorbed (count) |
|---|---|
| `baja jack sandwich steak sub` | `baja jack sandwich steak` (1,172) |
| `bacon baja chicken sandwich` | `bacon baja chicken sandwich sub` (1,171) |
| `cali fresh sandwich steak sub` | `cali fresh sandwich steak` (1,160) |
| `all american club sandwich sub` | `all american club sandwich` (1,158) |
| `buffalo chicken sandwich` | `buffalo chicken sandwich sub` (1,134) |
| `club sandwich sub subway` | `club sandwich subway` (1,129) |
| `meat mozza sandwich sub` | `meat mozza sandwich` (1,086) |
| `chicken grilled sandwich` | `chicken grilled sandwich sub` (729) |
| `italiano sandwich sub turkey` | `italiano sandwich turkey` (706) |
| `blt sandwich` | `blt` (622), `blt sub` (454) |
| `cheese sandwich steak sub` | `cheese steak sub` (565) |
| `italian sandwich sub` | `italian sub` (533) |
| `club sub` | `club sandwich` (459) |
| `sub veggie` | `sandwich veggie` (440) |
| `cheeseburger` | `cheeseburger sandwich` (356) |
| `pork pulled sandwich` | `pork pulled` (318) |

The largest skeleton groups (4 members merged together): `club subway`, then several 3-way groups: `tuna`, `swiss turkey`, `steak`, `sicilian`, `reuben`, `philly steak`, `parmigiana sausage`.

**Outputs:**
- `find_sub_sandwich_pairs.py` / `sub_sandwich_candidates.csv` — 2,411 candidate pairs
- `judge_sub_sandwich_pairs.py` / `sub_sandwich_judgments.csv` — every pair with YES/NO + reason
- `apply_sub_sandwich_merges.py` / `sub_sandwich_merges_applied.csv` — audit of 1,806 applied merges
- `dish_aliases_v11.csv` — alias key post-Layer-18 (172,949 rows)
- `dish_canonical_summary_v11.csv` — canonical list post-Layer-18 (115,348 dishes)

## Layer 19 — Drop bare-format canonicals

**Why:** a small number of canonicals are nothing but format words — `sandwich sub`, `burger`, `salad taco`, `bowl burrito`. These pass earlier filters because they're real strings on real menus, but they tell us nothing about the actual recipe (a "Sub Sandwich" entry could be any of the 100+ subs that restaurant sells; a `burger` entry could be any burger). They both fail the recipe-search test and act as buckets that absorb specific dishes whose normalized form happens to collapse to the same key.

**Rule:** drop any canonical whose tokens are ENTIRELY a subset of `FORMAT_TOKENS`, with `len(tokens) ≤ 2` (the cap is defensive — we never observed a 3-token all-format canonical, but want to be conservative).

```
FORMAT_TOKENS = {
  sub, subs, sandwich, sandwiches,
  wrap, wraps, bowl, bowls,
  burger, burgers, pizza, pizzas,
  taco, tacos, burrito, burritos,
  salad, salads, soup, soups,
  plate, plates,
}
```

**Stats (28 clusters dropped, 8,492 menu rows worth):**

| Canonical | Count |
|---|---|
| `sandwich sub` | 2,319 |
| `burger` | 2,120 |
| `sandwich` | 1,127 |
| `plate taco` | 566 |
| `bowl burrito` | 503 |
| `salad taco` | 428 |
| `burger sandwich` | 391 |
| `salad sandwich` | 276 |
| `pizza taco` | 186 |
| `burrito plate` | 131 |
| `burrito taco` | 108 |
| `burger pizza` | 80 |
| `burger sub` | 57 |
| `burrito salad` | 45 |
| `burger taco` | 29 |
| `sub` | 26 |
| `taco wrap` | 26 |
| `salad sub` | 25 |
| (10 more, all <20) | — |

**Effect:** 115,348 → **115,320 canonical dishes**.

**Implemented in:** `drop_bare_format.py`

**Outputs:**
- `dropped_bare_format.csv` — full audit
- `dish_aliases_v12.csv` — alias key post-Layer-19 (172,772 rows)
- `dish_canonical_summary_v12.csv` — canonical list post-Layer-19 (115,320 dishes)

## Layer 20 — LLM keep/drop on over-tokenized singleton fragments

**Why:** the v12 long tail still contained 60,900 singletons (count=1). Most are real long-tail dishes (regional Mexican `arroz con jaiba papas rellena`, Filipino `chow mein shrimp subgum`, Ethiopian `chikina enat kitfo tibs ye`) but a sub-fraction are over-tokenized fragments — alphabetized lists of options/sides/sauces/descriptors that survived L7/L8/L11 because they didn't match the patterns those layers caught. Examples:

- `bacon eggs ham links or patties sausage sausage scrapple` — list of breakfast options, not a dish
- `bacon choice eggs ham homefries or sausage toast` — list of order options
- `aioli chipotle crunch glaze ranch shiso soy spicy` — list of sauces
- `bacon filet prime usda veg` — quality descriptors
- `american breakfast classic meat without` — order options

**Critical constraint:** preserve all real long-tail ethnic dishes. Strategy:
1. Heuristic flag — only consider singletons with **≥5 tokens** AND no token in a curated `DISH_NOUN_ALLOWLIST`. The allowlist contains ~180 recognizable dish formats, proteins, cuisine markers (`pizza, pasta, taco, burrito, mofongo, ceviche, biryani, ramen, pho, banh, naan, fajita, tikka, ...`) — anything mentioning one of these is almost certainly a real composite dish.
2. Real long-tail dishes are doubly-protected: most are 1-3 tokens (don't hit the ≥5 threshold), and 5+ token ethnic dishes nearly always include an allowlist noun.
3. Send only the still-flagged set to the LLM with a strict prompt that **explicitly tells the model to KEEP regional/ethnic dishes it doesn't personally recognize**.

### Stage 1 — heuristic flag

**Implemented in:** `flag_long_singletons.py`. Filters singletons through the ≥5-token + no-allowlist-noun gate.

**Stats:**
- 60,900 singletons in v12
- 12,169 have ≥5 tokens
- 807 of those lack any allowlist dish noun → flagged for LLM

### Stage 2 — strict LLM keep/drop with international-aware prompt

**Implemented in:** `judge_long_singletons.py`. Same OpenRouter / Gemini Flash machinery, batch=15, concurrency=30. Key prompt:

> "KEEP if it's a real dish from any cuisine — including regional / ethnic dishes you may not recognize personally (Mexican, Puerto Rican, Cuban, Ethiopian, Thai, Vietnamese, Filipino, etc.). When the tokens look like a coherent dish name in a non-English language (mofongo, ropa vieja, huitlacoche, ceviche, kitfo, etc.), KEEP. DROP if it's clearly a list of options / sides / sauces / ingredients / bulk-pricing / quality descriptors / run-on alphabetized junk where you cannot identify a single dish."

**Throughput:** all 807 judged in **3 seconds**.

**Final tallies:**
| Verdict | Count |
|---|---|
| KEEP | 407 (50.4%) |
| DROP | 400 (49.6%) |
| err  | 0 |

**Sample KEEP verdicts (real dishes correctly preserved):**

| Canonical (alphabetized) | LLM identified as |
|---|---|
| `de jalapeno pupusa queso rajas` | pupusa de queso |
| `con dorada entera mojarra papas` | mojarra dorada con papas |
| `chile en guisado jitomate pollo verde` | chile guisado |
| `bap bi bim dol seafood sot` | bibimbap |
| `de la nortena res seco` | seco norteño |
| `cai heo rau thit xao` | Vietnamese stir-fry |
| `de mariscos mixtos mofongo relleno` | stuffed mofongo |
| `ag arepa de ita sapo` | arepa de sapoara |
| `chin look pla tom yum` | tom yum pla (fish) |
| `apanado bisteck con tallarian verde` | bisteck apanado |
| `churrasco costillas de de res` | costillas de res |
| `br coli con crema de empanada pechuga queso` | pechuga empanada |

**Sample DROP verdicts (real fragments correctly dropped):**

| Canonical | LLM reason |
|---|---|
| `american breakfast classic meat without` | list of options |
| `bacon choice eggs ham homefries or sausage toast` | order options |
| `aioli chipotle crunch glaze ranch shiso soy spicy` | sauce list |
| `bacon filet prime usda veg` | quality descriptors |
| `etouffee it jazz seafood up` | incoherent |
| `lubricated magnum thin trojan ultra` | non-food (slipped through Layer 1) |
| `chopped garlic leaves pea sauteed` | ingredients only |
| `ed mushrooms peas saut snow spicy` | ingredient list |

### Stage 3 — Apply drops

**Implemented in:** `apply_long_singleton_drops.py`. Removes the 400 DROP-verdict clusters from the alias and summary tables.

**Effect:** 115,320 → **114,920 canonical dishes** (400 dropped).

**Outputs:**
- `flag_long_singletons.py` / `long_singleton_flags.csv` — 807 flagged singletons
- `judge_long_singletons.py` / `long_singleton_judgments.csv` — every flagged item with KEEP/DROP + reason
- `apply_long_singleton_drops.py` / `dropped_long_singletons.csv` — 400 dropped canonicals
- `dish_aliases_v13.csv` — **final alias key (172,372 rows post-Layer-20)**
- `dish_canonical_summary_v13.csv` — **final canonical dish list (114,920 unique dishes)**

After Layer 20, `build_dish_index.py` was re-pointed at `dish_aliases_v13.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the further-merged canonicals (**1,125,114 rows, 42,555 restaurants, 107,794 distinct canonical dishes** appearing in actual menu data, 2,678 zip codes).

> **Note on a reverted Layer 18B attempt:** an additional pass was attempted to re-judge the 605 L18 NO verdicts with a stricter "burger ≡ burger sandwich" prompt. The relaxed prompt unlocked 517 new YES merges, but on review the model overcorrected — many of the merged pairs were genuinely different dishes (e.g., `eggplant parmesan` is typically served on noodles while `eggplant parmesan sub` is on bread; `chicken grilled` plate ≠ `chicken grilled sandwich`; `chicken teriyaki` over rice ≠ `chicken teriyaki sandwich`). The "bare side intrinsically a sandwich" criterion (true for `blt`, `cheeseburger`, `philly cheesesteak`, `reuben`, `cubano`, `gyro`) was the right principle but the LLM applied the looser version. Layer 18B was reverted in full and v13 remained the canonical state at that point. If revisited, the right approach is a curated allowlist of intrinsically-sandwich dish names rather than a relaxed prompt.

## Layer 21 — Drop add-on canonicals

**Why:** the v13 list still had 47 canonicals whose first token (or some token) is `add` / `addon` — these are menu add-on instructions ("Add Chicken", "Add Avocado", "Add Boiled Egg") and order modifiers, not dishes. Same pattern as Layer 12 (sides/combos) and Layer 16 (meal/dinner): if the canonical contains a trigger token, drop the cluster.

**Approach:** drop any canonical containing any of `{add, adds, addon, addons}`.

**Tokens deliberately NOT in the drop set:**
- `added` — could appear in legit dish descriptors (rare but defensive).
- `extra` — too risky (`extra cheese pizza` may be intentional; not always an add-on).
- `plus` — appears in real dish names.

**Stats (47 clusters dropped, 191 menu rows worth):**

| Trigger token | Count |
|---|---|
| add | 46 |
| addon | 1 |

**Top dropped:**

| Canonical | Total count |
|---|---|
| `add chipotle fajita ribs` | 32 |
| `add fajita jalape sausage` | 32 |
| `add fajita shrimp skewer` | 31 |
| `add fingers` | 11 |
| `add ravioli` | 8 |
| `add my order to utensils` | 8 |
| `add boiled egg` | 8 |
| `add chicken` | 6 |
| `add ensalada onetaco steak` | 5 |
| `add chicken ensalada onetaco` | 5 |
| `add chicken tender` | 2 |
| `add avocado burrito` | 2 |
| `add cart plastic receive to to ware` | 2 |

**Effect:** 114,920 → **114,873 canonical dishes**.

**Implemented in:** `drop_addons.py`

**Outputs:**
- `dropped_addons.csv` — audit of every dropped cluster + trigger token
- `dish_aliases_v15.csv` — **final alias key (172,322 rows post-Layer-21)**
- `dish_canonical_summary_v15.csv` — **final canonical dish list (114,873 dishes)**

(v14 was reserved for the reverted L18B attempt; v15 is the next clean snapshot.)

After Layer 21, `build_dish_index.py` was re-pointed at `dish_aliases_v15.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the further-cleaned canonicals (1,124,957 rows, 42,555 restaurants, 107,749 distinct canonical dishes appearing in actual menu data, 2,678 zip codes).

## Layer 22 — Strip artifact doubled tokens

**Why:** v15 had **1,012 canonicals** containing a duplicated token. Investigation of the missing-canonical gap (see "Why does v13 have 114,920 vocab but only 107,794 appearing in menu_dishes?" earlier) showed that doubled-token aliases are **unreachable at index time** because `build_dish_index.py:lookup_key` dedups via `set()`. So aliases like `bacon cheese egg egg` (alias_count=1,029) couldn't be matched by any raw menu row — those 1,029 menu rows fell through to "no canonical match."

But not all doubled tokens are artifacts. Some are real dish-name repetitions:

| Doubled token | Example dish |
|---|---|
| `mahi mahi` | Hawaiian fish |
| `huli huli` | Hawaiian rotisserie chicken |
| `dan dan` | Sichuan noodles |
| `bang bang` | shrimp/chicken with bang bang sauce |
| `peri peri` | Nando's piri-piri chicken |
| `boom boom` | shrimp/chicken with boom boom sauce |
| `shabu shabu` | Japanese hot pot |
| `yum yum` | dishes/sauce naming convention |
| `lau lau` | Hawaiian dish |
| `chop chop` | salad / brand |
| `pon pon`, `woo woo`, `kko kko` | various |

**Approach** (same shape as Layer 13 single-letter cleanup and Layer 15 chain-marketing strip):

1. For each canonical with one or more duplicated tokens, partition the dups into preserved (in `PRESERVE_DOUBLED` allowlist) vs artifact.
2. If ALL dups are preserved → leave the canonical alone.
3. Otherwise dedup the artifact tokens (keep one copy) but leave preserved tokens doubled. Re-sort.
4. **MERGE** if the cleaned form matches an existing canonical. **RENAME** otherwise.

**Distribution of which token was being doubled** (top 10):
| Token | # canonicals doubled in | Action |
|---|---|---|
| `chicken` | 76 | strip (artifact) |
| `de` | 74 | strip (Spanish "de de" never legit) |
| `mahi` | 63 | preserve |
| `pork` | 58 | strip |
| `one` | 58 | strip (numbered-menu artifact) |
| `fried` | 30 | strip |
| `tacos` | 23 | strip |
| `beef` | 22 | strip |
| `enchiladas` | 15 | strip |
| `bang` | 14 | preserve |

**Stats (1,012 canonicals examined):**
| Outcome | Count |
|---|---|
| preserved doubles only — no change | 150 |
| cleaned (had at least one artifact dup) | 862 |
| → rename | 854 |
| → merge | 8 |
| → drop | 0 |

**Sample renames (variations now collapsed under a clean canonical):**

| Old canonical | Cleaned to | Stripped dup |
|---|---|---|
| `chick chick fil strips` | `chick fil strips` | `chick` |
| `apples bacon casserole fried hashbrown or or sausage` | `apples bacon casserole fried hashbrown or sausage` | `or` |
| `chicken chicken eggs fried` | `chicken eggs fried` | `chicken` |
| `chicken chicken fried lickin plate` | `chicken fried lickin plate` | `chicken` |
| `cbr cheese mac mac` | `cbr cheese mac` | `mac` |
| `crust epic pepperoni pepperoni pizza stuffed` | `crust epic pepperoni pizza stuffed` | `pepperoni` |
| `beef braised carne de deshebrada enchiladas enchiladas shredded` | `beef braised carne de deshebrada enchiladas shredded` | `enchiladas` |
| `bistec de steak tacos tacos` | `bistec de steak tacos` | `tacos` |
| `chicken de pollo tostadas tostadas` | `chicken de pollo tostadas` | `tostadas` |

**Sample merges (highest-impact):**

| Singleton | Merged into | Stripped dup |
|---|---|---|
| `bacon cheese egg egg` (1,029 ct) | `bacon cheese egg` (cluster 130352) | `egg` |
| `buffalo cheese chicken mac mac` (39 ct) | `buffalo cheese chicken mac` | `mac` |
| `chicken chicken gen tso` | `chicken gen tso` | `chicken` |
| `roll roll year` | `roll year` | `roll` |
| `fried rice rice` | `fried rice` | `rice` |
| `beef sate sate` | `beef sate` | `sate` |
| `pad th th` | `pad th` | `th` |

**Effect:** 114,873 → **114,865 canonical dishes** (8 net reduction from merges; 854 in-place renames don't change the cluster count).

The much bigger effect is at index-time: 1,849 previously-unreachable menu rows now successfully look up a canonical, and 756 additional canonicals now appear in `menu_dishes.csv`.

**Implemented in:** `clean_doubled_tokens.py`

**Outputs:**
- `doubled_token_changes.csv` — full audit (cluster_id, old_canonical, total_count, action, cleaned, merged_into_cid, stripped_dups, preserved_dups)
- `dish_aliases_v16.csv` — **final alias key (172,322 rows post-Layer-22)**
- `dish_canonical_summary_v16.csv` — **final canonical dish list (114,865 dishes)**

After Layer 22, `build_dish_index.py` was re-pointed at `dish_aliases_v16.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the cleaned canonicals (1,126,806 rows, 42,557 restaurants, 108,505 distinct canonical dishes appearing in actual menu data, 2,678 zip codes).

## Layer 23 — Targeted quesadilla cleanup (manual review)

**Why:** manual review of all 80+ canonicals containing `quesadilla`/`quesadillas` surfaced two clear patterns of duplicates beyond what earlier automated layers caught:

- **Spanish↔English / filler-word duplicates** that didn't trigger Layer 10's curated synonym dict (`pollo→chicken`, `queso→cheese`, `carne` missing in `asada`/`carne asada`, `al pastor` vs `pastor`, `vegetable`/`vegetarian`/`veggie`).
- **Plural→singular leakage** where Layer 4's format-folding singularization missed a few canonicals (`brisket quesadillas`, `bacon chicken quesadillas ranch`, etc.).

These would normally be handled by extending Layer 10's `synonyms.csv` (the `pollo→chicken` / `queso→cheese` rules were noted as "promising future entries" in the Layer 10 docs but not yet added). For this targeted pass, encoded as explicit `(source_cid, target_cid, reason)` tuples to avoid re-running the whole pipeline.

### A. Merges (10 source clusters → 5 destination clusters)

| Source canonical (count) | → Target canonical (count) | Reason |
|---|---|---|
| `de pollo quesadilla` (59) | `chicken quesadilla` (1,440) | Spanish→English: pollo = chicken |
| `pollo quesadilla` (35) | `chicken quesadilla` (1,440) | Spanish→English: pollo = chicken |
| `de quesadilla queso` (44) | `cheese quesadilla` (2,330) | Spanish→English: queso = cheese |
| `quesadilla queso` (34) | `cheese quesadilla` (2,330) | Spanish→English: queso = cheese |
| `cheese only quesadilla` (32) | `cheese quesadilla` (2,330) | filler word: 'only' is non-distinguishing |
| `quesadilla vegetable` (55) | `quesadilla veggie` (202) | synonym: vegetable = veggie |
| `quesadilla vegetarian` (98) | `quesadilla veggie` (202) | synonym: vegetarian = veggie (menu context) |
| `pastor quesadilla` (74) | `al pastor quesadilla` (114) | Spanish article: 'al' prefix optional |
| `asada quesadilla` (66) | `asada carne quesadilla` (73) | missing token: 'carne asada' = 'asada' |
| `bf chicken quesadilla` (84) | `buffalo chicken quesadilla` (26) | abbreviation: bf = buffalo |

### B. Renames (4 plural→singular, no merge target exists)

| Old canonical (count) | → Renamed to | Reason |
|---|---|---|
| `brisket quesadillas` (291) | `brisket quesadilla` | plural→singular |
| `bacon chicken quesadillas ranch` (196) | `bacon chicken quesadilla ranch` | plural→singular |
| `bacon beef quesadillas ranch` (181) | `bacon beef quesadilla ranch` | plural→singular |
| `chicken quesadillas smoked` (29) | `chicken quesadilla smoked` | plural→singular |

**Rename mechanic (small fix vs Layer 13/15):** the previous rename pattern overwrote the cluster's "self" alias_name with the new canonical, dropping the old form from the alias key. This caused some raw menu rows (whose normalizer output matches the OLD form) to lose their lookup target — a small index-time leak. Layer 23 fixes this by writing TWO alias rows on rename: a new `self` row with `alias_name = new_canonical` (count 0, just for the index) and a `rename_preserved` row with `alias_name = old_canonical_form` keeping the original alias_count. Both point at the same cluster_id. Net effect: zero index-time row loss from renames.

### Audit captures every absorbed alias variant

Per the user's standing instruction to track which language variations collapse into each new canonical, `quesadilla_changes.csv` records every row of every absorbed alias with its method and the merge reason. **All 73 alias rows from the 10 merge sources** are preserved in the new alias key under the destination canonical. Spot examples:

`chicken quesadilla` now also catches: `de pollo quesadilla`, `de pollo quesadillas`, `de pollo quesadillita`, `mole pollo quesadilla`, `dorados pollo quesadilla`, `de machete pollo quesadilla`, `de huarache pollo quesadilla`, `criollo de pollo quesadilla`, `de lechera pollo quesadilla`, `de enmoladas pollo quesadilla`, `de maiz pollo quesadilla`, `de harina pollo quesadilla`, `de pechuga pollo quesadilla`, `con de fajita pollo quesadilla`, `carne de mixtas pollo quesadilla`, `pollo quesadilla`, `pollo quesadillas`, `pollo q quesadilla`, `lalo quesadilla`. (19 variants total.)

`cheese quesadilla` now also catches: `de quesadilla queso`, `de quesadillas queso`, `dinner quesadilla queso`, `quesadilla queso smothered`, `de longaniza quesadilla`, `de lujo quesadilla`, `de pernil quesadilla`, `cochinita de quesadilla`, `cerdo de quesadilla`, `flameado quesadilla queso`, `arroz de quesadilla`, `de panela quesadilla`, `de quesadilla rajas`, `harina quesadilla queso`, `blanco de quesadilla queso`, `ma quesadilla queso`, `de plate quesadilla queso`, `bistec de quesadilla queso`, `chimi de queso`, `de luxe quesadilla`, `quesadilla queso`, `quesadillas queso`, `cheese only quesadilla`, `cheese corn quesadilla`, `cheese only quesadilla special`, `cheese only quesadilla s`. (26 variants total.)

`quesadilla veggie` now also catches: `quesadilla vegetable`, `quesadilla vegetables`, `quesadilla vegetarian`, `quesadilla vegetarians`, `quesadilla vegetariana`, etc.

**Effect:** 114,865 → **114,855 canonical dishes** (10 merges).

**Items deliberately NOT merged** (judgment calls user wanted preserved):
- `chicken grilled quesadilla` (104) ↔ `chicken quesadilla` (1,440) — kept separate. While quesadillas are grilled by default, "grilled chicken" can mean the chicken protein is grilled (vs fried), which is a meaningful distinction.
- `grilled quesadilla shrimp/veggie/steak` likewise kept distinct.

**Implemented in:** `clean_quesadillas.py`

**Outputs:**
- `quesadilla_changes.csv` — full audit (action, source_cid, source_canonical, source_count, target, reason, absorbed_alias, absorbed_alias_count, alias_method) — one row per absorbed alias variant, with the language/synonym reason captured on every row.
- `dish_aliases_v17.csv` — **final alias key (172,326 rows post-Layer-23)** — slightly larger than v16 because `rename_preserved` rows add 4 new alias entries.
- `dish_canonical_summary_v17.csv` — **final canonical dish list (114,855 dishes)**

After Layer 23, `build_dish_index.py` was re-pointed at `dish_aliases_v17.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the merged canonicals (1,126,806 rows, 42,557 restaurants, 108,494 distinct canonical dishes appearing in actual menu data, 2,678 zip codes).

## Layer 24 — Parallel-agent multi-category cleanup

**Why:** the quesadilla manual review (Layer 23) exposed a generalizable playbook (Spanish↔English, plural→singular, article omission, filler words, abbreviations) that applies to every food category, not just quesadillas. With 11 obvious target categories — tacos, burritos, enchiladas/tostadas/tortas/tamales/sopes, fajitas/empanadas/flautas/nachos, pizza, pasta, wings/tenders, Asian noodles (lo mein/chow mein/pad thai/pho/ramen/udon/soba), Indian (curry/biryani/tikka/tandoori/masala), salads, and sushi/rolls — the rational thing was to dispatch the same playbook to each category in parallel.

### Stage 1 — Parallel-agent proposal generation (read-only)

11 sub-agents launched concurrently, each owning one category, each reading `dish_canonical_summary_v17.csv` and producing a structured `proposals/category_<name>.csv` with columns: `action, source_cid, source_canonical, source_count, target_cid, target_canonical, target_count, new_canonical, reason, confidence`.

The playbook handed to each agent included:
- Spanish→English merges: `pollo`/`chicken`, `queso`/`cheese`, `carne`/`beef`, `frijoles`/`beans`, `arroz`/`rice`, `camarones`/`gambas`/`shrimp`, `pescado`/`fish`, `aguacate`/`avocado`, `huevo`/`egg`, `cebolla`/`onion`, `puerco`/`pork`, `gallina`/`chicken`, `lengua`/`tongue`.
- Italian↔English merges where appropriate: `parmigiana`/`parmesan`, `funghi`/`mushroom`, `melanzane`/`eggplant`.
- Vietnamese↔English: `ga`/`chicken`, `bo`/`beef`, `tom`/`shrimp`, `chay`/`vegetarian`.
- Thai romanization: `phad`/`pad`, `lad na`/`nah rad`, `woon sen`/`woonsen`.
- Hindi↔English **flagged for caution** since Hindi names are often dish identity (`murgh`/`chicken`, `aloo`/`potato`, `gosht`/`meat`).
- Plural→singular: any `xxx tacos`/`xxx burritos`/`xxx tamales` where the singular sibling exists or no sibling exists.
- Article/filler omission: `al pastor`/`pastor`, `de pollo`/`pollo`, `con queso`/`queso`, `cheese only`/`cheese`.
- Abbreviations: `bf`/`buffalo` (caught the warning that in tacos `bf` ≡ "breakfast" not "buffalo"), `bbq`/`barbeque`/`barbecue`, `philly`/`philadelphia`, `cali`/`california`.
- Synonym pairs: `vegetable`/`veggie`/`vegetarian`/`veg`, `meatlovers`/`meat lovers`.
- Spelling fixes: `smokey`/`smoky`, `peperoni`/`pepperoni`, `proscuitto`/`prosciutto`, `vindalu`/`vindaloo`, `tika`/`tikka`, `biriyani`/`briyani`/`biryani`, `ceasar`/`caesar`.

Each agent was instructed to flag ambiguous calls as `judgment` confidence rather than auto-merge. Things explicitly preserved across agents: different proteins, different cooking methods, different sauces (`buffalo` vs `honey mustard`, `verde` vs `roja`, `mole` vs `salsa`, `tonkotsu` vs `shoyu` vs `miso ramen`), different spice levels, different bone-in/boneless wings, different sushi fillings, different pasta shapes (`penne` vs `ziti` vs `tortellini`), different curry styles (`madras` vs `vindaloo` vs `korma`).

Total proposals across 11 agents: **3,847** (1,130 high-confidence, 2,418 medium, 3 judgment, plus 296 schema-deviation issues that the validator caught).

### Stage 2 — Aggregation + cycle-aware applicator

`aggregate_proposals.py` merged all 11 proposal CSVs into `proposals/aggregated_high.csv`, validating each proposal against v17:
- `source_cid` must exist in v17 vocab.
- `target_cid` (for merges) must exist and not equal source.
- No duplicate `source_cid` across proposals (one cluster can't be acted on twice).
- Confidence labels normalized to `high` / `medium` / `judgment`.

`apply_categories.py` then applied the high-confidence batch with smart cycle handling:

1. **Renames first.** If a rename's `new_canonical` matches an existing cluster's name, it's auto-promoted to a merge into that existing cluster (rename→merge collision).
2. **Then merges.** If a merge's source was already a rename-source, the merge is dropped (the rename takes precedence). If the merge's target is itself a rename-source, the merge gets redirected to the rename's destination.
3. **Self-merges and cycles** (e.g., A↔B where A merges to B AND B's rename target is A's canonical) are detected and resolved into a single direction.

**Stats from the apply step:**
- Direct merges processed: 766
- Rename-promoted merges: 164
- Merges redirected via prior rename: 15
- Cycle-skipped merges: 164 (these are the cases where merge direction was wrong-way; the rename in the opposite direction took precedence)
- Pure renames: 36

**Effect:** v17 (114,855) → **v18 (113,925) canonical dishes** (930 net merges, 36 in-place renames).

### Per-category absorption results

| Category | Clusters absorbed | Notable patterns |
|---|---|---|
| **Sushi/Roll** | 452 | The `X roll sushi` ≡ `X roll` redundancy where `X` is a named sushi roll (philadelphia, california, dragon, rainbow, alaska, caterpillar, spider, volcano, etc.). Plus `philly` ≡ `philadelphia`, `cali` ≡ `california`, `yellow tail` ≡ `yellowtail`, vegetable/veggie spring roll synonyms. Carve-out: `sashimi sushi` ≡ a combo platter, NOT redundant — kept separate. |
| **Asian noodles** | 289 | The `pasta` token is upstream noise — restaurants file noodle dishes under "Pasta" menu sections, producing parallel `chicken lo mein` / `chicken lo mein pasta` clusters. Plus Vietnamese `ga`→`chicken`, `chay`→`vegetarian`; Thai `phad`→`pad`, `woonsen`→`woon sen`. |
| **Tacos** | 71 | Heavy Spanish→English (pollo, pescado, camaron, aguacate, frijoles, papa, puerco, queso, huevo, jamon); heavy `de` filler drops; `pastor`/`al pastor` consolidation; lengua/tongue; 23 plural→singular renames. Carve-out: in tacos `bf` = "breakfast" (NOT "buffalo" as in quesadillas). |
| **Mexican misc** (enchilada/tostada/torta/tamale/sopes) | 55 | Spanish→English (pollo/queso/carne/jamon/camaron/pescado/bistec/lengua/papa/puerco), `de X` article drops, color-sauce English↔Spanish (`green`↔`verdes`, `red`↔`rojas`), style: `breaded`=`milanesa`, `swiss`=`suizas`. |
| **Burritos** | 21 | Spanish→English (pollo/queso/carne/frijoles/camaron/pescado), pastor/asada Spanish-article drops, `bf`/`buffalo` (matches quesadilla precedent), 2 plural→singular renames. |
| **Pizza** | 21 | `barbeque`/`barbecue`→`bbq` (5 pairs incl. 159→1,347 chicken pair); `lover`↔`lovers` plural/singular (7 pairs); `meatlovers`→`meat lovers` (3); typo fixes `margarita`→`margherita`, `peperoni`→`pepperoni`, `proscuitto`→`prosciutto`; `cheese only` filler. |
| **Pasta** | 17 | Italian↔English `parmigiana`≡`parmesan` (`chicken parmigiana pasta` 158→`chicken parmesan pasta` 346); Thai `phad`/`pad` romanization (12 merges); `mac`/`macaroni`; `veggie`/`vegetable`/`vegetarian` synonyms. |
| **Mexican small** (fajita/flauta/empanada/nachos) | 17 | Spanish→English (pollo/camaron/res), `de` filler drops, plural→singular for fajitas, `nachos supremos`→`nachos supreme`. |
| **Wings/Tenders** | 10 | `barbecue`/`barbeque`→`bbq`, `only` filler word (5 clusters), `smokey`→`smoky` spelling, singular→plural pair fixes. |
| **Indian** | 8 | Sanskrit/Hindi transliterations (`navaratna`/`navarathan`→`navratan`, `vindalu`→`vindaloo`, `tika`→`tikka`, `biriyani`/`avakaya`); 1 plural→singular. Most Hindi/English word pairs flagged for separate user review. |
| **Salads** | 5 | `vegetarian`→`veggie`, typo `ceasar`/`cesar`→`caesar`, Spanish→English (`de pollo`→`chicken`, `mariscos`→`seafood`, `ensalada`→`salad`). |

### Variation tracking

Per the standing instruction to track which language variations collapse into each new canonical, `category_changes.csv` records every absorbed alias under its destination canonical with the merge reason. Spot examples:

`chicken taco` (cluster 727) absorbs: `pollo taco`, `de pollo taco`, `de pollo tacos`, `pollo tacos`, `chicken tacos`, plus various LLM-merged Spanish-language menu names — visible in the audit alongside the language-bridge reason.

`pad thai` (cluster 924) absorbs: `pad pasta thai` (the menu-section "pasta" noise variant, 766 menu rows), `pasta phad thai` (Thai romanization variant, 62 rows), and others.

`al pastor taco` (cluster 25548) absorbs: `pastor taco` (article-omitted, 312 rows) plus its alias variants.

`bbq chicken pizza` (cluster 25480) absorbs: `barbeque chicken pizza` (159 rows), `barbecue chicken pizza` (12 rows).

`philadelphia roll` (cluster 855) absorbs: `philly roll` (113 rows) plus its alias variants.

`enchiladas verdes` (cluster 762) absorbs: `enchiladas green` (85 rows) — green↔verdes color-sauce same dish.

### Items deliberately held back

The 2,418 medium-confidence and 198 judgment-confidence proposals were NOT auto-applied. The biggest medium chunk is **2,424 asian_noodles standalone renames** that would strip the `pasta` noise token from canonicals where no clean-name sibling exists. These are flagged for separate user review — stripping `pasta` from a name like `xyz lo mein pasta` (where no `xyz lo mein` exists) creates a new canonical and may discard meaningful information about the menu section. Surfaced as `proposals/aggregated_medium.csv` for opt-in batch approval.

The 198 judgment items (Indian Hindi/English pairs, sushi `roll` overload distinctions like bread-rolls vs cinnamon-rolls vs sushi-rolls, ambiguous filler-word cases, `garden`/`house` salad disambiguation) are surfaced in `proposals/aggregated_judgment.csv` as informational only.

**Implemented in:**
- `aggregate_proposals.py` — validates and buckets the 11 per-category proposal CSVs.
- `apply_categories.py` — cycle-aware applicator; reads `aggregated_high.csv`, applies merges/renames with rename-first ordering, writes audit.

**Outputs:**
- `proposals/category_*.csv` (11 files) + `*.md` summaries — per-agent proposals.
- `proposals/aggregated_high.csv` — the 1,130 high-confidence batch that was applied.
- `proposals/aggregated_medium.csv` — 2,418 medium-confidence held for user review.
- `proposals/aggregated_judgment.csv` — 3 judgment-only informational rows.
- `proposals/aggregation_report.md` — per-category breakdown and validation issues.
- `category_changes.csv` — full audit of every absorbed alias with category, merge reason, and language note.
- `dish_aliases_v18.csv` — **final alias key (172,326 rows post-Layer-24)**.
- `dish_canonical_summary_v18.csv` — **final canonical dish list (113,925 dishes)**.

After Layer 24, `build_dish_index.py` was re-pointed at `dish_aliases_v18.csv` and re-run so `menu_dishes.csv` / `menu_dishes.sqlite` reflect the merged canonicals (**1,126,856 rows, 42,557 restaurants, 107,581 distinct canonical dishes** appearing in actual menu data, 2,678 zip codes).

## Known limitations / not-yet-handled

- "chicken sandwich" and "crispy chicken sandwich" are still distinct — pure string match, no semantic clustering
- Misspellings stay separate
- Generic single-word entries that survived the filler strip (e.g., `italian`, `boneless`) likely collapse multiple distinct dishes into one bucket — over-dedup
- Non-restaurant items might still slip through inside restaurants we kept (e.g., a deli that lists batteries)
- Layer 7 used 30 independent rule-based classifiers per chunk — borderline keep/drop calls aren't consistent across chunks
- Token-sort step in Layer 3 means word order is lost ("chicken pizza" and "pizza chicken" merge); usually fine but loses some name structure (e.g., "Mexican burger" vs "burger Mexican-style")
- Layer 9 only handles spelling variants. Layer 10 added a curated synonym dict for the most common true synonyms (sub/hoagie, prawn/shrimp, etc.); broader semantic merging (Step B in Layer 9) was attempted and rejected and is not yet redone.
- Layer 9 token-count bucketing means `boneless wings` and `wings` stay separate even though they're arguably the same dish — by design (preserves variety information)
- Layer 10 dictionary is small (~13 distinct semantic merges). Adding entries is cheap: edit `synonyms.csv`, run `validate_synonyms.py`, mark `APPLY/SKIP`, run `apply_synonyms.py`. Promising future entries: `frijoles refritos → refried beans`, `pollo → chicken` (when in Spanish-only contexts), `carne → beef` (similar caveat).
- Curated dict cannot catch arbitrary semantic equivalences ("gourmet pizza" ↔ "specialty pizza"); for that, a future Layer 11 with LLM pairwise judging on embedding nearest-neighbors is the recommended path (see Layer 9 "Step B" notes for what NOT to do).

## Files produced

| File | What it is |
|---|---|
| `clean_db.py` | C1–C4 cleaning pipeline (in-place db modifications) |
| `dedup.py` | Layer 1 + Layer 2 (filter + dish-name normalization) |
| `categories.py` | Dump unique restaurant category tags |
| `export_restaurants.py` | Export filtered restaurants list |
| `category_canonical_mapping.csv` | C4 mapping: raw_tag → canonical_tag |
| `clean_menu_categories.py` | C5 cleanup script for menus.category |
| `menu_category_canonical_mapping.csv` | C5 mapping: raw_category → canonical_category |
| `unique_categories.csv` | All unique restaurant category tags (post-C4: 365 tags) |
| `unique_categories_to_exclude.csv` | User-marked exclusion list (87 tags marked with x) |
| `restaurants_filtered.csv` | 45,109 restaurants kept after Layer 1 |
| `unique_dishes_restaurants_only.csv` | 389,701 deduped dishes after Layers 1+2 |
| `unique_dishes.csv` | 576,699 deduped dishes — Layer 2 ONLY (no restaurant filter); kept for comparison |
| `split_for_agents.py` / `merge_classified.py` | Layer 6 chunk + merge scripts |
| `merge_classified_v2.py` | Layer 7 (strict pass) merge script |
| `unique_dishes_mains.csv` | Layer 6 result (lenient LLM): 276,431 rows |
| `unique_dishes_classified_v2.csv` | Layer 7 full audit: verdict + reason for every dish |
| `unique_dishes_mains_v2.csv` | Layer 7 keep-only result: 195,949 rows |
| `drop_long_fragments.py` | Layer 8 mechanical fragment-drop script |
| `dropped_long_fragments.csv` | Layer 8 audit: 398 long/repeat-token rows removed |
| `unique_dishes_mains_v3.csv` | Layer 8 result — 195,551 normalized dish names |
| `cluster_aliases.py` | Layer 9 alias-clustering script (bucketed fuzz.ratio) |
| `dish_aliases.csv` | Layer 9 alias key — 195,551 rows: canonical_name, alias_name, alias_count, cluster_id, method |
| `dish_canonical_summary.csv` | Layer 9 canonical list — 165,655 dishes |
| `synonyms.csv` | Layer 10 hand-curated synonym dictionary (mark APPLY/SKIP in notes column) |
| `validate_synonyms.py` / `synonym_validation.csv` | Layer 10 per-entry impact preview before apply |
| `apply_synonyms.py` | Layer 10 merge script |
| `synonym_merges.csv` | Layer 10 audit — which L9 clusters got combined and the triggering rewrite |
| `dish_aliases_v2.csv` | Layer 10 alias key — 195,551 rows |
| `dish_canonical_summary_v2.csv` | Layer 10 canonical list — 164,823 dishes |
| `flag_ingredients_and_numbers.py` | Layer 11A heuristic flagger (bare ingredients + redundant numbers) |
| `ingredients_and_numbers_review.csv` | Layer 11A per-row decisions (drop/review/keep) |
| `apply_ingredients_and_numbers.py` | Layer 11A applicator |
| `dropped_ingredients_and_numbers.csv` | Layer 11A audit — 1,612 dropped clusters |
| `dish_aliases_v3.csv` / `dish_canonical_summary_v3.csv` | Layer 11A result — 163,211 dishes |
| `split_review_for_agents.py` | Layer 11B chunker for the 10,779 review pile |
| `chunks_review/`, `chunks_review_classified/` | Layer 11B per-chunk LLM inputs/outputs |
| `merge_and_apply_review.py` | Layer 11B merger + applicator |
| `review_classified_merged.csv` | Layer 11B full audit (10,779 verdicts) |
| `dropped_review.csv` | Layer 11B audit — 10,204 dropped clusters |
| `dish_aliases_v4.csv` | Layer 11 alias key — 179,738 rows |
| `dish_canonical_summary_v4.csv` | Layer 11 canonical list — 153,007 dishes |
| `flag_sides_combos.py` | Layer 12 token-based side/combo flagger + applicator |
| `dropped_sides_combos.csv` | Layer 12 audit — 3,763 dropped clusters with trigger tokens |
| `dish_aliases_v5.csv` | Layer 12 alias key — 175,455 rows |
| `dish_canonical_summary_v5.csv` | Layer 12 canonical list — 149,244 dishes |
| `clean_single_letters.py` | Layer 13 cleanup script (strip floating single-letter tokens) |
| `single_letter_changes.csv` | Layer 13 audit (rename/merge/drop per cluster) |
| `dish_aliases_v6.csv` | Layer 13 alias key — 175,167 rows |
| `dish_canonical_summary_v6.csv` | Layer 13 canonical list — 148,181 dishes |
| `find_merge_candidates.py` | Layer 14 token-overlap candidate generator |
| `merge_candidates.csv` | Layer 14 candidate pairs (128,388) |
| `judge_merge_candidates.py` | Layer 14 async LLM judge (Gemini Flash via OpenRouter) |
| `candidate_judgments.csv` | Layer 14 verdicts — every pair with YES/NO + reason |
| `apply_judged_merges.py` | Layer 14 merge applicator |
| `llm_merges_applied.csv` | Layer 14 audit — 23,381 applied merges |
| `.env.openrouter` | OpenRouter API key (gitignored) |
| `dish_aliases_v7.csv` | Layer 14 alias key — 175,340 rows |
| `dish_canonical_summary_v7.csv` | Layer 14 canonical list — 124,800 dishes |
| `clean_chain_marketing.py` | Layer 15 strip script (`footlong`, `pro`) |
| `chain_marketing_changes.csv` | Layer 15 audit — 121 cleaned (88 merge / 33 rename) |
| `dish_aliases_v8.csv` | Layer 15 alias key — 175,340 rows |
| `dish_canonical_summary_v8.csv` | Layer 15 canonical list — 124,712 dishes |
| `drop_meal_dinner.py` | Layer 16 token-based drop script |
| `dropped_meal_dinner.csv` | Layer 16 audit — 1,815 dropped clusters with trigger token |
| `dish_aliases_v9.csv` | Layer 16 alias key — 172,949 rows |
| `dish_canonical_summary_v9.csv` | Layer 16 canonical list — 122,897 dishes |
| `find_merge_candidates_v2.py` | Layer 17 stage 1 — token-overlap candidate generator (against v9) |
| `merge_candidates_v2.csv` | Layer 17 candidate pairs — 69,346 |
| `judge_merge_candidates_v2.py` | Layer 17 stage 2 — async LLM judge (Gemini Flash via OpenRouter) |
| `candidate_judgments_v2.csv` | Layer 17 verdicts — every pair with YES/NO + reason |
| `apply_judged_merges_v2.py` | Layer 17 stage 3 — merge applicator |
| `llm_merges_applied_v2.csv` | Layer 17 audit — 5,743 applied merges |
| `dish_aliases_v10.csv` | Layer 17 alias key — 172,776 rows |
| `dish_canonical_summary_v10.csv` | Layer 17 canonical list — 117,154 dishes |
| `find_sub_sandwich_pairs.py` | Layer 18 stage 1 — skeleton-equal sub/sandwich candidate generator |
| `sub_sandwich_candidates.csv` | Layer 18 candidate pairs — 2,411 |
| `judge_sub_sandwich_pairs.py` | Layer 18 stage 2 — relaxed-prompt LLM judge |
| `sub_sandwich_judgments.csv` | Layer 18 verdicts — every pair with YES/NO + reason |
| `apply_sub_sandwich_merges.py` | Layer 18 stage 3 — merge applicator |
| `sub_sandwich_merges_applied.csv` | Layer 18 audit — 1,806 applied merges |
| `dish_aliases_v11.csv` | Layer 18 alias key — 172,949 rows |
| `dish_canonical_summary_v11.csv` | Layer 18 canonical list — 115,348 dishes |
| `drop_bare_format.py` | Layer 19 bare-format drop script |
| `dropped_bare_format.csv` | Layer 19 audit — 28 dropped clusters (8,492 menu rows) |
| `dish_aliases_v12.csv` | Layer 19 alias key — 172,772 rows |
| `dish_canonical_summary_v12.csv` | Layer 19 canonical list — 115,320 dishes |
| `flag_long_singletons.py` | Layer 20 stage 1 — heuristic flagger (≥5 tokens, no allowlist noun) |
| `long_singleton_flags.csv` | Layer 20 flagged singletons — 807 |
| `judge_long_singletons.py` | Layer 20 stage 2 — strict LLM keep/drop with international-aware prompt |
| `long_singleton_judgments.csv` | Layer 20 verdicts — every flagged item with KEEP/DROP + reason |
| `apply_long_singleton_drops.py` | Layer 20 stage 3 — drop applicator |
| `dropped_long_singletons.csv` | Layer 20 audit — 400 dropped clusters |
| `dish_aliases_v13.csv` | Layer 20 alias key — 172,372 rows |
| `dish_canonical_summary_v13.csv` | Layer 20 canonical list — 114,920 dishes |
| `drop_addons.py` | Layer 21 token-based add-on drop script |
| `dropped_addons.csv` | Layer 21 audit — 47 dropped clusters with trigger token |
| `dish_aliases_v15.csv` | Layer 21 alias key — 172,322 rows |
| `dish_canonical_summary_v15.csv` | Layer 21 canonical list — 114,873 dishes |
| `clean_doubled_tokens.py` | Layer 22 doubled-token cleanup script (with PRESERVE_DOUBLED allowlist) |
| `doubled_token_changes.csv` | Layer 22 audit — 862 cleaned (854 rename / 8 merge / 0 drop), 150 preserved unchanged |
| `dish_aliases_v16.csv` | Layer 22 alias key — 172,322 rows |
| `dish_canonical_summary_v16.csv` | Layer 22 canonical list — 114,865 dishes |
| `clean_quesadillas.py` | Layer 23 manual quesadilla cleanup (10 merges + 4 plural renames + bf→buffalo) |
| `quesadilla_changes.csv` | Layer 23 audit — every absorbed alias with merge reason and language note |
| `dish_aliases_v17.csv` | Layer 23 alias key — 172,326 rows |
| `dish_canonical_summary_v17.csv` | Layer 23 canonical list — 114,855 dishes |
| `proposals/category_*.csv` (11 files) | Layer 24 per-agent category proposals |
| `aggregate_proposals.py` | Layer 24 stage 2 aggregator + validator |
| `proposals/aggregated_{high,medium,judgment}.csv` | Layer 24 confidence-bucketed proposals |
| `proposals/aggregation_report.md` | Layer 24 per-category breakdown + validation issues |
| `apply_categories.py` | Layer 24 cycle-aware applicator (rename-first ordering) |
| `category_changes.csv` | Layer 24 audit — every absorbed alias with category, language reason |
| `dish_aliases_v18.csv` | **FINAL alias key — 172,326 rows post-Layer-24** |
| `dish_canonical_summary_v18.csv` | **FINAL canonical dish list — 113,925 unique dishes** |
| `build_dish_index.py` | Reconstruction join script (raw menus → canonical dish via alias key) |
| `menu_dishes.csv` / `menu_dishes.sqlite` | Final reconstructed table — 1,126,856 (restaurant, menu_item, canonical_dish) rows; 107,581 distinct canonicals; SQLite has indexes on canonical_dish, zip_code, restaurant_id |
