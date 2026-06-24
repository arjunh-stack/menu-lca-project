"""Layer 12 — drop canonicals containing side/snack/appetizer/combo/carte tokens.

These are dish-section indicators that survived Layers 1–11. A canonical name
containing any of these tokens is almost always a side, snack, appetizer,
combo meal, or "a la carte" item — not a main dish.

Skipped (too many false positives):
- 'sauce' / 'sauces' — used in real dish names (`chicken in garlic sauce`,
  `beef in oyster sauce` — Chinese dishes named for their sauce)
- 'dip' / 'dips' — mostly French Dip sandwiches (`dip french sandwich`)
- 'plain' — mixed (real `plain naan`, `plain dosa` vs side `plain rice`)
- 'add' / 'extra' / 'no' / 'w' — too many legitimate uses

Inputs:
  - dish_aliases_v4.csv
  - dish_canonical_summary_v4.csv

Outputs:
  - dish_aliases_v5.csv
  - dish_canonical_summary_v5.csv
  - dropped_sides_combos.csv (audit)
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

ALIAS_IN  = dpath("dish_aliases_v4.csv")
SUMM_IN   = dpath("dish_canonical_summary_v4.csv")
ALIAS_OUT = dpath("dish_aliases_v5.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v5.csv")
DROPPED   = dpath("dropped_sides_combos.csv")

DROP_TOKENS = {
    "snack", "snacks",
    "side", "sides",
    "appetizer", "appetizers", "starter", "starters",
    "topping", "toppings", "garnish", "garnishes",
    "condiment", "condiments",
    "combo", "combos",
    "carte",   # "a la carte" — alphabetized canonicals contain "carte" token
}

# Load all clusters
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

# Identify drops
drop_cids = {}
for cid, canon, cnt in clusters:
    toks = set(canon.split())
    hit = toks & DROP_TOKENS
    if hit:
        drop_cids[cid] = (canon, cnt, sorted(hit)[0])
print(f"flagged {len(drop_cids):,} clusters for drop")

# Per-token breakdown
from collections import Counter
token_counts = Counter(reason for _, (_, _, reason) in drop_cids.items())
print(f"\ndrop counts by trigger token:")
for tok, n in token_counts.most_common():
    print(f"  {tok:>15}: {n:>6,}")

# Filter alias table
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

# Filter summary
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

# Audit
with open(DROPPED, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "trigger_token"])
    for cid, (canon, cnt, tok) in sorted(drop_cids.items(), key=lambda x: -x[1][1]):
        w.writerow([cid, canon, cnt, tok])

print(f"\nwrote {ALIAS_OUT}")
print(f"wrote {SUMM_OUT}")
print(f"wrote {DROPPED}")
