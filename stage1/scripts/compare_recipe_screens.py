"""Layer 25 stage 2 — compare Gemini and DeepSeek Pro verdicts.

Gemini ran on all 113,925 canonicals (KEEP/DROP).
DeepSeek Pro ran only on Gemini-DROPs (30,879 items).

Buckets:
  - GEMINI_KEEP                 : Gemini said KEEP (DeepSeek didn't see)
  - BOTH_DROP                   : Gemini said DROP, DeepSeek confirmed DROP — safe to drop
  - GEMINI_DROP_PRO_RESCUE      : Gemini said DROP, DeepSeek said KEEP — disputed, rescue by default
  - HAS_ERROR                   : parse/api error somewhere

Outputs:
  - recipe_screen_compare.csv   (all canonicals, joined verdicts, bucket)
  - recipe_screen_review_samples.md (sampled BOTH_DROP and PRO_RESCUE for user spot-check)
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
import random
from collections import defaultdict
from pathlib import Path

GEMINI   = dpath("recipe_screen_gemini.csv")
DEEPSEEK = dpath("recipe_screen_deepseek.csv")
COMPARE  = dpath("recipe_screen_compare.csv")
REVIEW   = dpath("recipe_screen_review_samples.md")

random.seed(42)

# Load gemini (full)
gemini = {}
with open(GEMINI) as f:
    for row in csv.DictReader(f):
        gemini[int(row["cluster_id"])] = row

# Load deepseek (Gemini-DROPs only)
deepseek = {}
with open(DEEPSEEK) as f:
    for row in csv.DictReader(f):
        deepseek[int(row["cluster_id"])] = row

print(f"gemini judgments:   {len(gemini):,}")
print(f"deepseek judgments: {len(deepseek):,} (re-screen of Gemini-DROPs)")

buckets = defaultdict(list)
for cid, g in gemini.items():
    gv = g["verdict"]
    cnt = int(g["total_count"])
    rec = {
        "cluster_id":      cid,
        "canonical_name":  g["canonical_name"],
        "total_count":     cnt,
        "gemini_verdict":  gv,
        "gemini_reason":   g["reason"],
        "deepseek_verdict": "",
        "deepseek_reason":  "",
    }
    if gv in ("PARSE_ERROR", "API_ERROR"):
        bucket = "HAS_ERROR"
    elif gv == "KEEP":
        bucket = "GEMINI_KEEP"
    else:  # DROP
        d = deepseek.get(cid)
        if d is None:
            bucket = "HAS_ERROR"
        else:
            rec["deepseek_verdict"] = d["verdict"]
            rec["deepseek_reason"]  = d["reason"]
            if d["verdict"] == "DROP":
                bucket = "BOTH_DROP"
            elif d["verdict"] == "KEEP":
                bucket = "GEMINI_DROP_PRO_RESCUE"
            else:
                bucket = "HAS_ERROR"
    rec["bucket"] = bucket
    buckets[bucket].append(rec)

print("\n=== bucket sizes ===")
for b in ["GEMINI_KEEP", "BOTH_DROP", "GEMINI_DROP_PRO_RESCUE", "HAS_ERROR"]:
    rows = buckets[b]
    pct = 100 * len(rows) / len(gemini) if gemini else 0
    total_count_sum = sum(r["total_count"] for r in rows)
    print(f"  {b:24s}: {len(rows):>7,} ({pct:5.1f}%)  total menu rows: {total_count_sum:,}")

# Write full join CSV
with open(COMPARE, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "cluster_id", "canonical_name", "total_count",
        "gemini_verdict", "gemini_reason",
        "deepseek_verdict", "deepseek_reason",
        "bucket",
    ])
    w.writeheader()
    for b in ["BOTH_DROP", "GEMINI_DROP_PRO_RESCUE", "HAS_ERROR", "GEMINI_KEEP"]:
        rows = sorted(buckets[b], key=lambda r: -r["total_count"])
        for r in rows:
            w.writerow(r)
print(f"\nwrote {COMPARE}")

# Build review samples
def sample_with_top(rows, n_top=10, n_random=15):
    rs = sorted(rows, key=lambda x: -x["total_count"])
    top = rs[:n_top]
    rest = rs[n_top:]
    random.shuffle(rest)
    return top + rest[:n_random]

with open(REVIEW, "w") as f:
    f.write("# Layer 25 — Recipe-test screen review samples\n\n")
    f.write(f"**Two-model classification on {len(gemini):,} canonicals**\n\n")
    f.write("- Gemini Flash judged all canonicals (KEEP / DROP).\n")
    f.write("- DeepSeek V4 Pro re-judged the 30,879 Gemini-DROPs (validation pass).\n")
    f.write("- KEEPs are trusted on Gemini alone since over-keeping is the safe direction.\n\n")
    f.write("| Bucket | Count | % | Sum menu rows |\n|---|---|---|---|\n")
    for b in ["GEMINI_KEEP", "BOTH_DROP", "GEMINI_DROP_PRO_RESCUE", "HAS_ERROR"]:
        rows = buckets[b]
        pct = 100 * len(rows) / len(gemini)
        total = sum(r["total_count"] for r in rows)
        f.write(f"| {b} | {len(rows):,} | {pct:.1f}% | {total:,} |\n")

    f.write("\n---\n\n")
    f.write("## BOTH_DROP — both models said DROP (drop candidates)\n\n")
    f.write("These are safe to drop — both models agreed. Spot-check below.\n\n")
    drops = buckets["BOTH_DROP"]

    f.write("### Top 30 highest-count BOTH_DROP\n\n")
    f.write("| count | canonical | gemini reason | deepseek reason |\n|---|---|---|---|\n")
    for r in sorted(drops, key=lambda x: -x["total_count"])[:30]:
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['deepseek_reason']} |\n")

    by_reason = defaultdict(list)
    for r in drops:
        by_reason[r["gemini_reason"]].append(r)
    f.write("\n### Random samples by gemini reason\n")
    for reason in sorted(by_reason, key=lambda x: -len(by_reason[x])):
        rs = by_reason[reason]
        f.write(f"\n#### `gemini_reason = {reason}` ({len(rs):,} drops)\n\n")
        f.write("| count | canonical | gemini | deepseek |\n|---|---|---|---|\n")
        for r in sample_with_top(rs, n_top=5, n_random=10):
            f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['deepseek_reason']} |\n")

    f.write("\n---\n\n")
    f.write("## GEMINI_DROP_PRO_RESCUE — Gemini said DROP, Pro said KEEP\n\n")
    f.write("Pro's stronger reasoning rescued these from Gemini's over-aggression. Default: KEEP them.\n\n")
    rescues = buckets["GEMINI_DROP_PRO_RESCUE"]

    f.write("### Top 30 highest-count rescues\n\n")
    f.write("| count | canonical | gemini said DROP because | deepseek said KEEP because |\n|---|---|---|---|\n")
    for r in sorted(rescues, key=lambda x: -x["total_count"])[:30]:
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['deepseek_reason']} |\n")

    f.write("\n### Random sample of rescues (30)\n\n")
    f.write("| count | canonical | gemini | gem reason | deepseek | ds reason |\n|---|---|---|---|---|---|\n")
    for r in sample_with_top(rescues, n_top=10, n_random=20):
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_verdict']} | {r['gemini_reason']} | {r['deepseek_verdict']} | {r['deepseek_reason']} |\n")

print(f"wrote {REVIEW}")
