"""Layer 14 stage 1 — find candidate merges between long-tail singletons and
high-frequency canonicals using a token-overlap inverted index.

Approach:
  - Build inverted index from token → list of (cluster_id, canonical, count)
    over all clusters with count >= MIN_TARGET_COUNT (the merge-target pool).
  - For each singleton (count == 1) with 2–6 tokens:
      - Look up candidate targets via shared tokens (union of cluster_ids
        whose token list intersects the singleton's tokens).
      - Score each candidate: |shared_tokens| / |singleton_tokens|
      - Keep only candidates with score >= MIN_OVERLAP_RATIO and target
        count >= MIN_TARGET_COUNT.
      - Sort by (score desc, target_count desc), take top TOP_K per singleton.

Output:
  merge_candidates.csv — one row per pair:
    singleton_cid, singleton_name, target_cid, target_name, target_count,
    shared_tokens, overlap_ratio
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
from collections import defaultdict

IN  = dpath("dish_canonical_summary_v6.csv")
OUT = dpath("merge_candidates.csv")

MIN_TARGET_COUNT  = 5      # only suggest merging into clusters with >=5 instances
SINGLETON_MAX_CNT = 1      # which clusters are "singletons" (the source pool)
MIN_TOKENS        = 2      # ignore 1-token singletons (mostly real foreign dishes already)
MAX_TOKENS        = 6      # ignore longer ones (likely fragments, not merge candidates)
MIN_OVERLAP_RATIO = 0.60   # shared / singleton_tokens must be >= this
TOP_K             = 3      # keep top-K candidates per singleton

clusters = []
with open(IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        clusters.append((cid, row["canonical_name"], cnt))
print(f"loaded {len(clusters):,} clusters")

# Build inverted token index over targets
token_to_targets = defaultdict(list)  # token -> [(cid, name, count, token_set)]
n_targets = 0
for cid, name, cnt in clusters:
    if cnt < MIN_TARGET_COUNT:
        continue
    toks = set(name.split())
    for t in toks:
        token_to_targets[t].append((cid, name, cnt, toks))
    n_targets += 1
print(f"target pool (count >= {MIN_TARGET_COUNT}): {n_targets:,} clusters")
print(f"index: {len(token_to_targets):,} unique tokens")

# Walk singletons
candidates = []  # (singleton_cid, singleton_name, target_cid, target_name, target_count, shared, ratio)
n_singletons_considered = 0
n_singletons_with_match = 0
for cid, name, cnt in clusters:
    if cnt > SINGLETON_MAX_CNT:
        continue
    toks = set(name.split())
    if not (MIN_TOKENS <= len(toks) <= MAX_TOKENS):
        continue
    n_singletons_considered += 1
    # Aggregate target candidates by cid
    seen_targets = {}  # tcid -> (target_name, target_count, target_toks)
    for t in toks:
        for (tcid, tname, tcnt, ttoks) in token_to_targets.get(t, []):
            if tcid == cid:
                continue
            if tcid not in seen_targets:
                seen_targets[tcid] = (tname, tcnt, ttoks)
    if not seen_targets:
        continue
    scored = []
    for tcid, (tname, tcnt, ttoks) in seen_targets.items():
        shared = toks & ttoks
        ratio = len(shared) / len(toks)
        if ratio < MIN_OVERLAP_RATIO:
            continue
        # also require that target's token-set is similar in size (not >2x bigger, to avoid generic matches)
        if len(ttoks) > 2 * len(toks):
            continue
        scored.append((tcid, tname, tcnt, sorted(shared), ratio))
    if not scored:
        continue
    scored.sort(key=lambda x: (-x[4], -x[2]))
    for s in scored[:TOP_K]:
        candidates.append((cid, name, s[0], s[1], s[2], " ".join(s[3]), s[4]))
    n_singletons_with_match += 1

print(f"\nsingletons considered (2-6 tokens): {n_singletons_considered:,}")
print(f"singletons with >=1 candidate match: {n_singletons_with_match:,}")
print(f"total candidate pairs: {len(candidates):,}")

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "singleton_cid", "singleton_name",
        "target_cid", "target_name", "target_count",
        "shared_tokens", "overlap_ratio",
    ])
    candidates.sort(key=lambda r: (-r[6], -r[4]))  # by overlap_ratio desc, then target_count desc
    for r in candidates:
        w.writerow(r)
print(f"\nwrote {OUT}")
