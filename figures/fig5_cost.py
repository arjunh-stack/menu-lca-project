"""Figure 5 — Does price track impact & nutrition?

Is cheaper food worse (or better) for the planet and for health? For each
metric we plot the per-dish median menu price (x) against the metric (y),
overlaying a binned-median trend with its IQR band and a Spearman ρ.

Two bases (the menu price is per serving, so per-serving is the honest match):
  basis="serving" : GHG/water/land per SERVING  (per-kg × serving mass)
  basis="kg"      : GHG/water/land per KG        (Poore-Nemecek intensity)
Nutri-Score is a per-100g rating and ΔYLL is already per meal, so they are
identical across bases.

  ρ > 0 : pricier dishes score higher on this metric
Orientation: GHG/water/land/Nutri-Score lower = better; ΔYLL higher = better,
so the panel takeaway states the plain-English direction.

"Show both" weighting: unweighted main + prevalence-weighted (_weighted).

Outputs: figures/fig5_cost_{serving,kg}{,_weighted}.{pdf,png}
"""
from __future__ import annotations

import numpy as np

import figdata as fd
import rdylbu_style as rb

METRIC_ORDER = ["ghg", "water", "land", "nutriscore", "yll"]
PER_SERVING = {"ghg", "water", "land"}          # scaled by serving mass
PRICE_CAP_Q = 0.98
N_BINS = 12


def spearman(x, y, w=None):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if w is None:
        w = np.ones_like(rx)
    mx = np.average(rx, weights=w); my = np.average(ry, weights=w)
    cov = np.average((rx - mx) * (ry - my), weights=w)
    sx = np.sqrt(np.average((rx - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((ry - my) ** 2, weights=w))
    return cov / (sx * sy) if sx and sy else np.nan


def y_for(df, key, basis):
    """Return (values, unit) for a metric under the chosen basis."""
    m = fd.METRICS[key]
    v = df[m["col"]].to_numpy(float)
    if basis == "serving" and key in PER_SERVING:
        serving_kg = (df["recipe_mass_g"].to_numpy(float) / 1000.0
                      / df["n_servings"].to_numpy(float))
        return v * serving_kg, m["unit"].replace("/ kg", "/ serving")
    return v, m["unit"]


def panel(ax, df, key, weighted, basis):
    m = fd.METRICS[key]
    yvals, unit = y_for(df, key, basis)
    price = df["price"].to_numpy(float)
    w_all = df["total_count"].to_numpy(float) if weighted else np.ones(len(df))
    good = np.isfinite(price) & np.isfinite(yvals) & (price > 0)
    if m["log"]:
        good &= yvals > 0
    pcap = np.quantile(price[good], PRICE_CAP_Q)
    good &= price <= pcap
    x, y, w = price[good], yvals[good], w_all[good]

    ax.scatter(x, y, s=1, c="#BDBDBD", alpha=0.10, lw=0, rasterized=True)
    edges = np.unique(fd.wquantile(x, w, np.linspace(0, 1, N_BINS + 1)))
    cx, med, lo, hi = [], [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (x >= a) & (x <= b)
        if sel.sum() < 20:
            continue
        cx.append(np.average(x[sel], weights=w[sel]))
        med.append(fd.wquantile(y[sel], w[sel], 0.5))
        lo.append(fd.wquantile(y[sel], w[sel], 0.25))
        hi.append(fd.wquantile(y[sel], w[sel], 0.75))
    cx, med, lo, hi = map(np.array, (cx, med, lo, hi))
    ax.fill_between(cx, lo, hi, color=m["color"], alpha=0.18, lw=0)
    ax.plot(cx, med, color=m["color"], lw=1.8, marker="o", ms=2.5)

    rho = spearman(x, y, w)
    ax.annotate(rf"$\rho$ = {rho:+.2f}", xy=(0.96, 0.92), xycoords="axes fraction",
                ha="right", va="top", family=rb.MONO, fontsize=6.5,
                color=rb.INK, fontweight="bold")
    if m["log"]:
        ax.set_yscale("log")
        ax.set_ylim(np.percentile(y, 2), np.percentile(y, 98))
    ax.set_title(m["label"], fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold")
    ax.set_xlabel("menu price ($ / serving)")
    ax.set_ylabel(unit, fontsize=6.5)
    ax.grid(alpha=0.5)
    return rho


def takeaway(key, rho):
    m = fd.METRICS[key]
    if abs(rho) < 0.05:
        return "~ no relationship"
    pricier = "worse" if ((rho > 0) == (m["better"] == "lower")) else "better"
    return f"pricier -> {pricier}"


def make(df, weighted, basis, stem):
    fig, axes = rb.subplots(2, 3, width="double", height=4.6)
    axes = axes.ravel()
    rhos = {key: panel(ax, df, key, weighted, basis)
            for ax, key in zip(axes, METRIC_ORDER)}

    g = axes[5]; g.axis("off")
    g.text(0.0, 0.95, r"Spearman $\rho$ (price vs.)", family=rb.SERIF,
           fontsize=8.5, fontweight="bold", va="top")
    yy = 0.78
    for key in METRIC_ORDER:
        g.text(0.0, yy, fd.METRICS[key]["label"], fontsize=6, family=rb.MONO,
               va="top")
        g.text(0.66, yy, f"{rhos[key]:+.2f}", fontsize=6, family=rb.MONO,
               va="top", color=fd.METRICS[key]["color"], fontweight="bold")
        g.text(0.0, yy - 0.055, f"   {takeaway(key, rhos[key])}", fontsize=5,
               family=rb.MONO, va="top", color=rb.MUTED)
        yy -= 0.16

    basis_label = ("per serving (impact scaled by dish serving mass)"
                   if basis == "serving" else "per kg (Poore-Nemecek intensity)")
    wlabel = ("prevalence-weighted" if weighted else "unweighted")
    rb.serif_title(fig, "Does price track environmental & health impact?",
                   fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005, f"39,166-dish manifold · footprints {basis_label} · "
             f"price capped at {int(PRICE_CAP_Q*100)}th pct · {wlabel}",
             ha="center", va="bottom", family=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    rb.save(fig, stem)


def main():
    rb.apply()
    df = fd.build()
    for basis in ("serving", "kg"):
        make(df, False, basis, f"figures/fig5_cost_{basis}")
        make(df, True, basis, f"figures/fig5_cost_{basis}_weighted")


if __name__ == "__main__":
    main()
