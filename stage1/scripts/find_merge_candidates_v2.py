"""Layer 17 stage 1 — second-pass candidate generation against v9 canonicals.

Same algorithm as find_merge_candidates.py, but reading the post-Layer-16
state. After 14/15/16, many former singletons are now bigger clusters and new
merge opportunities exist.
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

IN  = dpath("dish_canonical_summary_v9.csv")
OUT = dpath("merge_candidates_v2.csv")

MIN_TARGET_COUNT  = 5
SINGLETON_MAX_CNT = 1
MIN_TOKENS        = 2
MAX_TOKENS        = 6
MIN_OVERLAP_RATIO = 0.60
TOP_K             = 3

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

token_to_targets = defaultdict(list)
n_targets = 0
for cid, name, cnt in clusters:
    if cnt < MIN_TARGET_COUNT:
        continue
    toks = set(name.split())
    for t in toks:
        token_to_targets[t].append((cid, name, cnt, toks))
    n_targets += 1
print(f"target pool (count >= {MIN_TARGET_COUNT}): {n_targets:,}")

candidates = []
n_singletons_considered = 0
n_singletons_with_match = 0
for cid, name, cnt in clusters:
    if cnt > SINGLETON_MAX_CNT:
        continue
    toks = set(name.split())
    if not (MIN_TOKENS <= len(toks) <= MAX_TOKENS):
        continue
    n_singletons_considered += 1
    seen = {}
    for t in toks:
        for (tcid, tname, tcnt, ttoks) in token_to_targets.get(t, []):
            if tcid == cid:
                continue
            if tcid not in seen:
                seen[tcid] = (tname, tcnt, ttoks)
    if not seen:
        continue
    scored = []
    for tcid, (tname, tcnt, ttoks) in seen.items():
        shared = toks & ttoks
        ratio = len(shared) / len(toks)
        if ratio < MIN_OVERLAP_RATIO:
            continue
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
    candidates.sort(key=lambda r: (-r[6], -r[4]))
    for r in candidates:
        w.writerow(r)
print(f"\nwrote {OUT}")
