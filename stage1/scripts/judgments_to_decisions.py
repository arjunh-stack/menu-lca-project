"""Convert dish_rescue_judgments.csv into dish_rescue_decisions.json so
apply_recipe_drops.py can pick it up."""

# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import csv, json
from collections import Counter

J = dpath("dish_rescue_judgments.csv")
O = dpath("dish_rescue_decisions.json")

decisions = {}
counts = Counter()
with open(J) as f:
    for row in csv.DictReader(f):
        cid = row["drop_cid"]
        if row["verdict"] == "YES":
            decisions[cid] = {
                "action": "merge",
                "canonical": row["dropped"],
                "target_cid": int(row["target_cid"]),
                "target_canonical": row["target"],
                "source": "gemini_auto_judge",
            }
            counts["merge"] += 1
        else:
            # NO / PARSE_ERROR / API_ERROR — leave dropped (no change needed,
            # but record the decision so future runs are reproducible)
            decisions[cid] = {"action": "drop", "canonical": row["dropped"]}
            counts[row["verdict"].lower()] += 1

with open(O, "w") as f:
    json.dump({
        "generated_at": "2026-05-11",
        "source": "judge_rescues_gemini.py",
        "model": "google/gemini-2.0-flash-001",
        "decisions": decisions,
    }, f, indent=1)
print("wrote", O)
print("counts:", dict(counts))
