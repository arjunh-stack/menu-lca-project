# METHODOLOGY

This is the canonical record of methodological decisions for the
**menu-item-impact** project, organized for direct use when writing the
paper's Methods section. Every load-bearing decision lives here with:
its rationale, where it's set in code/PLAN, and the date it was locked.

This is a **growing document**. When a new methodological decision is
made — add it here in the same turn, do not batch.

Companion documents:
- [`PLAN.md`](PLAN.md) — forward-looking project plan + repo-wide decisions
- [`PIPELINE_LAYERS.md`](PIPELINE_LAYERS.md) — historical Stage 1 cleaning layers
- [`DATA_CLEANING.md`](DATA_CLEANING.md) — per-layer Stage 1 audit detail
- [`FILTERING_LOG.md`](FILTERING_LOG.md) — chronological filter log
- per-stage `PLAN.md` files under `recipes/`, `lca/`, `nutrition/`, `phylogeny/`

---

## 1. Project framing

| Decision | Rationale | Locked |
|---|---|---|
| **The paper uses Poore & Nemecek 2018 as a *framing scaffold*, not a replication target.** We borrow P&N's structure (multi-indicator analysis, per-functional-unit distributions, concentration narrative, mitigation/substitution scenarios) and apply it at the restaurant-dish level rather than the 40-commodity-product level. We do not claim numerical replication of P&N. | The substrate (dish-level resolution + restaurant-level joins + price data) is different enough that numerical comparison is informative as scaffolding but not as replication. | 2026-05-11 |
| **Unit of analysis: the canonical restaurant dish (113,925 dishes).** Each dish is the menu-item-vocabulary-cleaned canonical from Stage 1 (e.g. "chicken alfredo pasta"). Menu-row-level joins (1.13 M rows) flow downstream. | The dish is the unit a consumer chooses; it is also the unit at which restaurants compete and substitute. The commodity level (P&N's unit) is one level too coarse for menu-choice questions. | 2026-05-11 |

## 2. System boundary

| Decision | Rationale | Locked |
|---|---|---|
| **Cradle-to-farm-gate.** AGRIBALYSE "agriculture + processing" stages only. Excluded: packaging, transport-to-retail, retail, consumer use, restaurant prep, cooking. | Narrower than P&N's cradle-to-retail (~12–15% GHG difference for protein-rich foods). Restaurant prep and cooking are research problems of their own; modeling them at scale would confound the ingredient-driven comparison the paper is about. Documented as a limitation. | `lca/PLAN.md` D3, `PLAN.md` R3, 2026-05-11 |
| **Cooking transformations not modeled at recipe level.** For impacts: irrelevant (outside boundary). For macros: handled by preferring cooked FDC entries when the ingredient name implies cooking. | One sentence in the FDC LLM disambiguator prompt vs. an explicit mass-loss model with too many degrees of freedom. FDC carries cooked entries for ~all common ingredients. | `nutrition/PLAN.md` D3, `PLAN.md` R5, 2026-05-11 |

## 3. Functional unit reporting

| Decision | Rationale | Locked |
|---|---|---|
| **Primary outputs are per-recipe totals.** `dish_lca.jsonl` and `dish_macros.jsonl` ship impacts and macros per recipe-as-prompted (4-serving). All per-functional-unit views — per-1000-kcal, per-100-g-protein, per-kg, per-serving — are **derived** at analysis time from the combination of per-recipe impacts + per-recipe macros + recipe mass. No per-serving denominator is hardcoded into the dataset schema. | The per-serving normalization is a reporting choice, not a measurement choice. Hardcoding it would bake assumptions into the data that are easier to revise downstream. | 2026-05-11 |
| **Headline functional unit for the paper's Fig 1 analog: per-1000-kcal.** Secondary cut: per-100-g-protein (mirrors P&N Fig 1A for direct comparison). | Per-1000-kcal is closer to "what people actually eat"; per-100-g-protein is the P&N comparison axis. Both fall out cheaply once nutrition is joined. | `PLAN.md` Q1, 2026-05-11 |

## 4. Impact indicators

| Decision | Rationale | Locked |
|---|---|---|
| **Three indicators reported in figures: GHG (kg CO₂e), water use (m³ scarcity-weighted), land use (Pt).** Acidification and eutrophication are computed and stored in the EF table but not surfaced in headline figures. | The three reported are the indicators that carry ~90% of P&N's public narrative and are the most widely understood by readers. Five-indicator analysis is the LCA standard; we keep the other two as columns for future use and audit. | `lca/PLAN.md` D1, `PLAN.md` R1, 2026-05-11 |
| **AGRIBALYSE v3.2 is the primary EF source.** Poore & Nemecek (2018) and SU-EATABLE LIFE (2020) supply cross-source range bounds for the Monte Carlo uncertainty propagation. | AGRIBALYSE has the best ingredient coverage (~15k products) and is the only source with multi-impact columns (water, land, acidification, eutrophication). EU bias is acknowledged as a limitation (lowers the geographic-correlation pedigree score). | `lca/PLAN.md` D1, 2026-05-11 |

## 5. Uncertainty propagation

| Decision | Rationale | Locked |
|---|---|---|
| **Triangular Monte Carlo, 10,000 draws per recipe**, on GHG only. Inputs: per-ingredient (min, recommended, max) EF triangle + Normal(σ=15%) mass noise. Outputs: mean, median, std, p5, p25, p75, p95 of per-recipe GHG. Plus top-5 per-ingredient variance contributors. | Defensible interval reporting; cheap (minutes at 107k recipe scale). Other indicators (water/land/acidification/eutrophication) stay deterministic in v1 because AGRIBALYSE doesn't publish ranges for them. | `lca/PLAN.md` D2, `lca/monte_carlo.py`, `lca/aggregate_lca.py`, 2026-05-11 |
| **ISO 14044 pedigree score, A–F**, per ingredient and per recipe (CO₂e-weighted). Five Weidema & Wesnæs indicators: reliability, completeness, temporal, geographic, technological correlation. Scored 1–5; averaged to a letter grade. | Standard LCA credibility signal complementary to the quantitative MC bounds. Enables downstream filtering ("ship dishes ≥ B"). Validation-slice run lands all 500 dishes at grade B (score 1.6–2.4): AGRIBALYSE-dominant, US-applied → geographic correlation 3 is the dominant signal, exactly what the indicator is for. | `lca/pedigree.py`, `lca/aggregate_lca.py`, ported from `../reverse-recipe/data_quality/pedigree.py`, 2026-05-11 |

## 6. Nutrition

| Decision | Rationale | Locked |
|---|---|---|
| **Four macronutrients: energy (kcal), protein (g), fat (g), carbohydrates (g).** | The set that matters for P&N-style functional-unit framing (per-1000-kcal, per-100-g-protein). Fiber/sugars/saturated-fat are one column-add away if/when needed. | `nutrition/PLAN.md` D2, `PLAN.md` R2, 2026-05-11 |
| **Deterministic ingredient → USDA FDC lookup; no LLM-estimated macros.** Macros computed as ∑ (per-ingredient grams × per-100-g macro). Ingredient → FDC matching uses the same architecture as the LCA matcher: embedding search + LLM disambiguation (one LLM call per unique ingredient string, not per dish). | FDC values are measured and auditable. The LLM-disambiguation pass for choosing the right FDC entry per ingredient adds a controlled LLM step where it earns its keep (string-matching variation) without putting the macro values themselves through an LLM. | `nutrition/PLAN.md` D2 + cooking section, 2026-05-11 |
| **FDC data sources: SR Legacy (7,793 foods) + FNDDS (5,432 prepared foods) + Foundation Foods (469 lab-analyzed, after filtering to `data_type='foundation_food'`).** Branded Foods (~500k packaged products) skipped. | SR Legacy covers raw and basic cooked ingredients; FNDDS covers prepared/composite forms; Foundation provides high-confidence lab-analyzed anchors. Branded Foods adds matching ambiguity without coverage gain — we are not looking up trademarked packaged goods in restaurant recipes. | `nutrition/PLAN.md` D1, 2026-05-11 |

## 7. Stage 1 (canonical dishes) methodological choices

Documented exhaustively in [`PIPELINE_LAYERS.md`](PIPELINE_LAYERS.md)
and [`DATA_CLEANING.md`](DATA_CLEANING.md). Summary of methodological
load-bearers, not the per-layer mechanics:

| Decision | Rationale | Locked |
|---|---|---|
| **Restaurant exclusions via user-curated category-tag list** (87 of 380 unique tags marked exclude: pharmacies, grocery, liquor, beauty, retail, dessert-only, bars). | Avoids systematic over-counting in the canonical-dish vocabulary by removing categories where "menu items" are not what consumers think of as restaurant dishes. The full tag list and verdicts are in `dedup.py:load_exclude_tags`. | Layer 1 of 24, 2026-04 |
| **Non-main-dish section exclusions** (17,209 distinct menu categories removed: drinks, desserts, sides, sauces, kids menus, delivery-app sections, catering bundles, salads, soups, sushi). | Restricts the dataset to main dishes — the unit consumers think of as "what I'm eating." Hand-reviewed; canonical lists in `dedup.py:load_excluded_menu_categories`. | Layer 2 of 24, 2026-04 |
| **Dish-name normalization preserves dish noun, removes size/qty/filler/order**, then token-sort. Token sort means word order becomes meaningless after normalization. | Reflects the user's framing question: "what *is* this dish, abstracted from menu phrasing?" Documented at `dedup.py:normalize`. | Layer 3 of 24, 2026-04 |
| **Two-pass LLM classification: lenient first (tie-breaker: keep), then strict re-pass (tie-breaker: drop).** Layer 6 and Layer 7 respectively. ~30 parallel Claude sub-agents per pass on ~9,500 rows each. Verdicts committed as frozen artifacts in `chunks_classified/` and `chunks_classified_v2/` (R10). | Two-pass with opposite tie-breakers gives a built-in robustness check — the strict pass overrides the lenient one only when it has a reason. The frozen verdicts make the layer deterministically replayable without re-querying Claude. | Layers 6–7, 2026-04 |
| **Alias clustering: per-token-count bucketed greedy fuzzy clustering with `rapidfuzz.fuzz.ratio ≥ 90`; highest-count alias wins canonical.** | Closer-than-90 token-set similarity reliably means same dish; bucketing by token count avoids "chicken" merging with "chicken alfredo pasta". | Layer 9, `cluster_aliases.py`, 2026-04 |
| **Curated synonyms dictionary** (sub/hoagie/grinder, prawn→shrimp, hamburger→burger, etc.) with explicit REJECTED entries for false-positive risks (wedge→sub, po→sub, hero→sub). | Captures domain knowledge that fuzzy clustering can't get — semantically equivalent terms with low string similarity. Committed in `synonyms.csv` with APPLY/REJECT annotations. | Layer 10, 2026-04 |
| **Multi-round LLM-judged long-tail merges (Gemini 2.0 Flash, temperature=0)** with token-overlap candidate generation. Layers 14, 17, 18, 20. | Cleans up the tail of compositionally-similar canonical names that fuzzy matching can't reach. Each round's YES/NO verdicts are committed as frozen judgment CSVs. | Layers 14, 17, 18, 20, 2026-04 to 2026-05 |
| **Layer 18B reverted in full** (over-relaxed re-judge of NO verdicts collapsed dishes that should stay separate: `eggplant parmesan` ≠ `eggplant parmesan sub`). | Failed-experiment record. Reverts are documented, not buried. | 2026-05 |
| **Parallel-agent multi-category cleanup, 11 categories** (tacos, burritos, mexican_misc, mexican_small, pizza, pasta, wings, asian_noodles, indian, salads, sushi), with per-category proposals consolidated and applied at high-confidence threshold. | Each category has its own subspace of dish-name variations (Spanish↔English, plural↔singular, abbreviation, regional name). Parallel agents specialized per category yield higher precision than a single global pass. | Layer 24, `proposals/` directory, 2026-05 |
| **Recipe-test cross-screen via two independent LLMs** (Gemini 2.0 Flash + DeepSeek v4 Pro), `temperature=0`, asking "could a chef Google this exact name and find a real, repeatable recipe?" Verdicts bucketed (BOTH_KEEP / BOTH_DROP / PRO_VETO / PRO_RESCUE) and applied with rescue carve-outs for verified chain items and obscure ethnic dishes (pro_reason ∈ {obscure, unknown, unrecognized} ∧ total_count ≥ 3). 33,620 drops + 1,072 rescues → v19 head with 79,590 canonicals. | Two-model cross-screen catches "looks like a dish but isn't actually one" cases that survived Layers 6/7's earlier classification — gibberish (7,920), vague names (`chicken mixed`, 6,851), possessives (`burger dave`, 3,595), generic tokens (`tenders`, 1,565). The rescue rule protects against false drops on regional/ethnic dishes the larger model doesn't personally recognize. Drops verdict CSVs frozen (R10): `recipe_screen_gemini.csv`, `recipe_screen_deepseek.csv`, `recipe_screen_deepseek_keeps.csv`, `dish_rescue_judgments.csv`, `recipe_drops_applied.csv`. | Layer 25, 2026-05-11 |

## 8. Validation discipline

| Decision | Rationale | Locked |
|---|---|---|
| **Validation cohort = top 500 canonical dishes by `total_count`** across Stages 2, 2b, 3. Same cohort across stages enables cross-pipeline spot-checks (impact × macros × price) without scaling first. | Top-500 by served-frequency are the dishes the paper's headline findings will lean on. Spot-checking ~20 of them against published numbers (Big Mac 563 kcal, P&N beef ~6 kg CO₂e/100g protein, etc.) catches systematic errors before paying for full runs. | `PLAN.md` R6, 2026-05-11 |
| **Per-stage full runs gated by explicit go-ahead** after validation-slice eyeballing. | Full runs cost real money and time; mistakes propagate. The slice-first discipline keeps the iteration loop tight. | each stage's `PLAN.md` execution order, 2026-05-11 |

## 9. Reproducibility model

| Decision | Rationale | Locked |
|---|---|---|
| **All OpenRouter calls use `temperature=0`** with pinned model IDs. | Deterministic API-level behavior (modulo OpenRouter provider drift). Documented across each script. | repo convention, 2026-04 |
| **Non-deterministic LLM decisions are pinned as committed data.** Claude sub-agent verdicts (Layers 6, 7, the cleanup-review pass) are committed as CSVs in `chunks_classified/`, `chunks_classified_v2/`, `chunks_review_classified/`. `apply_*.py` scripts consume them as the source of truth. | Re-runs replay the decisions deterministically. Re-querying the model (which is not version-pinnable) is not required and would produce drift on borderline cases. | `PLAN.md` R10, `README.md` "Frozen LLM-decision artifacts" table, 2026-05-11 |
| **Layer-by-layer alias snapshots committed** (`dish_aliases_v1.csv` → `_v18.csv`). | Any layer can be replayed from scratch by starting from its predecessor's snapshot. Auditable trail of every cleaning step. | repo convention, 2026-04 onward |
| **Random seeds**: `random.seed(42)` in clustering compare scripts; `--seed` CLI arg in `lca/aggregate_lca.py` for MC. | Where stochasticity is unavoidable, seeds make it reproducible. | various scripts, 2026-05 |
| **Pinned dependencies in `requirements.txt`** + `.env.openrouter.example` + `README.md` quickstart. | Reduces the activation energy for an external reader to re-run the pipeline from scratch. | repo root, 2026-05-11 |
| **`PIPELINE_LAYERS.md` row counts as informal regression test.** Re-running any layer should reproduce the documented before→after delta. Discrepancies surface integration breakage. | Formal tests don't exist yet; the row-count table is a usable proxy. | `PIPELINE_LAYERS.md`, 2026-04 onward |

### Known reproducibility gaps

| Gap | Severity | Mitigation status |
|---|---|---|
| ~~241 hardcoded absolute paths in Stage 1 scripts~~ | ~~High~~ | **RESOLVED 2026-05-18**: all 241 literals across 69 scripts rewritten to `dpath()` resolved by `paths.py` (repo-root anchor); data relocated to `stage1/{snapshots,frozen,intermediate}/`; move + rewrite driven by one shared map, verified (236/236 static refs resolve, all `.py` compile) |
| Kaggle source URL not pinned in README | High for external reproducibility | `README.md` has a `<TODO>` placeholder; one-line edit |
| Claude sub-agent model not pinnable | Medium | Mitigated by R10 — verdicts pinned as data |
| `menu_dishes.sqlite` (301 MB) exceeds GitHub file limit | Low | Reconstructed via `build_dish_index.py` from committed alias CSVs |
| OpenRouter provider drift | Low | Expected ≤1% decision drift on borderline cases per layer |
| No automated row-count regression tests | Medium | `PIPELINE_LAYERS.md` table provides a manual check |

## 10. Models per stage

OpenRouter model IDs as configured in code:

| Stage | Use | Model | Where set |
|---|---|---|---|
| 1 | Layers 6, 7, 24 sub-agents | Claude (model not pinned; verdicts frozen as CSVs) | `chunks_classified/`, `chunks_classified_v2/`, `proposals/` |
| 1 | Layer 11B + DeepSeek screens | `deepseek/deepseek-v4-pro` | `screen_keeps_deepseek*.py`, `screen_drops_deepseek.py`, `screen_keeps_cleanup.py` |
| 1 | Layers 14, 17, 18, 20 judges | `google/gemini-2.0-flash-001` | `judge_merge_candidates*.py`, `judge_sub_sandwich_pairs.py`, `judge_long_singletons.py`, `judge_rescues_gemini.py` |
| 1 | Alias clustering embeddings | `BAAI/bge-small-en-v1.5` (local sentence-transformer, 384-dim) | `cluster_aliases.py` |
| 2 | Ingredient + grams estimation | `deepseek/deepseek-chat-v3-0324` | `recipes/pipeline.py` |
| 2b (planned) | FDC disambiguation | `deepseek/deepseek-chat-v3-0324` | `nutrition/match_ingredients.py` (to be built) |
| 3 | EF source disambiguation | `deepseek/deepseek-chat-v3-0324` | `lca/matcher.py` |
| 3 | Ingredient embeddings | `all-MiniLM-L6-v2` (local sentence-transformer, 384-dim) | `lca/matcher.py` |
| 5 (planned) | Cluster labels | TBD; recommend `deepseek/deepseek-chat-v3-0324` for consistency | `phylogeny/label_clusters.py` (to be built) |

All OpenRouter calls use `temperature=0`. Two different sentence-transformer
models in the project (`BAAI/bge-small-en-v1.5` for Stage 1 clustering vs.
`all-MiniLM-L6-v2` for Stage 3 matching) — both 384-dim, never compared
cross-stage; mild inconsistency documented but not breaking.

## 11. Open methodological questions

These remain unresolved as of the latest update. Once resolved, the
decision moves up into the appropriate section above.

| Q | Question | Status |
|---|---|---|
| **Q1** | Cuisine-bucket labeling at the dish level (Stage 2 `cuisine_bucket` from restaurant-category tags leaks — grilled cheese → "beef"). The bucket name itself shouldn't be surfaced downstream as a cuisine label; the structural-reference prior it provides is fine. | `recipes/PLAN.md` Q2 |
| **Q2** | Geographic resolution for farm-stage EF adjustment. (a) ignore geography in v1 paper; (b) zip → region → ag-region EF for big-volume ingredients; (c) full per-zip production-mix estimates. Recommend (a) for paper, (b) for the online release. | `PLAN.md` Q2 |
| **Q3** | Phylogeny representation: tree (HAC dendrogram) vs manifold (UMAP+HDBSCAN). Build both, pick after seeing the layout. | `phylogeny/PLAN.md` Q1 + `PLAN.md` Q3 |
| **Q4** | Mass-weighted vs presence-only ingredient vectors for the phylogeny. User preference: mass-weighted; willing to be convinced. Cheap to compute both. | `phylogeny/PLAN.md` Q2 |
| **Q5** | Variance interpretation. P&N's variance reflects producer heterogeneity; ours reflects recipe variation + EF source range. Don't inherit P&N's narrative weight without earning it; honest framing is "within-canonical-dish variance across restaurants serving it." | `PLAN.md` Q5 |

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | Initial creation. Captures all decisions made through pedigree integration. |
| 2026-05-11 (later) | Documented Layer 25 recipe-test cross-screen retroactively (was applied 2026-05-11 but undocumented in PIPELINE_LAYERS / METHODOLOGY at the time). v19 (79,590 canonicals) is the new head. |
| 2026-05-18 | Directory reorg + hardcoded-path fix. Root 189→14 files; Stage-1 scripts/data moved into `stage1/{scripts,snapshots,frozen,intermediate,investigation}/` + `logs/`. Added `paths.py` repo-root anchor; rewrote all 241 hardcoded absolute paths to `dpath()`. **No data changed** — pure structural refactor; layer row counts and frozen verdicts are byte-identical, so reproducibility is unaffected (and improved: clone-and-run from any path now works). Closes the top "known reproducibility gap." |
