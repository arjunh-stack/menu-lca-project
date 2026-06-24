"""Reconstruct the filtered dataset:
   restaurant (id, name, full_address, zip, lat, lng, category)
     └── menu_item (raw_name, price_usd, menu_category)
            └── canonical_dish (+ via dish_aliases_v19.csv to all alias names)

Inputs:
  - mydb.sqlite (cleaned through C1–C5)
  - dish_aliases_v19.csv (final alias key, post-Layer-25)
  - synonyms.csv (Layer 10 — APPLY-only entries) — applied to the lookup key
    so that raw 'hoagie' menu items rewrite to 'sub' before lookup.

Filtering applied (must mirror Layers 1, 2, then alias-lookup yields
post-Layer-5/7/11/12 surviving canonicals):
  - Layer 1: drop restaurants whose category contains any user-excluded tag.
  - Layer 2: drop menu rows whose menu.category is in the excluded /
    ambiguous category lists.
  - Layer 3+4+10: normalize each menu name + fold format from menus.category
    + apply synonym rewrite. The result is the lookup key.
  - If lookup key is in the alias dict → the menu row maps to a canonical
    dish that survived all later filters (Layer 5/7/11/12).
  - If not → the canonical was dropped at some later layer; menu row is
    excluded from the final index.

Outputs:
  - menu_dishes.csv — one row per (restaurant_id, menu_item):
      restaurant_id, restaurant_name, full_address, zip_code, lat, lng,
      restaurant_category, menu_category, raw_menu_name, price_usd,
      canonical_dish
  - menu_dishes.sqlite — same data loaded as a single table for easy querying.
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
import sqlite3
import os
import sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(__file__))
from dedup import (
    normalize_with_format,
    load_exclude_tags,
    load_excluded_menu_categories,
    excluded_restaurant_ids,
)

DB         = dpath("mydb.sqlite")
ALIASES    = dpath("dish_aliases_v19.csv")
SYNONYMS   = dpath("synonyms.csv")
OUT_CSV    = dpath("menu_dishes.csv")
OUT_SQLITE = dpath("menu_dishes.sqlite")

# ─── Load alias key: normalized_name → canonical_name ───
print(f"loading {ALIASES}")
alias_to_canonical = {}
with open(ALIASES) as f:
    for row in csv.DictReader(f):
        alias_to_canonical[row["alias_name"]] = row["canonical_name"]
print(f"  {len(alias_to_canonical):,} alias→canonical entries")

# ─── Load Layer-10 synonyms (APPLY-only) for token rewrite ───
syn_map = {}
with open(SYNONYMS) as f:
    for row in csv.DictReader(f):
        if row["notes"].strip().upper().startswith("APPLY"):
            a = row["alias_token"].strip().lower()
            c = row["canonical_token"].strip().lower()
            if a != c:
                syn_map[a] = c
print(f"loaded {len(syn_map)} synonym tokens for rewrite")

def lookup_key(menu_name: str, menu_category: str) -> str | None:
    """Normalize a raw menu name through Layers 3+4+10 to produce the alias key."""
    base = normalize_with_format(menu_name, menu_category)
    if not base:
        return None
    toks = [syn_map.get(t, t) for t in base.split()]
    return " ".join(sorted(set(toks)))

# ─── Open db, load Layer-1 + Layer-2 filters ───
con = sqlite3.connect(DB)
exclude_tags = load_exclude_tags()
excluded_rids = excluded_restaurant_ids(con, exclude_tags)
excluded_menu_cats = load_excluded_menu_categories()
print(f"\nLayer 1: {len(excluded_rids):,} restaurants excluded by category tags")
print(f"Layer 2: {len(excluded_menu_cats):,} menu categories excluded")

# ─── Pull restaurants ───
print("\nloading restaurants...")
restaurants = {}
cur = con.execute("SELECT id, name, category, full_address, zip_code, lat, lng FROM restaurants")
for rid, name, cat, addr, zip_, lat, lng in cur:
    if rid in excluded_rids:
        continue
    restaurants[rid] = (name, cat, addr, zip_, lat, lng)
print(f"  kept {len(restaurants):,} restaurants after Layer 1")

# ─── Pull menus, filter, normalize, lookup ───
print("\nscanning menus, normalizing, looking up canonicals...")
out_rows = []
n_total = 0
n_excluded_layer2 = 0
n_excluded_no_restaurant = 0
n_no_match = 0
n_matched = 0
unmatched_keys = Counter()

cur = con.execute("SELECT restaurant_id, category, name, price_usd FROM menus")
for rid, mcat, mname, price in cur:
    n_total += 1
    if rid not in restaurants:
        n_excluded_no_restaurant += 1
        continue
    if mcat in excluded_menu_cats:
        n_excluded_layer2 += 1
        continue
    key = lookup_key(mname, mcat)
    if not key:
        n_no_match += 1
        continue
    canonical = alias_to_canonical.get(key)
    if canonical is None:
        n_no_match += 1
        if len(unmatched_keys) < 50:
            unmatched_keys[key] += 1
        continue
    n_matched += 1
    rest = restaurants[rid]
    # rest = (name, cat, addr, zip_, lat, lng)
    out_rows.append((
        rid, rest[0], rest[2], rest[3], rest[4], rest[5], rest[1],
        mcat, mname, price, canonical,
    ))

print(f"\nmenu rows scanned:          {n_total:>10,}")
print(f"  excluded (Layer 1 rest):  {n_excluded_no_restaurant:>10,}")
print(f"  excluded (Layer 2 cat):   {n_excluded_layer2:>10,}")
print(f"  no canonical match:       {n_no_match:>10,}  (filtered at L5/L7/L11/L12, or unparseable)")
print(f"  MATCHED → output:         {n_matched:>10,}")

# ─── Write CSV ───
print(f"\nwriting {OUT_CSV}")
with open(OUT_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "restaurant_id", "restaurant_name", "full_address", "zip_code",
        "lat", "lng", "restaurant_category",
        "menu_category", "raw_menu_name", "price_usd", "canonical_dish",
    ])
    for r in out_rows:
        w.writerow(r)
print(f"  {len(out_rows):,} rows")

# ─── Load to SQLite ───
print(f"\nwriting {OUT_SQLITE}")
if os.path.exists(OUT_SQLITE):
    os.remove(OUT_SQLITE)
out = sqlite3.connect(OUT_SQLITE)
out.execute("""
CREATE TABLE menu_dishes (
    restaurant_id INTEGER,
    restaurant_name TEXT,
    full_address TEXT,
    zip_code TEXT,
    lat REAL,
    lng REAL,
    restaurant_category TEXT,
    menu_category TEXT,
    raw_menu_name TEXT,
    price_usd REAL,
    canonical_dish TEXT
)
""")
out.executemany("INSERT INTO menu_dishes VALUES (?,?,?,?,?,?,?,?,?,?,?)", out_rows)
out.execute("CREATE INDEX idx_canonical ON menu_dishes(canonical_dish)")
out.execute("CREATE INDEX idx_zip ON menu_dishes(zip_code)")
out.execute("CREATE INDEX idx_restaurant ON menu_dishes(restaurant_id)")
out.commit()

# Distinct counts
n_rest = out.execute("SELECT COUNT(DISTINCT restaurant_id) FROM menu_dishes").fetchone()[0]
n_dish = out.execute("SELECT COUNT(DISTINCT canonical_dish) FROM menu_dishes").fetchone()[0]
n_zip  = out.execute("SELECT COUNT(DISTINCT zip_code) FROM menu_dishes").fetchone()[0]
print(f"\nfinal stats:")
print(f"  rows: {len(out_rows):,}")
print(f"  distinct restaurants: {n_rest:,}")
print(f"  distinct canonical dishes: {n_dish:,}")
print(f"  distinct zip codes: {n_zip:,}")

out.close()
con.close()
print("\nDONE")
