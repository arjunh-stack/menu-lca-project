"""Split the 11k review pile into 3 chunks for parallel LLM classification."""

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
import os
import math

REVIEW = dpath("ingredients_and_numbers_review.csv")
DROPPED_AUDIT = dpath("dropped_ingredients_and_numbers.csv")
OUT_DIR = dpath("chunks_review")
N_CHUNKS = 3

os.makedirs(OUT_DIR, exist_ok=True)

# Already-dropped cluster IDs (from Layer 11A) — exclude
already_dropped = set()
with open(DROPPED_AUDIT) as f:
    for row in csv.DictReader(f):
        already_dropped.add(int(row["cluster_id"]))

# Load review pile (verdict='review')
review_rows = []
with open(REVIEW) as f:
    for row in csv.DictReader(f):
        if row["verdict"].strip().lower() != "review":
            continue
        cid = int(row["cluster_id"])
        if cid in already_dropped:
            continue
        review_rows.append((cid, row["canonical_name"], int(row["total_count"]), row["reason"]))

# Sort by count desc — so highest-impact items get reviewed in chunk 01
review_rows.sort(key=lambda r: -r[2])
print(f"loaded {len(review_rows):,} review items")

chunk_size = math.ceil(len(review_rows) / N_CHUNKS)
for i in range(N_CHUNKS):
    chunk = review_rows[i*chunk_size : (i+1)*chunk_size]
    if not chunk:
        break
    path = f"{OUT_DIR}/chunk_{i+1:02d}.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id", "canonical_name", "total_count", "flagged_reason"])
        for r in chunk:
            w.writerow(r)
    print(f"  chunk_{i+1:02d}: {len(chunk):,} rows  →  {path}")
