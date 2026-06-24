"""Figure 1 — How impact & health metrics vary by cuisine.

Two compound box-and-whisker figures:
  fig1_impact_by_cuisine   GHG / water / land  (3 stacked panels, log y)
  fig1_health_by_cuisine   Nutri-Score / ΔYLL  (2 stacked panels, linear)

Each panel: one box per cuisine, boxes coloured on the RdYlBu ramp by their
own median badness (red = worse for planet/health, blue = better), cuisines
sorted worst→best. Box = weighted IQR, whiskers = weighted P5–P95, line =
median, diamond = mean.

"Show both" weighting: unweighted (one canonical dish = one point) is the
main figure; a prevalence-weighted variant (each dish weighted by the number
of restaurants serving it, total_count) is written with a _weighted suffix.

Outputs (figures/): fig1_impact_by_cuisine{,_weighted}.{pdf,png},
                    fig1_health_by_cuisine{,_weighted}.{pdf,png}
"""
from __future__ import annotations

import numpy as np

import figdata as fd
import rdylbu_style as rb

MIN_N = 150  # drop cuisines with too few dishes to box meaningfully


def wquantile(v: np.ndarray, w: np.ndarray, q: float) -> float:
    """Weighted quantile (q in [0,1]) via the cumulative-weight CDF."""
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return float(np.interp(q, cw, v))


def stats_for(v: np.ndarray, w: np.ndarray) -> dict:
    return dict(
        med=wquantile(v, w, 0.50),
        q1=wquantile(v, w, 0.25),
        q3=wquantile(v, w, 0.75),
        whislo=wquantile(v, w, 0.05),
        whishi=wquantile(v, w, 0.95),
        mean=float(np.average(v, weights=w)),
        n=len(v),
        wsum=float(w.sum()),
    )


def panel(ax, df, key, weighted):
    m = fd.METRICS[key]
    col = m["col"]
    # collect per-cuisine clean values + weights
    per = {}
    for cz in fd.CUISINE_ORDER:
        sub = df[df["cuisine"] == cz]
        v = sub[col].to_numpy(dtype=float)
        good = np.isfinite(v)
        if m["log"]:
            good &= v > 0
        v = v[good]
        if len(v) < MIN_N:
            continue
        w = (sub["total_count"].to_numpy(dtype=float)[good] if weighted
             else np.ones(len(v)))
        per[cz] = (v, w)

    st = {cz: stats_for(v, w) for cz, (v, w) in per.items()}
    # badness so red = worse: lower-is-better -> badness=median; higher-is-better -> -median
    badness = {cz: (s["med"] if m["better"] == "lower" else -s["med"])
               for cz, s in st.items()}
    order = sorted(st, key=lambda c: badness[c], reverse=True)  # worst (red) first

    b = np.array([badness[c] for c in order], dtype=float)
    norm = (b - b.min()) / (np.ptp(b) or 1)      # 1 = worst (highest badness), 0 = best
    cmap = rb.rdylbu_cmap()                        # cmap(0)=red, cmap(1)=blue
    colors = [cmap(1 - x) for x in norm]          # worst->red, best->blue

    bxp_stats = [dict(med=st[c]["med"], q1=st[c]["q1"], q3=st[c]["q3"],
                      whislo=st[c]["whislo"], whishi=st[c]["whishi"],
                      fliers=[], label=c) for c in order]
    bp = ax.bxp(bxp_stats, showfliers=False, widths=0.62, patch_artist=True,
                medianprops=dict(color=rb.INK, lw=1.2),
                whiskerprops=dict(color=rb.MUTED, lw=0.8),
                capprops=dict(color=rb.MUTED, lw=0.8),
                boxprops=dict(lw=0.6))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_edgecolor(rb.INK)
        patch.set_alpha(0.92)
    # mean diamond
    pos = np.arange(1, len(order) + 1)
    ax.scatter(pos, [st[c]["mean"] for c in order], marker="D", s=12,
               color="white", edgecolor=rb.INK, lw=0.6, zorder=5)

    if m["log"]:
        ax.set_yscale("log")
        # crop to IQR band so skew tails don't flatten the boxes
        lo = min(s["q1"] for s in st.values()) / 1.4
        hi = max(max(s["q3"] for s in st.values()),
                 max(s["mean"] for s in st.values())) * 1.4
        ax.set_ylim(lo, hi)
    ax.set_ylabel(f"{m['label']}\n({m['unit']})")
    ax.set_xticklabels(order, rotation=40, ha="right")
    ax.grid(axis="x", visible=False)
    return order


def make(df, keys, stem, title, weighted, height):
    fig, axes = rb.subplots(len(keys), 1, width="double", height=height,
                            sharex=False)
    if len(keys) == 1:
        axes = [axes]
    for ax, key in zip(axes, keys):
        panel(ax, df, key, weighted)
    wlabel = ("Prevalence-weighted by restaurants serving each dish"
              if weighted else "Each canonical dish counted once (unweighted)")
    rb.serif_title(fig, title, fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005,
             f"39,166-dish manifold · {wlabel} · box = IQR, whiskers = P5–P95, "
             f"line = median, white marker = mean · colour = RdYlBu by median "
             f"(red = worse, blue = better)",
             ha="center", va="bottom", fontfamily=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    rb.save(fig, stem)


def main():
    rb.apply()
    df = fd.build()
    for weighted, sfx in [(False, ""), (True, "_weighted")]:
        make(df, fd.IMPACT_METRICS, f"figures/fig1_impact_by_cuisine{sfx}",
             "Environmental impact by cuisine", weighted, height=7.2)
        make(df, fd.HEALTH_METRICS, f"figures/fig1_health_by_cuisine{sfx}",
             "Nutrition & health by cuisine", weighted, height=5.0)


if __name__ == "__main__":
    main()
