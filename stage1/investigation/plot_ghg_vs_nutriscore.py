#!/usr/bin/env python3
"""Scatter: per-kg GHG footprint vs Nutri-Score for the 39,166-dish manifold.

x = Nutri-Score (0–100, higher = less healthy; Clark-2022 scaling)
y = GHG (kg CO₂e / kg), log scale
Joined on cluster_id: nutrition/dish_nutriscore_manifold.csv ⋈ lca/dish_lca.jsonl
Points colored by Nutri-Score letter grade; binned-median trend + Spearman ρ.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != "/" and not os.path.exists(os.path.join(ROOT, "paths.py")):
    ROOT = os.path.dirname(ROOT)

NS = os.path.join(ROOT, "nutrition", "dish_nutriscore_manifold.csv")
LCA = os.path.join(ROOT, "lca", "dish_lca.jsonl")
OUT = os.path.join(ROOT, "phylogeny", "site", "ghg_vs_nutriscore.png")

GRADE_COLOR = {  # Nutri-Score palette: green (best) → red (worst)
    "A": "#1a9641", "B": "#a6d96a", "C": "#fee08b",
    "D": "#fdae61", "E": "#d7191c",
}

# ── load Nutri-Score per manifold cluster ─────────────────────────────
ns: dict[int, tuple[float, str]] = {}
with open(NS) as f:
    for r in csv.DictReader(f):
        ns[int(r["cluster_id"])] = (float(r["nutriscore_0to100"]), r["grade"])

# ── join GHG/kg ───────────────────────────────────────────────────────
x, y, grades = [], [], []
with open(LCA) as f:
    for line in f:
        d = json.loads(line)
        cid = d["cluster_id"]
        if cid not in ns:
            continue
        ghg = d.get("ghg_kgco2e_per_kg")
        if ghg is None or ghg <= 0:
            continue
        score, grade = ns[cid]
        x.append(score)
        y.append(ghg)
        grades.append(grade)

x = np.array(x); y = np.array(y); grades = np.array(grades)
# log x needs strictly positive scores
pos = x > 0
n_drop = int((~pos).sum())
if n_drop:
    print(f"dropped {n_drop} dishes with Nutri-Score <= 0 (log x)")
x, y, grades = x[pos], y[pos], grades[pos]
print(f"plotted dishes: {len(x):,}")

# Spearman ρ (rank correlation, robust to the log skew)
rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
rho = np.corrcoef(rx, ry)[0, 1]
print(f"Spearman rho(GHG, Nutri-Score) = {rho:.3f}")

# ── plot ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7.5))
for g in ["A", "B", "C", "D", "E"]:
    m = grades == g
    ax.scatter(x[m], y[m], s=7, alpha=0.25, linewidths=0,
               color=GRADE_COLOR[g], label=f"{g} (n={m.sum():,})")

# binned-median trend across the score range (log-spaced for the log x-axis)
bins = np.logspace(np.log10(x.min()), np.log10(x.max()), 16)
idx = np.digitize(x, bins)
bx, bmed = [], []
for b in range(1, len(bins)):
    m = idx == b
    if m.sum() >= 20:
        bx.append(x[m].mean()); bmed.append(np.median(y[m]))
ax.plot(bx, bmed, "-", color="black", lw=2.2, zorder=6, label="binned median GHG")

ax.set_yscale("log")
ax.set_xscale("log")
ax.set_xlabel("Nutri-Score (0–100, higher = less healthy)", fontsize=11)
ax.set_ylabel("GHG emissions (kg CO₂e / kg)", fontsize=11)
ax.set_title(
    "Per-kg GHG footprint vs Nutri-Score — 39,166-dish manifold\n"
    f"{len(x):,} dishes · Spearman ρ = {rho:.3f} · color = Nutri-Score grade, log y",
    fontsize=12,
)
from matplotlib.ticker import ScalarFormatter
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.set_minor_formatter(ScalarFormatter())
ax.set_xticks([5, 10, 20, 30, 50, 70])
ax.set_xticks([], minor=True)
ax.grid(which="both", ls=":", alpha=0.35)
ax.set_axisbelow(True)
leg = ax.legend(loc="upper left", fontsize=9, framealpha=0.9, markerscale=2.5)
for lh in leg.legend_handles[:5]:
    lh.set_alpha(1)
fig.tight_layout()
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print(f"wrote {OUT}")
