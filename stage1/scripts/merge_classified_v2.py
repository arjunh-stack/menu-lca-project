"""Merge all 30 v2-classified chunks → unique_dishes_classified_v2.csv (audit) +
unique_dishes_mains_v2.csv (only keepers, the strict-pass dish list)."""

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

CHUNK_DIR = dpath("chunks_classified_v2")
ALL_OUT   = dpath("unique_dishes_classified_v2.csv")
KEEP_OUT  = dpath("unique_dishes_mains_v2.csv")

files = sorted(glob.glob(f"{CHUNK_DIR}/chunk_*_classified.csv"))
print(f"merging {len(files)} chunk files")

reason_counts = Counter()
verdict_counts = Counter()
all_rows = []
keep_rows = []

for path in files:
    with open(path) as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if not row or len(row) < 4:
                continue
            verdict, reason, name, cnt = row[0], row[1], row[2], row[3]
            verdict_counts[verdict] += 1
            reason_counts[reason] += 1
            all_rows.append([verdict, reason, name, cnt])
            if verdict.strip().lower() == "keep":
                try:
                    keep_rows.append([name, int(cnt)])
                except ValueError:
                    keep_rows.append([name, 0])

with open(ALL_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["verdict", "reason", "normalized_name", "count"])
    w.writerows(all_rows)

keep_rows.sort(key=lambda r: -r[1])
with open(KEEP_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["normalized_name", "count"])
    for name, cnt in keep_rows:
        w.writerow([name, cnt])

print(f"\ntotal rows processed: {len(all_rows):,}")
print(f"verdict counts:")
for v, n in verdict_counts.most_common():
    print(f"  {v:>10}: {n:>7,}  ({100*n/len(all_rows):.1f}%)")
print(f"\nreason counts:")
for r, n in reason_counts.most_common():
    print(f"  {r:>15}: {n:>7,}  ({100*n/len(all_rows):.1f}%)")
print(f"\n→ wrote {ALL_OUT} ({len(all_rows):,} rows, full audit)")
print(f"→ wrote {KEEP_OUT} ({len(keep_rows):,} rows, strict pass)")
