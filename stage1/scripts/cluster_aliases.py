"""Layer 9 — hybrid alias clustering.

Step A: rapidfuzz token_set_ratio greedy clustering of all 195,551 dish names.
        Catches misspellings, token-order variants, trivial differences.
Step B: embed each Step-A canonical with sentence-transformers (bge-small),
        merge clusters whose canonicals are cosine-similar (synonym layer).
        Catches "hoagie ↔ sub", "flapjacks ↔ pancakes", etc.

Output (`dish_aliases.csv`):
    canonical_name, alias_name, alias_count, cluster_id, method
    where method ∈ {self, fuzzy, semantic} indicating how the alias joined.

Also writes `dish_canonical_summary.csv`:
    cluster_id, canonical_name, n_aliases, total_count
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
import time
import sys
from collections import defaultdict

import numpy as np
from rapidfuzz import fuzz, process
from tqdm import tqdm

IN  = dpath("unique_dishes_mains_v3.csv")
OUT_ALIASES = dpath("dish_aliases.csv")
OUT_SUMMARY = dpath("dish_canonical_summary.csv")

FUZZY_THRESHOLD   = 90    # fuzz.ratio (0-100); ≥90 = typo within same token count
SEMANTIC_THRESHOLD = 0.86 # cosine similarity (0-1); ≥0.86 = synonym
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 384-dim, ~30MB, fast on MPS
RUN_STEP_B = False        # semantic merge — disabled: union-find chained too aggressively

# ---------- load ----------
print(f"loading {IN}")
rows = []
with open(IN) as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        if not row or len(row) < 2:
            continue
        try:
            rows.append((row[0].strip(), int(row[1])))
        except ValueError:
            continue

# Sort by count desc so the most-common spelling becomes the canonical
rows.sort(key=lambda x: -x[1])
names = [n for n, _ in rows]
counts = {n: c for n, c in rows}
n_total = len(names)
print(f"loaded {n_total:,} dish names")

# ---------- step A: rapidfuzz greedy clustering ----------
# For each name (in count-desc order), try to attach to an existing cluster
# whose canonical scores ≥ FUZZY_THRESHOLD via token_set_ratio. If none,
# the name becomes a new cluster's canonical.
#
# This is O(N * K) where K = #clusters. Worst case O(N^2). Cap it by:
#   - sorting clusters by descending count and short-circuiting once we find
#     a hit (greedy)
#   - using rapidfuzz.process.extractOne with score_cutoff for C-speed
print(f"\nstep A — fuzzy clustering (fuzz.ratio ≥ {FUZZY_THRESHOLD}, bucketed by token count)")
t0 = time.time()

cluster_canonical = []   # list[str] — canonical name per cluster id
cluster_count     = []   # list[int] — total count of cluster (for ranking)
name_to_cluster   = {}   # name -> cluster_id

# Group names by token count. Within each group, only same-token-count names
# compete for clustering — this prevents "torta" from absorbing "carnitas torta"
# and "boneless wings" from absorbing "10 boneless wings".
# Names within each group are still processed in count-desc order (so the
# most-common spelling wins canonical).
from collections import defaultdict as _dd
groups = _dd(list)
for name in names:
    ntok = name.count(" ") + 1 if name else 0
    groups[ntok].append(name)

print(f"  token-count buckets: {sorted(groups.keys())[:10]}... (max {max(groups.keys())})")
print(f"  bucket sizes (top 10): {sorted([(k, len(v)) for k, v in groups.items()], key=lambda x: -x[1])[:10]}")

pbar = tqdm(
    total=n_total,
    desc="step A fuzzy",
    unit="name",
    smoothing=0.05,
    mininterval=2.0,
    miniters=1000,
)
for ntok in sorted(groups.keys()):
    bucket_names = groups[ntok]
    bucket_canonicals_idx = []  # global cluster ids that exist in this bucket
    bucket_canonicals_str = []  # parallel list of strings, for rapidfuzz
    for i, name in enumerate(bucket_names):
        pbar.update(1)
        if not bucket_canonicals_str:
            cid = len(cluster_canonical)
            cluster_canonical.append(name)
            cluster_count.append(counts[name])
            name_to_cluster[name] = cid
            bucket_canonicals_idx.append(cid)
            bucket_canonicals_str.append(name)
            continue
        match = process.extractOne(
            name,
            bucket_canonicals_str,
            scorer=fuzz.ratio,
            score_cutoff=FUZZY_THRESHOLD,
        )
        if match is None:
            cid = len(cluster_canonical)
            cluster_canonical.append(name)
            cluster_count.append(counts[name])
            name_to_cluster[name] = cid
            bucket_canonicals_idx.append(cid)
            bucket_canonicals_str.append(name)
        else:
            cid = bucket_canonicals_idx[match[2]]
            name_to_cluster[name] = cid
            cluster_count[cid] += counts[name]
        if pbar.n % 1000 == 0:
            pbar.set_postfix(ntok=ntok, clusters=len(cluster_canonical))
pbar.close()

n_clusters_a = len(cluster_canonical)
print(f"step A done in {time.time()-t0:.0f}s — {n_total:,} → {n_clusters_a:,} clusters")

# ---------- step B: semantic merge ----------
# Embed each Step-A canonical, compute cosine sim, merge any pair ≥ threshold.
# We need O(K^2) pair comparisons; faster path = brute-force GPU matmul on the
# embedding matrix. K ≈ 100k expected; 100k^2 floats = 40GB — too big.
# So: bucket by first-token-letter for a coarse pre-filter, then exact within bucket.
#   - Most semantic matches share the head noun's first letter (chicken/chicken,
#     pho/pho). Loses some cross-letter synonyms but keeps O(N) memory bounded.
if not RUN_STEP_B:
    print("\nstep B — SKIPPED (RUN_STEP_B = False)")
    parent = list(range(n_clusters_a))
    n_merges = 0
else:
    print(f"\nstep B — semantic merge (cosine ≥ {SEMANTIC_THRESHOLD}) via {EMBED_MODEL}")
    print("  loading model...")
    from sentence_transformers import SentenceTransformer

    device = "mps"
    model = SentenceTransformer(EMBED_MODEL, device=device)
    print(f"  encoding {n_clusters_a:,} canonicals on {device}...")
    t0 = time.time()
    embs = model.encode(
        cluster_canonical,
        batch_size=256,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    print(f"  encoded in {time.time()-t0:.0f}s, shape={embs.shape}")

    buckets = defaultdict(list)
    for cid, c in enumerate(cluster_canonical):
        head = c.split()[0] if c.split() else ""
        key = head[:1].lower() if head else "_"
        buckets[key].append(cid)

    print(f"  {len(buckets)} first-letter buckets, max bucket size = {max(len(v) for v in buckets.values()):,}")

    parent = list(range(n_clusters_a))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if cluster_count[ra] >= cluster_count[rb]:
            parent[rb] = ra
        else:
            parent[ra] = rb

    t0 = time.time()
    n_merges = 0
    for key, cids in tqdm(sorted(buckets.items()), desc="step B semantic", unit="bucket"):
        if len(cids) < 2:
            continue
        sub = embs[cids]
        sim = sub @ sub.T
        M = len(cids)
        iu, ju = np.triu_indices(M, k=1)
        mask = sim[iu, ju] >= SEMANTIC_THRESHOLD
        for i, j in zip(iu[mask], ju[mask]):
            union(cids[int(i)], cids[int(j)])
            n_merges += 1

    print(f"step B done in {time.time()-t0:.0f}s — {n_merges:,} pair merges")

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

# Compress union-find roots → final cluster ids
final_root = [find(i) for i in range(n_clusters_a)]
unique_roots = sorted(set(final_root))
root_to_final = {r: i for i, r in enumerate(unique_roots)}
n_clusters_b = len(unique_roots)
print(f"final cluster count: {n_clusters_a:,} → {n_clusters_b:,}")

# Pick canonical per final cluster = most-common name (alias_count desc, name asc)
final_aliases = defaultdict(list)   # final_cid -> [(name, count, step_a_cid), ...]
for name, a_cid in name_to_cluster.items():
    f_cid = root_to_final[final_root[a_cid]]
    final_aliases[f_cid].append((name, counts[name], a_cid))

final_canonical = {}
for f_cid, items in final_aliases.items():
    items.sort(key=lambda x: (-x[1], x[0]))
    final_canonical[f_cid] = items[0][0]

# ---------- write outputs ----------
print(f"\nwriting {OUT_ALIASES}")
with open(OUT_ALIASES, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["canonical_name", "alias_name", "alias_count", "cluster_id", "method"])
    for f_cid in sorted(final_aliases.keys(), key=lambda c: -sum(x[1] for x in final_aliases[c])):
        canon = final_canonical[f_cid]
        canon_a_cid = name_to_cluster[canon]
        for name, cnt, a_cid in sorted(final_aliases[f_cid], key=lambda x: -x[1]):
            if name == canon:
                method = "self"
            elif a_cid == canon_a_cid:
                # Same Step-A cluster as canonical → joined via fuzzy match
                method = "fuzzy"
            else:
                # Different Step-A cluster, same Step-B cluster → joined via semantic
                method = "semantic"
            w.writerow([canon, name, cnt, f_cid, method])

print(f"writing {OUT_SUMMARY}")
with open(OUT_SUMMARY, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "n_aliases", "total_count"])
    rows_out = []
    for f_cid, items in final_aliases.items():
        rows_out.append((f_cid, final_canonical[f_cid], len(items), sum(x[1] for x in items)))
    rows_out.sort(key=lambda r: -r[3])
    for r in rows_out:
        w.writerow(r)

print(f"\nDONE")
print(f"  {n_total:,} unique dish names")
print(f"  → {n_clusters_a:,} clusters after fuzzy (step A)")
print(f"  → {n_clusters_b:,} clusters after semantic merge (step B)")
print(f"  total alias-collapse: {n_total - n_clusters_b:,} ({100*(n_total - n_clusters_b)/n_total:.1f}%)")
