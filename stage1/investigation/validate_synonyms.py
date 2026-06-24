"""Validate synonyms.csv: for each entry, show what canonicals contain that token
and what they would map to if the synonym is applied.

Output: synonym_validation.csv with columns:
  alias_token, canonical_token, group, n_clusters_affected, total_count_affected,
  example_canonicals (top-5 by count, semicolon-joined),
  example_rewrites (top-5 by count, semicolon-joined: "before -> after")

Manual review then: in synonyms.csv, set notes='SKIP' on rows that look wrong.
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

SYN  = dpath("synonyms.csv")
SUMM = dpath("dish_canonical_summary.csv")
OUT  = dpath("synonym_validation.csv")

with open(SYN) as f:
    syn_rows = list(csv.DictReader(f))

print(f"loaded {len(syn_rows)} synonym entries")

clusters = []
with open(SUMM) as f:
    for row in csv.DictReader(f):
        try:
            clusters.append((row["canonical_name"], int(row["total_count"])))
        except (ValueError, KeyError):
            continue
print(f"loaded {len(clusters):,} canonical clusters")

# Index canonicals by tokens for fast lookup
token_to_clusters = defaultdict(list)
for canon, cnt in clusters:
    for tok in canon.split():
        token_to_clusters[tok].append((canon, cnt))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "alias_token", "canonical_token", "group", "notes",
        "n_clusters_affected", "total_count_affected",
        "example_canonicals_top5", "example_rewrites_top5",
    ])
    for syn in syn_rows:
        a = syn["alias_token"].strip()
        c = syn["canonical_token"].strip()
        # Skip self-canonical entries (just declaring canonicalness)
        if a == c:
            w.writerow([a, c, syn["group"], syn["notes"], 0, 0, "(self-canonical, no rewrite)", ""])
            continue
        matches = token_to_clusters.get(a, [])
        if not matches:
            w.writerow([a, c, syn["group"], syn["notes"], 0, 0, "(no canonicals contain this token)", ""])
            continue
        matches_sorted = sorted(matches, key=lambda x: -x[1])
        n_aff = len(matches)
        total = sum(cnt for _, cnt in matches)
        examples = "; ".join(f"{canon} ({cnt})" for canon, cnt in matches_sorted[:5])
        rewrites = []
        for canon, cnt in matches_sorted[:5]:
            new_tokens = [c if t == a else t for t in canon.split()]
            new_tokens = sorted(set(new_tokens))  # match Layer 3 normalization
            new_canon = " ".join(new_tokens)
            rewrites.append(f"{canon} -> {new_canon}")
        w.writerow([
            a, c, syn["group"], syn["notes"],
            n_aff, total,
            examples,
            "; ".join(rewrites),
        ])

print(f"wrote {OUT}")
