"""Figure 3 — Dietary flexibility vs. best-case improvement.

For every dish we sweep a flexibility radius r in the manifold and read off
the best improvement reachable by switching to a dish within r. One compound
figure, one panel per metric.

Per user: FLEXIBILITY (cosine radius) on the Y-axis, IMPROVEMENT POTENTIAL on
the X-axis. The curve answers "the more substitution I allow (higher up),
the more I could improve (further right)."

  impact + Nutri-Score : x = best-case % reduction
  ΔYLL                  : x = best-case lifetime years gained per meal

"Show both": unweighted main + prevalence-weighted (_weighted) supplement.

Outputs: figures/fig3_flexibility{,_weighted}.{pdf,png}
"""
from __future__ import annotations

import os

import numpy as np

import figdata as fd
import flexlib
import rdylbu_style as rb

METRIC_ORDER = ["ghg", "water", "land", "nutriscore", "yll"]
ANNOT_RADII = [0.05, 0.10, 0.20, 0.30]
CACHE = os.path.join(rb.FIG_DIR, "_flex_curves.npz")


def compute(rebuild=False):
    df = fd.build()
    counts = df["total_count"].to_numpy(dtype=float)
    if os.path.exists(CACHE) and not rebuild:
        z = np.load(CACHE)
        res = {k: z[k] for k in z.files}
        return res, counts
    V = fd.vectors()
    metrics = {k: df[fd.METRICS[k]["col"]].to_numpy(dtype=float) for k in METRIC_ORDER}
    better = {k: fd.METRICS[k]["better"] for k in METRIC_ORDER}
    res = flexlib.best_improvement(V, metrics, better)
    np.savez(CACHE, **res)
    return res, counts


def make(res, counts, weighted, stem):
    radii = res["radii"]
    w = counts if weighted else None
    fig, axes = rb.subplots(2, 3, width="double", height=4.6)
    axes = axes.ravel()

    for ax, key in zip(axes, METRIC_ORDER):
        m = fd.METRICS[key]
        mean, p25, _p50, p75 = flexlib.aggregate(res[key], w)
        is_pct = key != "yll"
        y_mean = mean * (100 if is_pct else 1)
        y_lo = p25 * (100 if is_pct else 1)
        y_hi = p75 * (100 if is_pct else 1)
        ax.fill_between(radii, y_lo, y_hi, color=m["color"], alpha=0.16, lw=0)
        ax.plot(radii, y_mean, color=m["color"], lw=1.8)
        # neighbour-count context at a few radii
        nmean = res["neigh"].mean(0)
        for rr in ANNOT_RADII:
            j = int(np.argmin(np.abs(radii - rr)))
            ax.annotate(f"~{nmean[j]:,.0f}", xy=(radii[j], y_mean[j]),
                        xytext=(2, 4), textcoords="offset points",
                        fontsize=4.6, family=rb.MONO, color=rb.MUTED, ha="center")
        ax.set_title(m["label"], fontfamily=rb.SERIF, fontsize=8.5,
                     fontweight="bold")
        ax.set_ylabel("years gained / meal" if key == "yll"
                      else "best-case reduction (%)")
        ax.set_xlabel("Flexibility (cosine radius)")
        ax.set_xlim(0, radii.max())
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.5)
    # 6th cell: legend / reading guide
    g = axes[5]
    g.axis("off")
    g.text(0.0, 0.92, "How to read", family=rb.SERIF, fontsize=8.5,
           fontweight="bold")
    g.text(0.0, 0.70,
           "Right = more willingness to\nsubstitute (bigger sphere).\n"
           "Up = bigger achievable\nimprovement.\n\n"
           "Line = mean, band = IQR.\nGrey = mean dishes in the\n"
           "sphere at that radius.",
           fontsize=5.6, va="top", linespacing=1.4)
    g.text(0.0, 0.02, "Honest regime: r < ~0.3.", fontsize=5.0, family=rb.MONO,
           color=rb.MUTED, va="bottom")

    wlabel = ("prevalence-weighted by restaurant count" if weighted
              else "unweighted (one dish = one point)")
    rb.serif_title(fig, "Dietary flexibility vs. best-case improvement",
                   fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005, f"39,166-dish manifold · best substitute within a "
             f"cosine sphere · {wlabel}", ha="center", va="bottom",
             family=rb.MONO, fontsize=5.2, color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    rb.save(fig, stem)


def main():
    rb.apply()
    res, counts = compute()
    make(res, counts, False, "figures/fig3_flexibility")
    make(res, counts, True, "figures/fig3_flexibility_weighted")


if __name__ == "__main__":
    main()
