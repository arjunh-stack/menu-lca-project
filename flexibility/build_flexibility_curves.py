#!/usr/bin/env python3
"""Diet-flexibility vs. footprint-abatement curves.

Question
--------
If a diner who wants dish X is willing to accept any dish "close enough" to
X in craving-space, how much GHG / water / land could they shed by switching
to the greenest acceptable substitute?  We sweep the willingness-to-substitute
("flexibility") as a radius in the dish manifold and read off the best-case
abatement.

Design (locked with the user, 2026-05-28)
-----------------------------------------
  * Distance space : native 384-D embedding, COSINE distance (the metric the
                     manifold was built on).  d(i,j) = 1 - <v_i, v_j>, vectors
                     are L2-normalised so this is exact.
  * Reduction      : BEST-CASE.  For center i at radius r,
                     reduction_i(r) = (f_i - min_{d(i,j)<=r} f_j) / f_i.
                     Self is included (d=0), so reduction >= 0 and is
                     non-decreasing in r.  "How much COULD you save."
  * Aggregation    : UNWEIGHTED mean across all center dishes (every canonical
                     dish counts once).  IQR band shown for context only.
  * Footprint basis: per-KG intensity (ghg_kgco2e_per_kg, water_m3_per_kg,
                     land_pt_per_kg).

Caveat (see header note in the figure)
---------------------------------------
Cosine distances are compressed: by r~0.3 the neighbour set is ~40% of all
dishes, so large-r abatement degenerates into "switch to the globally greenest
dish" and is NOT a meaningful substitution.  The honest regime is small r.

Inputs (read-only)
------------------
  phylogeny/data/dish_vectors.npy   (39166 x 384) float32, L2-normalised
  phylogeny/data/dish_meta.csv      idx -> cluster_id, canonical_name, ...
  lca/dish_lca.jsonl                cluster_id -> per-kg footprints

Outputs
-------
  flexibility/flexibility_curves.csv     curve data (radius x metric)
  flexibility/flexibility_abatement.png  3-panel compound figure
  flexibility/flexibility_summary.json   run metadata
"""
from __future__ import annotations

import csv
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "flexibility")
os.makedirs(OUT, exist_ok=True)

METRICS = [
    ("ghg", "ghg_kgco2e_per_kg", "GHG emissions", "kg CO₂e / kg", "#c0392b"),
    ("water", "water_m3_per_kg", "Water use", "m³ / kg", "#2980b9"),
    ("land", "land_pt_per_kg", "Land use", "Pt / kg", "#27ae60"),
]

# Radius grid: dense where the action is (small r), extending into saturation.
RADII = np.concatenate([
    np.round(np.linspace(0.00, 0.30, 31), 4),   # step 0.01 in the meaningful band
    np.round(np.linspace(0.325, 0.60, 12), 4),  # coarser tail to show saturation
])
BLOCK = 2000  # center dishes per block (B x N similarity matrix in RAM)


def load() -> tuple[np.ndarray, list[dict], dict[str, np.ndarray]]:
    """Return (vectors_with_lca, meta_rows, footprint_arrays) on the intersection."""
    vecs = np.load(os.path.join(ROOT, "phylogeny", "data", "dish_vectors.npy")).astype(np.float32)
    meta = list(csv.DictReader(open(os.path.join(ROOT, "phylogeny", "data", "dish_meta.csv"))))
    assert len(meta) == vecs.shape[0], "meta/vector row mismatch"

    lca: dict[int, dict] = {}
    with open(os.path.join(ROOT, "lca", "dish_lca.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            lca[d["cluster_id"]] = d

    keep_idx, kept_meta = [], []
    cols = {m[0]: [] for m in METRICS}
    for m in meta:
        idx = int(m["idx"])
        d = lca.get(int(m["cluster_id"]))
        if not d:
            continue
        vals = {key: d.get(col) for key, col, *_ in METRICS}
        if any(v is None or not np.isfinite(v) or v <= 0 for v in vals.values()):
            continue
        keep_idx.append(idx)
        kept_meta.append(m)
        for k, v in vals.items():
            cols[k].append(v)

    keep_idx = np.array(keep_idx)
    V = vecs[keep_idx]
    foot = {k: np.array(v, dtype=np.float64) for k, v in cols.items()}
    print(f"[load] kept {len(keep_idx)} dishes with vector + valid per-kg LCA "
          f"(of {vecs.shape[0]} vectors)")
    return V, kept_meta, foot


def compute_curves(V: np.ndarray, foot: dict[str, np.ndarray]):
    """Best-case fractional reduction per center per radius, then mean/IQR across centers."""
    n = V.shape[0]
    nr = len(RADII)
    # Per-center, per-radius best-case reduction, accumulated across blocks.
    red = {k: np.empty((n, nr), dtype=np.float32) for k in foot}
    neigh = np.empty((n, nr), dtype=np.float32)  # neighbour count (incl self)

    foot_row = {k: v[None, :] for k, v in foot.items()}  # 1 x N for broadcast

    for start in range(0, n, BLOCK):
        end = min(start + BLOCK, n)
        sim = V[start:end] @ V.T            # B x N cosine similarity
        D = 1.0 - sim                       # B x N cosine distance (>=0)
        np.clip(D, 0.0, None, out=D)
        # Guarantee self-inclusion: float32 self-similarity is ~0.99999994, so
        # a dish's distance to itself is ~6e-8 > 0 and would be dropped at r=0,
        # yielding an empty neighbourhood (reduction -> -inf). Pin self to 0 so
        # the r=0 anchor is exactly 0% reduction for every dish.
        rows = np.arange(end - start)
        D[rows, start + rows] = 0.0
        f_center = {k: foot[k][start:end] for k in foot}  # B
        for ri, r in enumerate(RADII):
            mask = D <= r                   # B x N bool
            neigh[start:end, ri] = mask.sum(axis=1)
            for k in foot:
                best = np.where(mask, foot_row[k], np.inf).min(axis=1)  # B
                red[k][start:end, ri] = (f_center[k] - best) / f_center[k]
        print(f"[curves] centers {end}/{n}")

    out = {"radius": RADII, "mean_neighbors": neigh.mean(axis=0),
           "median_neighbors": np.median(neigh, axis=0)}
    for k in foot:
        out[f"{k}_mean"] = red[k].mean(axis=0)
        out[f"{k}_p25"] = np.percentile(red[k], 25, axis=0)
        out[f"{k}_median"] = np.percentile(red[k], 50, axis=0)
        out[f"{k}_p75"] = np.percentile(red[k], 75, axis=0)
    return out


def write_csv(out: dict):
    path = os.path.join(OUT, "flexibility_curves.csv")
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
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), sharex=True)
    fig.suptitle(
        "Dietary flexibility vs. best-case footprint reduction in restaurant dishes",
        fontsize=14, fontweight="bold", y=0.99)

    for ai, (ax, (key, _col, title, unit, color)) in enumerate(zip(axes, METRICS)):
        mean = out[f"{key}_mean"] * 100
        p25 = out[f"{key}_p25"] * 100
        p75 = out[f"{key}_p75"] * 100
        ax.fill_between(r, p25, p75, color=color, alpha=0.15,
                        label="inter-quartile range")
        ax.plot(r, mean, color=color, lw=2.4, label="mean across dishes")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Flexibility  (cosine radius in dish manifold)")
        ax.set_ylabel(f"Best-case reduction vs. center dish (%)\n[{unit}]" if ai == 0
                      else "Best-case reduction (%)")
        ax.set_xlim(0, r.max())
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.25)
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9)

        # Secondary annotation: mean neighbour count at a few radii.
        for rr in (0.05, 0.10, 0.20, 0.30):
            j = int(np.argmin(np.abs(r - rr)))
            ax.annotate(f"~{out['mean_neighbors'][j]:,.0f} dishes",
                        xy=(r[j], mean[j]), xytext=(0, 6),
                        textcoords="offset points", fontsize=6.5,
                        color="#555", ha="center")

    note = (f"n = {n_dishes:,} canonical dishes with both a 384-D manifold vector "
            f"and valid per-kg LCA.  Distance = cosine in native embedding space; "
            f"reduction = (center − greenest dish within radius) / center, "
            f"unweighted mean.\nCaveat: cosine distances are compressed — beyond "
            f"r~0.3 the neighbour set is a large share of ALL dishes, so the curve "
            f"degenerates toward 'switch to the globally greenest dish' rather "
            f"than a true craving-preserving substitution.")
    fig.text(0.5, -0.04, note, ha="center", va="top", fontsize=8, color="#333",
             wrap=True)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    path = os.path.join(OUT, "flexibility_abatement.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"[plot] wrote {path}")


def main():
    V, meta, foot = load()
    out = compute_curves(V, foot)
    write_csv(out)
    plot(out, V.shape[0])

    def at(key, rr):
        return round(float(out[f"{key}_mean"][int(np.argmin(np.abs(RADII - rr)))] * 100), 1)

    summary = {
        "n_dishes": int(V.shape[0]),
        "distance": "cosine, native 384-D embedding",
        "reduction": "best-case (greenest neighbour within radius), unweighted mean",
        "footprint_basis": "per-kg",
        "radii": [float(x) for x in RADII],
        "metrics": [m[0] for m in METRICS],
        "headline": {
            m[0]: {"r0.05_pct": at(m[0], 0.05), "r0.10_pct": at(m[0], 0.10),
                   "r0.20_pct": at(m[0], 0.20)} for m in METRICS
        },
    }
    with open(os.path.join(OUT, "flexibility_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("[done]", json.dumps(summary["headline"], indent=2))


if __name__ == "__main__":
    main()
