"""Layer 16 — drop canonicals containing meal / dinner tokens.

Same pattern as Layer 12 (sides/combos): canonicals with these tokens are
almost always chain meal-deal redundancies of the underlying dish.

Examples that will drop:
  chicken meal mixed (1420) - chicken with mixed sides as a meal deal
  meal whopper (1191)        - same as whopper
  burger meal whopper (832)  - same as whopper
  chicken dinner (989)       - chicken served as dinner
  dinner handcrafted tenders (600) - same as handcrafted tenders
  dinner roasted turkey (245) - same as roasted turkey

DROP_TOKENS = {meal, meals, dinner, dinners}
NOT included: 'lunch'/'breakfast' (could carry distinct meaning),
              'platter' (real format word — seafood platter, kabob platter),
              'special' (mixed — too risky without LLM judgment)

Inputs:  dish_aliases_v8.csv, dish_canonical_summary_v8.csv
Outputs: dish_aliases_v9.csv, dish_canonical_summary_v9.csv, dropped_meal_dinner.csv
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

ALIAS_IN  = dpath("dish_aliases_v8.csv")
SUMM_IN   = dpath("dish_canonical_summary_v8.csv")
ALIAS_OUT = dpath("dish_aliases_v9.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v9.csv")
DROPPED   = dpath("dropped_meal_dinner.csv")

DROP_TOKENS = {"meal", "meals", "dinner", "dinners"}

clusters = []
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        clusters.append((cid, row["canonical_name"], cnt))
print(f"loaded {len(clusters):,} clusters")

drop_cids = {}
for cid, canon, cnt in clusters:
    toks = set(canon.split())
    hit = toks & DROP_TOKENS
    if hit:
        drop_cids[cid] = (canon, cnt, sorted(hit)[0])
print(f"flagged {len(drop_cids):,} clusters for drop")

token_counts = Counter(reason for _, (_, _, reason) in drop_cids.items())
print(f"\ndrop counts by trigger token:")
for tok, n in token_counts.most_common():
    print(f"  {tok:>10}: {n:>6,}")

kept_alias = 0
dropped_alias = 0
dropped_total = 0
with open(ALIAS_IN) as f, open(ALIAS_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in drop_cids:
            dropped_alias += 1
            try:
                dropped_total += int(row["alias_count"])
            except ValueError:
                pass
        else:
            kept_alias += 1
            w.writerow([row[k] for k in r.fieldnames])
print(f"\nalias rows: kept {kept_alias:,}, dropped {dropped_alias:,} (sum-of-counts {dropped_total:,})")

kept_clusters = 0
with open(SUMM_IN) as f, open(SUMM_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in drop_cids:
            continue
        kept_clusters += 1
        w.writerow([row[k] for k in r.fieldnames])
print(f"clusters: kept {kept_clusters:,}")

with open(DROPPED, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "trigger_token"])
    for cid, (canon, cnt, tok) in sorted(drop_cids.items(), key=lambda x: -x[1][1]):
        w.writerow([cid, canon, cnt, tok])

print(f"\nwrote {ALIAS_OUT}")
print(f"wrote {SUMM_OUT}")
print(f"wrote {DROPPED}")
