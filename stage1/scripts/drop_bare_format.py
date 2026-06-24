"""Layer 19 — drop canonicals that are nothing but format words.

A canonical like 'sandwich sub' or 'wrap' alone tells us nothing about the
actual dish — it's just the menu label "Sub Sandwich" or "Wrap" with no
distinguishing content. These leak through earlier layers because they're
real strings on real menus, but they collapse multiple distinct dishes into
one bucket and don't pass the recipe-search test.

Rule: drop any canonical whose tokens are entirely a subset of FORMAT_TOKENS,
provided len(tokens) <= MAX_BARE_TOKENS. The cap prevents accidentally dropping
genuine multi-word format combinations someone might construct (none observed,
but defense-in-depth).

Inputs:  dish_aliases_v11.csv, dish_canonical_summary_v11.csv
Outputs: dish_aliases_v12.csv, dish_canonical_summary_v12.csv, dropped_bare_format.csv
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
from collections import defaultdict

ALIAS_IN  = dpath("dish_aliases_v11.csv")
SUMM_IN   = dpath("dish_canonical_summary_v11.csv")
ALIAS_OUT = dpath("dish_aliases_v12.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v12.csv")
DROPPED   = dpath("dropped_bare_format.csv")

FORMAT_TOKENS = {
    "sub", "subs", "sandwich", "sandwiches",
    "wrap", "wraps",
    "bowl", "bowls",
    "burger", "burgers",
    "pizza", "pizzas",
    "taco", "tacos",
    "burrito", "burritos",
    "salad", "salads",
    "soup", "soups",
    "plate", "plates",
}
MAX_BARE_TOKENS = 2

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
    toks = canon.split()
    if not toks or len(toks) > MAX_BARE_TOKENS:
        continue
    if all(t in FORMAT_TOKENS for t in toks):
        drop_cids[cid] = (canon, cnt)
print(f"flagged {len(drop_cids):,} bare-format clusters for drop")

print("\ntop dropped:")
for cid, (canon, cnt) in sorted(drop_cids.items(), key=lambda x: -x[1][1])[:15]:
    print(f"  {cnt:>6,}  {canon}")

kept_alias = dropped_alias = dropped_total = 0
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

print(f"\nrebuilding {SUMM_OUT}")
agg = defaultdict(lambda: [None, 0, 0])
with open(ALIAS_OUT) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["alias_count"])
        except (ValueError, KeyError):
            continue
        agg[cid][0] = row["canonical_name"]
        agg[cid][1] += 1
        agg[cid][2] += cnt
with open(SUMM_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "n_aliases", "total_count"])
    for cid, (canon, n_al, tot) in sorted(agg.items(), key=lambda x: -x[1][2]):
        w.writerow([cid, canon, n_al, tot])
print(f"  {len(agg):,} final clusters")

with open(DROPPED, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count"])
    for cid, (canon, cnt) in sorted(drop_cids.items(), key=lambda x: -x[1][1]):
        w.writerow([cid, canon, cnt])
print(f"\nwrote {DROPPED}")
