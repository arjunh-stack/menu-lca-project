# Nutrition pipeline — porting plan

**Scope.** Recipe (`[{ingredient, grams}, ...]`) → per-recipe macros: energy
(kcal), protein (g), fat (g), carbohydrates (g). One file in, one file out.
Lets us reframe per-dish impacts in P&N-style nutritional functional units
(per 1000 kcal, per 100 g protein) when the analysis step needs them.

This is **step 2b** in the project — runs in parallel with the LCA step (3),
because both steps consume the same recipes.jsonl input. No dependency
between them.

## Source: USDA FoodData Central (FDC) bulk CSVs

Local-only data — no FDC API calls at match time. Three of the FDC data
types are useful for ingredient→macros lookup; the fourth (Branded Foods)
is skipped.

| Data type | File | Why we use it | Skip? |
|---|---|---|---|
| **SR Legacy** | `data/sr_legacy/` | 7,793 standard reference foods — raw ingredients ("Chicken, broilers or fryers, breast, meat only, raw") and basic cooked forms. The workhorse for plain ingredients. | keep |
| **FNDDS** (Survey) | `data/fndds/` | 5,432 prepared/composite foods reflecting what people actually eat ("Spaghetti, cooked, fat not added in cooking"). Critical for cooked/composite ingredient strings from the LLM recipe pass. | keep |
| **Foundation Foods** | `data/foundation/` | 469 high-quality lab-analyzed foods (rows with `data_type='foundation_food'`). Small but high-confidence. Useful for headline ingredients. **Caveat:** the bulk CSV also contains ~87k forensic chain-of-custody rows (`sample_food`, `sub_sample_food`, `market_acquisition`, `agricultural_acquisition`) — the ingest step must filter to `data_type='foundation_food'`. | keep |
| **Branded Foods** | — | ~500k packaged products. Mostly noise for recipe ingredients (we're not looking up "Heinz Ketchup, 14 oz bottle"). Adds matching ambiguity. | **skip** |

After filtering Foundation Foods, total food rows across the three sources
≈ 13,694. Per-food macro values live in `food_nutrient.csv` keyed by
`fdc_id`. We extract the four nutrients we care about (energy kcal,
protein g, fat g, carb g per 100g) and produce a single flat lookup
table at port time.

## What changes vs. the LCA matcher

The architecture mirrors `lca/matcher.py` deliberately — dedupe ingredient
strings first, match the unique set once, aggregate per-recipe in memory.
Two intentional differences:

1. **No remote API at match time.** AGRIBALYSE / SU-EATABLE / P&N already
   live as small local CSVs in `lca/data/`. FDC is similar in shape but
   bigger (FNDDS + SR Legacy + Foundation = ~14k food rows after the
   macro extraction). Embedding search is purely local.

2. **Cooked-vs-raw selection happens inside the LLM disambiguator.** See
   "Cooking transformation handling" below.

Reuse from the LCA side:
- The sentence-transformer model and embedding pipeline (already in
  `lca/data/embeddings/`).
- The deduped `ingredients_unique.csv` from
  `recipes/recipes.jsonl` — both steps consume the same unique-ingredient
  set, no point doing it twice.
- The OpenRouter LLM-disambiguation prompt skeleton from `lca/matcher.py`;
  swap the candidate-list source from AGRIBALYSE rows to FDC rows and
  swap the rubric (see below).

## Cooking transformation handling

**Decision: don't model cooking losses at the recipe level. Push the
choice into ingredient→FDC matching.**

When the LLM disambiguator picks an FDC entry for a recipe-derived
ingredient string:
- If the ingredient name implies cooking ("fried chicken", "grilled
  steak", "roasted potatoes", "boiled rice"), prefer the cooked FDC
  entry ("Chicken, broilers or fryers, breast, meat only, cooked,
  fried").
- If the ingredient name is neutral or raw ("chicken breast", "potato",
  "rice"), prefer the raw FDC entry.
- FNDDS has cooked-form entries for essentially every common ingredient;
  SR Legacy covers raw and basic cooked forms. Between the two we have
  good coverage.

Reasoning: the user-facing macros need to reflect "as eaten" (cooking
loses water in meat, gains oil in fried items, etc.). Modeling those
transformations explicitly at the recipe level is too many degrees of
freedom for too little benefit when FDC already has cooked entries
measured. The cost is ~one extra sentence in the LLM disambiguation
prompt: "Prefer cooked entries when the ingredient name implies cooking."

For the impact (LCA) side this issue doesn't exist — impact is locked at
the raw-ingredient level, cooking transformations are outside the
cradle-to-farm-gate boundary.

## Pipeline shape

Five scripts, all idempotent / resumable like the rest of the project.

```
nutrition/
├── PLAN.md                       (this file)
├── port_fdc_data.py              (one-time) read SR Legacy + FNDDS + Foundation
│                                  CSVs, join with food_nutrient.csv, extract
│                                  energy/protein/fat/carb per 100g, write
│                                  fdc_macro_table.csv keyed by fdc_id.
│                                  Also write fdc_descriptions.csv for embedding.
├── precompute_fdc_embeddings.py  (one-time) sentence-transformer embed every
│                                  FDC description, write to embeddings.npy.
├── match_ingredients.py          ingredients_unique.csv → ingredient_fdc_table.csv
│                                  Mirrors lca/match_ingredients.py architecture.
│                                  Embedding search → LLM disambiguation with
│                                  cooked/raw preference rule.
├── aggregate_macros.py           recipes.jsonl × ingredient_fdc_table.csv
│                                   → dish_macros.jsonl (per cluster_id)
│                                  Pure in-process arithmetic.
└── data/
    ├── sr_legacy/                (FDC SR Legacy bulk CSV, unzipped)
    ├── fndds/                    (FDC FNDDS bulk CSV, unzipped)
    ├── foundation/               (FDC Foundation Foods bulk CSV, unzipped)
    ├── fdc_macro_table.csv       (built by port_fdc_data.py)
    ├── fdc_descriptions.csv      (built by port_fdc_data.py)
    └── embeddings.npy            (built by precompute_fdc_embeddings.py)
```

## Output schema

`dish_macros.jsonl`, one row per cluster_id:

```json
{
  "cluster_id": 12345,
  "canonical_name": "...",
  "recipe_mass_g": 1700.0,
  "n_servings": 4,
  "energy_kcal_per_recipe": 2080,
  "protein_g_per_recipe": 145,
  "fat_g_per_recipe": 88,
  "carb_g_per_recipe": 165,
  "energy_kcal_per_serving": 520,
  "protein_g_per_serving": 36,
  "fat_g_per_serving": 22,
  "carb_g_per_serving": 41,
  "match_rate": 1.0,
  "unmatched": [],
  "ingredients": [
    {"ingredient": "chicken breast", "grams": 600, "matched_fdc": "Chicken, broilers or fryers, breast, meat only, cooked, fried",
     "fdc_id": 171477, "source": "sr_legacy", "kcal": 990, "protein_g": 186, "fat_g": 24, "carb_g": 0,
     "confidence": 0.92}, ...
  ]
}
```

Joins cleanly with `dish_canonical_summary_v18.csv`, `recipes.jsonl`, and
the eventual `dish_lca.jsonl`.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| **D1** | **Use SR Legacy + FNDDS + Foundation Foods, skip Branded Foods.** | SR Legacy + FNDDS together cover raw and cooked-prepared variants for essentially every recipe ingredient. Branded Foods (~500k packaged products) adds matching ambiguity without coverage gain — we're not looking up trademarked products in dish recipes. |
| **D2** | **Four nutrients: energy (kcal), protein (g), fat (g), carbohydrates (g).** | Standard macros + kcal. Enables P&N-style functional units (per 1000 kcal, per 100 g protein). Adding fiber/sugars/saturated-fat later is one column of work. |
| **D3** | **Cooking transformations handled by FDC entry selection, not explicit recipe-level modeling.** | See "Cooking transformation handling" section. |
| **D4** | **Recipes are assumed 4-serving** (matches the step-2 prompt). Per-serving = per-recipe ÷ 4. | The step-2 prompt explicitly anchors on "standard 4-serving recipe." If/when a kcal-density-based serving normalizer is built, the per-serving values can be re-derived; the per-recipe totals don't change. |
| **D5** | **First run: validation slice — top 500 canonical dishes by `total_count`.** Eyeball ~20 dishes against published nutrition data (USDA SuperTracker / restaurant published nutrition) before scaling. | Same validation cohort as recipes step (`recipes/recipes_validation.jsonl`) and the LCA validation slice. Lets us cross-check all three pipelines on the same dishes. |
| **D6** | **Reuse the LCA pipeline's deduped ingredient set and sentence-transformer model.** | The same ~5–15k unique ingredient strings are matched on both sides. One dedup pass, one embedding model, two matchers. |

## Execution order

1. **Done** — FDC bulk CSVs downloaded and unzipped under `data/`.
2. **Done** — `port_fdc_data.py` → `data/fdc_macro_table.csv` (13,602
   foods) + `data/fdc_descriptions.csv`. See FILTERING_LOG Layer NUT-1.
3. **Done** — `precompute_fdc_embeddings.py` → `data/embeddings/*.npy`.
4. **Superseded** — `match_ingredients.py` collects the unique ingredient
   set inline from the recipes JSONL (same pattern as
   `lca/match_ingredients.py`); no separate `ingredients_unique.csv` step.
5. **Done** — `match_ingredients.py` on the 500-dish slice: 514/533
   unique ingredients matched, 98.9% occurrence-weighted. Cooked-vs-raw
   rule verified (grilled chicken → grilled FDC entry, etc.).
6. **Done** — `aggregate_macros.py` on the slice → `dish_macros.jsonl`
   (500 dishes). 98.3% mean ingredient-mass match; macros Atwater-
   consistent to ~1% (median); spot dishes within published ranges.
7. **Done** — full run on all 75,324 recipes, executed on a remote Mac
   mini via `run_on_mini.sh` / `fetch_from_mini.sh`. 12,103 unique
   ingredients (98.2% occurrence-weighted match); `dish_macros.jsonl`
   98.6% mean ingredient-mass match, Atwater-consistent to 0.9% median.
   See FILTERING_LOG Layer NUT-3.
8. (Later) `join_to_menu_rows.py` to surface per-row macros alongside
   per-row impacts in `menu_dishes.sqlite`; optionally extend
   `_MANUAL_OVERRIDES` to close the quality tail (generic `oil`, `whole
   chicken`, etc. — see NUT-3 follow-ups).

A `FILTERING_LOG.md` entry per script run, same convention as the rest
of the project.

## Open questions

**Q1 — Serving size normalization.** D4 hardcodes 4 servings per recipe
because the step-2 prompt did. In reality "1 serving of grilled cheese"
and "1 serving of beef stew" are not the same caloric portion. Should we
add a kcal-density-based serving normalizer (e.g., normalize to 600
kcal/serving), or leave per-recipe / per-serving as the two reported
units and let downstream analysis pick?

**Q2 — Functional-unit reporting.** Both per-100-g-protein and
per-1000-kcal are P&N functional units. Once `dish_macros.jsonl` and
`dish_lca.jsonl` are joined, computing both is trivial. The question is
which the figures lead with. Recommend per-1000-kcal as the primary
functional unit (closer to "what humans actually eat") with per-100-g-
protein as the headline-comparison cut against P&N's Fig 1A.

**Q3 — Cross-validation against the LLM-derived alternative.** Initial
plan was the deterministic-FDC route; in some future state it might be
worth one LLM-macros pass on the validation slice as a sanity check
("does the deterministic answer roughly match a foundation-model
estimate?"). Cheap, ~$2, ~5 min. Not blocking — just a nice-to-have
during validation.
