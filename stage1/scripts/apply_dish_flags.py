"""
Layer 5 — drop normalized dishes flagged X or ? in unique_dishes_flagged.csv.
Outputs unique_dishes_final.csv with only the dishes that look real.
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

IN  = dpath("unique_dishes_flagged.csv")
OUT = dpath("unique_dishes_final.csv")

kept = 0
dropped_x = 0
dropped_q = 0
dropped_rows = 0

with open(IN) as f, open(OUT, "w", newline="") as g:
    r = csv.reader(f)
    w = csv.writer(g)
    next(r, None)  # skip header
    w.writerow(["normalized_name", "count"])
    for row in r:
        if not row:
            continue
        flag = row[0].strip().lower()
        name = row[1]
        cnt_str = row[2] if len(row) > 2 else "0"
        cnt = int(cnt_str) if cnt_str.isdigit() else 0
        if flag == "x":
            dropped_x += 1
            dropped_rows += cnt
        elif flag == "?":
            dropped_q += 1
            dropped_rows += cnt
        else:
            kept += 1
            w.writerow([name, cnt])

print(f"kept       : {kept:,}")
print(f"dropped X  : {dropped_x:,}")
print(f"dropped ?  : {dropped_q:,}")
print(f"menu rows dropped (sum of counts): {dropped_rows:,}")
print(f"\nwrote {OUT}")
