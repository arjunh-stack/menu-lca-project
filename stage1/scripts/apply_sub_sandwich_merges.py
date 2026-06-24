"""Layer 18 stage 3 — apply YES sub/sandwich merges to v10 → v11.

For each singleton with a YES verdict, re-point its alias rows to the target.
One-step merge (no chaining).

Inputs:  dish_aliases_v10.csv, dish_canonical_summary_v10.csv, sub_sandwich_judgments.csv
Outputs: dish_aliases_v11.csv, dish_canonical_summary_v11.csv, sub_sandwich_merges_applied.csv
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

ALIAS_IN  = dpath("dish_aliases_v10.csv")
SUMM_IN   = dpath("dish_canonical_summary_v10.csv")
JUDG      = dpath("sub_sandwich_judgments.csv")
ALIAS_OUT = dpath("dish_aliases_v11.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v11.csv")
AUDIT     = dpath("sub_sandwich_merges_applied.csv")

best_target = {}
n_yes = 0
with open(JUDG) as f:
    for row in csv.DictReader(f):
        if row["verdict"] != "YES":
            continue
        n_yes += 1
        scid = int(row["singleton_cid"])
        tcid = int(row["target_cid"])
        tcnt = int(row["target_count"])
        cur = best_target.get(scid)
        if cur is None or tcnt > cur[1]:
            best_target[scid] = (tcid, tcnt)
print(f"loaded {n_yes:,} YES verdicts → {len(best_target):,} unique singletons to merge")

def resolve(scid):
    tcid = best_target[scid][0]
    if tcid in best_target:
        return best_target[tcid][0]
    return tcid

final_target = {scid: resolve(scid) for scid in best_target}

canon_by_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        canon_by_cid[int(row["cluster_id"])] = row["canonical_name"]
print(f"loaded {len(canon_by_cid):,} clusters")

print(f"\nrewriting alias table → {ALIAS_OUT}")
n_in = n_repointed = 0
audit_rows = []
with open(ALIAS_IN) as f, open(ALIAS_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        n_in += 1
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            w.writerow([row[k] for k in r.fieldnames])
            continue
        if cid in final_target:
            new_cid = final_target[cid]
            new_canon = canon_by_cid.get(new_cid, row["canonical_name"])
            w.writerow([new_canon, row["alias_name"], row["alias_count"], new_cid, "sub_sandwich_merge"])
            n_repointed += 1
            if row["method"].strip().lower() == "self":
                audit_rows.append((cid, row["alias_name"], row["alias_count"], new_cid, new_canon))
        else:
            w.writerow([row[k] for k in r.fieldnames])
print(f"  alias rows: {n_in:,} in, {n_repointed:,} re-pointed")

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
print(f"  {len(agg):,} final clusters (was {len(canon_by_cid):,})")

with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["singleton_cid", "singleton_name", "singleton_count", "target_cid", "target_canonical"])
    audit_rows.sort(key=lambda r: -int(r[2]) if str(r[2]).isdigit() else 0)
    for r in audit_rows:
        w.writerow(r)
print(f"\nwrote {AUDIT} ({len(audit_rows):,} merges)")
