"""For a few bare-protein dish names, show category coverage and what categories they live in."""

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
from dedup import load_exclude_tags, excluded_restaurant_ids, load_excluded_menu_categories

DB = dpath("mydb.sqlite")
PROTEINS = ["Tuna", "Chicken", "Roast Beef", "Salmon", "Turkey", "Ham", "Italian", "Steak", "Shrimp", "Pepperoni"]

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

for p in PROTEINS:
    cur.execute("""
        SELECT category, COUNT(*) FROM menus
        WHERE TRIM(name) = ?
          AND restaurant_id NOT IN (SELECT id FROM _bad)
          AND (category IS NULL OR category NOT IN (SELECT cat FROM _bad_cats))
        GROUP BY category ORDER BY 2 DESC
    """, (p,))
    rows = cur.fetchall()
    total = sum(n for _, n in rows)
    null_n = sum(n for c, n in rows if c is None or c == "")
    print(f"\n=== {p!r} ({total} rows, {null_n} no-category) ===")
    for cat, n in rows[:8]:
        print(f"  {n:>5}  {cat or '(NULL)'}")
