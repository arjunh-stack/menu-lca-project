#!/usr/bin/env python3
"""Three-panel compound box-plot figure: per-kg GHG / water / land footprint
of the 39,166-dish manifold, grouped by restaurant cuisine.

One box per cuisine (15 cuisines from phylogeny/data/dish_classes.csv), one
panel per impact dimension. One point per canonical dish (unweighted). Joined
on cluster_id to lca/dish_lca.jsonl. Per-kg functional unit (Poore-Nemecek
intensity). Log y-axis because per-dish impacts are heavily right-skewed.

Run from anywhere; paths anchored to the repo root via paths.py.
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ── repo-root anchor ──────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != "/" and not os.path.exists(os.path.join(ROOT, "paths.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

CLASSES = os.path.join(ROOT, "phylogeny", "data", "dish_classes.csv")
LCA = os.path.join(ROOT, "lca", "dish_lca.jsonl")
OUT = os.path.join(ROOT, "phylogeny", "site", "cuisine_impact_boxplots.png")

# ── impact panels (field, label, unit) ───────────────────────────────
PANELS = [
    ("ghg_kgco2e_per_kg", "GHG emissions", "kg CO₂e / kg"),
    ("water_m3_per_kg", "Freshwater withdrawal", "m³ / kg"),
    ("land_pt_per_kg", "Land use", "Pt / kg"),
]

# ── load cuisine label per manifold cluster ──────────────────────────
cuisine: dict[int, str] = {}
with open(CLASSES) as f:
    for r in csv.DictReader(f):
        cuisine[int(r["cluster_id"])] = r["cuisine"]

# ── load per-kg impacts, restricted to the manifold ──────────────────
# data[cuisine][field] -> list of per-dish values
data: dict[str, dict[str, list]] = {c: {p[0]: [] for p in PANELS} for c in set(cuisine.values())}
n_dishes = 0
with open(LCA) as f:
    for line in f:
        d = json.loads(line)
        cid = d["cluster_id"]
        if cid not in cuisine:
            continue
        vals = [d.get(p[0]) for p in PANELS]
        if any(v is None or v <= 0 for v in vals):  # log axis needs > 0
            continue
        cz = cuisine[cid]
        for (field, _, _), v in zip(PANELS, vals):
            data[cz][field].append(v)
        n_dishes += 1

print(f"plotted dishes (all 3 per-kg present & >0): {n_dishes}")

# ── stable per-cuisine colors (fixed regardless of panel ordering) ────
all_cuisines = sorted(data, key=lambda c: np.mean(data[c][PANELS[0][0]]), reverse=True)
n_per = {c: len(data[c][PANELS[0][0]]) for c in all_cuisines}
cmap = plt.get_cmap("tab20")
colors = {c: cmap(i % 20) for i, c in enumerate(all_cuisines)}

# ── figure: 3 stacked panels, each ranked by its OWN mean (descending) ─
fig, axes = plt.subplots(3, 1, figsize=(13, 14))

for ax, (field, title, unit) in zip(axes, PANELS):
    order = sorted(data, key=lambda c: np.median(data[c][field]), reverse=True)
    positions = np.arange(len(order))
    series = [data[c][field] for c in order]
    means = [np.mean(s) for s in series]
    # crop y to the box (IQR) range across cuisines, so long whisker tails
    # don't stretch the scale — boxes fill the panel
    q1s = [np.percentile(s, 25) for s in series]
    q3s = [np.percentile(s, 75) for s in series]
    # keep the mean diamond (the sort key) in frame even when right-skew
    # pushes it above Q3
    ylo, yhi = min(q1s) / 1.3, max(max(q3s), max(means)) * 1.3
    bp = ax.boxplot(
        series,
        positions=positions,
        widths=0.62,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color="black", linewidth=1.4),
        whiskerprops=dict(color="0.4"),
        capprops=dict(color="0.4"),
    )
    for patch, c in zip(bp["boxes"], order):
        patch.set_facecolor(colors[c])
        patch.set_alpha(0.85)
        patch.set_edgecolor("0.25")
    # mean marker (the ranking variable)
    ax.scatter(positions, means, marker="D", s=34, color="white",
               edgecolor="black", zorder=5, label="mean")
    ax.set_yscale("log")
    ax.set_ylim(ylo, yhi)
    ax.set_ylabel(f"{title}\n({unit})", fontsize=11)
    ax.grid(axis="y", which="both", ls=":", alpha=0.4)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.6, len(order) - 0.4)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{c}\n(n={n_per[c]:,})" for c in order],
                       rotation=45, ha="right", fontsize=9)
    ax.legend(loc="upper right", fontsize=9, frameon=True)

fig.suptitle(
    "Per-kg environmental footprint by restaurant cuisine — ranked by median\n"
    f"39,166-dish manifold · {n_dishes:,} dishes · line = median (sort key), boxes = IQR, diamond = mean · y cropped to IQR range, log scale",
    fontsize=13,
    y=0.99,
)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print(f"wrote {OUT}")
