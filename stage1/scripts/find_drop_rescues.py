"""Scan every dropped cluster for "real dish hiding inside a jumbled long form".

A drop is a rescue candidate if its canonical tokens are a STRICT SUPERSET of
some v19 canonical (i.e. the kept dish is sitting inside the jumbled drop with
≤ N extra noise tokens). Output is shaped exactly like dish_review_data.json so
the same swipe tool can review it.

Inputs:
  - recipe_drops_applied.csv         (every dropped cluster)
  - dish_canonical_summary_v19.csv   (kept-dish universe = merge target set)
  - dish_aliases_v18.csv             (raw alias forms for display)
  - recipes/dish_context.csv         (human-readable raw_menu_name)

Output:
  - dish_rescue_data.json
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
V19_SUM  = dpath("dish_canonical_summary_v19.csv")
ALIASES  = dpath("dish_aliases_v18.csv")
CONTEXT  = dpath("recipes/dish_context.csv")
OUT      = dpath("dish_rescue_data.json")

MIN_DROP_COUNT     = 5
MIN_TARGET_COUNT   = 20
MAX_NOISE_TOKENS   = 2
MAX_SUGGESTIONS    = 3

# Hide useless single-token "category" targets that we don't want to merge
# concrete drops into ("burger", "salad", "pizza" etc.).
SINGLE_TOKEN_TARGET_BLOCKLIST = {
    "burger", "salad", "pizza", "sandwich", "wrap", "bowl", "soup",
    "side", "sides", "appetizer", "drink", "kids", "combo",
}

def tokens(s):
    return frozenset(re.findall(r"[a-z0-9]+", s.lower()))

# v19 target universe (filtered for sanity)
targets = []
token_to_targets = defaultdict(list)
with open(V19_SUM) as f:
    for row in csv.DictReader(f):
        cid = int(row["cluster_id"])
        name = row["canonical_name"]
        cnt = int(row["total_count"])
        if cnt < MIN_TARGET_COUNT: continue
        toks = tokens(name)
        if not toks: continue
        if len(toks) == 1 and next(iter(toks)) in SINGLE_TOKEN_TARGET_BLOCKLIST:
            continue
        idx = len(targets)
        targets.append((cid, name, cnt, toks))
        for t in toks:
            token_to_targets[t].append(idx)
print(f"v19 merge-target universe: {len(targets):,} canonicals")

# Aliases per cluster
aliases_by_cid = defaultdict(list)
with open(ALIASES) as f:
    for row in csv.DictReader(f):
        aliases_by_cid[int(row["cluster_id"])].append({
            "name": row["alias_name"],
            "count": int(row["alias_count"]),
            "method": row["method"],
        })

# Raw display names
raw_name_by_cid = {}
with open(CONTEXT) as f:
    for row in csv.DictReader(f):
        cid_str = row.get("cluster_id", "").strip()
        if cid_str.isdigit():
            raw_name_by_cid[int(cid_str)] = row["top_raw_name"]

# Scan every dropped cluster
candidates = []
n_drops_seen = 0
n_drops_with_match = 0
with open(DROPS) as f:
    for row in csv.DictReader(f):
        drop_cnt = int(row["total_count"])
        if drop_cnt < MIN_DROP_COUNT: continue
        n_drops_seen += 1
        drop_cid  = int(row["cluster_id"])
        drop_name = row["canonical_name"]
        drop_toks = tokens(drop_name)
        if len(drop_toks) < 2:
            # A 1-token drop can't be a STRICT superset of any target with content.
            continue

        # Candidate target indices = those sharing at least one token
        seen_idx = set()
        for t in drop_toks:
            for idx in token_to_targets.get(t, ()):
                seen_idx.add(idx)

        scored = []
        for idx in seen_idx:
            tcid, tname, tcnt, ttoks = targets[idx]
            if not ttoks.issubset(drop_toks):
                continue
            noise = len(drop_toks - ttoks)
            if noise == 0:  # same token set — would already be the same cluster
                continue
            if noise > MAX_NOISE_TOKENS:
                continue
            scored.append((noise, -tcnt, tcid, tname, tcnt, sorted(drop_toks - ttoks)))
        if not scored: continue
        n_drops_with_match += 1
        scored.sort()  # noise asc, then target count desc

        suggestions = [
            {
                "cluster_id": s[2],
                "canonical":  s[3],
                "count":      s[4],
                "shared_tokens": sorted(drop_toks - set(s[5])),
                "noise_tokens":  s[5],
            }
            for s in scored[:MAX_SUGGESTIONS]
        ]

        # Display: raw_menu_name first, then top alias forms (excluding self/fuzzy noise)
        raw_forms = []
        if drop_cid in raw_name_by_cid:
            raw_forms.append(raw_name_by_cid[drop_cid])
        for a in sorted(aliases_by_cid.get(drop_cid, []), key=lambda x: -x["count"]):
            if a["name"] not in raw_forms:
                raw_forms.append(a["name"])
            if len(raw_forms) >= 3:
                break
        raw_forms = raw_forms[:3]

        candidates.append({
            "cluster_id":        drop_cid,
            "canonical":         drop_name,
            "count":             drop_cnt,
            "pro_reason":        f"{row['bucket']} ({row['gemini_reason']} / {row['pro_reason']})",
            "raw_forms":         raw_forms,
            "merge_suggestions": suggestions,
            "_top_noise":        scored[0][0],
            "_top_tcnt":         -scored[0][1],
        })

print(f"drops scanned (count >= {MIN_DROP_COUNT}): {n_drops_seen:,}")
print(f"  with at least one subset-match target: {n_drops_with_match:,}")

# Sort by impact. Best matches first: smaller noise wins, larger target count breaks ties,
# then larger drop count (impact).
candidates.sort(key=lambda c: (c["_top_noise"], -c["_top_tcnt"], -c["count"]))
for c in candidates:
    c.pop("_top_noise"); c.pop("_top_tcnt")

with open(OUT, "w") as f:
    json.dump({
        "generated_at": "2026-05-11",
        "mode": "drop-rescue",
        "min_drop_count":   MIN_DROP_COUNT,
        "min_target_count": MIN_TARGET_COUNT,
        "max_noise_tokens": MAX_NOISE_TOKENS,
        "total":            len(candidates),
        "items":            candidates,
    }, f, indent=1)
print(f"\nwrote {OUT}  ({len(candidates):,} items)")
print(f"\n=== top 12 by match quality ===")
for c in candidates[:12]:
    s = c["merge_suggestions"][0]
    print(f"  {c['canonical']!r}  ({c['count']} menus)")
    print(f"     → {s['canonical']!r}  ({s['count']} menus, noise={s['noise_tokens']})")
