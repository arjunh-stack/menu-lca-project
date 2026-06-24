"""Layer 11B — merge 3 LLM-classified review chunks and apply drops to the
post-Layer-11A v3 dataset.

Reads:
  - chunks_review_classified/chunk_{01,02,03}_classified.csv (verdict, reason)
  - dish_aliases_v3.csv (post-11A alias key)
  - dish_canonical_summary_v3.csv (post-11A canonical list)

Writes:
  - dish_aliases_v4.csv (post-11B alias key)
  - dish_canonical_summary_v4.csv (post-11B canonical list)
  - review_classified_merged.csv (full audit, all 10,779 rows + verdicts)
  - dropped_review.csv (just the drops, sorted by count desc)
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
import glob
from collections import Counter

CHUNKS = dpath("chunks_review_classified")
ALIAS_IN  = dpath("dish_aliases_v3.csv")
SUMM_IN   = dpath("dish_canonical_summary_v3.csv")
ALIAS_OUT = dpath("dish_aliases_v4.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v4.csv")
MERGED    = dpath("review_classified_merged.csv")
DROPPED   = dpath("dropped_review.csv")

# Merge chunk outputs
all_rows = []
for path in sorted(glob.glob(f"{CHUNKS}/chunk_*_classified.csv")):
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                cid = int(row["cluster_id"])
                cnt = int(row["total_count"])
            except (ValueError, KeyError):
                continue
            all_rows.append((cid, row["canonical_name"], cnt, row["verdict"].strip().lower(), row["reason"]))
print(f"loaded {len(all_rows):,} classified review rows")

verdict_counts = Counter(r[3] for r in all_rows)
reason_counts = Counter(r[4] for r in all_rows if r[3] == "drop")
print(f"verdicts: {dict(verdict_counts)}")
print(f"drop reasons: {dict(reason_counts)}")

drop_cids = {r[0]: (r[1], r[2], r[4]) for r in all_rows if r[3] == "drop"}
print(f"\n{len(drop_cids):,} cluster_ids to drop")

# Write full audit
with open(MERGED, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "verdict", "reason"])
    for r in sorted(all_rows, key=lambda r: -r[2]):
        w.writerow(r)

with open(DROPPED, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "reason"])
    for cid, (canon, cnt, reason) in sorted(drop_cids.items(), key=lambda x: -x[1][1]):
        w.writerow([cid, canon, cnt, reason])

# Filter alias table
kept_alias = 0
dropped_alias = 0
dropped_total = 0
with open(ALIAS_IN) as f, open(ALIAS_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in drop_cids:
            dropped_alias += 1
            try:
                dropped_total += int(row["alias_count"])
            except ValueError:
                pass
        else:
            kept_alias += 1
            w.writerow([row[k] for k in r.fieldnames])
print(f"\nalias rows: kept {kept_alias:,}, dropped {dropped_alias:,} (sum-of-counts {dropped_total:,})")

# Filter summary
kept_clusters = 0
with open(SUMM_IN) as f, open(SUMM_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in drop_cids:
            continue
        kept_clusters += 1
        w.writerow([row[k] for k in r.fieldnames])
print(f"clusters: kept {kept_clusters:,}")

print(f"\nwrote {ALIAS_OUT}")
print(f"wrote {SUMM_OUT}")
print(f"wrote {MERGED}")
print(f"wrote {DROPPED}")
