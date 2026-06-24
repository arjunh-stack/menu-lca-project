"""Build dish_review_data.json for the swipe-review tool.

Inputs:
  - recipe_drops_applied.csv (filter PRO_VETO + count >= MIN_COUNT)
  - dish_aliases_v18.csv     (top 3 alias forms per cluster)
  - recipes/dish_context.csv (top_raw_name — un-token-sorted human-readable form)
  - dish_canonical_summary_v19.csv (merge-target universe)

Output:
  - dish_review_data.json
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
import json
import re
from collections import defaultdict

DROPS    = dpath("recipe_drops_applied.csv")
ALIASES  = dpath("dish_aliases_v18.csv")
CONTEXT  = dpath("recipes/dish_context.csv")
SUMMARY  = dpath("dish_canonical_summary_v19.csv")
OUT      = dpath("dish_review_data.json")

MIN_COUNT = 10
MAX_SUGGESTIONS = 3

# Load candidate set: PRO_VETO drops with count >= MIN_COUNT
candidates = []
with open(DROPS) as f:
    for row in csv.DictReader(f):
        if row["bucket"] != "PRO_VETO":
            continue
        cnt = int(row["total_count"])
        if cnt < MIN_COUNT:
            continue
        candidates.append({
            "cluster_id": int(row["cluster_id"]),
            "canonical":  row["canonical_name"],
            "count":      cnt,
            "pro_reason": row["pro_reason"],
        })
print(f"candidates: {len(candidates):,}")

# Load alias forms per cluster (top 3 by alias_count, exclude self/fuzzy)
aliases_by_cid = defaultdict(list)
with open(ALIASES) as f:
    for row in csv.DictReader(f):
        method = row["method"]
        aliases_by_cid[int(row["cluster_id"])].append({
            "name":   row["alias_name"],
            "count":  int(row["alias_count"]),
            "method": method,
        })

# Load raw display names from dish_context.csv
raw_name_by_cid = {}
with open(CONTEXT) as f:
    for row in csv.DictReader(f):
        cid_str = row.get("cluster_id", "").strip()
        if not cid_str.isdigit():
            continue
        raw_name_by_cid[int(cid_str)] = row["top_raw_name"]

# Load merge-target universe = v19 canonicals
targets = []          # (cluster_id, canonical, count, set-of-tokens)
token_to_targets = defaultdict(list)  # token → list of target indices
with open(SUMMARY) as f:
    for row in csv.DictReader(f):
        cid = int(row["cluster_id"])
        name = row["canonical_name"]
        cnt = int(row["total_count"])
        toks = set(re.findall(r"[a-z0-9]+", name.lower()))
        idx = len(targets)
        targets.append((cid, name, cnt, toks))
        for t in toks:
            token_to_targets[t].append(idx)
print(f"merge-target universe: {len(targets):,} canonicals, {len(token_to_targets):,} unique tokens")

# Build records
records = []
for c in candidates:
    cid = c["cluster_id"]
    toks = set(re.findall(r"[a-z0-9]+", c["canonical"].lower()))

    # Top 3 raw display forms: prefer top_raw_name if available, else alias_names ranked
    raw_forms = []
    if cid in raw_name_by_cid:
        raw_forms.append(raw_name_by_cid[cid])
    extra = sorted(aliases_by_cid.get(cid, []), key=lambda x: -x["count"])
    for a in extra:
        if a["name"] not in raw_forms:
            raw_forms.append(a["name"])
        if len(raw_forms) >= 3:
            break
    raw_forms = raw_forms[:3]

    # Merge suggestions: scan only targets sharing at least one token with cand
    candidate_idx_set = set()
    for t in toks:
        for idx in token_to_targets.get(t, ()):
            candidate_idx_set.add(idx)

    scored = []
    for idx in candidate_idx_set:
        tcid, tname, tcnt, ttoks = targets[idx]
        if tcid == cid:
            continue  # don't suggest itself
        shared = toks & ttoks
        if not shared:
            continue
        # Subset match = target's tokens are entirely inside the candidate's
        # tokens. These are real shorter dishes hiding inside a jumbled long
        # form (e.g., "fried rice" inside "fried pasta rice"), which we want to
        # surface. Rank these first.
        is_subset = ttoks.issubset(toks)
        noise_in_target = len(ttoks - toks)  # tokens in target NOT in candidate
        scored.append((
            is_subset,
            noise_in_target,        # fewer extra tokens in target = closer match
            len(shared),
            tcnt,
            tcid, tname, sorted(shared),
        ))
    # Sort: subset-first, then fewer noise tokens, then more shared, then bigger target
    scored.sort(key=lambda x: (-int(x[0]), x[1], -x[2], -x[3]))
    suggestions = [
        {"cluster_id": s[4], "canonical": s[5], "count": s[3], "shared_tokens": s[6]}
        for s in scored[:MAX_SUGGESTIONS]
    ]

    records.append({
        "cluster_id":        cid,
        "canonical":         c["canonical"],
        "count":             c["count"],
        "pro_reason":        c["pro_reason"],
        "raw_forms":         raw_forms,
        "merge_suggestions": suggestions,
    })

# Sort by count desc so the user sees biggest-impact drops first
records.sort(key=lambda r: -r["count"])

with open(OUT, "w") as f:
    json.dump({
        "generated_at": "2026-05-11",
        "min_count":    MIN_COUNT,
        "bucket":       "PRO_VETO",
        "total":        len(records),
        "items":        records,
    }, f, indent=1)

print(f"wrote {OUT}  ({len(records):,} items)")
print(f"  highest count: {records[0]['count']:,}  ({records[0]['canonical']!r})")
print(f"  lowest count:  {records[-1]['count']:,}  ({records[-1]['canonical']!r})")
print(f"  items with >=1 merge suggestion: {sum(1 for r in records if r['merge_suggestions']):,}")
