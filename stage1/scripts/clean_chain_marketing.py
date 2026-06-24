"""Layer 15 — strip Subway/chain marketing tokens (footlong, pro) from canonicals.

Same pattern as Layer 13 single-letter cleanup: for each canonical containing
a strip-token, remove it, re-sort, then either MERGE into an existing canonical
or RENAME the cluster's canonical to the stripped form.

STRIP_TOKENS = {footlong, pro}
  - footlong: pure size descriptor (12-inch sandwich), 115 canonicals
  - pro:      Subway "Pro" double-meat upsell, 30 canonicals
  NOT included: 'style' — used in legit prep contexts (street style, kosher style,
                home style, Chicago stuffed style) where it carries dish meaning.

Inputs:  dish_aliases_v7.csv, dish_canonical_summary_v7.csv
Outputs: dish_aliases_v8.csv, dish_canonical_summary_v8.csv
         chain_marketing_changes.csv (audit)
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
from collections import defaultdict, Counter

ALIAS_IN  = dpath("dish_aliases_v7.csv")
SUMM_IN   = dpath("dish_canonical_summary_v7.csv")
ALIAS_OUT = dpath("dish_aliases_v8.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v8.csv")
AUDIT     = dpath("chain_marketing_changes.csv")

STRIP_TOKENS = {"footlong", "pro"}

def strip(name: str) -> str:
    return " ".join(sorted(t for t in name.split() if t not in STRIP_TOKENS))

clusters = []
canonical_to_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        canon = row["canonical_name"]
        clusters.append((cid, canon, cnt))
        canonical_to_cid[canon] = cid
print(f"loaded {len(clusters):,} clusters")

merge_into = {}
rename_to  = {}
drop_cids  = set()
audit_rows = []

n_hit = 0
for cid, canon, cnt in clusters:
    toks = canon.split()
    if not (set(toks) & STRIP_TOKENS):
        continue
    n_hit += 1
    cleaned = strip(canon)
    if not cleaned:
        drop_cids.add(cid)
        audit_rows.append((cid, canon, cnt, "drop", "(empty after strip)", ""))
    elif cleaned in canonical_to_cid and canonical_to_cid[cleaned] != cid:
        target = canonical_to_cid[cleaned]
        merge_into[cid] = target
        audit_rows.append((cid, canon, cnt, "merge", cleaned, target))
    else:
        rename_to[cid] = cleaned
        audit_rows.append((cid, canon, cnt, "rename", cleaned, ""))

print(f"\n{n_hit:,} canonicals contain strip tokens ({sorted(STRIP_TOKENS)})")
print(f"actions: {dict(Counter(r[3] for r in audit_rows))}")

# Map merged-into target → canonical name
target_canonical = {}
for cid in merge_into.values():
    for c, can, _ in clusters:
        if c == cid:
            target_canonical[cid] = can
            break

print(f"\nrewriting alias table → {ALIAS_OUT}")
kept = 0
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
            continue
        if cid in merge_into:
            target = merge_into[cid]
            new_canon = target_canonical[target]
            new_method = "chain_strip_merge" if row["method"].strip().lower() == "self" else row["method"]
            w.writerow([new_canon, row["alias_name"], row["alias_count"], target, new_method])
            kept += 1
            continue
        if cid in rename_to:
            new_canon = rename_to[cid]
            if row["method"].strip().lower() == "self":
                w.writerow([new_canon, new_canon, row["alias_count"], cid, "self"])
            else:
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, row["method"]])
            kept += 1
            continue
        w.writerow([row[k] for k in r.fieldnames])
        kept += 1
print(f"  kept {kept:,} alias rows")

# Rebuild summary
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
print(f"  {len(agg):,} final clusters (was {len(clusters):,})")

with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "old_canonical", "total_count", "action", "cleaned", "merged_into_cid"])
    audit_rows.sort(key=lambda r: -r[2])
    for r in audit_rows:
        w.writerow(r)
print(f"wrote {AUDIT}")
