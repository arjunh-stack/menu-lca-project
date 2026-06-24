"""Stage 5.3 — dish vectors → 2D manifold layout + density regions.

The dendrogram (build_tree.py) forces every dish into a single-parent
tree. This step builds the honest alternative: a 2D projection where a
dish can sit between regions, so multi-parent dishes ("chicken alfredo
pizza") aren't mis-filed. The web tool toggles between the two.

Projection: UMAP (cosine metric) when umap-learn is importable; if it
is not — e.g. a numba/numpy ABI mismatch on the run host — it falls
back to scikit-learn t-SNE so the unattended pipeline still finishes.
The method actually used is recorded in the output and surfaced in the
UI, so the fallback is never silent.

Density regions: scikit-learn HDBSCAN on the 2-D projection, giving an
optional region-colour overlay that lines up with what the eye sees as
a blob on the scatter. (HDBSCAN on the raw 384-d vectors is single-
threaded and minutes-slow with no payoff here — the overlay is about
the *visible* map.)

Output (phylogeny/data/):
  umap.json   {method, n, points:[{idx,x,y,region}, ...]}
              region = -1 for HDBSCAN noise

Usage:
  python3 build_umap.py
"""
import json
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DISH_VEC = DATA_DIR / "dish_vectors.npy"
UMAP_JSON = DATA_DIR / "umap.json"


def project(vecs: np.ndarray) -> tuple[np.ndarray, str]:
    """2D projection — UMAP if available, else t-SNE."""
    try:
        import umap  # noqa: F401
        print("  projecting with UMAP (cosine) ...")
        reducer = umap.UMAP(n_neighbors=25, min_dist=0.15, metric="cosine",
                            random_state=42, verbose=True)
        return reducer.fit_transform(vecs), "umap"
    except Exception as e:  # ImportError or numba/ABI failure
        print(f"  UMAP unavailable ({type(e).__name__}: {e})")
        print("  falling back to scikit-learn t-SNE ...")
        from sklearn.manifold import TSNE
        xy = TSNE(n_components=2, metric="cosine", init="pca",
                  perplexity=40, random_state=42).fit_transform(vecs)
        return xy, "tsne"


def regions(xy: np.ndarray) -> np.ndarray:
    """HDBSCAN density labels on the 2-D layout (-1 == noise). Fast: a
    KD-tree in 2-D handles 39k points in well under a second."""
    try:
        from sklearn.cluster import HDBSCAN
        print("  HDBSCAN density regions (on 2-D layout) ...")
        return HDBSCAN(min_cluster_size=60).fit_predict(xy)
    except Exception as e:
        print(f"  HDBSCAN skipped ({type(e).__name__}: {e})")
        return np.full(len(xy), -1, dtype=int)


def main():
    vecs = np.load(DISH_VEC).astype(np.float32)
    print(f"projecting {len(vecs):,} dishes ...")

    xy, method = project(vecs)
    region = regions(np.asarray(xy, dtype=np.float64))

    # normalize coords into a stable [0, 1000] box for the frontend
    xy = np.asarray(xy, dtype=np.float64)
    mn, mx = xy.min(0), xy.max(0)
    span = np.where((mx - mn) > 0, mx - mn, 1.0)
    xy = (xy - mn) / span * 1000.0

    points = [
        {"idx": i, "x": round(float(xy[i, 0]), 2),
         "y": round(float(xy[i, 1]), 2), "region": int(region[i])}
        for i in range(len(vecs))
    ]
    UMAP_JSON.write_text(json.dumps({
        "method": method,
        "n": len(points),
        "n_regions": int(region.max()) + 1 if region.max() >= 0 else 0,
        "points": points,
    }))
    print(f"DONE — {method} layout for {len(points):,} dishes → {UMAP_JSON.name}")


if __name__ == "__main__":
    main()
