
# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import sqlite3
import csv
import html
from collections import Counter

DB = dpath("mydb.sqlite")

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT category FROM restaurants WHERE category IS NOT NULL AND category != ''")

individual = Counter()
combined = Counter()
for (cat,) in cur:
    cat = html.unescape(cat).strip()
    combined[cat] += 1
    for tag in cat.split(","):
        tag = tag.strip()
        if tag:
            individual[tag] += 1

print(f"unique individual category tags : {len(individual):,}")
print(f"unique full category strings    : {len(combined):,}")

out = dpath("unique_categories.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["category_tag", "restaurant_count"])
    for tag, n in individual.most_common():
        w.writerow([tag, n])
print(f"wrote {out}")
