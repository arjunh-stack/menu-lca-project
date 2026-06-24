"""Layer 22 — clean doubled-token canonicals.

The v15 alias key has 1,012 canonicals containing a duplicated token
(`bacon cheese egg egg`, `chicken chicken fried`, `enchiladas enchiladas`,
`pepperoni pepperoni pizza`, etc.). These are mostly normalization artifacts
from earlier layers (Layer 4 format-folding, Layer 10 synonym rewrite, Layer 13
single-letter-strip, etc.) where a token was added to a name that already
contained it. They are also unreachable at index time because
`build_dish_index.py:lookup_key` dedups via `set()`.

But SOME doubled tokens are legitimate dish-name repetitions:
  - `mahi mahi`     (Hawaiian fish)
  - `huli huli`     (Hawaiian chicken)
  - `dan dan`       (Sichuan noodles)
  - `bang bang`     (shrimp/chicken)
  - `peri peri`     (Nando's chicken)
  - `boom boom`     (shrimp, sauce)
  - `shabu shabu`   (Japanese hot pot)
  - `yum yum`       (sauce / dish naming convention)
  - `lau lau`       (Hawaiian)
  - `chop chop`     (salad, brand)
  - `pon pon`, `woo woo`, `kko kko`, `kee kee`, etc.

Approach (same shape as Layer 13 single-letter cleanup):
For each canonical with one or more duplicate tokens:
  1. Identify the doubled tokens.
  2. If EVERY doubled token is in PRESERVE_DOUBLED → keep the canonical as-is.
  3. Otherwise, strip duplicates of the non-preserved tokens (keep one copy each).
     Preserved-doubled tokens stay doubled.
  4. Re-sort the resulting tokens.
  5. If cleaned form == an existing canonical → MERGE this cluster into it.
  6. If cleaned form has ≥1 token and is not an existing canonical → RENAME.
  7. If cleaned form is empty → DROP (shouldn't happen).

Inputs:  dish_aliases_v15.csv, dish_canonical_summary_v15.csv
Outputs: dish_aliases_v16.csv, dish_canonical_summary_v16.csv, doubled_token_changes.csv
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
from collections import defaultdict, Counter

ALIAS_IN  = dpath("dish_aliases_v15.csv")
SUMM_IN   = dpath("dish_canonical_summary_v15.csv")
ALIAS_OUT = dpath("dish_aliases_v16.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v16.csv")
AUDIT     = dpath("doubled_token_changes.csv")

PRESERVE_DOUBLED = {
    # Hawaiian / Polynesian
    "mahi", "huli", "lau", "kalua",
    # Chinese / Sichuan
    "dan", "kung", "pao",
    # Thai / SE Asian
    "kee", "mao", "kai", "gai", "tom",
    # Korean
    "kko", "bibim",
    # Japanese
    "shabu",
    # African / Portuguese
    "peri",
    # American / restaurant brand-ish but commonly used as dish name
    "bang", "boom", "yum", "yummy", "woo", "pon", "chop",
    # other
    "naan", "soon", "won",
}

clusters = []
canonical_to_cid = {}
with open(SUMM_IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["total_count"])
        except (ValueError, KeyError):
            continue
        canon = row["canonical_name"]
        clusters.append((cid, canon, cnt))
        canonical_to_cid.setdefault(canon, cid)
print(f"loaded {len(clusters):,} clusters")

def doubled_tokens(toks):
    c = Counter(toks)
    return {t for t, n in c.items() if n >= 2}

def clean(name):
    """Return cleaned form: dedup all non-preserved doubled tokens, keep preserved doubles."""
    toks = name.split()
    dups = doubled_tokens(toks)
    if not dups:
        return name, set(), set()
    to_strip = dups - PRESERVE_DOUBLED   # tokens whose duplicates we drop
    preserved = dups & PRESERVE_DOUBLED  # tokens we leave doubled
    if not to_strip:
        return name, set(), preserved
    new_toks = []
    seen_strip = set()
    for t in toks:
        if t in to_strip:
            if t in seen_strip:
                continue
            seen_strip.add(t)
        new_toks.append(t)
    return " ".join(sorted(new_toks)), to_strip, preserved

merge_into = {}
rename_to  = {}
drop_cids  = set()
audit_rows = []

n_hit = 0
n_no_change = 0  # all dups were preserved
for cid, canon, cnt in clusters:
    cleaned, stripped, preserved = clean(canon)
    if not stripped:
        if preserved:
            n_no_change += 1
        continue
    n_hit += 1
    if not cleaned:
        drop_cids.add(cid)
        audit_rows.append((cid, canon, cnt, "drop", "(empty)", "", ",".join(sorted(stripped)), ",".join(sorted(preserved))))
    elif cleaned in canonical_to_cid and canonical_to_cid[cleaned] != cid:
        target = canonical_to_cid[cleaned]
        merge_into[cid] = target
        audit_rows.append((cid, canon, cnt, "merge", cleaned, target, ",".join(sorted(stripped)), ",".join(sorted(preserved))))
    else:
        rename_to[cid] = cleaned
        audit_rows.append((cid, canon, cnt, "rename", cleaned, "", ",".join(sorted(stripped)), ",".join(sorted(preserved))))

print(f"\ncanonicals with doubled tokens: {n_hit + n_no_change:,}")
print(f"  preserved doubles only (no change): {n_no_change:,}")
print(f"  cleaned (had at least one artifact dupe): {n_hit:,}")
print(f"  → actions: {dict(Counter(r[3] for r in audit_rows))}")

target_canonical = {}
for cid in merge_into.values():
    for c, can, _ in clusters:
        if c == cid:
            target_canonical[cid] = can
            break

print(f"\nrewriting alias table → {ALIAS_OUT}")
kept = 0
with open(ALIAS_IN) as f, open(ALIAS_OUT, "w", newline="") as g:
    r = csv.DictReader(f)
    w = csv.writer(g)
    w.writerow(r.fieldnames)
    for row in r:
        try:
            cid = int(row["cluster_id"])
        except ValueError:
            continue
        if cid in drop_cids:
            continue
        if cid in merge_into:
            target = merge_into[cid]
            new_canon = target_canonical[target]
            new_method = "doubled_strip_merge" if row["method"].strip().lower() == "self" else row["method"]
            w.writerow([new_canon, row["alias_name"], row["alias_count"], target, new_method])
            kept += 1
            continue
        if cid in rename_to:
            new_canon = rename_to[cid]
            if row["method"].strip().lower() == "self":
                w.writerow([new_canon, new_canon, row["alias_count"], cid, "self"])
            else:
                w.writerow([new_canon, row["alias_name"], row["alias_count"], cid, row["method"]])
            kept += 1
            continue
        w.writerow([row[k] for k in r.fieldnames])
        kept += 1
print(f"  kept {kept:,} alias rows")

print(f"\nrebuilding {SUMM_OUT}")
agg = defaultdict(lambda: [None, 0, 0])
with open(ALIAS_OUT) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["alias_count"])
        except (ValueError, KeyError):
            continue
        agg[cid][0] = row["canonical_name"]
        agg[cid][1] += 1
        agg[cid][2] += cnt
with open(SUMM_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "n_aliases", "total_count"])
    for cid, (canon, n_al, tot) in sorted(agg.items(), key=lambda x: -x[1][2]):
        w.writerow([cid, canon, n_al, tot])
print(f"  {len(agg):,} final clusters (was {len(clusters):,})")

with open(AUDIT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "old_canonical", "total_count", "action", "cleaned", "merged_into_cid", "stripped_dups", "preserved_dups"])
    audit_rows.sort(key=lambda r: -r[2])
    for r in audit_rows:
        w.writerow(r)
print(f"wrote {AUDIT}")
