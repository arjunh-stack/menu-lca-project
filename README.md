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

> **Note on this repository.** This is a public mirror of the project's
> code and methodology. The large source and output data (multi-gigabyte
> SQLite databases, full per-recipe JSONL outputs, embeddings, and the
> versioned alias snapshots) are not included here; they are documented
> in the methodology files and are reconstructable from the pipeline.
> Small reference tables and validation samples are included so the code
> is legible end to end. The emphasis here is on the method and the code,
> not on shipping the full dataset.

The project plan, decisions, and orchestration live in
[`PLAN.md`](PLAN.md). The canonical record of methodological decisions —
the source for the paper's Methods section — lives in
[`METHODOLOGY.md`](METHODOLOGY.md). Each stage has its own `PLAN.md`
in its folder (`recipes/`, `lca/`, `nutrition/`, `phylogeny/`).

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
#    alias snapshots (uses dish_aliases_v19.csv — the latest,
#    Layer-25-filtered vocab — resolved via paths.py, no path edits
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

The pipeline includes LLM calls — some deterministic (OpenRouter at
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
| 6 — Lenient classification | Claude sub-agents, 30 parallel | `chunks/*.csv` (inputs) + `chunks_classified/*.csv` (verdicts) |
| 7 — Strict reclassification | Claude sub-agents, 30 parallel | `chunks_v2/*.csv` + `chunks_classified_v2/*.csv` |
| Cleanup review | Claude sub-agents, 3 parallel | `chunks_review/*.csv` + `chunks_review_classified/*.csv` |
| 11B — Digit-with-no-match strict pass | DeepSeek v4 Pro, 4 shards | `recipe_screen_deepseek_keeps_shard{0..3}.csv`, merged into `recipe_screen_deepseek_keeps.csv` |
| 14 — Long-tail merges (round 1) | Gemini 2.0 Flash | `candidate_judgments.csv` → `llm_merges_applied.csv` |
| 17 — Long-tail merges (round 2) | Gemini 2.0 Flash | `candidate_judgments_v2.csv` |
| 18 — Sub↔sandwich merges | Gemini 2.0 Flash | `sub_sandwich_judgments.csv` → `sub_sandwich_merges_applied.csv` |
| 20 — Long-singleton judgments | Gemini 2.0 Flash | `long_singleton_judgments.csv` |
| 24 — Category cleanup | Claude sub-agents, 11 parallel | `proposals/category_*.csv` (per-category proposals) + `proposals/aggregated_*.csv` (consolidated) |
| 25 — Recipe-test cross-screen | Gemini 2.0 Flash + DeepSeek v4 Pro | `recipe_screen_gemini.csv` (113,925 verdicts), `recipe_screen_deepseek.csv` (30,879 DROP re-screen), `recipe_screen_deepseek_keeps.csv` (82,606 KEEP re-screen), `dish_rescue_judgments.csv` (1,072 rescues), `recipe_drops_applied.csv` (33,620 applied drops) |
| Various drops (16, 19, 21, 22) | Deterministic rules | `dropped_meal_dinner.csv`, `dropped_bare_format.csv`, `dropped_addons.csv`, `doubled_token_changes.csv` |

## Models per stage

OpenRouter model IDs as configured in code:

| Stage | Use | Model |
|---|---|---|
| 1 (cleaning) | Layer 6, 7, 24 sub-agents | Claude (model = whichever model was running at the time; non-pinned, verdicts frozen as CSV) |
| 1 (cleaning) | Layer 11B + DeepSeek screens | `deepseek/deepseek-v4-pro` |
| 1 (cleaning) | Layers 14, 17, 18, 20 judges | `google/gemini-2.0-flash-001` |
| 1 (cleaning) | Alias clustering embeddings | `BAAI/bge-small-en-v1.5` (local sentence-transformer) |
| 2 (recipes) | Ingredient + grams estimation | `deepseek/deepseek-chat-v3-0324` |
| 2b (nutrition, planned) | FDC disambiguation | `deepseek/deepseek-chat-v3-0324` (planned, mirrors stage 3) |
| 3 (LCA) | AGRIBALYSE/SU-EATABLE disambiguation | `deepseek/deepseek-chat-v3-0324` |
| 3 (LCA) | Ingredient embeddings | `all-MiniLM-L6-v2` (local sentence-transformer) |
| 5 (phylogeny, planned) | Cluster labels | TBD — recommended `deepseek/deepseek-chat-v3-0324` for consistency |

All OpenRouter calls use `temperature=0` for determinism.

## Stage status

| Stage | Folder | Status |
|---|---|---|
| 1. Canonical dishes | repo root + `proposals/` + `chunks*/` | **done through Layer 25** (79,590 canonicals in v19; `menu_dishes.sqlite` rebuild from v19 pending) |
| 2. Recipes | `recipes/` | 500-dish validation done; full run pending |
| 2b. Nutrition | `nutrition/` | **full run done** — `dish_macros.jsonl`, all 75,324 dishes (99.0% ingredient-mass match, 62,712 fully matched, Atwater-consistent to 0.9%) |
| 3. LCA | `lca/` | matcher validated on 533 ingredients (530/533 matched); `aggregate_lca.py` exists, MC + pedigree pending |
| 4. Analysis & figures | `analysis/` (to be created) | not started |
| 5. Phylogeny | `phylogeny/` | **v1 built** — 39,166-dish compositional dendrogram + UMAP, interactive static site in `phylogeny/site/` |

## Known reproducibility gaps

1. **~~Hardcoded absolute paths.~~ RESOLVED.** Every Stage 1 script
   previously hardcoded machine-specific absolute paths. All 241 such
   literals across 69 scripts were rewritten to `dpath("<file>")`,
   resolved at runtime by `paths.py` (the repo-root anchor). Each script
   carries a small bootstrap header that walks up to `paths.py`, so
   scripts run correctly from any working directory and after `git
   clone` to any location. Data files were relocated
   into `stage1/{snapshots,frozen,intermediate}/` and the move + the
   rewrite are driven by the same map in `paths.py`, so they cannot
   disagree. Stage 2/3 newer scripts already used relative paths.
2. **Kaggle source URL.** The exact Kaggle dataset slug for
   `mydb.sqlite` is not yet pinned in this README. Once filled in
   (5,117,217 menu rows, 63,469 restaurants), the README quickstart
   becomes end-to-end runnable.
3. **`menu_dishes.sqlite` is gitignored** (301 MB exceeds GitHub's
   100 MB per-file limit). Reconstruct with `python3
   build_dish_index.py` from the committed alias CSVs +
   `mydb.sqlite`.
4. **No tests.** Re-running any layer doesn't verify it reproduces
   the documented row count; you have to eyeball the deltas against
   `PIPELINE_LAYERS.md`.
5. **Provider drift.** OpenRouter models occasionally update under
   the same ID (DeepSeek v3 dated `0324` is mostly stable; Gemini
   Flash has changed under `google/gemini-2.0-flash-001` over time).
   For paper-grade reproducibility on a re-run, expect ≤1 % decision
   drift on borderline cases per OpenRouter layer.

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

proposals/                Stage 1 Layer 24 — frozen LLM category proposals
recipes/                  Stage 2 — dish → ingredients + grams
nutrition/                Stage 2b — recipe → kcal/protein/fat/carb
lca/                      Stage 3 — recipe → GHG/water/land
phylogeny/                Stage 5 — interactive dish-similarity tool:
                          precompute/ (pipeline), site/ (static D3 app)
flexibility/              substitution / abatement-curve analysis
figures/                  publication figure scripts (matplotlib)
```

Large committed data referenced above (the `chunks*/` verdict dumps, the
`stage1/snapshots/` alias chain, and the SQLite/JSONL outputs) lives in
the full working tree and is excluded from this public mirror; the
methodology files describe how each is produced.
