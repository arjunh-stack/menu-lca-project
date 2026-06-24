"""Aggregate per-category proposals into a single review batch.

Reads all proposals/category_*.csv, normalizes confidence labels, validates
each row against dish_canonical_summary_v17.csv, and writes:

  - proposals/aggregated_high.csv     — high-confidence merges/renames to apply
  - proposals/aggregated_medium.csv   — medium-confidence (user review needed)
  - proposals/aggregated_judgment.csv — low/judgment/flag/info (informational only)
  - proposals/aggregation_report.md   — summary stats

Validation:
  - source_cid must exist in v17 summary
  - target_cid (for merges) must exist in v17 summary
  - source_cid != target_cid
  - no duplicate source_cid across all proposals (cross-category conflict)
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
import os
from collections import defaultdict
from pathlib import Path

PROPOSALS_DIR = Path(dpath("proposals"))
SUMM = dpath("dish_canonical_summary_v17.csv")

OUT_HIGH = PROPOSALS_DIR / "aggregated_high.csv"
OUT_MED  = PROPOSALS_DIR / "aggregated_medium.csv"
OUT_JUDG = PROPOSALS_DIR / "aggregated_judgment.csv"
REPORT   = PROPOSALS_DIR / "aggregation_report.md"

# Load v17 cluster ids and counts
v17_cids = {}
v17_canonical = {}
with open(SUMM) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
        except (ValueError, KeyError):
            continue
        v17_cids[cid] = int(row["total_count"])
        v17_canonical[cid] = row["canonical_name"]

# Confidence normalization
def normalize_conf(c):
    if c is None: return "unknown"
    c = c.strip().lower()
    if c in ("high",): return "high"
    if c in ("medium", "med"): return "medium"
    if c in ("low", "judgment", "flag", "info", ""): return "judgment"
    return "unknown"

all_rows = []
issues = []
file_stats = defaultdict(lambda: defaultdict(int))

for csv_path in sorted(PROPOSALS_DIR.glob("category_*.csv")):
    cat = csv_path.stem.replace("category_", "")
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            row["_source_file"] = cat
            row["_line"] = i
            row["_conf_norm"] = normalize_conf(row.get("confidence", ""))
            all_rows.append(row)
            file_stats[cat][row["_conf_norm"]] += 1

print(f"loaded {len(all_rows):,} proposals from {len(file_stats)} categories")

def maybe_int(s):
    try: return int(s)
    except (ValueError, TypeError): return None

# Validate + dedup
seen_sources = {}
high, medium, judgment = [], [], []
for r in all_rows:
    action = (r.get("action") or "").strip().lower()
    src = maybe_int(r.get("source_cid"))
    tgt = maybe_int(r.get("target_cid"))
    if action not in ("merge", "rename"):
        issues.append((r["_source_file"], r["_line"], f"unknown action: {action}"))
        continue
    if src is None:
        issues.append((r["_source_file"], r["_line"], "missing source_cid"))
        continue
    if src not in v17_cids:
        issues.append((r["_source_file"], r["_line"], f"source_cid {src} not in v17"))
        continue
    if action == "merge":
        if tgt is None:
            issues.append((r["_source_file"], r["_line"], "merge missing target_cid"))
            continue
        if tgt not in v17_cids:
            issues.append((r["_source_file"], r["_line"], f"target_cid {tgt} not in v17"))
            continue
        if src == tgt:
            issues.append((r["_source_file"], r["_line"], "self-merge"))
            continue
    if action == "rename":
        new_canon = (r.get("new_canonical") or "").strip()
        if not new_canon:
            issues.append((r["_source_file"], r["_line"], "rename missing new_canonical"))
            continue
    if src in seen_sources:
        prior = seen_sources[src]
        issues.append((r["_source_file"], r["_line"], f"duplicate source_cid {src}, also at {prior}"))
        continue
    seen_sources[src] = (r["_source_file"], r["_line"])
    bucket = high if r["_conf_norm"] == "high" else (medium if r["_conf_norm"] == "medium" else judgment)
    bucket.append(r)

print(f"validated:")
print(f"  high:     {len(high):,}")
print(f"  medium:   {len(medium):,}")
print(f"  judgment: {len(judgment):,}")
print(f"  issues:   {len(issues):,}")

# Write output files
out_cols = ["category", "action", "source_cid", "source_canonical", "source_count",
            "target_cid", "target_canonical", "target_count", "new_canonical",
            "reason", "confidence_orig"]

def write_bucket(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(out_cols)
        rows.sort(key=lambda r: (r["_source_file"], -(maybe_int(r.get("source_count")) or 0)))
        for r in rows:
            w.writerow([
                r["_source_file"],
                r.get("action", ""),
                r.get("source_cid", ""),
                r.get("source_canonical", ""),
                r.get("source_count", ""),
                r.get("target_cid", ""),
                r.get("target_canonical", ""),
                r.get("target_count", ""),
                r.get("new_canonical", ""),
                r.get("reason", ""),
                r.get("confidence", ""),
            ])

write_bucket(high, OUT_HIGH)
write_bucket(medium, OUT_MED)
write_bucket(judgment, OUT_JUDG)

# Report
with open(REPORT, "w") as f:
    f.write("# Proposal aggregation report\n\n")
    f.write(f"**Total proposals:** {len(all_rows):,} across {len(file_stats)} categories\n\n")
    f.write(f"After validation: {len(high) + len(medium) + len(judgment):,} valid, {len(issues):,} issues\n\n")
    f.write("## Per-category breakdown\n\n")
    f.write("| Category | total | high | medium | judgment |\n|---|---|---|---|---|\n")
    for cat in sorted(file_stats):
        s = file_stats[cat]
        total = sum(s.values())
        f.write(f"| {cat} | {total} | {s.get('high',0)} | {s.get('medium',0)} | {s.get('judgment',0)} |\n")
    f.write(f"\n## Aggregated buckets\n\n")
    f.write(f"- `aggregated_high.csv`: **{len(high):,} rows** — recommended for auto-apply\n")
    f.write(f"- `aggregated_medium.csv`: **{len(medium):,} rows** — needs user review\n")
    f.write(f"- `aggregated_judgment.csv`: **{len(judgment):,} rows** — informational only\n\n")
    if issues:
        f.write(f"## Validation issues ({len(issues)})\n\n")
        for cat, line, msg in issues[:50]:
            f.write(f"- `{cat}.csv:{line}` — {msg}\n")
        if len(issues) > 50:
            f.write(f"\n... and {len(issues)-50} more\n")
print(f"\nwrote {REPORT}")
print(f"wrote {OUT_HIGH}, {OUT_MED}, {OUT_JUDG}")
