"""Stage 5.2 — dish vectors → hierarchical tree (the "phylogeny").

Hierarchical agglomerative clustering (Ward linkage) over the L2-normed
dish embeddings. Ward on normalized vectors approximates cosine geometry
while letting SciPy build the full dendrogram in one pass. The result is
a binary tree whose leaves are dishes and whose internal nodes are
clades — progressively finer as you descend.

The tree shape is a *compositional-similarity* clustering rendered as a
phylogeny; it is not an evolutionary tree (see PLAN.md).

It also picks the subset of internal nodes worth naming. Labelling all
~n-1 internal nodes would be absurd, so it cuts the dendrogram at three
granularities (--cuts, default 24/150/800 clusters) and records the
maximal subtree node behind each flat cluster. label_clades.py names
exactly those.

Outputs (phylogeny/data/):
  tree.json     nested dendrogram. Leaf  {id:"L<idx>", leaf:true, dish_idx,
                cluster_id, name, cuisine_bucket, total_count, n_ingredients}
                Internal {id:"N<k>", height, n_leaves, children:[...]}
  clades.json   list of nodes to label: {node_id, level, n_leaves,
                top_dish_idxs:[...]}  — level 0 coarsest

Usage:
  python3 build_tree.py
  python3 build_tree.py --cuts 24 150 800
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage, to_tree, fcluster

# A 39k-leaf Ward dendrogram can be several thousand levels deep on its
# longest path; every traversal here recurses to tree depth.
sys.setrecursionlimit(1_000_000)

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DISH_VEC = DATA_DIR / "dish_vectors.npy"
DISH_META = DATA_DIR / "dish_meta.csv"
TREE_JSON = DATA_DIR / "tree.json"
CLADES_JSON = DATA_DIR / "clades.json"


def load_meta() -> list[dict]:
    with open(DISH_META) as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cuts", type=int, nargs="+", default=[24, 150, 800],
                    help="Cluster counts for the labelled clade levels")
    args = ap.parse_args()

    vecs = np.load(DISH_VEC).astype(np.float64)
    meta = load_meta()
    n = len(vecs)
    assert n == len(meta), f"vector/meta mismatch: {n} vs {len(meta)}"
    print(f"linkage (Ward) over {n:,} dishes ...")
    Z = linkage(vecs, method="ward")  # SciPy computes pdist internally

    # --- nested tree -------------------------------------------------
    # Node ids come straight from SciPy's ClusterNode.id so that the
    # clade list below references the *same* ids the tree carries:
    # leaves are [0, n), internal nodes [n, 2n-2].
    root = to_tree(Z)
    n_internal = [0]

    def build(node):
        if node.is_leaf():
            m = meta[node.id]
            return {
                "id": f"L{node.id}",
                "leaf": True,
                "dish_idx": node.id,
                "cluster_id": int(m["cluster_id"]),
                "name": m["canonical_name"] or m["top_raw_name"],
                "cuisine_bucket": m["cuisine_bucket"],
                "total_count": int(m["total_count"]),
                "n_ingredients": int(m["n_ingredients"]),
            }
        n_internal[0] += 1
        return {
            "id": f"N{node.id}",
            "height": round(float(node.dist), 5),
            "n_leaves": int(node.get_count()),
            "children": [build(node.left), build(node.right)],
        }

    tree = build(root)
    TREE_JSON.write_text(json.dumps(tree))
    print(f"  tree.json — {n_internal[0]:,} internal nodes")

    # --- clade selection for labelling -------------------------------
    # For each cut, every flat cluster is exactly the leaf set of one
    # subtree. Find that subtree's node id with a single post-order pass:
    # a node "is" the clade for cluster c iff all its leaves carry c and
    # its parent's leaves do not.
    totals = np.array([int(m["total_count"]) for m in meta])
    clades, seen = [], set()
    for level, k in enumerate(args.cuts):
        if k >= n:
            continue
        assign = fcluster(Z, t=k, criterion="maxclust")  # 1-based per leaf

        # post-order: each node -> cluster id if its whole subtree is one
        # cluster, else -1 (MIXED). Only scalars are stored (O(n) memory);
        # leaf lists are gathered on demand for selected clades.
        node_val = {}

        def tag(node):
            if node.is_leaf():
                node_val[node.id] = int(assign[node.id])
                return
            tag(node.left)
            tag(node.right)
            lv, rv = node_val[node.left.id], node_val[node.right.id]
            node_val[node.id] = lv if (lv == rv and lv != -1) else -1

        tag(root)

        def subtree_leaves(node, acc):
            if node.is_leaf():
                acc.append(node.id)
            else:
                subtree_leaves(node.left, acc)
                subtree_leaves(node.right, acc)
            return acc

        def collect(node, parent_uniform):
            v = node_val[node.id]
            if v != -1 and not parent_uniform:
                leaves = subtree_leaves(node, [])
                key = (min(leaves), len(leaves))
                if key not in seen:
                    seen.add(key)
                    top = sorted(leaves, key=lambda i: -totals[i])[:20]
                    clades.append({
                        "node_id": f"N{node.id}",  # matches tree.json
                        "level": level,
                        "n_leaves": len(leaves),
                        "top_dish_idxs": [int(i) for i in top],
                    })
                return  # whole subtree is one clade; stop descending
            if not node.is_leaf():
                collect(node.left, v != -1)
                collect(node.right, v != -1)

        collect(root, False)
        print(f"  cut k={k}: cumulative {len(clades):,} unique clades")

    CLADES_JSON.write_text(json.dumps(clades))
    print(f"DONE — {len(clades):,} clades to label → {CLADES_JSON.name}")


if __name__ == "__main__":
    # Run on a thread with a large stack so the deep recursive traversals
    # of a tall dendrogram can't overflow the C stack and segfault.
    import threading
    import traceback
    threading.stack_size(512 * 1024 * 1024)
    box = {}

    def _run():
        try:
            main()
        except BaseException as e:  # propagate to the parent for exit code
            box["err"] = e
            traceback.print_exc()

    t = threading.Thread(target=_run)
    t.start()
    t.join()
    if "err" in box:
        sys.exit(1)
