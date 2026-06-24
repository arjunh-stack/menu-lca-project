"""Hero figure — the dish manifold, painted by impact, health & price.

The UMAP layout of the 39,166-dish manifold (phylogeny/data/umap.json), shown
as small multiples. Each panel is the SAME map; only the colour changes — one
metric per panel, on the RdYlBu ramp oriented so red = worse, blue = better.
This shows *where* on the manifold the green / healthy / cheap dishes live and
whether those neighbourhoods coincide.

Outputs: figures/fig_hero_manifold.{pdf,png}
"""
from __future__ import annotations

import json
import os

import numpy as np

import figdata as fd
import rdylbu_style as rb

UMAP = os.path.join(fd.ROOT, "phylogeny", "data", "umap.json")
# (key, log-transform-before-colour, is_badness_value)
PANELS = ["ghg", "water", "land", "nutriscore", "yll", "price"]
PRICE = dict(label="Menu price", unit="$ (red = pricier)", color="#A50026")


def badness(df, key):
    """Return (values, label, unit) oriented so higher = worse, NaN preserved."""
    if key == "price":
        return df["price"].to_numpy(float), "Menu price", "red = pricier"
    m = fd.METRICS[key]
    v = df[m["col"]].to_numpy(float)
    if m["log"]:
        v = np.where(v > 0, np.log10(v), np.nan)
    if m["better"] == "higher":           # flip so higher = worse
        v = -v
    return v, m["label"], m["unit"]


def main():
    rb.apply()
    df = fd.build()
    pts = json.load(open(UMAP))["points"]
    idx = np.array([p["idx"] for p in pts])
    xy = np.array([[p["x"], p["y"]] for p in pts], dtype=float)

    cmap = rb.rdylbu_cmap(reverse=True)    # cmap(1) = red = worse
    fig, axes = rb.subplots(2, 3, width="double", height=5.0)
    axes = axes.ravel()

    for ax, key in zip(axes, PANELS):
        vals, label, unit = badness(df, key)
        v = vals[idx]
        good = np.isfinite(v)
        # colour scale clipped to 2–98th pct of badness so outliers don't wash out
        lo, hi = np.nanpercentile(v[good], [2, 98])
        norm = np.clip((v - lo) / (hi - lo or 1), 0, 1)
        # background: dishes missing this metric in light grey
        ax.scatter(xy[~good, 0], xy[~good, 1], s=1.2, c="#E8E8E8", lw=0,
                   rasterized=True)
        ax.scatter(xy[good, 0], xy[good, 1], s=1.4, c=cmap(norm[good]),
                   lw=0, alpha=0.75, rasterized=True)
        ax.set_title(label, fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold")
        ax.text(0.5, -0.04, unit, transform=ax.transAxes, ha="center",
                va="top", fontsize=5.2, family=rb.MONO, color=rb.MUTED)
        ax.set_xticks([]); ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    rb.serif_title(fig, "The dish manifold, painted by impact, health & price",
                   fontsize=11, fontweight="bold", y=1.0)
    fig.text(0.5, 0.02, "Same UMAP layout in every panel · each point = one "
             "canonical dish · colour = RdYlBu (red = worse / pricier, "
             "blue = better / cheaper) · grey = metric missing",
             ha="center", va="bottom", family=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    rb.save(fig, "figures/fig_hero_manifold")


if __name__ == "__main__":
    main()
