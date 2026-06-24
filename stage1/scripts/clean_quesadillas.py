"""Layer 23 — targeted quesadilla cleanup.

Manual review of all canonicals containing 'quesadilla' / 'quesadillas' surfaced
two clear classes of duplicates:

  A) Spanish↔English / filler-word / format-word merges (10 clusters merge
     into 5 destination clusters).
  B) Plural→singular renames (4 clusters whose canonical has 'quesadillas'
     where no singular sibling exists, so just rename).
  C) bf → buffalo abbreviation merge (1 cluster).

Inputs:  dish_aliases_v16.csv, dish_canonical_summary_v16.csv
Outputs: dish_aliases_v17.csv, dish_canonical_summary_v17.csv, quesadilla_changes.csv
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

ALIAS_IN  = dpath("dish_aliases_v16.csv")
SUMM_IN   = dpath("dish_canonical_summary_v16.csv")
ALIAS_OUT = dpath("dish_aliases_v17.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v17.csv")
AUDIT     = dpath("quesadilla_changes.csv")

# (source_cid, target_cid, reason) — always merge into the higher-count target
MERGES = [
    (26925, 667, "Spanish→English: pollo = chicken"),
    (2101,  667, "Spanish→English: pollo = chicken"),
    (27572, 658, "Spanish→English: queso = cheese"),
    (2255,  658, "Spanish→English: queso = cheese"),
    (27261, 658, "filler word: 'only' is non-distinguishing"),
    (1743,  976, "synonym: vegetable = veggie"),
    (1444,  976, "synonym: vegetarian = veggie (menu context)"),
    (1396,  26114, "Spanish article: 'al pastor' / 'pastor' same dish"),
    (1559,  26267, "missing token: 'carne asada' / 'asada' same dish"),
    (26531, 27675, "abbreviation: bf = buffalo"),
]

# (source_cid, new_canonical, reason)
RENAMES = [
    (947,   "brisket quesadilla", "plural→singular"),
    (84613, "bacon chicken quesadilla ranch", "plural→singular"),
    (84620, "bacon beef quesadilla ranch", "plural→singular"),
    (27395, "chicken quesadilla smoked", "plural→singular"),
]

# Load summary to get current canonicals + counts
canon_by_cid = {}
count_by_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        cid = int(row["cluster_id"])
        canon_by_cid[cid] = row["canonical_name"]
        count_by_cid[cid] = int(row["total_count"])
print(f"loaded {len(canon_by_cid):,} clusters")

# Validate
print("\nplanned merges:")
for src, tgt, reason in MERGES:
    if src not in canon_by_cid:
        print(f"  ⚠ source {src} not found"); continue
    if tgt not in canon_by_cid:
        print(f"  ⚠ target {tgt} not found"); continue
    print(f"  cid {src} '{canon_by_cid[src]}' ({count_by_cid[src]}) → cid {tgt} '{canon_by_cid[tgt]}' ({count_by_cid[tgt]})  [{reason}]")

print("\nplanned renames:")
for src, new_canon, reason in RENAMES:
    if src not in canon_by_cid:
        print(f"  ⚠ source {src} not found"); continue
    print(f"  cid {src} '{canon_by_cid[src]}' ({count_by_cid[src]}) → '{new_canon}'  [{reason}]")

merge_into = {src: tgt for src, tgt, _ in MERGES}
merge_reason = {src: reason for src, _, reason in MERGES}
rename_to = {src: new for src, new, _ in RENAMES}
rename_reason = {src: reason for src, _, reason in RENAMES}

# Pre-collect aliases per source cluster for the audit
src_aliases = defaultdict(list)
target_cids = set(merge_into.values()) | set(merge_into.keys()) | set(rename_to.keys())
with open(ALIAS_IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in merge_into or cid in rename_to:
            src_aliases[cid].append((row["alias_name"], int(row["alias_count"]), row["method"]))

# Rewrite alias table
print(f"\nrewriting alias table → {ALIAS_OUT}")
n_in = n_repointed = n_renamed = 0
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
        if cid in merge_into:
            new_cid = merge_into[cid]
            new_canon = canon_by_cid[new_cid]
            method = "manual_quesadilla_merge" if row["method"].strip().lower() == "self" else row["method"]
            w.writerow([new_canon, row["alias_name"], row["alias_count"], new_cid, method])
            n_repointed += 1
        elif cid in rename_to:
            new_canon = rename_to[cid]
            if row["method"].strip().lower() == "self":
                # Write the new self alias AND preserve the old alias_name as a
                # fuzzy alias so raw menu rows that normalize to the old form
                # still find this cluster.
                w.writerow([new_canon, new_canon, 0, cid, "self"])
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, "rename_preserved"])
            else:
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, row["method"]])
            n_renamed += 1
        else:
            w.writerow([row[k] for k in r.fieldnames])
print(f"  alias rows: {n_in:,} in, {n_repointed:,} re-pointed (merges), {n_renamed:,} canonical-renamed")

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
print(f"  {len(agg):,} final clusters (was {len(canon_by_cid):,})")

# Audit — capture every variant that collapsed into each new canonical, with reason
with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["action", "source_cid", "source_canonical", "source_count", "target_cid_or_new_canonical", "reason", "absorbed_alias", "absorbed_alias_count", "alias_method"])
    for src, tgt, reason in MERGES:
        if src not in canon_by_cid: continue
        for alias, alias_cnt, method in src_aliases[src]:
            w.writerow(["merge", src, canon_by_cid[src], count_by_cid[src],
                        f"{tgt} → {canon_by_cid[tgt]}", reason, alias, alias_cnt, method])
    for src, new_canon, reason in RENAMES:
        if src not in canon_by_cid: continue
        for alias, alias_cnt, method in src_aliases[src]:
            w.writerow(["rename", src, canon_by_cid[src], count_by_cid[src],
                        new_canon, reason, alias, alias_cnt, method])
print(f"\nwrote {AUDIT}")
