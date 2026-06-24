"""Layer 8 — drop pathological long-fragment rows from unique_dishes_mains_v2.csv.

A row is a long fragment if it has too many tokens or too many repeated tokens
(signs of an alphabetized concatenation of an entire menu section).

Rules (drop if ANY hit):
  - >12 tokens total
  - any single token appears >=3 times
  - >=2 tokens that each appear >=2 times
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
from collections import Counter

IN  = dpath("unique_dishes_mains_v2.csv")
OUT = dpath("unique_dishes_mains_v3.csv")
DROPPED = dpath("dropped_long_fragments.csv")

MAX_TOKENS = 12

kept = 0
dropped = 0
dropped_rows_count = 0

with open(IN) as f, open(OUT, "w", newline="") as g, open(DROPPED, "w", newline="") as d:
    r = csv.reader(f)
    w = csv.writer(g)
    dw = csv.writer(d)
    header = next(r)
    w.writerow(header)
    dw.writerow(["reason", "normalized_name", "count"])
    for row in r:
        if not row or len(row) < 2:
            continue
        name = row[0]
        cnt_str = row[1] if len(row) > 1 else "0"
        cnt = int(cnt_str) if cnt_str.isdigit() else 0
        toks = name.split()
        n = len(toks)
        c = Counter(toks)
        max_rep = max(c.values()) if c else 0
        n_repeated = sum(1 for v in c.values() if v >= 2)

        is_fragment = (
            n > MAX_TOKENS
            or max_rep >= 3
            or n_repeated >= 2
        )
        if is_fragment:
            dropped += 1
            dropped_rows_count += cnt
            dw.writerow([
                f"tokens={n} max_rep={max_rep} repeated={n_repeated}",
                name,
                cnt,
            ])
        else:
            kept += 1
            w.writerow(row)

print(f"kept   : {kept:,}")
print(f"dropped: {dropped:,}  (sum-of-counts: {dropped_rows_count:,})")
print(f"\nwrote {OUT}")
print(f"wrote {DROPPED}")
