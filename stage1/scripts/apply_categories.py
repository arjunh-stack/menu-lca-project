"""Layer 24 — apply 1,130 high-confidence category-cleanup merges/renames.

Reads `proposals/aggregated_high.csv` (the post-validation high-confidence
batch from 11 parallel category-proposal agents). Applies merges and renames
to v17 → v18.

Key behavior — rename-collision auto-merge:
  When a rename's new_canonical matches an EXISTING cluster's canonical_name,
  treat the rename as a merge into that cluster instead. (The agents only
  emitted renames when they didn't see a sibling, but post-aggregation other
  category passes may have created an effective sibling.)

Inputs:
  - dish_aliases_v17.csv, dish_canonical_summary_v17.csv
  - proposals/aggregated_high.csv

Outputs:
  - dish_aliases_v18.csv, dish_canonical_summary_v18.csv
  - category_changes.csv (audit, including absorbed alias variants)
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
from pathlib import Path

ALIAS_IN  = dpath("dish_aliases_v17.csv")
SUMM_IN   = dpath("dish_canonical_summary_v17.csv")
PROPS     = dpath("proposals/aggregated_high.csv")
ALIAS_OUT = dpath("dish_aliases_v18.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v18.csv")
AUDIT     = dpath("category_changes.csv")

# Load v17 summary
canon_by_cid = {}
count_by_cid = {}
canonical_to_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        cid = int(row["cluster_id"])
        canon_by_cid[cid] = row["canonical_name"]
        count_by_cid[cid] = int(row["total_count"])
        canonical_to_cid.setdefault(row["canonical_name"], cid)
print(f"loaded {len(canon_by_cid):,} v17 clusters")

# Read proposals — split into renames and merges, process renames first
# (rename→merge auto-collisions take precedence; subsequent merges into a
#  cluster that's already a rename-source get redirected to the rename's target).
raw_renames = []
raw_merges = []
with open(PROPS) as f:
    for row in csv.DictReader(f):
        try:
            src = int(row["source_cid"])
        except (ValueError, KeyError):
            continue
        if src not in canon_by_cid:
            continue
        if row["action"] == "rename":
            new_canon = row["new_canonical"].strip()
            if not new_canon:
                continue
            raw_renames.append((src, new_canon, row["reason"], row["category"]))
        elif row["action"] == "merge":
            try:
                tgt = int(row["target_cid"])
            except (ValueError, KeyError):
                continue
            if tgt not in canon_by_cid or tgt == src:
                continue
            raw_merges.append((src, tgt, row["reason"], row["category"]))

merge_into = {}
merge_reason = {}
rename_to = {}
rename_reason = {}
proposal_category = {}
n_merges = n_renames = n_rename_to_merge = n_merge_redirected = n_cycle_skip = 0

# Process renames first
for src, new_canon, reason, cat in raw_renames:
    existing_cid = canonical_to_cid.get(new_canon)
    if existing_cid is not None and existing_cid != src:
        merge_into[src] = existing_cid
        merge_reason[src] = f"rename→merge collision: {reason}"
        proposal_category[src] = cat
        n_rename_to_merge += 1
    else:
        rename_to[src] = new_canon
        rename_reason[src] = reason
        proposal_category[src] = cat
        n_renames += 1

# Process merges — redirect through any rename-collision that was already created
for src, tgt, reason, cat in raw_merges:
    # If src is already in merge_into (it was a rename-source whose target was
    # an existing cluster), the rename takes priority — drop this merge.
    if src in merge_into:
        n_cycle_skip += 1
        continue
    # If tgt is in merge_into, redirect to its destination (one hop).
    if tgt in merge_into:
        tgt = merge_into[tgt]
        if tgt == src:
            n_cycle_skip += 1
            continue
        n_merge_redirected += 1
    merge_into[src] = tgt
    merge_reason[src] = reason
    proposal_category[src] = cat
    n_merges += 1

print(f"\nproposed actions:")
print(f"  merges:                       {n_merges:,}")
print(f"  renames:                      {n_renames:,}")
print(f"  renames-promoted-merges:      {n_rename_to_merge:,} (rename target matched an existing canonical)")
print(f"  merges-redirected-via-rename: {n_merge_redirected:,} (target was already a rename source)")
print(f"  cycle-skipped merges:         {n_cycle_skip:,}")

# One-step chain resolution: if A merges into B and B merges into C, follow once
def resolve(scid):
    tgt = merge_into.get(scid)
    if tgt is None:
        return scid
    if tgt in merge_into:
        return merge_into[tgt]
    return tgt
final_target = {scid: resolve(scid) for scid in merge_into}

# Pre-collect aliases per source for the audit
src_aliases = defaultdict(list)
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
n_in = n_repointed = n_renamed_alias = 0
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
            new_canon = canon_by_cid[new_cid]
            method = "category_merge" if row["method"].strip().lower() == "self" else row["method"]
            w.writerow([new_canon, row["alias_name"], row["alias_count"], new_cid, method])
            n_repointed += 1
        elif cid in rename_to:
            new_canon = rename_to[cid]
            if row["method"].strip().lower() == "self":
                # Preserve old self alias as a fuzzy alias too
                w.writerow([new_canon, new_canon, 0, cid, "self"])
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, "rename_preserved"])
            else:
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, row["method"]])
            n_renamed_alias += 1
        else:
            w.writerow([row[k] for k in r.fieldnames])
print(f"  alias rows: {n_in:,} in, {n_repointed:,} re-pointed (merges), {n_renamed_alias:,} canonical-renamed")

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

# Audit — capture every absorbed alias with reason and category
with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["category", "action", "source_cid", "source_canonical", "source_count",
                "target_cid_or_new_canonical", "reason", "absorbed_alias", "absorbed_alias_count", "alias_method"])
    for src in sorted(set(merge_into.keys()) | set(rename_to.keys())):
        cat = proposal_category.get(src, "")
        if src in merge_into:
            tgt = final_target[src]
            action = "rename→merge" if src in rename_to else "merge"
            for alias, cnt, method in src_aliases[src]:
                w.writerow([cat, action, src,
                            canon_by_cid[src], count_by_cid[src],
                            f"{tgt} → {canon_by_cid[tgt]}", merge_reason[src], alias, cnt, method])
        else:
            for alias, cnt, method in src_aliases[src]:
                w.writerow([cat, "rename", src, canon_by_cid[src], count_by_cid[src],
                            rename_to[src], rename_reason[src], alias, cnt, method])
print(f"\nwrote {AUDIT}")
