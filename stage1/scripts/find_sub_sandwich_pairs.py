"""Layer 18 stage 1 — find canonical pairs that differ only by sub/sandwich tokens.

For each canonical, compute its "skeleton" = sorted tokens with all of
{sub, subs, sandwich, sandwiches} stripped. Group canonicals by skeleton; any
group with ≥2 distinct canonicals (each with ≥1 sub/sandwich token in original)
yields candidate merge pairs.

We then emit pairs (singleton_lower_count, target_higher_count) so the apply
script merges into the bigger one.

Inputs:  dish_canonical_summary_v10.csv
Outputs: sub_sandwich_candidates.csv
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

IN  = dpath("dish_canonical_summary_v10.csv")
OUT = dpath("sub_sandwich_candidates.csv")

STRIP = {"sub", "subs", "sandwich", "sandwiches"}
MIN_SKELETON_TOKENS = 1  # require at least 1 non-format token (e.g. "italian")

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

skeleton_to_clusters = defaultdict(list)
for cid, name, cnt in clusters:
    toks = name.split()
    has_format = any(t in STRIP for t in toks)
    skel_toks = sorted(t for t in toks if t not in STRIP)
    if len(skel_toks) < MIN_SKELETON_TOKENS:
        continue
    skel = " ".join(skel_toks)
    skeleton_to_clusters[skel].append((cid, name, cnt, has_format))

candidates = []
n_groups = 0
for skel, members in skeleton_to_clusters.items():
    if len(members) < 2:
        continue
    # require at least one member to have a format token (sub/sandwich) — otherwise
    # this isn't a sub/sandwich merge case
    if not any(m[3] for m in members):
        continue
    n_groups += 1
    members_sorted = sorted(members, key=lambda x: -x[2])
    target = members_sorted[0]
    for other in members_sorted[1:]:
        # singleton = lower-count side; target = higher-count side
        candidates.append((other[0], other[1], other[2], target[0], target[1], target[2], skel))

print(f"groups with ≥2 sub/sandwich variants: {n_groups:,}")
print(f"candidate pairs: {len(candidates):,}")

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["singleton_cid", "singleton_name", "singleton_count",
                "target_cid", "target_name", "target_count", "skeleton"])
    candidates.sort(key=lambda r: -r[5])
    for r in candidates:
        w.writerow(r)
print(f"wrote {OUT}")
