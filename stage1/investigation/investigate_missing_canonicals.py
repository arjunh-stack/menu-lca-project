"""Investigate the gap: 114,920 canonicals in v13 vs 107,794 in menu_dishes.

Find the missing canonicals, look at their aliases, and figure out why each
alias fails to appear when we re-scan raw menus.
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
import os
import sqlite3
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
ALIASES    = dpath("dish_aliases_v13.csv")
SUMM       = dpath("dish_canonical_summary_v13.csv")
INDEX      = dpath("menu_dishes.sqlite")
SYNONYMS   = dpath("synonyms.csv")

# 1) Vocabulary from v13 summary
vocab = set()
canon_to_count = {}
with open(SUMM) as f:
    for row in csv.DictReader(f):
        vocab.add(row["canonical_name"])
        canon_to_count[row["canonical_name"]] = int(row["total_count"])
print(f"v13 vocabulary:                  {len(vocab):,}")

# 2) Canonicals appearing in built menu_dishes
con = sqlite3.connect(INDEX)
appearing = {row[0] for row in con.execute("SELECT DISTINCT canonical_dish FROM menu_dishes")}
con.close()
print(f"appearing in menu_dishes:        {len(appearing):,}")

missing = vocab - appearing
print(f"missing (in vocab, not seen):    {len(missing):,}")
print(f"alien (in seen, not in vocab):   {len(appearing - vocab):,}  (should be 0)")

# 3) Build canonical -> [(alias_name, alias_count)] map from v13 alias key
canon_to_aliases = defaultdict(list)
alias_to_canon = {}
with open(ALIASES) as f:
    for row in csv.DictReader(f):
        canon_to_aliases[row["canonical_name"]].append((row["alias_name"], int(row["alias_count"])))
        alias_to_canon[row["alias_name"]] = row["canonical_name"]
print(f"\ndistinct alias_name strings:     {len(alias_to_canon):,}")

# 4) Replicate the index-time normalizer to compute which aliases would match
syn_map = {}
with open(SYNONYMS) as f:
    for row in csv.DictReader(f):
        if row["notes"].strip().upper().startswith("APPLY"):
            a = row["alias_token"].strip().lower()
            c = row["canonical_token"].strip().lower()
            if a != c:
                syn_map[a] = c

def lookup_key(menu_name, menu_category):
    base = normalize_with_format(menu_name, menu_category)
    if not base:
        return None
    toks = [syn_map.get(t, t) for t in base.split()]
    return " ".join(sorted(set(toks)))

# 5) Re-scan raw menus, producing a multiset: lookup_key -> [restaurant_excluded?, cat_excluded?, matched?]
con = sqlite3.connect(DB)
exclude_tags = load_exclude_tags()
excluded_rids = excluded_restaurant_ids(con, exclude_tags)
excluded_menu_cats = load_excluded_menu_categories()

# For each alias_name in v13, count: (a) how often it's produced by some raw menu row,
# split by what filtered the producing rows.
alias_seen_kept = Counter()        # produced by a row that survived L1+L2
alias_seen_l1   = Counter()        # produced only by rows filtered at L1 (restaurant)
alias_seen_l2   = Counter()        # produced only by rows filtered at L2 (menu cat)
alias_unseen    = set(alias_to_canon.keys())

print("\nscanning raw menus...")
n_total = 0
cur = con.execute("SELECT restaurant_id, category, name FROM menus")
for rid, mcat, mname in cur:
    n_total += 1
    if n_total % 500_000 == 0:
        print(f"  {n_total:,} rows scanned, unseen aliases remaining: {len(alias_unseen):,}")
    key = lookup_key(mname, mcat)
    if not key:
        continue
    if key not in alias_to_canon:
        continue
    # this raw row produces a key matching a v13 alias
    alias_unseen.discard(key)
    if rid in excluded_rids:
        alias_seen_l1[key] += 1
    elif mcat in excluded_menu_cats:
        alias_seen_l2[key] += 1
    else:
        alias_seen_kept[key] += 1
con.close()
print(f"  done. {n_total:,} rows scanned")
print(f"\naliases never produced by any raw menu row: {len(alias_unseen):,}")

# 6) Per missing canonical, classify why it's missing
n_missing = len(missing)
n_only_l1 = 0          # all aliases come only from L1-excluded restaurants
n_only_l2 = 0          # all aliases come only from L2-excluded categories
n_only_l1_l2 = 0       # mix of L1/L2, but no kept rows
n_no_raw_match = 0     # NO raw row produces any of the canonical's aliases (normalizer drift)
n_partial = 0          # at least one alias matched a kept row, but canonical still missed (?)
examples = {"only_l1": [], "only_l2": [], "only_l1_l2": [], "no_raw_match": [], "partial": []}

for canon in missing:
    aliases = canon_to_aliases[canon]
    kept = sum(alias_seen_kept[a] for a, _ in aliases)
    l1   = sum(alias_seen_l1[a]   for a, _ in aliases)
    l2   = sum(alias_seen_l2[a]   for a, _ in aliases)
    raw_total = kept + l1 + l2
    if raw_total == 0:
        n_no_raw_match += 1
        if len(examples["no_raw_match"]) < 8:
            examples["no_raw_match"].append((canon, aliases[:3]))
    elif kept > 0:
        n_partial += 1
        if len(examples["partial"]) < 8:
            examples["partial"].append((canon, kept, l1, l2))
    elif l1 > 0 and l2 == 0:
        n_only_l1 += 1
        if len(examples["only_l1"]) < 8:
            examples["only_l1"].append((canon, l1, aliases[:3]))
    elif l2 > 0 and l1 == 0:
        n_only_l2 += 1
        if len(examples["only_l2"]) < 8:
            examples["only_l2"].append((canon, l2, aliases[:3]))
    else:
        n_only_l1_l2 += 1
        if len(examples["only_l1_l2"]) < 8:
            examples["only_l1_l2"].append((canon, l1, l2))

print(f"\n=== Missing-canonical breakdown (of {n_missing:,}) ===")
print(f"  no raw row produces any alias       : {n_no_raw_match:>6,}  ← normalizer/data drift since v13 was built")
print(f"  all-aliases from L1-excluded only   : {n_only_l1:>6,}  ← restaurant categories that got excluded")
print(f"  all-aliases from L2-excluded only   : {n_only_l2:>6,}  ← menu categories that got excluded")
print(f"  mix of L1+L2 only (no kept)         : {n_only_l1_l2:>6,}  ← combination of above")
print(f"  partial: at least one kept (BUG?)   : {n_partial:>6,}  ← shouldn't happen, indicates lookup-time bug")

print("\n=== Sample: no_raw_match (likely normalizer drift) ===")
for canon, alis in examples["no_raw_match"]:
    print(f"  canonical: '{canon}'")
    for a, c in alis:
        print(f"     alias: '{a}'  (alias_count={c})")
print("\n=== Sample: only_l1 (raw rows exist but restaurant excluded) ===")
for canon, l1, alis in examples["only_l1"]:
    print(f"  canonical: '{canon}'  (L1-rows={l1})")
    for a, c in alis:
        print(f"     alias: '{a}'  (alias_count={c})")
print("\n=== Sample: only_l2 (raw rows exist but menu_category excluded) ===")
for canon, l2, alis in examples["only_l2"]:
    print(f"  canonical: '{canon}'  (L2-rows={l2})")
    for a, c in alis:
        print(f"     alias: '{a}'  (alias_count={c})")
print("\n=== Sample: only_l1_l2 (mix) ===")
for canon, l1, l2 in examples["only_l1_l2"]:
    print(f"  canonical: '{canon}'  (L1={l1}, L2={l2})")
print("\n=== Sample: partial (BUG?) ===")
for canon, kept, l1, l2 in examples["partial"]:
    print(f"  canonical: '{canon}'  (kept={kept}, L1={l1}, L2={l2})")
