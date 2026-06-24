# LCA pipeline — porting plan

**Scope.** Recipe (`[{ingredient, grams}, ...]`) → per-recipe life-cycle
impacts: GHG (kg CO₂e), water use (m³ world-eq), land use (Pt). One file
in, one file out. Downstream "what's the impact of a Chipotle bowl in
zip 94305 vs the same bowl in 10003" comes later by joining the per-recipe
output to `menu_dishes.sqlite`.

This is **step 3** in the project. Steps 1+2 already produced canonical
dishes (113,925) and will produce a recipe per dish (`recipes/recipes.jsonl`,
107,579 rows expected).

## Source: `../reverse-recipe/`

That sibling repo ships an end-to-end product-LCA pipeline (9 steps,
~3,500 lines across many modules). We need a small slice of it. Most of
it solves a problem we don't have.

### What we actually need (from `reverse-recipe/`)

| Module | Role | Why we want it |
|---|---|---|
| `approach_hybrid.py` (~929 lines) | Ingredient → AGRIBALYSE/SU-EATABLE/P&N match (synonym dict → embedding search → LLM disambiguation) | This is the core intelligence. Reuse the synonym dict and embedding-search machinery verbatim; the LLM-disambiguation prompt mostly verbatim. |
| `carbon_data_multi.py` (~472 lines) | Unified accessor over Poore & Nemecek (47 products, hardcoded), AGRIBALYSE v3.2 (~15k products, CSV), SU-EATABLE LIFE (324 products, xlsx). Returns min/median/max range per ingredient. | This is our EF table. AGRIBALYSE is the workhorse because it's the only one with multi-impact columns (water, land, eutrophication). |
| `ef_cache.py` (~231 lines) | Local JSON cache with provenance metadata (method, paper, confidence). | Reduces re-matching cost and gives auditability per ingredient. |
| `impact_categories/multi_impact.py` | Water-use / land-use / eutrophication aggregation off AGRIBALYSE columns. | Hits the "carbon emissions, land use, water use" ask directly. |
| `data/agribalyse/*.csv` | Source data: 15k products + stage breakdown + ingredient-level rows. | The actual numbers. ~50 MB; check in. |
| `data/su-eatable/*.xlsx` | 324 food items, 841-publication meta-analysis with uncertainty indicators. | Complements AGRIBALYSE; gives uncertainty bounds. |
| `data/embeddings/*.npy` | Pre-computed sentence-transformer embeddings for AGRIBALYSE + SU-EATABLE names. | Saves the embed-on-startup cost; reuse as-is. |
| `uncertainty_propagation/monte_carlo.py` | Triangular MC (10k draws) over (min, recommended, max) per ingredient. | Per-dish uncertainty intervals. Cheap, well-isolated. |
| `data_quality/pedigree.py` | ISO 14044 pedigree score (A–D) per ingredient/aggregate. | Cheap and useful for downstream filtering ("only ship dishes ≥B"). |

Total real code being ported: **~1,800 lines** of the ~3,500 in
reverse-recipe. The rest of reverse-recipe we drop (next section).

### What we drop entirely

The big drop: **the whole upstream "reverse" half**. reverse-recipe's
purpose is to take a packaged-product nutrition label and *infer* the
ingredient grams. We already have grams from step 2. So:

- `nutrient_estimator.py` — LLM estimates ingredient masses from nutrition
  panel. **Not needed**; recipes already have grams.
- `solver.py` — scipy constrained optimization to refine grams against
  label nutrients. **Not needed**; same reason.
- `fdc_client.py` — USDA FDC API client for product lookup. **Not needed**;
  not consuming product photos or labels.
- `product_classification.py` + concentration factors (3× yogurt, 10× hard
  cheese, etc.). **Not needed**; our recipes describe what's in the dish
  before cooking, not finished products with hidden concentration ratios.
- `packaging_transport/stage_estimator.py` — packaging + transport CO2
  estimation per packaged product. **Not needed**; restaurant dishes don't
  have packaging. (See open question Q3 on whether to add a fixed
  restaurant overhead instead.)
- `report_generation/report_generator.py` (~42 KB) — per-product ISO
  14040/14044 markdown report. **Not needed at 107k-dish scale** — a
  markdown report per dish is the wrong artifact. We'll surface one
  aggregate report covering the whole vocab + per-dish JSON rows.
- `emissions_direct_match.py`, `emissions_matcher.py`,
  `emissions_matcher_llm.py`, `emissions_estimator_unknown.py` — older /
  exploratory matching strategies superseded by `approach_hybrid.py`. Keep
  the one we use; drop the others.
- `sensitivity_analysis/sensitivity.py` — Pareto + EF perturbation per
  product. Maybe later, but probably not at 107k scale.
- `app.py` (Streamlit UI), all `test_*.py`, `recipe_generator.py`,
  visualization scripts — out of scope.

## What changes when we port

1. **Input shape.** reverse-recipe took an `extracted_data` dict per
   product (nutrition label + ingredients-text + serving size + packaging
   type). We take a JSONL row from `recipes/recipes.jsonl`:
   ```json
   {"cluster_id": 12345, "canonical_name": "...", "top_raw_name": "Chicken Tikka Masala",
    "cuisine_bucket": "indian", "total_count": 4711,
    "ingredients": [{"ingredient": "chicken breast", "grams": 600.0, "proportion_pct": 35.2}, ...]}
   ```

2. **Concurrency model.** reverse-recipe uses a 6-worker pool inside one
   product run because ingredients-per-product is the unit of parallelism.
   We have ~107k recipes × ~8 ingredients each = ~860k ingredient lookups,
   most of which are duplicates. **Invert the model**: dedup ingredient
   strings *first*, match the unique set once (cached, parallel), then
   aggregate per-recipe purely in-process. This is the highest-leverage
   architectural change.

3. **Matching budget.** The dedup'd ingredient vocabulary is probably
   ~5–15k unique strings (most dishes share "chicken", "rice", "tomato",
   "olive oil"). One-time match cost is cheap. After the first run the
   cache absorbs nearly everything; subsequent runs (e.g. after a recipe
   re-generation) cost ~0.

4. **Output schema.** JSONL keyed by `cluster_id`, joins cleanly against
   `dish_canonical_summary_v18.csv` and `menu_dishes.sqlite`:
   ```json
   {
     "cluster_id": 12345,
     "canonical_name": "...",
     "recipe_mass_g": 1700.0,
     "ghg_kgco2e_per_recipe": 4.12,
     "ghg_kgco2e_per_kg": 2.42,
     "water_m3_per_recipe": 0.058,
     "water_m3_per_kg": 0.034,
     "land_pt_per_recipe": 0.91,
     "land_pt_per_kg": 0.535,
     "uncertainty_p5_p95_ghg": [3.21, 5.18],
     "data_quality_grade": "B",
     "match_rate": 1.0,
     "unmatched": [],
     "ingredients": [
       {"ingredient": "chicken breast", "grams": 600, "matched_lci": "Chicken, breast, raw",
        "source": "agribalyse", "ghg_g": 3360, "water_m3": 0.024, "land_pt": 0.41,
        "pedigree": "A", "confidence": 0.92}, ...
     ]
   }
   ```

5. **Functional unit.** reverse-recipe normalizes everything to "per
   serving" using the nutrition-label serving size. We don't have that.
   For now ship two: **per-recipe** (the 4-serving recipe the step-2
   prompt asked for) and **per-kg-of-recipe**. Per-serving could be added
   later if we estimate kcal per recipe (cheap LLM pass, or join to a
   density table).

## Pipeline shape

Six scripts, run in order. Each idempotent / resumable like the
step-1/step-2 layers.

```
lca/
├── PLAN.md                       (this file)
├── port_reference_data.py        (one-time) copy/process reverse-recipe data
│                                  files into lca/data/
├── dedup_ingredients.py          (one-time per recipes.jsonl)
│                                  recipes.jsonl → ingredients_unique.csv
│                                  (~860k strings → ~5–15k unique)
├── match_ingredients.py          ingredients_unique.csv → ingredient_ef_table.csv
│                                  ports approach_hybrid + ef_cache.
│                                  Async OpenRouter; sharded like screen_keeps;
│                                  cache by ingredient string.
├── aggregate_lca.py              recipes.jsonl × ingredient_ef_table.csv
│                                   → dish_lca.jsonl (per cluster_id)
│                                  pure in-process arithmetic. Apply MC
│                                  + pedigree per recipe.
├── join_to_menu_rows.py          dish_lca.jsonl × menu_dishes.sqlite
│                                   → menu_row_lca.parquet or columns added
│                                  to menu_dishes.sqlite. The downstream
│                                  artefact for "menu-item-impact" analysis.
└── data/
    ├── agribalyse/*.csv          (ported from reverse-recipe/data/)
    ├── su-eatable/*.xlsx
    ├── embeddings/*.npy
    ├── poore_nemecek.py          (hardcoded dict moved out of carbon_data_multi)
    ├── ef_cache.json             (grows; checked in)
    └── ingredient_synonyms.json  (the SYNONYM_DICT, extracted from approach_hybrid)
```

The split between `match_ingredients.py` and `aggregate_lca.py` is the
key change vs. reverse-recipe. They run a tight per-product loop;
we run a global match → per-recipe-aggregation. This is also what makes
the whole thing cheap: ~860k ingredient lookups would be expensive, ~10k
is not.

## Decisions (locked in 2026-05-11)

| # | Decision | Rationale |
|---|---|---|
| **D1** | **AGRIBALYSE v3.2 is the primary EF source**, with Poore & Nemecek and SU-EATABLE as supplementary sources (used for MC range bounds and pedigree). | Best ingredient coverage (~15k products) and the only one with multi-impact columns we need (water, land). EU bias acknowledged as a documented limitation. |
| **D2** | **Full triangular Monte Carlo, 10k draws per recipe.** Carry min/median/max per ingredient EF; sample each independently. Report p5, median, p95 per impact category per recipe. | reverse-recipe's MC module is well-isolated and pure NumPy. Marginal cost is minutes even at 107k-recipe scale. Gives defensible intervals. |
| **D3** | **System boundary = cradle-to-farm-gate.** AGRIBALYSE "agriculture + processing" stages only; exclude packaging, transport-to-retail, retail, consumer use. | Restaurants don't have consumer packaging; modeling restaurant prep/overhead is a separate research problem that would confound the ingredient comparison. Document as limitation; the downstream join step can add a flat per-meal constant if needed. |
| **D4** | **Match raw ingredient strings as-is.** No pre-normalization layer. Rely on `approach_hybrid`'s synonym dict + embedding search + LLM disambiguation to absorb variation. | Step 2's LLM is already temperature=0 so variation should be modest. Embedding search handles "chicken breast" vs "boneless skinless chicken breast" gracefully. Adding a normalize layer is reversible if matching quality is poor on the validation slice. |
| **D5** | **First run: validation slice only — top 500 canonical dishes by `total_count` from the latest available summary** (currently `dish_canonical_summary_v18.csv`, will switch to whatever supersedes it once the canonical cleanup is done). | Full 107k run is gated on explicit go-ahead. Validation slice is for inspecting matched LCI names + spot-checking ~20 dishes against literature before committing to the full run. |

Input to the validation slice: top 500 rows by `total_count` from the
latest `dish_canonical_summary_v*.csv`, joined to whatever recipe rows
exist for them in `recipes/recipes.jsonl`. If recipes for those 500
aren't generated yet, the LCA step waits — it's downstream of recipes.

## Execution order

1. **Wait** for recipe-pipeline output to cover the top-500 validation slice.
   (Canonical-dish cleanup is still in flight; the slice will pin to
   whatever the latest summary is at run time.)
2. `port_reference_data.py` — copy AGRIBALYSE CSVs, SU-EATABLE xlsx,
   pre-computed embeddings, P&N hardcoded dict into `lca/data/`. One-time.
3. Port `approach_hybrid` + `carbon_data_multi` + `ef_cache` into
   `lca/matcher.py`. Strip dead branches (no concentration factors, no
   packaging stage, no nutrient-estimator hooks). Keep the synonym dict,
   embedding-search, and LLM-disambiguation prompt.
4. `dedup_ingredients.py` — pull the ingredient strings from the top-500
   recipes; report the unique count.
5. `match_ingredients.py` on the validation slice's unique ingredients
   (expect ~hundreds). Eyeball the matched LCI names.
6. `aggregate_lca.py` on the validation slice. Spot-check ~20 dishes by
   hand against literature (Poore & Nemecek table headline numbers:
   ~60 kg CO₂e/kg beef, ~20 kg/kg cheese, ~6 kg/kg chicken,
   ~2 kg/kg tofu, ~0.4 kg/kg vegetables).
7. **STOP. Wait for explicit go-ahead before scaling beyond the slice.**
8. (Later, post-approval) full run + `join_to_menu_rows.py`.

A FILTERING_LOG.md entry per script run, same convention as the rest of
the project.
