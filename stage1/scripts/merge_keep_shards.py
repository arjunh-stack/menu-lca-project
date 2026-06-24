"""Merge sharded Pro KEEP-screen outputs into the main CSV.

Reads recipe_screen_deepseek_keeps_shard{0..3}.csv and appends to
recipe_screen_deepseek_keeps.csv (de-duping by cluster_id).

Then identifies any cluster_ids in the Gemini-KEEP set that are still missing
and writes them to recipe_screen_deepseek_keeps_missing.csv for a cleanup pass.
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
from pathlib import Path

GEMINI    = dpath("recipe_screen_gemini.csv")
MAIN      = dpath("recipe_screen_deepseek_keeps.csv")
SHARDS    = [dpath(f"recipe_screen_deepseek_keeps_shard{i}.csv")
             for i in range(4)]
MISSING   = dpath("recipe_screen_deepseek_keeps_missing.csv")

# Load existing main
main_done = set()
main_rows = []
with open(MAIN) as f:
    rd = csv.DictReader(f)
    header = rd.fieldnames
    for row in rd:
        cid = int(row["cluster_id"])
        if cid not in main_done:
            main_done.add(cid)
            main_rows.append(row)

print(f"main pre-merge: {len(main_rows):,}")

# Append shards (skipping dupes against main)
n_appended = 0
for shard_path in SHARDS:
    with open(shard_path) as f:
        for row in csv.DictReader(f):
            cid = int(row["cluster_id"])
            if cid not in main_done:
                main_done.add(cid)
                main_rows.append(row)
                n_appended += 1

print(f"appended from shards: {n_appended:,}")
print(f"main post-merge: {len(main_rows):,}")

# Write merged main
with open(MAIN, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    for r in main_rows:
        w.writerow(r)

# Find missing from the Gemini-KEEP set
gemini_keeps = []
with open(GEMINI) as f:
    for row in csv.DictReader(f):
        if row["verdict"] == "KEEP":
            gemini_keeps.append(row)

missing = [r for r in gemini_keeps if int(r["cluster_id"]) not in main_done]
print(f"\ngemini-KEEPs: {len(gemini_keeps):,}")
print(f"missing after merge: {len(missing):,}")

if missing:
    with open(MISSING, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id", "canonical_name", "total_count"])
        for r in missing:
            w.writerow([r["cluster_id"], r["canonical_name"], r["total_count"]])
    print(f"wrote {MISSING}")
    for r in missing[:5]:
        print(f"  cid={r['cluster_id']} name={r['canonical_name']!r}")
