#!/usr/bin/env python3
"""Diet-flexibility vs. best-case Nutri-Score improvement (single panel).

Companion to build_flexibility_curves.py (GHG/water/land). Same machinery,
one health metric instead of three environmental footprints.

Metric
------
Nutri-Score on the 0-100 scale (nutriscore_0to100, Clark-2022 layer). Higher =
LESS healthy (grade A mean ~23, grade E mean ~64), so it is oriented exactly
like a footprint: a diner "improves" by moving to a LOWER score. We therefore
reuse the identical best-case reduction definition.

Design (mirrors the footprint figure, locked 2026-05-28)
--------------------------------------------------------
  * Distance   : native 384-D embedding, COSINE distance.
  * Reduction  : BEST-CASE. reduction_i(r) = (s_i - min_{d<=r} s_j) / s_i,
                 self included (d pinned to 0) so reduction in [0,1],
                 non-decreasing in r. "How much healthier COULD you go."
  * Aggregation: UNWEIGHTED mean across center dishes; IQR band for context.

Caveat (same as footprints): cosine distances are compressed, so beyond r~0.3
the neighbour set is a large share of ALL dishes and the curve degenerates
toward "switch to the single healthiest dish", not a craving-preserving swap.

Inputs (read-only)
------------------
  phylogeny/data/dish_vectors.npy          (39166 x 384) float32, L2-norm
  nutrition/dish_nutriscore_manifold.csv   idx-aligned to the vectors

Outputs
-------
  flexibility/nutriscore_curve.csv
  flexibility/nutriscore_flexibility.png
  flexibility/nutriscore_summary.json
"""
from __future__ import annotations

import csv
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "flexibility")
os.makedirs(OUT, exist_ok=True)

COLOR = "#8e44ad"  # distinct from the GHG/water/land panels
RADII = np.concatenate([
    np.round(np.linspace(0.00, 0.30, 31), 4),
    np.round(np.linspace(0.325, 0.60, 12), 4),
])
BLOCK = 2000


def load() -> tuple[np.ndarray, np.ndarray]:
    """Return (vectors_with_score, score_0to100) on the valid intersection."""
    vecs = np.load(os.path.join(ROOT, "phylogeny", "data", "dish_vectors.npy")).astype(np.float32)
    rows = list(csv.DictReader(open(os.path.join(ROOT, "nutrition", "dish_nutriscore_manifold.csv"))))
    assert len(rows) == vecs.shape[0], "manifold csv / vector row mismatch"

    keep_idx, scores = [], []
    for r in rows:
        idx = int(r["idx"])
        s = r.get("nutriscore_0to100")
        try:
            s = float(s)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(s) or s <= 0:
            continue
        keep_idx.append(idx)
        scores.append(s)

    keep_idx = np.array(keep_idx)
    V = vecs[keep_idx]
    s = np.array(scores, dtype=np.float64)
    print(f"[load] kept {len(keep_idx)} dishes with vector + valid Nutri-Score "
          f"(of {vecs.shape[0]} vectors)")
    return V, s


def compute_curve(V: np.ndarray, s: np.ndarray):
    n = V.shape[0]
    nr = len(RADII)
    red = np.empty((n, nr), dtype=np.float32)
    neigh = np.empty((n, nr), dtype=np.float32)
    s_row = s[None, :]

    for start in range(0, n, BLOCK):
        end = min(start + BLOCK, n)
        D = 1.0 - (V[start:end] @ V.T)
        np.clip(D, 0.0, None, out=D)
        rows = np.arange(end - start)
        D[rows, start + rows] = 0.0          # pin self-distance to 0
        s_center = s[start:end]
        for ri, r in enumerate(RADII):
            mask = D <= r
            neigh[start:end, ri] = mask.sum(axis=1)
            best = np.where(mask, s_row, np.inf).min(axis=1)
            red[start:end, ri] = (s_center - best) / s_center
        print(f"[curve] centers {end}/{n}")

    return {
        "radius": RADII,
        "mean_neighbors": neigh.mean(axis=0),
        "score_mean": red.mean(axis=0),
        "score_p25": np.percentile(red, 25, axis=0),
        "score_median": np.percentile(red, 50, axis=0),
        "score_p75": np.percentile(red, 75, axis=0),
    }


def write_csv(out: dict):
    path = os.path.join(OUT, "nutriscore_curve.csv")
    keys = list(out.keys())
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for i in range(len(out["radius"])):
            w.writerow([f"{out[k][i]:.6g}" for k in keys])
    print(f"[csv] wrote {path}")


def plot(out: dict, n_dishes: int):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = out["radius"]
    mean = out["score_mean"] * 100
    p25 = out["score_p25"] * 100
    p75 = out["score_p75"] * 100

    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    ax.fill_between(r, p25, p75, color=COLOR, alpha=0.15, label="inter-quartile range")
    ax.plot(r, mean, color=COLOR, lw=2.4, label="mean across dishes")
    ax.set_title("Dietary flexibility vs. best-case\nNutri-Score improvement in restaurant dishes",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Flexibility  (cosine radius in dish manifold)")
    ax.set_ylabel("Best-case Nutri-Score reduction vs. center dish (%)\n[lower 0–100 score = healthier]")
    ax.set_xlim(0, r.max())
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    for rr in (0.05, 0.10, 0.20, 0.30):
        j = int(np.argmin(np.abs(r - rr)))
        ax.annotate(f"~{out['mean_neighbors'][j]:,.0f} dishes",
                    xy=(r[j], mean[j]), xytext=(0, 6),
                    textcoords="offset points", fontsize=6.5, color="#555", ha="center")

    note = (f"n = {n_dishes:,} canonical dishes with a 384-D manifold vector and a "
            f"valid Nutri-Score (0–100, Clark-2022; lower = healthier).\nReduction = "
            f"(center − healthiest dish within radius) / center, unweighted mean. "
            f"Caveat: beyond r~0.3 the neighbour set is a large share of ALL dishes.")
    fig.text(0.5, -0.02, note, ha="center", va="top", fontsize=7.5, color="#333", wrap=True)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    path = os.path.join(OUT, "nutriscore_flexibility.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"[plot] wrote {path}")


def main():
    V, s = load()
    out = compute_curve(V, s)
    write_csv(out)
    plot(out, V.shape[0])

    def at(rr):
        return round(float(out["score_mean"][int(np.argmin(np.abs(RADII - rr)))] * 100), 1)

    summary = {
        "n_dishes": int(V.shape[0]),
        "metric": "nutriscore_0to100 (lower=healthier)",
        "distance": "cosine, native 384-D embedding",
        "reduction": "best-case (healthiest neighbour within radius), unweighted mean",
        "radii": [float(x) for x in RADII],
        "headline_pct": {"r0.05": at(0.05), "r0.10": at(0.10), "r0.20": at(0.20)},
    }
    with open(os.path.join(OUT, "nutriscore_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("[done]", json.dumps(summary["headline_pct"], indent=2))


if __name__ == "__main__":
    main()
