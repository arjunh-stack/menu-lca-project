"""Show the raw menu names that collapse into a few suspicious normalized buckets."""

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
from collections import Counter
from dedup import normalize, load_exclude_tags, excluded_restaurant_ids, load_excluded_menu_categories

DB = dpath("mydb.sqlite")
SUSPICIOUS = ["italian", "boneless", "cut", "bucket", "handcrafted", "chicken"]

con = sqlite3.connect(DB)
cur = con.cursor()
bad = excluded_restaurant_ids(con, load_exclude_tags())
bad_cats = load_excluded_menu_categories()
cur.execute("DROP TABLE IF EXISTS _bad")
cur.execute("CREATE TEMP TABLE _bad (id INTEGER PRIMARY KEY)")
cur.executemany("INSERT INTO _bad VALUES (?)", ((i,) for i in bad))
cur.execute("DROP TABLE IF EXISTS _bad_cats")
cur.execute("CREATE TEMP TABLE _bad_cats (cat TEXT PRIMARY KEY)")
cur.executemany("INSERT OR IGNORE INTO _bad_cats VALUES (?)", ((c,) for c in bad_cats))
cur.execute("""
    SELECT m.name FROM menus m
    WHERE m.restaurant_id NOT IN (SELECT id FROM _bad)
      AND (m.category IS NULL OR m.category NOT IN (SELECT cat FROM _bad_cats))
""")

buckets = {s: Counter() for s in SUSPICIOUS}
for (name,) in cur:
    if not name:
        continue
    n = normalize(name)
    if n in buckets:
        buckets[n][name.strip()] += 1

for key, raws in buckets.items():
    print(f"\n=== '{key}' ← {sum(raws.values()):,} rows / {len(raws):,} distinct raw names ===")
    for raw, cnt in raws.most_common(8):
        print(f"  {cnt:>5}  {raw}")
