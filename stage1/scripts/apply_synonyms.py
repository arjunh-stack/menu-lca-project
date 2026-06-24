"""Layer 10 — apply curated synonym dict to merge cluster aliases.

Reads:
  - synonyms.csv (only rows where notes starts with 'APPLY')
  - dish_aliases.csv (Layer 9 output: every alias, with cluster_id)

For each Layer 9 cluster, rewrite its canonical name's tokens via the synonym
map. Then group clusters whose rewritten canonicals are equal (after dedup +
sort) — those clusters merge. Within each merged group, the new canonical is
the rewritten form of the highest-count member's name (so e.g. if `italian sub`
has 50k count and `italian hoagie` has 100, both merge under canonical
`italian sub`).

Outputs:
  - dish_aliases_v2.csv (final alias key, post-Layer-10): every name from v3
    mapped to its final canonical, with method ∈ {self, fuzzy, synonym}.
  - dish_canonical_summary_v2.csv: one row per final cluster.
  - synonym_merges.csv: audit — for each Layer-10 merge, the L9 clusters that
    got combined and the rewrite that triggered it.
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
ALIAS_IN  = dpath("dish_aliases.csv")
ALIAS_OUT = dpath("dish_aliases_v2.csv")
SUMM_OUT  = dpath("dish_canonical_summary_v2.csv")
MERGES_OUT = dpath("synonym_merges.csv")

# Load APPLY-only synonym map
syn_map = {}
with open(SYN) as f:
    for row in csv.DictReader(f):
        notes = row["notes"].strip().upper()
        if not notes.startswith("APPLY"):
            continue
        a = row["alias_token"].strip().lower()
        c = row["canonical_token"].strip().lower()
        if a == c:
            continue
        syn_map[a] = c
print(f"loaded {len(syn_map)} APPLY synonym entries")
for a, c in sorted(syn_map.items()):
    print(f"  {a:>14} -> {c}")

def rewrite(canon):
    """Apply synonym map to tokens, dedup, sort. Returns (new_key, was_rewritten)."""
    toks = canon.split()
    new_toks = [syn_map.get(t, t) for t in toks]
    rewritten = new_toks != toks
    new_toks = sorted(set(new_toks))
    return " ".join(new_toks), rewritten

# Load Layer 9 cluster info: for each cluster_id, gather its canonical (the
# name where method=self) and its total_count (sum of alias_counts).
print(f"\nloading {ALIAS_IN}")
cluster_canonical = {}    # cid -> canonical name
cluster_total     = defaultdict(int)
all_aliases       = []    # list of (canonical, alias, count, cid, method)
with open(ALIAS_IN) as f:
    for row in csv.DictReader(f):
        try:
            cid = int(row["cluster_id"])
            cnt = int(row["alias_count"])
        except ValueError:
            continue
        all_aliases.append((row["canonical_name"], row["alias_name"], cnt, cid, row["method"]))
        cluster_total[cid] += cnt
        if row["method"].strip().lower() == "self":
            cluster_canonical[cid] = row["canonical_name"]
print(f"loaded {len(cluster_canonical):,} L9 clusters, {len(all_aliases):,} alias rows")

# For each L9 cluster, compute its rewrite key. Group clusters by rewrite key.
key_to_cluster_ids = defaultdict(list)
cluster_was_rewritten = {}
for cid, canon in cluster_canonical.items():
    key, rewritten = rewrite(canon)
    key_to_cluster_ids[key].append(cid)
    cluster_was_rewritten[cid] = rewritten

# For each rewrite-group: pick the highest-count L9 cluster as the "head".
# The new canonical = rewrite of the head's canonical (so synonym terms in the
# head's name also get normalized).
n_groups_with_merge = sum(1 for cids in key_to_cluster_ids.values() if len(cids) > 1)
print(f"\nrewrite groups: {len(key_to_cluster_ids):,} (of which {n_groups_with_merge:,} merge ≥2 L9 clusters)")

# Map each L9 cluster_id -> final cluster_id (= highest-count cluster in its group)
cid_to_final = {}
final_canonical = {}
merges_audit = []   # (final_canonical_name, [(merged_in_canonical, merged_in_count), ...])
for key, cids in key_to_cluster_ids.items():
    if len(cids) == 1:
        cid = cids[0]
        cid_to_final[cid] = cid
        final_canonical[cid] = rewrite(cluster_canonical[cid])[0] if cluster_was_rewritten[cid] else cluster_canonical[cid]
        continue
    # Multiple clusters merge — choose head by max total_count, ties by lex
    head = max(cids, key=lambda c: (cluster_total[c], -ord(cluster_canonical[c][0]) if cluster_canonical[c] else 0))
    head_canon_rewritten, _ = rewrite(cluster_canonical[head])
    for cid in cids:
        cid_to_final[cid] = head
    final_canonical[head] = head_canon_rewritten
    merges_audit.append((
        head_canon_rewritten,
        sorted([(cluster_canonical[c], cluster_total[c], c) for c in cids if c != head], key=lambda x: -x[1])[:10],
        cluster_canonical[head],
        cluster_total[head],
    ))

# Write the new alias table. Each original alias row gets:
#   new canonical_name = final_canonical[cid_to_final[old_cid]]
#   new cluster_id = cid_to_final[old_cid]
#   new method:
#     - "self" if alias_name == new canonical_name
#     - "synonym" if the original L9 cluster was merged into a different L9 cluster
#                  via synonym rewrite (i.e. cid_to_final[old_cid] != old_cid),
#                  OR if the alias's name was rewritten (alias name had a synonym token)
#     - else keep original ("fuzzy" or whatever)
print(f"\nwriting {ALIAS_OUT}")
seen_self = set()
with open(ALIAS_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["canonical_name", "alias_name", "alias_count", "cluster_id", "method"])
    rows_out = []
    for canon_old, alias, cnt, old_cid, method_old in all_aliases:
        final_cid = cid_to_final[old_cid]
        new_canon = final_canonical[final_cid]
        if alias == new_canon:
            method = "self"
        elif final_cid != old_cid:
            # Cluster got merged into another via synonym
            method = "synonym"
        elif new_canon != canon_old:
            # Same cluster, but canonical name itself got rewritten (cluster was head AND had a synonym token)
            method = "synonym" if method_old == "self" else method_old
        else:
            method = method_old
        rows_out.append((new_canon, alias, cnt, final_cid, method))
    # Ensure each final cluster has exactly one "self" row — if rewriting eliminated the canonical's match, promote highest-count alias
    by_final = defaultdict(list)
    for r in rows_out:
        by_final[r[3]].append(r)
    final_rows = []
    for fcid, rs in by_final.items():
        canon = rs[0][0]
        # Re-evaluate self: row whose alias == canon and is only one
        self_rows = [r for r in rs if r[1] == canon]
        if len(self_rows) == 1:
            final_rows.extend(rs)
        elif len(self_rows) == 0:
            # No alias matches canonical (e.g. all aliases were rewritten away). Promote highest-count.
            rs_sorted = sorted(rs, key=lambda r: -r[2])
            head_alias = rs_sorted[0][1]
            new_rs = []
            for r in rs:
                if r[1] == head_alias:
                    new_rs.append((canon, r[1], r[2], r[3], "self"))
                else:
                    new_rs.append(r)
            final_rows.extend(new_rs)
        else:
            # Multiple aliases match canonical (shouldn't happen): keep first as self, rest as synonym
            for i, r in enumerate(rs):
                if r[1] == canon and i == 0:
                    final_rows.append(r)
                elif r[1] == canon:
                    final_rows.append((r[0], r[1], r[2], r[3], "synonym"))
                else:
                    final_rows.append(r)
    final_rows.sort(key=lambda r: (-sum(x[2] for x in by_final[r[3]]), r[3], -r[2]))
    for r in final_rows:
        w.writerow(r)

# Summary
print(f"writing {SUMM_OUT}")
final_clusters = defaultdict(lambda: [None, 0, 0])  # fcid -> [canonical, n_aliases, total_count]
for r in final_rows:
    canon, alias, cnt, fcid, method = r
    final_clusters[fcid][0] = canon
    final_clusters[fcid][1] += 1
    final_clusters[fcid][2] += cnt
with open(SUMM_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cluster_id", "canonical_name", "n_aliases", "total_count"])
    for fcid, (canon, n_al, tot) in sorted(final_clusters.items(), key=lambda x: -x[1][2]):
        w.writerow([fcid, canon, n_al, tot])

# Audit
print(f"writing {MERGES_OUT}")
with open(MERGES_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["final_canonical", "head_l9_canonical", "head_count", "n_merged_clusters", "merged_in_examples_top10"])
    merges_audit.sort(key=lambda x: -x[3])
    for final_canon, merged_in, head_canon, head_count in merges_audit:
        examples = "; ".join(f"{n} ({cnt})" for n, cnt, _ in merged_in)
        w.writerow([final_canon, head_canon, head_count, len(merged_in)+1, examples])

# Final stats
n_l9 = len(cluster_canonical)
n_final = len(final_clusters)
print(f"\nDONE")
print(f"  L9 clusters: {n_l9:,}")
print(f"  L10 clusters: {n_final:,}")
print(f"  collapsed: {n_l9 - n_final:,} ({100*(n_l9-n_final)/n_l9:.1f}%)")
