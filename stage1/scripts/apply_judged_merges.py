"""Layer 14 stage 3 — apply LLM-judged YES merges to the v6 dish key.

For each singleton with one or more YES verdicts in candidate_judgments.csv:
  - Pick the highest-count YES target as the merge destination.
  - Re-point the singleton's alias rows to that target's cluster_id and rewrite
    canonical_name to the target's. Mark method='llm_merge'.

No chaining: a target cluster's alias rows aren't themselves merged again
even if the target also appears as a singleton elsewhere (which can happen
because clusters with count ≥ 1 can be both singletons in the source pool and
have other singletons pointing at them in another row).

Inputs:  dish_aliases_v6.csv, dish_canonical_summary_v6.csv, candidate_judgments.csv
Outputs: dish_aliases_v7.csv, dish_canonical_summary_v7.csv, llm_merges_applied.csv
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

ALIAS_IN  = dpath("dish_aliases_v6.csv")
SUMM_IN   = dpath("dish_canonical_summary_v6.csv")
JUDG      = dpath("candidate_judgments.csv")
ALIAS_OUT = dpath("dish_aliases_v7.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v7.csv")
AUDIT     = dpath("llm_merges_applied.csv")

# Pick the best target per singleton: highest target_count among YES verdicts
best_target = {}  # singleton_cid -> (target_cid, target_name, target_count)
n_yes = 0
with open(JUDG) as f:
    for row in csv.DictReader(f):
        if row["verdict"] != "YES":
            continue
        n_yes += 1
        scid = int(row["singleton_cid"])
        tcid = int(row["target_cid"])
        tcnt = int(row["target_count"])
        tname = row["target_name"]
        cur = best_target.get(scid)
        if cur is None or tcnt > cur[2]:
            best_target[scid] = (tcid, tname, tcnt)
print(f"loaded {n_yes:,} YES verdicts → {len(best_target):,} unique singletons to merge")

# Don't merge a singleton into a target that is itself merging away (no chaining)
# But we need to still produce a deterministic 1-step merge: target stays in place.
# If target_cid is also in best_target.keys() (target itself was a singleton merging
# elsewhere), let's still treat it as a valid target — its own row count will move
# according to its merge later. So we just apply both merges in their own rows.
# However: this could cause inconsistency where target's alias rows say
# "canonical=X" but X's cluster was merged into Y. Easier rule: skip merges where
# target is itself a singleton that's being merged. Tally how often this happens.
target_also_being_merged = sum(1 for (tcid, _, _) in best_target.values() if tcid in best_target)
print(f"  of those, {target_also_being_merged:,} target a cluster that is itself being merged "
      f"— we'll process targets first and not chain")

# Resolve chain: walk each singleton to its final target (one step max to avoid
# transitivity bugs)
def resolve(scid):
    if scid not in best_target:
        return scid
    tcid, _, _ = best_target[scid]
    if tcid in best_target:
        # Target itself is merging — follow exactly one more hop, no further
        return best_target[tcid][0]
    return tcid

final_target = {scid: resolve(scid) for scid in best_target}

# Load summary to know each cluster's canonical name
canon_by_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        canon_by_cid[int(row["cluster_id"])] = row["canonical_name"]
print(f"loaded {len(canon_by_cid):,} clusters from summary")

# Process alias table: re-point merged singletons
print(f"\nrewriting alias table → {ALIAS_OUT}")
n_in = 0
n_repointed = 0
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
            new_method = "llm_merge"
            w.writerow([new_canon, row["alias_name"], row["alias_count"], new_cid, new_method])
            n_repointed += 1
            if row["method"].strip().lower() == "self":
                # Audit: record this merge
                audit_rows.append((
                    cid, row["alias_name"], row["alias_count"],
                    new_cid, new_canon,
                ))
        else:
            w.writerow([row[k] for k in r.fieldnames])
print(f"  alias rows: {n_in:,} in, {n_repointed:,} re-pointed")

# Rebuild summary from new alias table
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
n_out = len(agg)
print(f"  {n_out:,} final clusters (was {len(canon_by_cid):,})")

with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["singleton_cid", "singleton_name", "singleton_count", "target_cid", "target_canonical"])
    audit_rows.sort(key=lambda r: -int(r[2]) if str(r[2]).isdigit() else 0)
    for r in audit_rows:
        w.writerow(r)
print(f"\nwrote {AUDIT} ({len(audit_rows):,} merges)")
