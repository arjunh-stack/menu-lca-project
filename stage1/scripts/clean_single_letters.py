"""Layer 13 — clean canonicals containing floating single-letter tokens.

Almost all single-letter tokens are parsing artifacts:
  - apostrophe-s split:    `burger dave s`  ← "Dave's Burger"
  - apostrophe-n split:    `chick melt n tater`  ← "Chick'n Melt 'n Tater"
  - acronym split:         `b l t wrap`  ← "BLT Wrap", `b footlong italian m pro sandwich t` ← Subway BMT
  - w from w/:             `bacon breakfast platter w`  ← "Breakfast Platter w/ Bacon"

For each canonical with one or more single-letter tokens:
  1. Strip the single-letter tokens, keep remaining tokens, sort.
  2. If stripped form == an existing canonical → MERGE this cluster into it
     (alias rows get re-pointed; the noisy canonical disappears).
  3. If stripped form has ≥2 tokens but no match → RENAME the canonical to
     the cleaner form (cluster stays, just gets a tidier label).
  4. If stripped form has <2 tokens → DROP the cluster (residual is too thin
     to be a real dish on its own).

Inputs:  dish_aliases_v5.csv, dish_canonical_summary_v5.csv
Outputs: dish_aliases_v6.csv, dish_canonical_summary_v6.csv
         single_letter_changes.csv (audit: what got merged/renamed/dropped)
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

ALIAS_IN  = dpath("dish_aliases_v5.csv")
SUMM_IN   = dpath("dish_canonical_summary_v5.csv")
ALIAS_OUT = dpath("dish_aliases_v6.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v6.csv")
AUDIT     = dpath("single_letter_changes.csv")

def strip_singles(name: str) -> str:
    return " ".join(sorted(t for t in name.split() if len(t) > 1))

# Load summary
clusters = []  # (cid, canon, total_count)
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

# Decisions
merge_into = {}    # noisy_cid -> target_cid (cluster gets absorbed)
rename_to  = {}    # cid -> new_canonical_name
drop_cids  = set()
audit_rows = []

n_singles = 0
for cid, canon, cnt in clusters:
    has_single = any(len(t) == 1 for t in canon.split())
    if not has_single:
        continue
    n_singles += 1
    cleaned = strip_singles(canon)
    if cleaned in canonical_to_cid and canonical_to_cid[cleaned] != cid:
        target = canonical_to_cid[cleaned]
        merge_into[cid] = target
        audit_rows.append((cid, canon, cnt, "merge", cleaned, target))
    elif len(cleaned.split()) >= 2:
        rename_to[cid] = cleaned
        audit_rows.append((cid, canon, cnt, "rename", cleaned, ""))
    else:
        drop_cids.add(cid)
        audit_rows.append((cid, canon, cnt, "drop", cleaned, ""))

print(f"\n{n_singles:,} canonicals contain single-letter tokens")
action_counts = Counter(r[3] for r in audit_rows)
print(f"actions:")
for a, n in action_counts.most_common():
    print(f"  {a:>8}: {n:>5,}")

# Process alias table:
#   - rows with cid in drop_cids → drop entirely
#   - rows with cid in merge_into → re-point to target cid + canonical_name = target's canonical
#   - rows with cid in rename_to → keep cid, rewrite canonical_name; if alias_name matches old canonical
#     and is the 'self' row, the alias_name should also be rewritten to the new canonical
target_canonical = {}
for cid in merge_into.values():
    # find canonical name for that target
    for c, can, _ in clusters:
        if c == cid:
            target_canonical[cid] = can
            break

print(f"\nrewriting alias table → {ALIAS_OUT}")
kept = 0
dropped_rows = 0
dropped_total_count = 0
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
            dropped_rows += 1
            try:
                dropped_total_count += int(row["alias_count"])
            except ValueError:
                pass
            continue
        if cid in merge_into:
            target = merge_into[cid]
            new_canon = target_canonical[target]
            new_alias = row["alias_name"]
            # The merged-in alias is no longer 'self' relative to the new canonical
            new_method = "single_letter_merge" if new_alias == row["canonical_name"] else row["method"]
            w.writerow([new_canon, new_alias, row["alias_count"], target, new_method])
            kept += 1
            continue
        if cid in rename_to:
            new_canon = rename_to[cid]
            old_canon = row["canonical_name"]
            new_alias = row["alias_name"]
            # If this row was the 'self' for the old canonical, replace its alias_name with the cleaned canonical
            if row["method"].strip().lower() == "self":
                w.writerow([new_canon, new_canon, row["alias_count"], cid, "self"])
            else:
                w.writerow([new_canon, new_alias, row["alias_count"], cid, row["method"]])
            kept += 1
            continue
        # Untouched cluster
        w.writerow([row[k] for k in r.fieldnames])
        kept += 1
print(f"  kept {kept:,} alias rows, dropped {dropped_rows:,} (sum-of-counts {dropped_total_count:,})")

# Rebuild summary from aliases
print(f"\nrebuilding {SUMM_OUT}")
agg = defaultdict(lambda: [None, 0, 0])  # cid -> [canonical, n_aliases, total_count]
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

# Audit
with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "old_canonical", "total_count", "action", "cleaned", "merged_into_cid"])
    audit_rows.sort(key=lambda r: -r[2])
    for r in audit_rows:
        w.writerow(r)
print(f"wrote {AUDIT}")
