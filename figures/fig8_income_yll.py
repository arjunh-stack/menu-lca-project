"""Figure 8 — Neighbourhood income vs. the healthiness of what's on the menu.

x = ZIP median household income (ACS 2024 5-yr, B19013, real dollars).
y = mean ΔYLL of the dishes actually served in that ZIP (lifetime years
    gained per meal; higher = healthier), averaged over real menu rows.

Each point is one ZIP, sized by how many priced+scored menu rows it has.
A menu-row-weighted binned-median trend and a weighted Spearman ρ summarise
whether richer neighbourhoods are served healthier food.

Reuses the ZIP aggregate built by fig6_geographic.py (cached _zip_agg.npz)
and joins the income pulled by fetch_zip_income.py (data/zip_income.csv).

Outputs: figures/fig8_income_yll.{pdf,png}
"""
from __future__ import annotations

import csv
import os
import sqlite3
from collections import defaultdict

import numpy as np

import figdata as fd
import rdylbu_style as rb

INCOME_CSV = os.path.join(rb.FIG_DIR, "data", "zip_income.csv")
ZIP_AGG = os.path.join(rb.FIG_DIR, "_zip_agg.npz")
MIN_ROWS = 40
INCOME_CAP_Q = 0.99      # trim the long right tail of income for readability


def zip_yll():
    """ZIP -> (mean ΔYLL, n menu rows) over priced + manifold-scored rows.
    Built fresh here keyed by ZIP string (the npz cache stores lat/lng, not ZIP)."""
    df = fd.build()
    yll_by_name = {r.canonical_name: r.yll for r in df.itertuples()
                   if np.isfinite(r.yll)}
    con = sqlite3.connect(fd.MENUDB)
    acc = defaultdict(list)
    for zc, name in con.execute(
            "select zip_code, canonical_dish from menu_dishes "
            "where price_usd is not null and price_usd>0 and zip_code is not null"):
        y = yll_by_name.get(name)
        if y is not None:
            acc[str(zc)].append(y)
    con.close()
    return {z: (float(np.mean(v)), len(v)) for z, v in acc.items()
            if len(v) >= MIN_ROWS}


def wspearman(x, y, w):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    mx, my = np.average(rx, weights=w), np.average(ry, weights=w)
    cov = np.average((rx - mx) * (ry - my), weights=w)
    sx = np.sqrt(np.average((rx - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((ry - my) ** 2, weights=w))
    return cov / (sx * sy)


def main():
    rb.apply()
    income = {r["zip"]: float(r["median_hh_income"])
              for r in csv.DictReader(open(INCOME_CSV))
              if r["median_hh_income"]}
    yll = zip_yll()
    zips = [z for z in yll if z in income and income[z] > 0]
    inc = np.array([income[z] for z in zips])
    y = np.array([yll[z][0] for z in zips])
    w = np.array([yll[z][1] for z in zips], dtype=float)
    print(f"[fig8] {len(zips)} ZIPs with income + ΔYLL")

    cap = np.quantile(inc, INCOME_CAP_Q)
    keep = inc <= cap
    inc, y, w = inc[keep], y[keep], w[keep]
    inck = inc / 1000.0

    fig, ax = rb.figure(width="single", height=3.1)

    # points coloured on RdYlBu by ΔYLL (red = less healthy, blue = healthier)
    lo, hi = np.percentile(y, [5, 95])
    norm = np.clip((y - lo) / (hi - lo or 1), 0, 1)
    cmap = rb.rdylbu_cmap()                       # 0=red(worse), 1=blue(better)
    ax.scatter(inck, y, s=np.clip(w / 12, 2, 40), c=cmap(norm),
               alpha=0.55, lw=0, rasterized=True)

    # menu-row-weighted binned median trend over income quantile bins
    edges = np.unique(fd.wquantile(inck, w, np.linspace(0, 1, 11)))
    cx, med = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (inck >= a) & (inck <= b)
        if sel.sum() < 8:
            continue
        cx.append(np.average(inck[sel], weights=w[sel]))
        med.append(fd.wquantile(y[sel], w[sel], 0.5))
    ax.plot(cx, med, color=rb.INK, lw=1.8, marker="o", ms=3,
            label="menu-row-weighted median")

    rho = wspearman(inck, y, w)
    ax.annotate(rf"weighted Spearman $\rho$ = {rho:+.2f}  (≈ flat)",
                xy=(0.04, 0.05), xycoords="axes fraction", ha="left", va="bottom",
                family=rb.MONO, fontsize=6, fontweight="bold", color=rb.INK)
    ax.axhline(0, color=rb.MUTED, lw=0.6, ls=":")

    ax.set_xlabel("ZIP median household income ($1,000s)")
    ax.set_ylabel(r"mean $\Delta$YLL of dishes served"
                  "\n(yrs gained / meal · higher = healthier)", fontsize=6.5)
    rb.serif_title(ax, "Neighbourhood income barely predicts menu healthiness",
                   fontsize=8.6, fontweight="bold")
    ax.grid(alpha=0.5)
    ax.legend(loc="upper left", fontsize=5.6)

    fig.text(0.5, -0.02,
             f"{len(inck):,} US ZIP codes · ≥{MIN_ROWS} priced menu rows each · "
             f"income = ACS 2024 5-yr median household (B19013) · "
             r"$\Delta$YLL from the "
             f"39k dish manifold · point size = menu rows · colour = "
             r"$\Delta$YLL (red = less healthy)", ha="center", va="top",
             family=rb.MONO, fontsize=4.4, color=rb.MUTED, wrap=True)
    fig.tight_layout()
    rb.save(fig, "figures/fig8_income_yll")


if __name__ == "__main__":
    main()
