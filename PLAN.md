# menu-item-impact — project plan

## Thesis

This is a new paper that **uses Poore & Nemecek 2018** ("Reducing food's
environmental impacts through producers and consumers", *Science*
360:987–992) **as a framing scaffold — not a study to replicate.**
P&N reported per-nutritional-unit impacts across 40 commodity products
from a 1,530-study meta-analysis. We borrow their framing — multi-
indicator analysis, per-functional-unit distributions, concentration
narrative, mitigation/substitution scenarios — and apply it at a
different level of resolution: 113,925 canonical restaurant dishes
joined to 1.13 M real menu rows across 42,557 US restaurants and
2,678 zip codes, with prices.

The shift is one level downstream of P&N: from "what does it cost the
planet to grow this commodity?" to "what does it cost the planet to
order this dish?" Some P&N findings translate directly (animal-vs-
plant skew, within-category variance, concentration of impact);
others don't (producer heterogeneity is not measurable at the menu-
item level; cooking and restaurant prep are outside our boundary). We
do not claim P&N-style numerical replication; we claim a P&N-style
*framework* applied to a different unit of analysis.

The data substrate gives leverage P&N did not have: per-dish, per-
restaurant, geographically resolved, and price-attached.

## Pipeline overview

Five stages. Each owns a folder with a stage-level `PLAN.md` and its
own scripts; this document is the orchestrator.

| Stage | Folder | Status | What it produces |
|---|---|---|---|
| **1. Canonical dishes** | repo root (`dedup.py`, `cluster_aliases.py`, etc.) + `proposals/` | **done through Layer 25** (audited in `PIPELINE_LAYERS.md` / `DATA_CLEANING.md` / `FILTERING_LOG.md`) | 79,590 canonical dishes in `dish_canonical_summary_v19.csv` + `dish_aliases_v19.csv`; raw-menu joinable via `menu_dishes.sqlite` (currently v18-built — needs rebuild against v19; post-rebuild = 75,325 canonicals with menu rows over ~1.0 M menu rows) |
| **2. Recipes** | `recipes/` (see `recipes/PLAN.md`) | validation slice done (top 500, `recipes_validation.jsonl`); full 107 k run pending | per-dish `[{ingredient, grams, proportion_pct}, ...]` from DeepSeek v3, cuisine-anchored structural few-shot |
| **2b. Nutrition** | `nutrition/` (see `nutrition/PLAN.md`) | not started; FDC bulk CSVs downloaded and ready | per-dish kcal, protein g, fat g, carb g (per recipe and per serving), via FDC matching mirrored on the LCA matcher |
| **3. LCA** | `lca/` (see `lca/PLAN.md`) | matcher done on validation slice (530/533 unique ingredients matched, `ingredient_ef_table.csv`); aggregation step pending | per-dish GHG (kg CO₂e), water (m³), land (Pt), with Monte Carlo uncertainty + ISO 14044 pedigree |
| **4. Analysis & figures** | `analysis/` (not yet created) | not started | paper figures: P&N-framed distributions, stage decomposition, concentration, substitution scenarios, geographic; menu-row-level join surfaced back into `menu_dishes.sqlite` |
| **5. Phylogeny** | `phylogeny/` (see `phylogeny/PLAN.md`) | not started | interactive online artifact (published in tandem with the paper, not a paper figure): dish-similarity layout grounded in mass-weighted ingredient composition |

Stages 2b and 3 run in **parallel** off the same `recipes.jsonl`. They
have no dependency on each other. Stages 4 and 5 are independent
publication outputs (paper figures vs. online interactive artifact).

## Repo-wide decisions

These bind across all four stages.

| # | Decision | Where set | Note |
|---|---|---|---|
| **R1** | **Three impact indicators only: GHG, water, land use.** Drop acidification and eutrophication from the analysis output. | `lca/PLAN.md` D1 | AGRIBALYSE carries all five at zero marginal cost; the matcher writes all five columns and the analysis layer chooses the three to surface. |
| **R2** | **Four macros only: energy (kcal), protein (g), fat (g), carbohydrates (g).** | `nutrition/PLAN.md` D2 | The four that matter for P&N-style functional-unit framing. |
| **R3** | **Cradle-to-farm-gate system boundary.** AGRIBALYSE "agriculture + processing" stages only; exclude packaging, transport-to-retail, retail, consumer use, restaurant prep, cooking. | `lca/PLAN.md` D3 | Narrower than P&N's cradle-to-retail boundary by ~12–15% GHG for protein-rich. Documented as limitation; any direct numerical comparison to P&N must apply this gap. |
| **R4** | **4-serving recipe assumption.** The step-2 prompt anchors on "standard 4-serving recipe," and downstream per-serving = per-recipe ÷ 4 until/unless a kcal-density-based serving normalizer is added. | `recipes/pipeline.py` prompt; `nutrition/PLAN.md` D4 | Per-serving outputs from this assumption are coarse — pre-publication a kcal-anchored normalizer is recommended. |
| **R5** | **Cooking transformations not modeled at recipe level.** For impacts: irrelevant (outside the boundary). For macros: handled by preferring cooked FDC entries when the ingredient name implies cooking. | `nutrition/PLAN.md` "Cooking transformation handling" | One-sentence add in the FDC LLM disambiguator prompt; no recipe-level mass-loss model. |
| **R6** | **Validation discipline.** Each stage runs first on the **top-500 canonical dishes by `total_count`**, lockstep across stages 2, 2b, 3. Spot-check ~20 dishes against literature before scaling beyond the slice. | each stage `PLAN.md` "execution order" | Same cohort across stages means cross-pipeline sanity checks (impact vs macros vs price) are possible on the slice without scaling first. |
| **R7** | **FILTERING_LOG.md discipline.** Every filter / exclusion / normalization step appends a layer to `FILTERING_LOG.md` at the repo root. Applies to every stage. | repo convention | Auditable trail of every transformation. Already 30+ layers logged from stage 1; stages 2/2b/3 inherit the convention. |
| **R8** | **Reuse the deduped ingredient set between stages 2b and 3.** One unique-ingredient extraction off `recipes.jsonl`; both matchers consume it. | `nutrition/PLAN.md` D6 | Avoids two separate dedupe passes. ~5–15 k unique strings on the full 107 k recipes. |
| **R9** | **Output joins are keyed on `cluster_id`.** Every per-dish artifact (`recipes.jsonl`, `dish_macros.jsonl`, `dish_lca.jsonl`) keys to `cluster_id` from `dish_canonical_summary_v19.csv`. | repo convention | Final merge into `menu_dishes.sqlite` is a single multi-way join on `cluster_id`. |
| **R10** | **Non-deterministic LLM decisions are pinned as committed data, not re-runnable code.** Where a layer used Claude sub-agents (non-pinned model, non-zero temperature), the per-row verdicts are committed as CSVs (`chunks_classified/`, `chunks_classified_v2/`, `chunks_review_classified/`, `proposals/category_*.csv`). `apply_*.py` scripts consume these as the source of truth. | `README.md` "Frozen LLM-decision artifacts" table | Re-runs replay the verdicts deterministically. Re-querying Claude is not required. For OpenRouter layers (DeepSeek, Gemini Flash) `temperature=0` + stable model IDs give deterministic replay modulo provider drift. |

## Stage details

### Stage 1 — Canonical dishes (done)

Raw Kaggle SQLite (`mydb.sqlite`, 5.1 M menu rows, 63,469 restaurants) →
25 cleaning layers → 79,590 canonical dishes (v19 head).
`menu_dishes.sqlite` currently reconstructed from v18 (May 6); pending
rebuild against v19 will produce 75,325 canonicals with menu rows over
~1.0 M rows. ~4,258 v19 vocab orphans (no menu row matches via alias
lookup) — down from 6,344 under v18 because Layer 25's recipe-test
screen dropped many would-be orphans as non-dishes.

Highlights from the cleaning: 30-agent parallel LLM classification
(layers 6, 7), `rapidfuzz` alias clustering (layer 9), curated synonyms
(layer 10), 4-shard parallel OpenRouter LLM screens (layer 11B), LLM-
judged long-tail merges (layers 14, 17), the `rename_preserved`
mechanic (layer 23) that keeps both new and old aliases under the same
cluster_id for reconstruction stability, and parallel-agent category
cleanup (layer 24).

Full layer-by-layer in `PIPELINE_LAYERS.md` and `DATA_CLEANING.md`.

**Two outstanding state-syncing items before stage 2 scales:**
1. **Rebuild `menu_dishes.sqlite` against v19 aliases.** `build_dish_index.py` hardcodes `dish_aliases_v18.csv`; update to `_v19.csv` and rerun. Drops 32,256 v18 canonicals that Layer 25 ruled non-dishes. (~5 min.)
2. **Filter v19 vocab orphans.** 4,258 canonicals in v19 don't match any menu row after rebuild. Filter `dish_canonical_summary_v19.csv` to `cluster_id`s with menu rows before passing to `recipes/precompute_dish_context.py`. (~5 min.)

### Stage 2 — Recipes (validation slice done)

`recipes/PLAN.md`. Async OpenRouter calls to DeepSeek v3, cuisine-
bucketed structural few-shot anchoring grams proportions, resumable
JSONL writer keyed by `cluster_id`. Validation slice: 500 dishes in
54 s, 100 % parse ok. Full run estimate ~$35, ~75 min at 25/s, sharded.

**Decision still open** (`recipes/PLAN.md` Q2): cuisine-bucket
assignment is voted from `restaurants.category` tags, which means a
grilled cheese sandwich served at burger joints ends up in bucket
`"beef"`. For grams *proportions* this is fine (the "beef" bucket's
structural reference fits sandwiches/burgers), but the bucket label is
not a cuisine label and shouldn't be surfaced downstream as one.

### Stage 2b — Nutrition (not started)

`nutrition/PLAN.md`. Deterministic ingredient→USDA-FDC matching + LLM
disambiguation, mirrored on `lca/matcher.py`. Outputs per-dish kcal +
protein + fat + carb (per recipe and per serving). FDC bulk CSVs
(SR Legacy, FNDDS, Foundation Foods filtered to `foundation_food`) are
already in `nutrition/data/` totaling ~13.7 k food rows after Foundation
Foods filter.

Cross-validation against an LLM-derived macros estimate is captured as
an optional check on the validation slice (`nutrition/PLAN.md` Q3).

### Stage 3 — LCA (matcher validated, aggregation pending)

`lca/PLAN.md`. AGRIBALYSE-first ingredient→EF matching (synonym dict →
embedding search → LLM disambiguation), Poore & Nemecek and SU-EATABLE
LIFE as supplementary sources for MC range bounds and pedigree.
Validation slice matched 530/533 unique ingredients (3 unmatched:
`ranch dressing` and 2 others — investigate before full run). Of the
matched, 526 picked up AGRIBALYSE multi-impact (water, land).

Outstanding to complete the stage:
1. `aggregate_lca.py` validated on the 500-dish slice. Needs P&N spot-check against ~20 known dishes.
2. Per-recipe Monte Carlo (10 k draws, triangular over min/median/max). Wired and working — `dish_lca_validation.jsonl` carries MC bounds + top variance drivers.
3. Per-recipe ISO 14044 pedigree score. **Done** — `lca/pedigree.py` ported from `../reverse-recipe/data_quality/pedigree.py`, wired into `aggregate_lca.py`. Validation slice: all 500 dishes grade B (score 1.60–2.39), driven by AGRIBALYSE geographic mismatch for US dishes — exactly the signal the indicator is designed to surface.
4. `join_to_menu_rows.py` — join `dish_lca.jsonl` × `menu_dishes.sqlite` to surface per-row impacts. Not yet built.
5. Full ingredient match (current `ingredient_ef_table.csv` covers only the 533 ingredients from the validation slice). Needed before full `aggregate_lca.py` run.

### Stage 4 — Analysis & figures (not started)

Not yet a folder. Once stages 2, 2b, 3 produce their per-cluster JSONL
artifacts, stage 4 builds the actual P&N-analog outputs. Proposed:

**`analysis/PLAN.md`** to be written when stage 3 aggregation is done.
Sketch of what it covers:

1. **`dish_panel.parquet`** — the master per-canonical-dish table.
   Columns: `cluster_id`, `canonical_name`, `total_count`,
   `recipe_mass_g`, `n_servings`, `kcal_per_serving`,
   `protein_g_per_serving`, `ghg_kgco2e_per_serving`,
   `water_m3_per_serving`, `land_pt_per_serving`, plus per-1000-kcal
   and per-100-g-protein normalizations, plus uncertainty intervals
   from MC. The substrate everything else joins to.
2. **Fig 1 analog** — distribution of per-100-g-protein and per-1000-
   kcal impact across canonical dishes, faceted by Tier-1 cuisine bin
   (~12 bins from a flat LLM categorization pass). Mean + 10th + 90th
   percentile per bin. The headline figure.
3. **Fig 3 analog** — per-dish ingredient-stage decomposition. "Which
   ingredient drives this dish's footprint?" Stacked-bar across a
   representative set of dishes.
4. **Concentration figure** — cumulative-impact curve over menu rows
   ordered by per-row impact. P&N's "25 % of producers = 53 % of
   impact" analog: "X % of dishes served = Y % of restaurant-food
   impact."
5. **Substitution scenarios** — cuisine-matched plant substitutions at
   the menu-item level. "If every burger joint's beef burger were the
   plant-based equivalent, US restaurant-food GHG drops by Z."
6. **Per-dollar impact axis** — impact / `price_usd`. The leverage P&N
   couldn't compute. Cross-cuisine comparison.
7. **Geographic figure** (stretch goal) — per-zip aggregate impact /
   protein / kcal. Uses the 2,678 zip codes already in
   `menu_dishes.sqlite`.

Stage 5's dish-similarity manifold ("phylogeny") is a separate
artifact, not a paper figure; see `phylogeny/PLAN.md`.

## Validation strategy

Locked across stages: the top-500 canonical dishes by `total_count`
from `dish_canonical_summary_v19.csv` form the validation cohort. Each
stage runs on this cohort first; cross-pipeline checks happen on the
same dishes; full-run go-ahead is gated explicitly per stage.

Status of the 500-dish slice:
- Stage 2 recipes: **done** (`recipes/recipes_validation.jsonl`, 500/500).
- Stage 2b nutrition: not yet.
- Stage 3 LCA matching: **done** (`lca/ingredient_ef_table.csv` covers
  the 533 unique ingredients from the slice). Stage 3 aggregation: not
  yet.

When all three are done on the slice, cross-pipeline spot-checks worth
running before scaling:
- Headline ingredients (beef, chicken, cheese, rice) have impact per kg
  within order-of-magnitude of P&N Fig 1.
- Macros for ~20 well-known dishes (Big Mac, Caesar salad, chicken
  burrito) within ~15 % of published values.
- Impact:protein ratio shows the P&N animal-vs-plant skew.

## Open questions (cross-cutting)

**Q1 — Functional-unit primary axis for headline figures.** P&N leads
with per-100-g-protein (protein-rich foods) and per-1000-kcal (starches)
because the framing is comparable nutrition. We can compute both
trivially once nutrition + LCA are joined. Recommend per-1000-kcal as
the primary axis ("the dish you actually eat") with per-100-g-protein
as the headline-comparison cut against P&N's Fig 1A.

**Q2 — Geographic resolution.** 2,678 zip codes are in
`menu_dishes.sqlite`. P&N stresses geography drives most of farm-stage
variation. Three levels of ambition: (a) just report dish-level impacts
ignoring geography (simplest); (b) zip → region → adjust farm-stage
EFs for big-volume ingredients (beef, dairy, rice) using AGRIBALYSE
country-level rows or USDA regional data (medium); (c) full per-zip-
weighted production-mix estimates (research-grade). (a) for paper v1,
(b) for the online release.

**Q3 — Dish-similarity representation: tree vs manifold.** Details in
`phylogeny/PLAN.md`. The user's framing is "phylogeny" — a tree-shaped
diagram showing dish similarity, with the understanding that it's not
literal biological ancestry. Real dish relationships are multi-parent
(chicken alfredo pizza descends from both pizza and chicken alfredo),
so a strict tree forces decisions the data doesn't support. The plan
captures both tree and manifold options and proposes building both
before picking.

**Q4 — Per-serving normalization.** R4 hardcodes 4 servings/recipe. A
kcal-density-based serving normalizer (e.g., normalize to 600 kcal/
serving for entrees) would give a more realistic per-serving axis but
adds a layer of estimation. Defer until validation slice macros exist;
cheap to add then.

**Q5 — Variance attribution.** P&N's variance is the central finding
because it reflects producer heterogeneity. Ours is mostly LLM-recipe
+ EF-source spread, not producer choice. Don't inherit P&N's narrative
weight on variance without earning it. The honest framing: within-
canonical-dish variance reflects recipe variation across restaurants
serving the same dish (the LCA matcher gets the same EF for every
restaurant); cross-canonical-dish variance is the menu-choice axis.

## File-naming + convention pointers

- **`METHODOLOGY.md`** at repo root — canonical record of every
  methodological decision (framing, system boundary, functional unit,
  indicators, MC + pedigree, validation discipline, reproducibility
  model, models per stage, open questions). The source for the paper's
  Methods section. Add to this in the same turn as any new decision.
- **Per-stage `PLAN.md`** — in each stage folder (`recipes/`, `lca/`,
  `nutrition/`, `phylogeny/`, eventually `analysis/`). Stage-internal
  decisions live there.
- **`FILTERING_LOG.md`** at repo root — chronological log of every
  filter/exclusion/normalization, across all stages. Appended in the
  same turn as the change (R7).
- **`PIPELINE_LAYERS.md`** + **`DATA_CLEANING.md`** at repo root —
  stage-1 historical record. Frozen unless stage 1 reopens.
- **Per-stage per-dish JSONL output**, keyed on `cluster_id` (R9):
  `recipes/recipes.jsonl`, `nutrition/dish_macros.jsonl`,
  `lca/dish_lca.jsonl`. The eventual `dish_panel.parquet` joins all
  three.
- **Per-cluster summary CSV** — `dish_canonical_summary_v19.csv` is
  the current stage-1 head. Each stage-1 alias version pair
  (`dish_aliases_v<N>.csv` + `dish_canonical_summary_v<N>.csv`)
  preserved for audit.

## Execution roadmap

Short-term, in order:

1. Finish stage 3: write `lca/aggregate_lca.py` on the 500-dish slice.
   Spot-check ~20 dishes against P&N table.
2. Begin stage 2b: `nutrition/port_fdc_data.py` + `precompute_fdc_
   embeddings.py` + `nutrition/match_ingredients.py` on the same 500
   slice.
3. Cross-pipeline spot-check on the validation slice (see Validation
   strategy).
4. Filter `dish_canonical_summary_v19.csv` to canonicals with menu
   rows (drop the ~6,344 vocab/seen orphans) before scaling.
5. Parallel full runs: stage 2 (full recipes), then stages 2b + 3 on
   the resulting full `recipes.jsonl`.
6. Create `analysis/` folder + `analysis/PLAN.md`. Build
   `dish_panel.parquet` and the headline paper figures.
7. Stage 5: build the phylogeny artifact per `phylogeny/PLAN.md`.
   Independent from stage 4 — can start as soon as stage 2 recipes
   are full-run; impact/kcal overlays slot in once stages 2b and 3
   are also full-run.

The big-bang dependency chain: stages 2, 2b, 3 all gate on the recipes
output. Once stage 2 full-run is done, 2b and 3 run in parallel and
stage 4 is unblocked.
