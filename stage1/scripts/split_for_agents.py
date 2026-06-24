"""Split unique_dishes_final.csv into 30 chunks for parallel agent classification."""

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
import math

IN  = dpath("unique_dishes_final.csv")
OUT_DIR = dpath("chunks")
N_CHUNKS = 30

with open(IN) as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]
print(f"total rows: {len(data):,}")

chunk_size = math.ceil(len(data) / N_CHUNKS)
print(f"chunk size: {chunk_size:,}")

for i in range(N_CHUNKS):
    chunk = data[i * chunk_size : (i + 1) * chunk_size]
    if not chunk:
        break
    path = f"{OUT_DIR}/chunk_{i+1:02d}.csv"
    with open(path, "w", newline="") as g:
        w = csv.writer(g)
        w.writerow(header)
        w.writerows(chunk)
    print(f"  chunk_{i+1:02d}: {len(chunk):,} rows  →  {path}")
