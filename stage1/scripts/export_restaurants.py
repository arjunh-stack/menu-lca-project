"""Export restaurants kept after Layer 1 (user-defined per-tag exclusion)."""

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

DB = dpath("mydb.sqlite")
EXCLUDE_FILE = dpath("unique_categories_to_exclude.csv")
OUT = dpath("restaurants_filtered.csv")


def load_exclude_tags():
    tags = set()
    with open(EXCLUDE_FILE) as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) >= 2 and row[1].strip().lower() == "x":
                tags.add(html.unescape(row[0]).strip())
    return tags


def main():
    exclude = load_exclude_tags()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT id, name, category, full_address FROM restaurants ORDER BY name")
    kept = 0
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "category", "full_address"])
        for rid, name, cat, addr in cur:
            if cat:
                tags = {t.strip() for t in html.unescape(cat).split(",")}
                if tags & exclude:
                    continue
            w.writerow([rid, name, cat or "", addr or ""])
            kept += 1
    print(f"wrote {kept:,} restaurants to {OUT}")


if __name__ == "__main__":
    main()
