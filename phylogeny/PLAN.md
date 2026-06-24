# Phylogeny — porting plan

**Scope.** An **interactive online artifact** that visualizes the
relationships between canonical dishes by compositional similarity.
Published *in tandem with* the paper, **not inside** the paper. Lets a
reader explore ~107k dishes, see which dishes are compositionally close
to which, and overlay impact / nutrition / cuisine / price as color.

This is stage 5 of the project. It's a sibling to the paper-figures
work in `analysis/`, not a downstream of it — both are publication
outputs, one for the page, one for the web.

## What it is

A 2D (or pseudo-tree) layout of canonical dishes where:

- **Position** encodes compositional similarity. Two dishes near each
  other share ingredients in similar proportions.
- **Color** can be swapped between overlays: cuisine bin, GHG impact,
  water, land, kcal/serving, protein/serving, price/serving, restaurant
  count, geographic concentration.
- **Hover/click** reveals dish name, top-5 ingredients with mass shares,
  impact + nutrition summary with uncertainty intervals, and a sample
  of restaurants serving it.
- **Zoom levels** show coarser cluster labels at low zoom (e.g., "Pasta
  dishes," "Beef-based Mexican") and individual dishes at high zoom.

The "phylogeny" framing is shape-not-meaning: the diagram looks like a
phylogenetic tree (hierarchical, with internal labeled nodes for
clusters), but the relationships are compositional similarity, not
biological or historical ancestry. Dish lineage is real — fettuccine
alfredo "descends" from carbonara in a culinary sense — but it's not
what this diagram measures. The diagram measures: *given two dishes,
how similar are their ingredient compositions?*

## What it is NOT

- **Not a literal phylogeny.** No common-ancestor claims. The tree
  shape is a hierarchical-clustering rendering, not an evolutionary
  one.
- **Not a paper figure.** ~107k canonicals exceeds what can be read on
  a printed page. The paper may include a static zoomed-in screenshot
  or a few exemplar branches, but the full artifact lives on the web.
- **Not single-parent.** "Chicken alfredo pizza" descends from both
  pizza and chicken alfredo, in any sensible reading. A strict tree
  forces a parent choice the data doesn't support. The manifold view
  handles this naturally; the dendrogram view does not. The diagram
  needs to acknowledge this honestly.

## Algorithm sketch

**Input:** `recipes.jsonl` (one row per `cluster_id`, ingredient list
with mass and proportion_pct), keyed to `dish_canonical_summary_v18.csv`.

**Ingredient canonicalization.** Before vectorizing, normalize
ingredient strings using the same mapping that the LCA matcher uses
(via `lca/ingredient_ef_table.csv` keyed on raw ingredient → canonical
LCI name). This collapses "chicken breast," "boneless chicken breast,"
"boneless skinless chicken breast" into one ingredient so they don't
fragment the vector. Reuses the matcher's resolved set; no new LLM
calls.

**Vector representation.** Two options, both worth building:

- **A — Sparse proportion vector.** One column per canonical ingredient
  (~5–15 k cols). Each dish is a row where cell `(d, i) = mass-share
  of ingredient i in dish d` (sums to ~100 per row). Mostly zeros.
- **B — Dense embedding.** Mass-weighted average of per-ingredient
  sentence-transformer embeddings (already on disk at
  `lca/data/embeddings/`). One 384-dim dense vector per dish. Smooths
  similar ingredients together — "chicken breast" and "chicken thigh"
  are already close in embedding space, so dishes that swap one for
  the other read as more similar than they would under sparse.

The user's stated preference is **mass-weighted** (not presence-only)
because the goal is "two dishes with similar compositions sit together."
A presence-only variant is a one-line variation worth eyeballing if
the mass-weighted layout looks dominated by 2–3 high-mass ingredients
(e.g., bread/pasta swamps every sandwich and pasta dish into one blob).

**Distance metric.** For sparse proportion vectors (option A):

- **Cosine on √proportion** — standard, fast, handles sparsity. Default.
- **Jensen-Shannon divergence** — cleaner theoretical fit for
  proportion vectors (compares two probability distributions). Bounded
  [0, 1], symmetric. Recommended for the "defensible in print" framing.
- **Aitchison distance** — *correct* compositional metric (CLR
  transform → Euclidean) but pukes on heavy sparsity. Skip.

For dense embedding (option B), cosine on the 384-dim vector is the
standard winner.

**Layout.** Two outputs, built in parallel:

- **Manifold view (UMAP).** Reduce the vector to 2D with UMAP.
  Optionally cluster with HDBSCAN on the original (not the UMAP-
  reduced) vectors to label regions. Renders as a scatter plot;
  zooming reveals tighter clusters. No forced single-parent. Best for
  "show me a global picture."
- **Tree view (HAC dendrogram).** Hierarchical agglomerative clustering
  with average linkage on the distance matrix. Cut at multiple heights
  to give multiple levels of cluster labels. Renders as a radial or
  rectangular dendrogram. Looks like a phylogeny. Forces single-parent
  per dish — multi-parent dishes get placed at their best-single-
  parent location with a documented limitation.

The user's framing leans dendrogram (the word "phylogeny" implies
tree-shape). Recommend building both and picking after seeing them on
the same data; the dendrogram makes a cleaner static-image story but
the manifold gives an honest layout. Possibly ship both as toggles in
the same web artifact.

**Cluster labeling.** Once clusters exist (HDBSCAN regions or
dendrogram cuts at chosen heights):

1. For each cluster, take 15–20 representative dishes (highest
   `total_count` within the cluster).
2. Send to LLM (DeepSeek v3, GPT-4o-mini, etc., one call per cluster):
   "Here are 20 dish names: [...]. Return a short (≤4 words) category
   label that describes this group."
3. Cache by cluster signature so re-runs are free.

Labels at multiple zoom levels: top-level (e.g., "Italian Pasta"),
mid-level (e.g., "Cream-based Pasta"), leaf-level (the canonical dish
name itself).

**Overlays.** Each dish carries (joined at viz-build time):

- Cuisine bin (from the Tier-1 flat LLM categorization in stage 4).
- GHG, water, land impact per serving + per-1000 kcal + per-100g
  protein (from `lca/dish_lca.jsonl`).
- kcal, protein, fat, carb per serving (from
  `nutrition/dish_macros.jsonl`).
- Mean price per serving (from `menu_dishes.sqlite` rows for that
  cluster).
- Restaurant count (`total_count`).
- Top zip-code concentration (where it's served).

The viz lets the user swap which dimension drives the color scale.

## Pipeline shape

```
phylogeny/
├── PLAN.md                       (this file)
├── build_vectors.py              recipes.jsonl + ingredient_ef_table.csv
│                                   → dish_vectors.parquet (sparse + dense)
├── compute_distances.py          dish_vectors.parquet
│                                   → pairwise_distance.npy (k-nearest-
│                                     neighbors only, not full n²)
├── cluster_hac.py                pairwise_distance.npy
│                                   → dendrogram.json + cluster_labels.csv
├── cluster_umap.py               dish_vectors.parquet
│                                   → umap_xy.parquet + hdbscan_labels.csv
├── label_clusters.py             cluster_labels.csv + recipes.jsonl
│                                   → cluster_label_table.csv
│                                  (LLM call per cluster, cached)
├── build_web_artifact.py         everything above + overlays
│                                   → web/ (static HTML + JSON for hosting)
└── data/
    └── (generated artifacts)
```

n² distance for 107k dishes = 11.4 B pairs, far too many. Use
approximate-nearest-neighbors (Annoy / HNSW) to compute only the k≈50
nearest neighbors per dish, which is what both UMAP and HAC actually
need.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| **D1** | **Substrate is mass-weighted ingredient composition**, not presence-only and not name-embedding. | User's call. Goal is "dishes with similar compositions sit together," which mass-weighted directly encodes. |
| **D2** | **Build both tree (HAC dendrogram) and manifold (UMAP+HDBSCAN) views**, pick or ship both after seeing them on the same data. | Word "phylogeny" implies a tree, but manifold is more honest about multi-parent inheritance. Cheap to compute both. |
| **D3** | **Ingredient canonicalization reuses the LCA matcher's resolved set**, not a separate normalization layer. | Same problem solved twice = drift. The LCA matcher already canonicalizes via embedding search + LLM disambiguation; reuse. |
| **D4** | **Cluster labels come from an LLM pass over representative dish names per cluster**, not hand-curated. | 100+ clusters at multiple zoom levels. Hand-curation doesn't scale; LLM labels are good enough at this granularity. Cache per cluster signature so re-runs are free. |
| **D5** | **Filter to `total_count ≥ 2`** for the published artifact. | Single-restaurant canonicals (count=1) are mostly long-tail menu-naming noise and would dominate the periphery of the layout while adding nothing to the story. The full 107k stays in the backend tables. Number can be retuned after seeing the layout. |
| **D6** | **Ship as a static-hosted web artifact** (no backend), with all data precomputed at build time and bundled. | Lets it live next to the paper indefinitely with no infra. Tech stack is open (Q3 below). |

## Execution order

1. **Wait** on `recipes/recipes.jsonl` full run (stage 2 full) and on
   `lca/ingredient_ef_table.csv` for the full ingredient vocabulary
   (so D3 canonicalization works against the production set, not the
   500-slice subset).
2. `build_vectors.py` — produce both sparse and dense per-dish vectors.
3. `compute_distances.py` — k-NN distance matrix via Annoy / HNSW.
4. `cluster_hac.py` + `cluster_umap.py` in parallel — tree and manifold
   outputs.
5. `label_clusters.py` — one LLM call per cluster, cached. Cheap.
6. `build_web_artifact.py` — bundle everything with overlays from
   `dish_lca.jsonl` + `dish_macros.jsonl` + `menu_dishes.sqlite`.
7. **Iterate** on the layout — distance metric, mass-weight vs
   presence, count filter, color scale. Stage 5 is a visualization
   problem; expect 3–5 layout revisions before it reads well.

Overlays from stages 2b and 3 can be added later — the layout (steps
2–5) only needs recipes. Color the dots gray and ship; later runs swap
in the impact / nutrition overlays.

A `FILTERING_LOG.md` entry per script run (R7 from the top-level plan).

## Open questions

**Q1 — Tree vs manifold for the primary view.** Cheap to build both;
decide after seeing them. Current lean: ship a toggle in the web
artifact so both are available, default to whichever reads better.

**Q2 — Mass-weighted vs presence-only.** User's stated preference is
mass-weighted, with willingness to be convinced otherwise. Both are
trivial to compute. Worth eyeballing the layout under each before
committing: if mass-weighted has every sandwich and pasta dish blob
together because bread/pasta dominates the mass share, presence-only
or √proportion-weighted may be the better story.

**Q3 — Web tech stack.** Open. Candidates: deck.gl (scales to 107k
points), Observable Plot (clean for ≤10 k), d3 (full control,
expensive at 100k), Plotly (easy, mediocre at scale). Decision deferred
to first layout iteration.

**Q4 — Count filter threshold (D5).** `total_count ≥ 2` is a starting
guess. Worth examining the empirical distribution after stage 2 full
run — maybe ≥3 or ≥5 reads better.

**Q5 — Cuisine-bin anchoring.** Should the layout pre-anchor major
cuisine bins (force "Italian" dishes to one region of the plot) for
readability, or let the algorithm place dishes purely on composition?
Anchoring helps readability at the cost of a layer of human structure.
Recommend: don't anchor; trust the composition to do the work.

**Q6 — Multi-parent honesty.** For the tree view (HAC dendrogram),
dishes like "chicken alfredo pizza" sit somewhere on a single branch
even though their lineage is multi-parent. Options: (a) accept and
note the limitation; (b) ship the manifold as primary and tree as
secondary; (c) add an explicit "other-parents" link on the dish's
detail card. (a) is the cheapest; (c) is the most honest. Decide
after seeing the layout.

---

## v1 — AS BUILT (2026-05-21)

The questions above were resolved with the user and v1 was built. What
actually shipped differs from the speculative pipeline shape above:

**Locked decisions**

| Q | Resolution |
|---|---|
| Q1 | Ship **both** — `Phylogeny` (dendrogram) + `Manifold` (UMAP) toggle. |
| Q2 / D1 | **Semantic embeddings**, not sparse proportion vectors: each dish = proportion-weighted mean of `all-MiniLM-L6-v2` ingredient embeddings (384-d), L2-normed. Smooths near-synonym ingredients. |
| Q3 | **Static site**, vanilla D3 v7 (vendored) + Canvas, no build step, no backend. Served by `python3 -m http.server`. |
| Q4 / D5 | `total_count ≥ 2` for v1 → **39,166 dishes** (from 75,324). `build_vectors.py --min-count 1` adds the long tail back. |
| Q5 | Not anchored — composition does the placement. |
| D4 | LLM clade labels — DeepSeek v3, 966 clades over 3 cut levels (k≈24/150/800), frozen to `frozen/clade_labels.csv`. |
| — | Uniqueness metric **deferred** — visual isolation carries it for v1. |

**As-built pipeline** (`precompute/`, orchestrated by `run_phylo.sh`):

```
build_vectors.py     recipes.jsonl  → dish_vectors.npy + dish_meta.csv
build_tree.py        vectors → tree.json (SciPy Ward HAC) + clades.json
build_umap.py        vectors → umap.json (UMAP cosine; t-SNE fallback)
label_clades.py      clades.json → frozen/clade_labels.csv (DeepSeek v3)
export_site_data.py  → site/data/{tree,umap,manifest}.json + dishes/shard_*
```

No `compute_distances.py` / ANN step — 39k dishes is small enough for
SciPy to build the full Ward dendrogram directly. The frontend lives in
`site/` (`index.html` + `style.css` + `app.js`, RdYlBu design system).

**Run model.** Heavy compute runs on the Mac mini: `deploy_to_mini.sh`
ships the scripts + launches `run_phylo.sh` detached under tmux +
caffeinate; `fetch_from_mini.sh` pulls the `site/data/` bundle back. The
recipe→LCA inputs already live on the mini from the earlier runs.

**Still open for v2:** add `total_count==1` long tail; nutrition
overlays once Stage 2b lands; uniqueness score; radial tree option.
