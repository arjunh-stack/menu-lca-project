# menu-lca-project

An automated, five-stage pipeline that turns a 5.1 M-row Kaggle
restaurant-menu dump into per-dish environmental impact (GHG, water,
land) and nutrition (kcal, protein, fat, carb), joined to ~1.0 M real
menu rows across 42,557 US restaurants and 2,678 zip codes, using Poore
& Nemecek 2018 as a framing scaffold (not a study to replicate).

The pipeline reconstructs each dish into ingredients and grams with an
LLM, matches every ingredient to AGRIBALYSE and SU-EATABLE LIFE emission
factors through a hybrid synonym → embedding-search → LLM-disambiguation
matcher, and reports each impact with a triangular Monte Carlo
uncertainty interval and an ISO 14044 pedigree (data-quality) grade.

> **Note on this repository.** This is a point-in-time snapshot of an
> active research project, shared as a public mirror of the code and
> methodology while the work is ongoing. The core pipeline (canonical-dish
> resolution, nutrition, and the LCA matcher with its Monte Carlo and
> pedigree modules) is built and validated; remaining work is mostly
> scaling the validated pieces to the full dish set and writing up the
> downstream analysis. The large source and output data (multi-gigabyte
> SQLite databases, full per-recipe JSONL outputs, embeddings, and the
> versioned alias snapshots) are not included here; they are documented in
> the methodology files and are reconstructable from the pipeline. Small
> reference tables and validation samples are included so the code is
> legible end to end. The emphasis is on the method and the code, not on
> shipping a finished dataset.

The project plan, decisions, and orchestration live in
[`PLAN.md`](PLAN.md). The canonical record of methodological decisions,
the source for the paper's Methods section, lives in
[`METHODOLOGY.md`](METHODOLOGY.md). Each stage has its own `PLAN.md`
in its folder (`recipes/`, `lca/`, `nutrition/`, `phylogeny/`).

## What to look at first

The heart of this project is the life-cycle assessment stage in
[`lca/`](lca/). It takes a recipe (ingredients and grams) and returns
per-recipe GHG, water, and land impacts, each with a quantified
uncertainty interval and a data-quality grade:

- [`lca/matcher.py`](lca/matcher.py) resolves each free-text ingredient
  to an emission factor through a hybrid pipeline: a synonym dictionary,
  then embedding-based nearest-neighbor search, then LLM disambiguation,
  drawing on AGRIBALYSE, SU-EATABLE LIFE, and Poore & Nemecek.
- [`lca/monte_carlo.py`](lca/monte_carlo.py) runs a 10,000-draw
  triangular Monte Carlo over each emission factor's (min, recommended,
  max) bounds and reports the full distribution plus per-ingredient
  variance contributions.
- [`lca/pedigree.py`](lca/pedigree.py) scores each estimate with an
  ISO 14044 data-quality pedigree, so every number carries a grade for
  how well-supported it is.
- [`lca/aggregate_lca.py`](lca/aggregate_lca.py) ties these together
  into the per-recipe output.

The same architecture, gathering parameters from references, propagating
uncertainty, and grading provenance, is intended to generalize beyond
food to any system where you need a cost or impact estimate with explicit
uncertainty.

## Quickstart

```bash
# 1. Python 3.11 environment + deps
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. API key (free at https://openrouter.ai/keys)
cp .env.openrouter.example .env.openrouter
# edit .env.openrouter and paste your key

# 3. Get the raw Kaggle source database (a public restaurant-menu
#    dataset; 5,117,217 menu rows and 63,469 restaurants when
#    downloaded). Place it at the repo root as `mydb.sqlite`.

# 4. Reconstruct the canonical menu_dishes.sqlite from the committed
#    alias snapshots (uses dish_aliases_v19.csv – the latest,
#    Layer-25-filtered vocab – resolved via paths.py, no path edits
#    needed; run from anywhere):
python3 build_dish_index.py
# This re-applies the canonical-dish mapping (stage 1 frozen output)
# to mydb.sqlite and produces menu_dishes.sqlite (~301 MB) with
# ~1.0 M rows joining raw menus to ~75,325 canonical dishes
# (v19; was 107,581 under v18 before Layer 25's recipe-test screen).

# 5. Run any downstream stage. Examples:
python3 recipes/precompute_dish_context.py
python3 recipes/pipeline.py --top 500           # 500-dish validation
python3 lca/match_ingredients.py
python3 lca/aggregate_lca.py                    # if you've finished step 3
```

## Reproducibility model

The pipeline includes LLM calls – some deterministic (OpenRouter at
`temperature=0`), some not (Claude sub-agents in the original cleaning
pass). The repo's reproducibility strategy is:

1. **Deterministic LLM layers**: re-runnable. All OpenRouter scripts
   set `temperature=0` and use stable model IDs. Identical inputs
   produce identical outputs (modulo provider drift).
2. **Non-deterministic LLM layers (Claude sub-agents in Stage 1
   Layers 6, 7, and the chunks_review pass)**: pinned as committed
   data, not re-runnable. The Claude per-row verdicts are saved as
   CSVs (one per parallel-agent chunk) in `chunks_classified/`,
   `chunks_classified_v2/`, and `chunks_review_classified/`. The
   `apply_*.py` scripts consume these CSVs as the source of truth.
   Re-running the pipeline replays the verdicts deterministically;
   you do **not** need to re-query Claude.
3. **Layer-by-layer snapshots**: every transformation produces a
   versioned alias snapshot (`dish_aliases_v<N>.csv` +
   `dish_canonical_summary_v<N>.csv`, v1 → v18). You can rewind to
   any layer and replay forward.
4. **Audit trail**: `FILTERING_LOG.md`, `DATA_CLEANING.md`, and
   `PIPELINE_LAYERS.md` record the rule, before→after row counts,
   and implementing file for every transformation.

## Frozen LLM-decision artifacts

| Stage 1 layer | Method | Frozen dictionary |
|---|---|---|
| 6 – Lenient classification | Claude sub-agents, 30 parallel | `chunks/*.csv` (inputs) + `chunks_classified/*.csv` (verdicts) |
| 7 – Strict reclassification | Claude sub-agents, 30 parallel | `chunks_v2/*.csv` + `chunks_classified_v2/*.csv` |
| Cleanup review | Claude sub-agents, 3 parallel | `chunks_review/*.csv` + `chunks_review_classified/*.csv` |
| 11B – Digit-with-no-match strict pass | DeepSeek v4 Pro, 4 shards | `recipe_screen_deepseek_keeps_shard{0..3}.csv`, merged into `recipe_screen_deepseek_keeps.csv` |
| 14 – Long-tail merges (round 1) | Gemini 2.0 Flash | `candidate_judgments.csv` → `llm_merges_applied.csv` |
| 17 – Long-tail merges (round 2) | Gemini 2.0 Flash | `candidate_judgments_v2.csv` |
| 18 – Sub↔sandwich merges | Gemini 2.0 Flash | `sub_sandwich_judgments.csv` → `sub_sandwich_merges_applied.csv` |
| 20 – Long-singleton judgments | Gemini 2.0 Flash | `long_singleton_judgments.csv` |
| 24 – Category cleanup | Claude sub-agents, 11 parallel | `proposals/category_*.csv` (per-category proposals) + `proposals/aggregated_*.csv` (consolidated) |
| 25 – Recipe-test cross-screen | Gemini 2.0 Flash + DeepSeek v4 Pro | `recipe_screen_gemini.csv` (113,925 verdicts), `recipe_screen_deepseek.csv` (30,879 DROP re-screen), `recipe_screen_deepseek_keeps.csv` (82,606 KEEP re-screen), `dish_rescue_judgments.csv` (1,072 rescues), `recipe_drops_applied.csv` (33,620 applied drops) |
| Various drops (16, 19, 21, 22) | Deterministic rules | `dropped_meal_dinner.csv`, `dropped_bare_format.csv`, `dropped_addons.csv`, `doubled_token_changes.csv` |

## Models per stage

OpenRouter model IDs as configured in code:

| Stage | Use | Model |
|---|---|---|
| 1 (cleaning) | Layer 6, 7, 24 sub-agents | Claude (version not pinned; verdicts frozen as CSV for deterministic replay) |
| 1 (cleaning) | Layer 11B + DeepSeek screens | `deepseek/deepseek-v4-pro` |
| 1 (cleaning) | Layers 14, 17, 18, 20 judges | `google/gemini-2.0-flash-001` |
| 1 (cleaning) | Alias clustering embeddings | `BAAI/bge-small-en-v1.5` (local sentence-transformer) |
| 2 (recipes) | Ingredient + grams estimation | `deepseek/deepseek-chat-v3-0324` |
| 2b (nutrition, planned) | FDC disambiguation | `deepseek/deepseek-chat-v3-0324` (planned, mirrors stage 3) |
| 3 (LCA) | AGRIBALYSE/SU-EATABLE disambiguation | `deepseek/deepseek-chat-v3-0324` |
| 3 (LCA) | Ingredient embeddings | `all-MiniLM-L6-v2` (local sentence-transformer) |
| 5 (phylogeny, planned) | Cluster labels | TBD – recommended `deepseek/deepseek-chat-v3-0324` for consistency |

All OpenRouter calls use `temperature=0` for determinism.

## Stage status

What is built and validated: the canonical-dish vocabulary (Stage 1), the
full nutrition run over all dishes (Stage 2b), the LCA matcher and its
Monte Carlo and pedigree modules (Stage 3), and a first version of the
dish-similarity phylogeny (Stage 5). What remains is mostly scaling the
validated pieces to the full dish set and the downstream analysis.

| Stage | Folder | Status |
|---|---|---|
| 2b. Nutrition | `nutrition/` | **Full run complete.** All 75,324 dishes (99.0% ingredient-mass match, 62,712 fully matched, Atwater-consistent to 0.9%). |
| 1. Canonical dishes | repo root + `proposals/` | **Complete through Layer 25.** 79,590 canonical dishes (v19); the `menu_dishes.sqlite` rebuild from v19 is a one-command step. |
| 3. LCA | `lca/` | **Matcher, Monte Carlo, and pedigree implemented and validated.** Matcher validated on 533 ingredients (530/533 matched); `monte_carlo.py`, `pedigree.py`, and `aggregate_lca.py` in place. Full-dataset aggregate run pending. |
| 5. Phylogeny | `phylogeny/` | **v1 built.** 39,166-dish compositional dendrogram + UMAP with an interactive static site in `phylogeny/site/`. |
| 2. Recipes | `recipes/` | 500-dish validation complete; full-dataset run pending. |
| 4. Analysis & figures | `figures/` | Figure scripts in place; the consolidated analysis write-up is in progress. |

## Reproducibility notes

This section documents how the pipeline is made reproducible and the
practical limits of that, so a reader knows exactly what to expect on a
re-run.

1. **Location-independent paths.** Every script resolves its data through
   `dpath("<file>")`, resolved at runtime by `paths.py` (the repo-root
   anchor). 241 machine-specific absolute-path literals across 69 scripts
   were rewritten this way, and each script carries a small bootstrap
   header that walks up to `paths.py`. Scripts therefore run correctly
   from any working directory and after `git clone` to any location.
2. **Frozen non-deterministic decisions.** The LLM classification and
   merge decisions are committed as CSV verdicts and replayed by the
   `apply_*.py` scripts, so re-runs reproduce the same vocabulary without
   re-querying any model. See the "Frozen LLM-decision artifacts" table
   above.
3. **Verification by layer deltas.** Each transformation's
   before-and-after row counts and rule are recorded in
   `PIPELINE_LAYERS.md`, `FILTERING_LOG.md`, and `DATA_CLEANING.md`. A
   re-run is checked against those documented deltas rather than against
   a unit-test suite; building automated tests around the documented row
   counts is a natural next step.
4. **Data reconstruction.** The large built artifacts are gitignored
   because they exceed GitHub's 100 MB per-file limit. `menu_dishes.sqlite`
   is rebuilt with `python3 build_dish_index.py` from the committed alias
   CSVs plus the raw Kaggle `mydb.sqlite`; the Kaggle dataset slug is
   noted as a to-fill item so the quickstart becomes end-to-end runnable.
5. **Provider drift.** OpenRouter models occasionally update under the
   same ID (DeepSeek v3 dated `0324` is mostly stable; Gemini Flash has
   changed under `google/gemini-2.0-flash-001` over time). For
   paper-grade reproducibility on a re-run, expect ≤1% decision drift on
   borderline cases per OpenRouter layer; the frozen verdicts above
   eliminate this for the layers that matter most.

## Repo layout

```
/                         docs + config + the keystone bridge scripts only
  paths.py                repo-root anchor: file→location map + dpath()
  build_dish_index.py     rebuilds menu_dishes.sqlite from a v-snapshot
  dedup.py                shared normalization module (imported by Stage 1)
  mydb.sqlite             raw Kaggle input (gitignored)
  menu_dishes.{sqlite,csv} built canonical join (gitignored)
  README/PLAN/METHODOLOGY/PIPELINE_LAYERS/DATA_CLEANING/FILTERING_LOG.md

stage1/scripts/           the ~58 pipeline-layer scripts (clean_*, apply_*,
                          flag_*, drop_*, judge_*, screen_*, classify_*)
stage1/snapshots/         versioned alias chain dish_aliases_v2..v19.csv +
                          summaries + frozen Layer-10 synonyms.csv
stage1/frozen/            non-deterministic LLM verdicts replayed by
                          apply_*.py (judgments, recipe_screen_*, rescues)
stage1/intermediate/      deterministic outputs / audit / scratch CSVs
stage1/investigation/     trace / test / plot one-offs (non-pipeline)
logs/                     run logs

proposals/                Stage 1 Layer 24 – frozen LLM category proposals
recipes/                  Stage 2 – dish → ingredients + grams
nutrition/                Stage 2b – recipe → kcal/protein/fat/carb
lca/                      Stage 3 – recipe → GHG/water/land
phylogeny/                Stage 5 – interactive dish-similarity tool:
                          precompute/ (pipeline), site/ (static D3 app)
flexibility/              substitution / abatement-curve analysis
figures/                  publication figure scripts (matplotlib)
```

Large committed data referenced above (the `chunks*/` verdict dumps, the
`stage1/snapshots/` alias chain, and the SQLite/JSONL outputs) lives in
the full working tree and is excluded from this public mirror; the
methodology files describe how each is produced.
