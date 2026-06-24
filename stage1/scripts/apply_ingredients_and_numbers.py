"""Layer 11A — apply confident drops from ingredients_and_numbers_review.csv.

Reads the review CSV, drops every row where verdict='drop'. The aliases that
were attached to those clusters in the Layer-10 alias key are dropped as well.

Inputs:
  - ingredients_and_numbers_review.csv (verdict column)
  - dish_aliases_v2.csv (Layer 10 alias key)
  - dish_canonical_summary_v2.csv (Layer 10 canonical list)

Outputs:
  - dish_aliases_v3.csv
  - dish_canonical_summary_v3.csv
  - dropped_ingredients_and_numbers.csv (audit: every dropped cluster + reason)
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

REVIEW = dpath("ingredients_and_numbers_review.csv")
ALIAS_IN  = dpath("dish_aliases_v2.csv")
SUMM_IN   = dpath("dish_canonical_summary_v2.csv")
ALIAS_OUT = dpath("dish_aliases_v3.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v3.csv")
AUDIT_OUT = dpath("dropped_ingredients_and_numbers.csv")

# Load drop set
drop_cids = {}
with open(REVIEW) as f:
    for row in csv.DictReader(f):
        if row["verdict"].strip().lower() == "drop":
            drop_cids[int(row["cluster_id"])] = (row["canonical_name"], int(row["total_count"]), row["reason"])
print(f"loaded {len(drop_cids):,} cluster ids to drop")

# Filter alias table
kept_alias_rows = 0
dropped_alias_rows = 0
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
            dropped_alias_rows += 1
            try:
                dropped_total_count += int(row["alias_count"])
            except ValueError:
                pass
        else:
            kept_alias_rows += 1
            w.writerow([row[k] for k in r.fieldnames])
print(f"alias rows: kept {kept_alias_rows:,}, dropped {dropped_alias_rows:,} (sum-of-counts {dropped_total_count:,})")

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
with open(AUDIT_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "reason"])
    for cid, (canon, cnt, reason) in sorted(drop_cids.items(), key=lambda x: -x[1][1]):
        w.writerow([cid, canon, cnt, reason])
print(f"\nwrote {ALIAS_OUT}")
print(f"wrote {SUMM_OUT}")
print(f"wrote {AUDIT_OUT}")
