"""Layer 20 stage 3 — drop the LLM-DROP singletons from v12 → v13.

Inputs:  dish_aliases_v12.csv, dish_canonical_summary_v12.csv, long_singleton_judgments.csv
Outputs: dish_aliases_v13.csv, dish_canonical_summary_v13.csv, dropped_long_singletons.csv
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

ALIAS_IN  = dpath("dish_aliases_v12.csv")
SUMM_IN   = dpath("dish_canonical_summary_v12.csv")
JUDG      = dpath("long_singleton_judgments.csv")
ALIAS_OUT = dpath("dish_aliases_v13.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v13.csv")
DROPPED   = dpath("dropped_long_singletons.csv")

drop_cids = {}
with open(JUDG) as f:
    for row in csv.DictReader(f):
        if row["verdict"] == "DROP":
            drop_cids[int(row["cluster_id"])] = (row["canonical_name"], row["reason"])
print(f"loaded {len(drop_cids):,} DROP verdicts")

kept_alias = dropped_alias = 0
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
        else:
            kept_alias += 1
            w.writerow([row[k] for k in r.fieldnames])
print(f"alias rows: kept {kept_alias:,}, dropped {dropped_alias:,}")

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
    w.writerow(["cluster_id", "canonical_name", "reason"])
    for cid, (canon, reason) in sorted(drop_cids.items()):
        w.writerow([cid, canon, reason])
print(f"\nwrote {DROPPED}")
