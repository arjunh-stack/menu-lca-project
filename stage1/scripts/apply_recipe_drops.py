"""Layer 25 — apply approved recipe-test drops.

Rule:
  DROP if bucket == BOTH_DROP
  DROP if bucket == PRO_VETO UNLESS:
    - canonical_name is in RESCUE_CANONICALS (verified chain item by web search), OR
    - pro_reason in {obscure, unknown, unrecognized} AND total_count >= 3
      (protect ethnic dishes Pro doesn't recognize)
  KEEP everything else (BOTH_KEEP, PRO_RESCUE, HAS_ERROR)

Inputs:
  - recipe_screen_compare_v2.csv  (3-way verdict comparator output)
  - dish_aliases_v18.csv
  - dish_canonical_summary_v18.csv

Outputs:
  - dish_aliases_v19.csv          (filtered alias table)
  - dish_canonical_summary_v19.csv (filtered canonical list)
  - recipe_drops_applied.csv      (audit of every dropped cluster)
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

COMPARE     = dpath("recipe_screen_compare_v2.csv")
ALIASES_IN  = dpath("dish_aliases_v18.csv")
SUMMARY_IN  = dpath("dish_canonical_summary_v18.csv")
ALIASES_OUT = dpath("dish_aliases_v19.csv")
SUMMARY_OUT = dpath("dish_canonical_summary_v19.csv")
AUDIT       = dpath("recipe_drops_applied.csv")

# Web-verified real chain items — rescue these from PRO_VETO
RESCUE_CANONICALS = {
    "cali fresh sandwich steak sub",              # Subway Cali Fresh Steak
    "baja jack sandwich steak sub",               # Subway Baja Jack pattern-match
    "lover pepperoni pizza",                       # Pizza Hut Pepperoni Lover's
    "gourmet lover meat pizza",                    # Pizza Hut Meat Lover's variant
    "burger meat whataburger",                     # Whataburger
    "burger whataburger",                          # Whataburger
    "burger meat whataburger whatameal",           # Whataburger Whatameal
    "burger whataburger whatameal",                # Whataburger Whatameal
    "burger cheese jalape whataburger whatameal",  # Whataburger Whatameal
    "bacon burger cheese whataburger whatameal",   # Whataburger Whatameal
    "sandwich whatachick whatameal",               # Whataburger Whatachick'n
    "chicken sandwich spicy whatameal",            # Whataburger
    "chicken grilled sandwich whatameal",          # Whataburger
    "big cheese kahuna steak sub",                 # Quiznos Big Kahuna
    "beef cheddar classic",                        # Arby's Classic Beef 'n Cheddar
    "beef cheddar pound",                          # Arby's Half-Pound Beef 'n Cheddar
    "cheeseburger mega monster",                   # Hardee's Monster family
    "bbq cowboy",                                  # Hardee's BBQ Cowboy
    "burrito egg normous",                         # Burger King Egg-normous
    "steamer sub york",                            # Quiznos NY Steamer
    "beyond burger wraptor",                       # Carl's Jr Beyond Wraptor (verified)
    "chicken fried luann steak",                   # Luby's LuAnn (verified)
    "buffalitos chicken grilled wrap",             # Buffalo Wild Wings Buffalitos (verified)
    "lad na pasta",                                # Thai Lad Na (verified)
    "all natural roasted turkey",                  # Subway All-Natural Roasted Turkey pattern
}

PROTECT_REASONS_ETHNIC = {"obscure", "unknown", "unrecognized"}

# User-flagged rescues from the L25-drop sample review. Pure rescues just stay
# as-is; merge rescues get folded into an existing canonical.
PURE_RESCUES = {
    19,      # pancakes — generic but valid recipe-search target
    38,      # waffle — same reasoning as pancakes; needed as merge target
    84454,   # gai goo moo pan = "moo goo gai pan" token-sorted, real Chinese dish
    1258,    # fillet fish
}

# source_cluster_id → (target_cluster_id, target_canonical_name)
MERGE_RESCUES = {
    # variants → pancakes
    84465: (19, "pancakes"),       # friendly gluten original pancakes
    25683: (19, "pancakes"),       # breakfast feast pancakes
    84546: (19, "pancakes"),       # bacon creations feast pancake
    84547: (19, "pancakes"),       # creations feast pancake sausage
    # variants → french toast
    84540: (691, "french toast"),  # breakfast feast french toast
    # variants → waffle
    25689: (38, "waffle"),         # breakfast feast waffles
    # variants → bowl burrito chicken (generic burrito bowl)
    84536: (28086, "bowl burrito chicken"),  # bowl burrito chicken mexico
    # ribs variants → pork ribs / bbq ribs
    25596:  (969, "pork ribs"),    # order original ribs
    84483:  (1143, "bbq ribs"),    # bbq house order ribs
    84484:  (1143, "bbq ribs"),    # chipotle honey order ribs
    130370: (1143, "bbq ribs"),    # dry order ribs rub texas
    # chicken sandwich variants
    84549: (25456, "chicken sandwich spicy"),  # chicken sandwich spicy take
    84548: (687, "chicken sandwich"),          # chicken sandwich signature take
}
RESCUED_CIDS = PURE_RESCUES | set(MERGE_RESCUES.keys())

# Pull in decisions from the swipe-review tool AND the LLM auto-judge.
# Loading order matters: swipe decisions (manual) win over auto-judge decisions
# (automated) — so process swipe file last.
import json, os
DECISIONS_FILES = [
    dpath("dish_rescue_decisions.json"),  # Gemini auto-judge on drop rescues
    dpath("dish_review_decisions.json"),  # User swipes — applied last so they override
]
n_tool_keep = n_tool_merge = n_tool_drop_confirm = 0
seen_in_decisions = set()
for path in DECISIONS_FILES:
    if not os.path.exists(path):
        continue
    with open(path) as _f:
        _dec = json.load(_f)["decisions"]
    for cid_str, v in _dec.items():
        cid = int(cid_str)
        if v["action"] == "keep":
            # If a later file says keep but an earlier file said merge, drop the merge.
            MERGE_RESCUES.pop(cid, None)
            if cid not in PURE_RESCUES:
                PURE_RESCUES.add(cid)
                RESCUED_CIDS.add(cid)
                n_tool_keep += 1
        elif v["action"] == "merge":
            if cid in PURE_RESCUES:
                continue  # earlier 'keep' wins
            MERGE_RESCUES[cid] = (int(v["target_cid"]), v["target_canonical"])
            RESCUED_CIDS.add(cid)
            if cid not in seen_in_decisions:
                n_tool_merge += 1
        elif v["action"] == "drop":
            if cid not in seen_in_decisions:
                n_tool_drop_confirm += 1
        seen_in_decisions.add(cid)
print(f"loaded decisions files: +{n_tool_keep} keep, +{n_tool_merge} merge, "
      f"{n_tool_drop_confirm} drop-confirms (already dropped)")

drops = set()
audit_rows = []
rescue_counts = defaultdict(int)
bucket_drop_count = defaultdict(int)

with open(COMPARE) as f:
    for row in csv.DictReader(f):
        bucket = row["bucket"]
        cid    = int(row["cluster_id"])
        name   = row["canonical_name"]
        cnt    = int(row["total_count"])
        pro_r  = row["pro_reason"]

        if cid in RESCUED_CIDS:
            rescue_counts["user_rescue" + ("_merge" if cid in MERGE_RESCUES else "_pure")] += 1
            continue
        if bucket == "BOTH_DROP":
            drops.add(cid)
            bucket_drop_count["BOTH_DROP"] += 1
            audit_rows.append([cid, name, cnt, "BOTH_DROP", row["gemini_reason"], pro_r])
        elif bucket == "PRO_VETO":
            if name in RESCUE_CANONICALS:
                rescue_counts["chain_rescue"] += 1
                continue
            if pro_r in PROTECT_REASONS_ETHNIC and cnt >= 3:
                rescue_counts["ethnic_rescue"] += 1
                continue
            drops.add(cid)
            bucket_drop_count["PRO_VETO"] += 1
            audit_rows.append([cid, name, cnt, "PRO_VETO", row["gemini_reason"], pro_r])

print(f"=== drop set ===")
print(f"  BOTH_DROP dropped:  {bucket_drop_count['BOTH_DROP']:,}")
print(f"  PRO_VETO  dropped:  {bucket_drop_count['PRO_VETO']:,}")
print(f"  rescues:            {dict(rescue_counts)}")
print(f"  total clusters dropped: {len(drops):,}")

# Write audit
with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "total_count", "bucket", "gemini_reason", "pro_reason"])
    for r in sorted(audit_rows, key=lambda x: -x[2]):
        w.writerow(r)
print(f"\nwrote {AUDIT}")

# Filter aliases.
#   - cluster_id in drops → drop the row
#   - cluster_id in MERGE_RESCUES → rewrite cluster_id + canonical_name to target,
#     tag method as 'l25_merge_rescue' for audit
#   - else → keep as-is
n_in = n_out = n_dropped_aliases = n_merged_aliases = 0
n_alias_count_in = n_alias_count_out = 0
with open(ALIASES_IN) as f, open(ALIASES_OUT, "w", newline="") as out:
    rd = csv.DictReader(f)
    wr = csv.DictWriter(out, fieldnames=rd.fieldnames)
    wr.writeheader()
    for row in rd:
        n_in += 1
        ac = int(row["alias_count"])
        n_alias_count_in += ac
        cid = int(row["cluster_id"])
        if cid in drops:
            n_dropped_aliases += 1
            continue
        if cid in MERGE_RESCUES:
            target_cid, target_name = MERGE_RESCUES[cid]
            row["cluster_id"]     = str(target_cid)
            row["canonical_name"] = target_name
            row["method"]         = "l25_merge_rescue"
            n_merged_aliases += 1
        wr.writerow(row)
        n_out += 1
        n_alias_count_out += ac

print(f"\naliases: {n_in:,} → {n_out:,}  (dropped {n_dropped_aliases:,}, merged-rewrite {n_merged_aliases:,})")
print(f"sum(alias_count): {n_alias_count_in:,} → {n_alias_count_out:,}  (dropped {n_alias_count_in - n_alias_count_out:,})")

# Canonicalize by max-count alias.
# Policy: for each cluster, the canonical_name is the alias with the highest
# alias_count. Merge-rescue rows are excluded from voting because they represent
# noise variants the user explicitly folded into the target — they shouldn't
# rename the target cluster.
#
# Tiebreaker: fewer tokens > shorter string > alphabetic.
MERGE_RESCUE_METHODS = {"l25_merge_rescue"}

cluster_aliases = defaultdict(list)
with open(ALIASES_OUT) as f:
    for row in csv.DictReader(f):
        cluster_aliases[int(row["cluster_id"])].append(row)

def has_single_letter_token(name):
    """B.M.T. → 'b m t'; "General's" → "general s"; "Beef 'n Cheddar" → "n".
    Single-letter tokens are almost always tokenization artifacts."""
    return any(len(t) == 1 for t in name.split())

new_canonical = {}
n_renamed = 0
rename_examples = []
for cid, rows in cluster_aliases.items():
    voters = [r for r in rows if r["method"] not in MERGE_RESCUE_METHODS]
    if not voters:
        voters = rows  # cluster only has rescue rows — fall back to all
    # Prefer aliases free of single-letter tokens. Fall back to all voters if
    # the cluster has nothing clean.
    clean = [r for r in voters if not has_single_letter_token(r["alias_name"])]
    pool = clean if clean else voters
    def sort_key(r):
        name = r["alias_name"]
        return (-int(r["alias_count"]), len(name.split()), len(name), name)
    chosen = sorted(pool, key=sort_key)[0]["alias_name"]
    new_canonical[cid] = chosen
    old = rows[0]["canonical_name"]
    if chosen != old:
        n_renamed += 1
        if len(rename_examples) < 15:
            rename_examples.append((cid, old, chosen, sum(int(r["alias_count"]) for r in rows)))

# Rewrite ALIASES_OUT with updated canonical_name
with open(ALIASES_OUT) as f:
    rd = csv.DictReader(f)
    fields = rd.fieldnames
    rows_all = [dict(r) for r in rd]
for r in rows_all:
    r["canonical_name"] = new_canonical[int(r["cluster_id"])]
with open(ALIASES_OUT, "w", newline="") as out:
    wr = csv.DictWriter(out, fieldnames=fields)
    wr.writeheader()
    for r in rows_all:
        wr.writerow(r)

print(f"\ncanonicalize pass: {n_renamed:,} clusters renamed (canonical_name shifted to max-count alias)")
if rename_examples:
    print("  examples:")
    for cid, old, new, cnt in rename_examples:
        print(f"    cid={cid:>6}  count={cnt:>6}  {old!r:50s} → {new!r}")

# Rebuild summary by aggregating the (now-renamed) aliases file.
agg_count = defaultdict(int)
agg_n_aliases = defaultdict(int)
cid_to_canonical = {}
with open(ALIASES_OUT) as f:
    for row in csv.DictReader(f):
        cid = int(row["cluster_id"])
        agg_count[cid] += int(row["alias_count"])
        agg_n_aliases[cid] += 1
        cid_to_canonical.setdefault(cid, row["canonical_name"])

with open(SUMMARY_OUT, "w", newline="") as out:
    wr = csv.writer(out)
    wr.writerow(["cluster_id", "canonical_name", "n_aliases", "total_count"])
    for cid in sorted(agg_count, key=lambda c: -agg_count[c]):
        wr.writerow([cid, cid_to_canonical[cid], agg_n_aliases[cid], agg_count[cid]])

print(f"\nsummary: rebuilt from filtered aliases → {len(agg_count):,} canonicals")
print(f"sum(total_count): {sum(agg_count.values()):,}")
