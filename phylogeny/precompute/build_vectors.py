"""Stage 5.1 — dish → semantic recipe vector.

For every canonical dish that survives the v1 filter, build one dense
384-dim vector that encodes "what this recipe is made of, in what
proportions" — so that two dishes with similar mass-weighted ingredient
mixes land close together under cosine/Euclidean geometry.

Method:
  1. Read recipes.jsonl. Keep a dish iff it has a non-error ingredient
     list AND total_count >= --min-count (default 2; drops the ~36k
     single-restaurant long-tail dishes for v1 — rerun with
     --min-count 1 to add them back).
  2. Collect the distinct ingredient strings (lowercased) and embed each
     once with all-MiniLM-L6-v2 (the same sentence-transformer the LCA
     matcher uses). Cache to ingredient_embeddings.npy so reruns skip it.
  3. Each dish vector = proportion-weighted mean of its ingredient
     embeddings, then L2-normalized. Mass-weighted (not presence-only)
     so proportion differences move dishes apart.

Outputs (phylogeny/data/):
  ingredient_embeddings.npy   (n_ingredients, 384) float32  — cache
  ingredient_names.json       list[str], row-aligned to the cache
  dish_vectors.npy            (n_dishes, 384) float32       — L2-normed
  dish_meta.csv               idx,cluster_id,canonical_name,top_raw_name,
                              cuisine_bucket,total_count,n_ingredients
                              (idx == row in dish_vectors.npy)

Usage:
  python3 build_vectors.py                 # min-count 2 (v1 default)
  python3 build_vectors.py --min-count 1   # full corpus
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent          # phylogeny/precompute
PHYLO_DIR = SCRIPT_DIR.parent                         # phylogeny
REPO = PHYLO_DIR.parent                               # repo root
DATA_DIR = PHYLO_DIR / "data"

RECIPES = REPO / "recipes" / "recipes.jsonl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

ING_EMB = DATA_DIR / "ingredient_embeddings.npy"
ING_NAMES = DATA_DIR / "ingredient_names.json"
DISH_VEC = DATA_DIR / "dish_vectors.npy"
DISH_META = DATA_DIR / "dish_meta.csv"


def load_dishes(min_count: int) -> list[dict]:
    """Read recipes.jsonl; keep non-error dishes with usable ingredient
    mass and total_count >= min_count."""
    kept, n_err, n_zeromass, n_belowmin = [], 0, 0, 0
    with open(RECIPES) as f:
        for line in f:
            d = json.loads(line)
            if d.get("error"):
                n_err += 1
                continue
            ings = d.get("ingredients") or []
            if not ings:
                n_zeromass += 1
                continue
            # weight by proportion_pct; fall back to grams if all zero.
            w = [float(i.get("proportion_pct") or 0) for i in ings]
            if sum(w) <= 0:
                w = [float(i.get("grams") or 0) for i in ings]
            if sum(w) <= 0:
                n_zeromass += 1
                continue
            if int(d.get("total_count") or 0) < min_count:
                n_belowmin += 1
                continue
            kept.append({
                "cluster_id": d["cluster_id"],
                "canonical_name": d.get("canonical_name", ""),
                "top_raw_name": d.get("top_raw_name", ""),
                "cuisine_bucket": d.get("cuisine_bucket", "default"),
                "total_count": int(d.get("total_count") or 0),
                "ingredients": [
                    (str(i.get("ingredient", "")).strip().lower(), wt)
                    for i, wt in zip(ings, w)
                    if str(i.get("ingredient", "")).strip()
                ],
            })
    print(f"  kept {len(kept):,} dishes "
          f"(dropped {n_err} error, {n_zeromass} zero-mass, "
          f"{n_belowmin:,} below min-count {min_count})")
    return [d for d in kept if d["ingredients"]]


def embed_ingredients(names: list[str]) -> np.ndarray:
    """Encode distinct ingredient strings; reuse the on-disk cache when it
    already covers exactly this name set."""
    if ING_EMB.exists() and ING_NAMES.exists():
        cached = json.loads(ING_NAMES.read_text())
        if cached == names:
            print(f"  ingredient embedding cache hit ({len(names):,})")
            return np.load(ING_EMB)
        print("  ingredient cache stale — re-encoding")
    from sentence_transformers import SentenceTransformer
    print(f"  loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(names, batch_size=256, show_progress_bar=True,
                        normalize_embeddings=True).astype(np.float32)
    np.save(ING_EMB, emb)
    ING_NAMES.write_text(json.dumps(names))
    return emb


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-count", type=int, default=2,
                    help="Drop dishes with total_count below this (default 2)")
    args = ap.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"reading {RECIPES.name} (min-count {args.min_count}) ...")
    dishes = load_dishes(args.min_count)

    # distinct ingredient vocabulary, stable order
    vocab = sorted({ing for d in dishes for ing, _ in d["ingredients"]})
    ing_idx = {name: i for i, name in enumerate(vocab)}
    print(f"  {len(vocab):,} distinct ingredients")

    emb = embed_ingredients(vocab)

    print("building dish vectors ...")
    vecs = np.zeros((len(dishes), emb.shape[1]), dtype=np.float32)
    for row, d in enumerate(dishes):
        idxs = np.array([ing_idx[ing] for ing, _ in d["ingredients"]])
        w = np.array([wt for _, wt in d["ingredients"]], dtype=np.float32)
        v = (emb[idxs] * w[:, None]).sum(0) / w.sum()
        norm = np.linalg.norm(v)
        vecs[row] = v / norm if norm > 0 else v
    np.save(DISH_VEC, vecs)

    with open(DISH_META, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "cluster_id", "canonical_name", "top_raw_name",
                    "cuisine_bucket", "total_count", "n_ingredients"])
        for row, d in enumerate(dishes):
            w.writerow([row, d["cluster_id"], d["canonical_name"],
                        d["top_raw_name"], d["cuisine_bucket"],
                        d["total_count"], len(d["ingredients"])])

    print(f"DONE — {len(dishes):,} dish vectors → {DISH_VEC.name}, "
          f"{DISH_META.name}")


if __name__ == "__main__":
    main()
