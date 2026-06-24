"""Figure 4 — Do smarter diet decisions have planetary alignment?

Two complementary views of whether the healthy choice and the green choice
are the same choice.

(A) WHOLE DATASET — Spearman correlation among all five metrics, oriented so
    "higher = worse" (ΔYLL sign flipped). Red cell = the planet-bad dishes are
    also the health-bad dishes (alignment); blue = they trade off.

(B,C) WITHIN A FLEXIBILITY SPHERE (r = R0) — the Pareto / co-benefit test.
    For each dish, take the single best substitute in its sphere under ONE
    objective and ask what it does to the OTHER:
      (B) climate-first: pick the greenest neighbour; x = GHG cut achieved,
          y = health change it also delivers. Upper-right = win-win.
      (C) health-first: pick the healthiest neighbour; x = health gained,
          y = GHG change it also delivers.
    The share of dishes in the win-win (upper-right) quadrant is the headline.

(D) Co-benefit rates summarised as bars.

Outputs: figures/fig4_alignment.{pdf,png}
"""
from __future__ import annotations

import os

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

import figdata as fd
import flexlib
import rdylbu_style as rb

R0 = 0.10                      # flexibility radius for the within-sphere panels
METRIC_ORDER = ["ghg", "water", "land", "nutriscore", "yll"]
PICKS_CACHE = os.path.join(rb.FIG_DIR, f"_flex_picks_r{int(R0*100):03d}.npz")
DENSITY = LinearSegmentedColormap.from_list(
    "rdylbu_density", ["#FEE090", "#FDAE61", "#F46D43", "#D73027", "#A50026"])


def spearman_matrix(cols: dict[str, np.ndarray]):
    keys = list(cols)
    # rank each metric once (NaN -> drop pairwise)
    n = len(next(iter(cols.values())))
    M = np.full((len(keys), len(keys)), np.nan)
    for i, a in enumerate(keys):
        for j, b in enumerate(keys):
            x, y = cols[a], cols[b]
            good = np.isfinite(x) & np.isfinite(y)
            rx = np.argsort(np.argsort(x[good])).astype(float)
            ry = np.argsort(np.argsort(y[good])).astype(float)
            M[i, j] = np.corrcoef(rx, ry)[0, 1]
    return keys, M


def load_picks(df, V):
    if os.path.exists(PICKS_CACHE):
        z = np.load(PICKS_CACHE)
        return z["green"], z["healthy"]
    ghg = df["ghg"].to_numpy(float)
    yll = df["yll"].to_numpy(float)
    picks = flexlib.best_picks(V, {"green": (ghg, "lower"),
                                   "healthy": (yll, "higher")}, R0)
    np.savez(PICKS_CACHE, green=picks["green"], healthy=picks["healthy"])
    return picks["green"], picks["healthy"]


def quad_scatter(ax, x, y, xlabel, ylabel, title, ylim=None, xlim=None):
    good = np.isfinite(x) & np.isfinite(y)
    x, y = x[good], y[good]
    winwin = float(np.mean((x > 1e-6) & (y > 1e-6))) * 100   # on full data
    # clip only the VIEW so outlier tails don't flatten the bulk
    xv = np.clip(x, *xlim) if xlim else x
    yv = np.clip(y, *ylim) if ylim else y
    ax.hexbin(xv, yv, gridsize=45, cmap=DENSITY, mincnt=1, bins="log",
              linewidths=0)
    ax.axhline(0, color=rb.INK, lw=0.6)
    ax.axvline(0, color=rb.INK, lw=0.6)
    if ylim:
        ax.set_ylim(*ylim)
    if xlim:
        ax.set_xlim(*xlim)
    ax.annotate(f"win–win\n{winwin:.0f}%", xy=(0.97, 0.95),
                xycoords="axes fraction", ha="right", va="top",
                family=rb.SERIF, fontsize=7.5, fontweight="bold",
                color="#A50026")
    ax.set_xlabel(xlabel, fontsize=6.5)
    ax.set_ylabel(ylabel, fontsize=6.5)
    ax.set_title(title, fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold")
    ax.grid(alpha=0.4)
    return winwin


def main():
    rb.apply()
    df = fd.build()
    V = fd.vectors()
    ghg = df["ghg"].to_numpy(float)
    yll = df["yll"].to_numpy(float)
    nutri = df["nutriscore"].to_numpy(float)

    green, healthy = load_picks(df, V)

    fig, axes = rb.subplots(2, 2, width="double", height=6.0)
    (axA, axB), (axC, axD) = axes

    # ── A: whole-dataset Spearman correlation (badness-oriented) ──────────
    badness = {k: (-df[fd.METRICS[k]["col"]].to_numpy(float) if fd.METRICS[k]["better"] == "higher"
                   else df[fd.METRICS[k]["col"]].to_numpy(float)) for k in METRIC_ORDER}
    keys, M = spearman_matrix(badness)
    im = axA.imshow(M, cmap=rb.rdylbu_cmap(reverse=True), vmin=-1, vmax=1)
    labels = [fd.METRICS[k]["label"].split(" (")[0] for k in keys]
    axA.set_xticks(range(len(keys))); axA.set_yticks(range(len(keys)))
    axA.set_xticklabels(labels, rotation=40, ha="right", fontsize=6)
    axA.set_yticklabels(labels, fontsize=6)
    for i in range(len(keys)):
        for j in range(len(keys)):
            axA.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                     fontsize=5.5, family=rb.MONO,
                     color=("white" if abs(M[i, j]) > 0.55 else rb.INK))
    axA.set_title("Whole-dataset alignment of 'badness'",
                  fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold")
    axA.grid(False)
    cb = fig.colorbar(im, ax=axA, fraction=0.046, pad=0.04)
    cb.set_label("Spearman ρ  (red = aligned)", fontsize=5.5)
    cb.ax.tick_params(labelsize=5)

    # ── B: climate-first co-benefit ───────────────────────────────────────
    ghg_cut = (ghg - ghg[green]) / ghg                  # >=0 by construction
    health_delivered = yll[green] - yll                 # +good / -trade-off
    wB = quad_scatter(axB, ghg_cut * 100, health_delivered,
                      "GHG cut from greenest swap (%)",
                      r"$\Delta$YLL also delivered (yrs)",
                      "Go green → what happens to health?",
                      ylim=(-1.5, 1.5))

    # ── C: health-first co-benefit ────────────────────────────────────────
    yll_gain = yll[healthy] - yll                        # >=0 by construction
    ghg_delivered = (ghg - ghg[healthy]) / ghg * 100     # +also greener
    wC = quad_scatter(axC, yll_gain, ghg_delivered,
                      r"$\Delta$YLL from healthiest swap (yrs)",
                      "GHG also cut (%)",
                      "Get healthy → what happens to GHG?",
                      ylim=(-150, 100))

    # ── D: co-benefit summary bars ────────────────────────────────────────
    eps = 1e-6
    can_green = ghg_cut > eps
    can_heal = yll_gain > eps
    rates = [
        ("Greenest swap\nalso healthier",
         np.mean(health_delivered[can_green] > 0) * 100, "#D73027"),
        ("Healthiest swap\nalso greener",
         np.mean(ghg_delivered[can_heal] > 0) * 100, "#313695"),
        ("Both improve\n(win–win exists)", wB, "#A50026"),
    ]
    ypos = np.arange(len(rates))
    axD.barh(ypos, [r[1] for r in rates], color=[r[2] for r in rates],
             alpha=0.9, height=0.6)
    for i, (_, v, _) in enumerate(rates):
        axD.text(v + 1.5, i, f"{v:.0f}%", va="center", fontsize=6.5,
                 family=rb.MONO, fontweight="bold")
    axD.set_yticks(ypos); axD.set_yticklabels([r[0] for r in rates], fontsize=6)
    axD.set_xlim(0, 100); axD.set_xlabel("share of dishes (%)", fontsize=6.5)
    axD.invert_yaxis()
    axD.set_title(f"Co-benefit rates (r = {R0})", fontfamily=rb.SERIF,
                  fontsize=8.5, fontweight="bold")
    axD.grid(axis="y", visible=False)

    rb.serif_title(fig, "Do smarter diet decisions have planetary alignment?",
                   fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005, f"39,166-dish manifold · within-sphere panels use the "
             f"single best substitute at flexibility r = {R0} · density = log "
             f"count of dishes", ha="center", va="bottom", family=rb.MONO,
             fontsize=5.2, color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    rb.save(fig, "figures/fig4_alignment")


if __name__ == "__main__":
    main()
