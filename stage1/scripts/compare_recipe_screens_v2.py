"""Layer 25 stage 2b — 3-way comparator: Gemini + DeepSeek-on-Gemini-DROPs +
DeepSeek-on-Gemini-KEEPs.

Buckets:
  - BOTH_KEEP          : Gemini KEEP, Pro KEEP — safe to keep
  - PRO_RESCUE         : Gemini DROP, Pro KEEP — kept (Pro vetoed Gemini DROP)
  - BOTH_DROP          : Gemini DROP, Pro DROP — drop
  - PRO_VETO           : Gemini KEEP, Pro DROP — drop candidate (Pro vetoed Gemini KEEP)
  - HAS_ERROR          : any parse/api error

Outputs:
  - recipe_screen_compare_v2.csv   (all canonicals, joined 3-way verdicts, bucket)
  - recipe_screen_review_v2.md     (sampled review of new PRO_VETO bucket especially)
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
DS_DROP  = dpath("recipe_screen_deepseek.csv")
DS_KEEP  = dpath("recipe_screen_deepseek_keeps.csv")
COMPARE  = dpath("recipe_screen_compare_v2.csv")
REVIEW   = dpath("recipe_screen_review_v2.md")

random.seed(42)

def load_csv_by_cid(path):
    d = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            d[int(row["cluster_id"])] = row
    return d

gemini  = load_csv_by_cid(GEMINI)
ds_drop = load_csv_by_cid(DS_DROP)
ds_keep = load_csv_by_cid(DS_KEEP)

print(f"gemini:   {len(gemini):,}")
print(f"ds_drop:  {len(ds_drop):,} (Pro re-screen of Gemini-DROPs)")
print(f"ds_keep:  {len(ds_keep):,} (Pro re-screen of Gemini-KEEPs)")

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
        "pro_verdict":     "",
        "pro_reason":      "",
    }
    if gv in ("PARSE_ERROR", "API_ERROR"):
        bucket = "HAS_ERROR"
    elif gv == "KEEP":
        d = ds_keep.get(cid)
        if d is None:
            bucket = "HAS_ERROR"
        else:
            rec["pro_verdict"] = d["verdict"]
            rec["pro_reason"]  = d["reason"]
            if d["verdict"] == "KEEP":
                bucket = "BOTH_KEEP"
            elif d["verdict"] == "DROP":
                bucket = "PRO_VETO"
            else:
                bucket = "HAS_ERROR"
    else:  # gemini DROP
        d = ds_drop.get(cid)
        if d is None:
            bucket = "HAS_ERROR"
        else:
            rec["pro_verdict"] = d["verdict"]
            rec["pro_reason"]  = d["reason"]
            if d["verdict"] == "DROP":
                bucket = "BOTH_DROP"
            elif d["verdict"] == "KEEP":
                bucket = "PRO_RESCUE"
            else:
                bucket = "HAS_ERROR"
    rec["bucket"] = bucket
    buckets[bucket].append(rec)

print("\n=== bucket sizes ===")
for b in ["BOTH_KEEP", "PRO_RESCUE", "BOTH_DROP", "PRO_VETO", "HAS_ERROR"]:
    rows = buckets[b]
    pct = 100 * len(rows) / len(gemini) if gemini else 0
    total_count_sum = sum(r["total_count"] for r in rows)
    print(f"  {b:12s}: {len(rows):>7,} ({pct:5.1f}%)  menu rows: {total_count_sum:>10,}")

# Write full join CSV
with open(COMPARE, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "cluster_id", "canonical_name", "total_count",
        "gemini_verdict", "gemini_reason",
        "pro_verdict", "pro_reason",
        "bucket",
    ])
    w.writeheader()
    # write in bucket priority order, by count desc within each
    for b in ["PRO_VETO", "BOTH_DROP", "PRO_RESCUE", "HAS_ERROR", "BOTH_KEEP"]:
        rows = sorted(buckets[b], key=lambda r: -r["total_count"])
        for r in rows:
            w.writerow(r)
print(f"\nwrote {COMPARE}")

# Sampling
def sample_with_top(rows, n_top=10, n_random=15):
    rs = sorted(rows, key=lambda x: -x["total_count"])
    top = rs[:n_top]
    rest = rs[n_top:]
    random.shuffle(rest)
    return top + rest[:n_random]

with open(REVIEW, "w") as f:
    f.write("# Layer 25 — Recipe-test 2-model review (v2)\n\n")
    f.write(f"**Two-model classification on {len(gemini):,} canonicals.**\n\n")
    f.write("- Gemini Flash judged all canonicals (KEEP / DROP).\n")
    f.write("- DeepSeek V4 Pro re-judged BOTH the Gemini-DROPs AND the Gemini-KEEPs.\n")
    f.write("- All disagreements surfaced — no model is auto-trusted.\n\n")

    f.write("## Bucket sizes\n\n")
    f.write("| Bucket | Count | % | Menu rows | Recommended action |\n|---|---|---|---|---|\n")
    actions = {
        "BOTH_KEEP":   "KEEP",
        "PRO_RESCUE":  "KEEP (Pro vetoed Gemini DROP)",
        "BOTH_DROP":   "DROP",
        "PRO_VETO":    "**SPOT-CHECK** (Pro vetoed Gemini KEEP — NEW)",
        "HAS_ERROR":   "KEEP (safe)",
    }
    for b in ["BOTH_KEEP", "PRO_RESCUE", "BOTH_DROP", "PRO_VETO", "HAS_ERROR"]:
        rows = buckets[b]
        pct = 100 * len(rows) / len(gemini)
        total = sum(r["total_count"] for r in rows)
        f.write(f"| {b} | {len(rows):,} | {pct:.1f}% | {total:,} | {actions[b]} |\n")

    if_dropped_total = sum(r["total_count"] for r in buckets["BOTH_DROP"]) + \
                       sum(r["total_count"] for r in buckets["PRO_VETO"])
    canonicals_after = len(buckets["BOTH_KEEP"]) + len(buckets["PRO_RESCUE"]) + len(buckets["HAS_ERROR"])
    f.write(f"\n**If you accept all proposed drops (BOTH_DROP + PRO_VETO):**\n")
    f.write(f"- Canonicals dropped: {len(buckets['BOTH_DROP']) + len(buckets['PRO_VETO']):,}\n")
    f.write(f"- Menu rows dropped: {if_dropped_total:,}\n")
    f.write(f"- Projected v19 canonicals: {canonicals_after:,}\n\n")

    f.write("---\n\n")
    f.write("## PRO_VETO — Gemini said KEEP, Pro said DROP\n\n")
    f.write("**These are the new drop candidates that need your spot-check.** "
            "Pro thinks these names don't pass the recipe-search test even though Gemini did.\n\n")
    veto = buckets["PRO_VETO"]

    f.write("### Top 30 highest-count PRO_VETO\n\n")
    f.write("| count | canonical | gemini said KEEP because | pro said DROP because |\n|---|---|---|---|\n")
    for r in sorted(veto, key=lambda x: -x["total_count"])[:30]:
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['pro_reason']} |\n")

    by_reason = defaultdict(list)
    for r in veto:
        by_reason[r["pro_reason"]].append(r)
    f.write("\n### Random samples by Pro's DROP reason\n")
    for reason in sorted(by_reason, key=lambda x: -len(by_reason[x])):
        rs = by_reason[reason]
        f.write(f"\n#### `pro_reason = {reason}` ({len(rs):,} pro-vetoes)\n\n")
        f.write("| count | canonical | gemini reason | pro reason |\n|---|---|---|---|\n")
        for r in sample_with_top(rs, n_top=5, n_random=10):
            f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['pro_reason']} |\n")

    f.write("\n---\n\n")
    f.write("## BOTH_DROP — both models said DROP (already-validated drops)\n\n")
    f.write("Re-showing top of bucket for completeness.\n\n")
    drops = buckets["BOTH_DROP"]
    f.write("### Top 20 highest-count BOTH_DROP\n\n")
    f.write("| count | canonical | gemini reason | pro reason |\n|---|---|---|---|\n")
    for r in sorted(drops, key=lambda x: -x["total_count"])[:20]:
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['pro_reason']} |\n")

    f.write("\n---\n\n")
    f.write("## PRO_RESCUE — Gemini said DROP, Pro said KEEP (already-validated rescues)\n\n")
    f.write("Re-showing top of bucket for completeness.\n\n")
    rescues = buckets["PRO_RESCUE"]
    f.write("### Top 20 highest-count PRO_RESCUE\n\n")
    f.write("| count | canonical | gemini said DROP because | pro said KEEP because |\n|---|---|---|---|\n")
    for r in sorted(rescues, key=lambda x: -x["total_count"])[:20]:
        f.write(f"| {r['total_count']} | `{r['canonical_name']}` | {r['gemini_reason']} | {r['pro_reason']} |\n")

print(f"wrote {REVIEW}")
