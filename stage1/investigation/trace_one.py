
# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import sys
import sqlite3
from collections import Counter
from dedup import normalize, load_exclude_tags, excluded_restaurant_ids, load_excluded_menu_categories

DB = dpath("mydb.sqlite")
target = sys.argv[1] if len(sys.argv) > 1 else "tuna"

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
    SELECT m.name, m.category FROM menus m
    WHERE m.restaurant_id NOT IN (SELECT id FROM _bad)
      AND (m.category IS NULL OR m.category NOT IN (SELECT cat FROM _bad_cats))
""")

raws = Counter()
cats = Counter()
for name, cat in cur:
    if not name:
        continue
    if normalize(name) == target:
        raws[name.strip()] += 1
        cats[cat or "(none)"] += 1

print(f"=== {target!r} ← {sum(raws.values()):,} rows / {len(raws):,} distinct raw names ===")
for raw, cnt in raws.most_common(20):
    print(f"  {cnt:>5}  {raw}")
print(f"\n  most common menu.category for these rows:")
for c, cnt in cats.most_common(10):
    print(f"  {cnt:>5}  {c}")
