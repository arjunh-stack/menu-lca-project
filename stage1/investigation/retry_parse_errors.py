"""Strip PARSE_ERROR / API_ERROR rows out of candidate_judgments.csv so the
main judge script can re-process them on next run."""

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
import shutil

P = dpath("candidate_judgments.csv")
BAK = P + ".bak"

shutil.copy(P, BAK)
print(f"backed up to {BAK}")

kept = []
removed = 0
with open(BAK) as f:
    r = csv.DictReader(f)
    fieldnames = r.fieldnames
    for row in r:
        if row["verdict"] in ("YES", "NO"):
            kept.append(row)
        else:
            removed += 1

with open(P, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(kept)
print(f"kept {len(kept):,}, removed {removed:,} (will re-judge on next run)")
