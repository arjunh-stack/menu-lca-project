"""Figure 7 — Flexibility while keeping macros similar.

The flexibility curves (Fig 3) let the substitute be anything compositionally
close. Here we add a nutrition guardrail: the substitute must also have a
SIMILAR macro split (protein/fat/carb as % of calories), within a tolerance —
not exact. We measure how much best-case improvement survives.

Macro distance = total variation between macro-share vectors (0.5·Σ|Δshare|),
read as "the % of calories that would have to shift." TOL = 10 ("similar").

Panels:
  5 metric panels — best-case improvement vs flexibility radius, two lines:
     any substitute  vs  macro-matched (TV ≤ 10).  Same centre set (dishes
     with a macro profile) for a fair comparison.
  1 panel — best-case GHG & Nutri-Score improvement vs how strict the macro
     match is, at fixed flexibility r = 0.15. Shows you keep most of the win
     even near-exact.

Outputs: figures/fig7_macro_flexibility.{pdf,png}
"""
from __future__ import annotations

import os

import numpy as np

import figdata as fd
import flexlib
import rdylbu_style as rb

METRIC_ORDER = ["ghg", "water", "land", "nutriscore", "yll"]
TOL0 = 10.0                     # "similar macros" tolerance for the curve panels
R_FIXED = 0.15                  # radius for the tolerance-sweep panel
TOLS = [2, 4, 6, 8, 10, 14, 18, 25, 40, 70, 1e9]
CACHE = os.path.join(rb.FIG_DIR, "_macro_flex.npz")


def macro_shares(df):
    p = df["protein_serving"].to_numpy(float) * 4
    f = df["fat_serving"].to_numpy(float) * 9
    c = df["carb_serving"].to_numpy(float) * 4
    tot = p + f + c
    with np.errstate(invalid="ignore", divide="ignore"):
        M = np.stack([p, f, c], 1) / tot[:, None] * 100
    return M


def compute(df, V, M):
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        return {k: z[k] for k in z.files}
    metrics = {k: df[fd.METRICS[k]["col"]].to_numpy(float) for k in METRIC_ORDER}
    better = {k: fd.METRICS[k]["better"] for k in METRIC_ORDER}
    radii = flexlib.DEFAULT_RADII
    any_ = flexlib.best_improvement(V, metrics, better, radii, block=1500)
    mm = flexlib.best_improvement(V, metrics, better, radii, macro=M,
                                  macro_tol=TOL0, block=1500)
    sweep_ghg = flexlib.improvement_vs_tol(V, metrics["ghg"], "lower",
                                           R_FIXED, TOLS, M, block=1500)
    sweep_ns = flexlib.improvement_vs_tol(V, metrics["nutriscore"], "lower",
                                          R_FIXED, TOLS, M, block=1500)
    out = {"radii": radii, "sweep_ghg": sweep_ghg, "sweep_ns": sweep_ns}
    for k in METRIC_ORDER:
        out[f"any_{k}"] = any_[k]
        out[f"mm_{k}"] = mm[k]
    np.savez(CACHE, **out)
    return out


def main():
    rb.apply()
    df = fd.build()
    V = fd.vectors()
    M = macro_shares(df)
    have = np.isfinite(M).all(1)               # fair common centre set
    res = compute(df, V, M)
    radii = res["radii"]

    fig, axes = rb.subplots(2, 3, width="double", height=4.8)
    axes = axes.ravel()

    for ax, key in zip(axes, METRIC_ORDER):
        m = fd.METRICS[key]
        scale = 1 if key == "yll" else 100
        a_mean, *_ = flexlib.aggregate(res[f"any_{key}"][have])
        mm_mean, *_ = flexlib.aggregate(res[f"mm_{key}"][have])
        ax.plot(radii, a_mean * scale, color="#B0B0B0", lw=1.6,
                label="any substitute")
        ax.plot(radii, mm_mean * scale, color=m["color"], lw=2.0,
                label="macro-matched (≤10)")
        ax.set_title(m["label"], fontfamily=rb.SERIF, fontsize=8.5,
                     fontweight="bold")
        ax.set_ylabel("years gained / meal" if key == "yll"
                      else "best-case reduction (%)", fontsize=6.5)
        ax.set_xlabel("Flexibility (cosine radius)", fontsize=6.5)
        ax.set_xlim(0, radii.max()); ax.set_ylim(bottom=0)
        ax.grid(alpha=0.5)
        if key == "ghg":
            ax.legend(loc="lower right", fontsize=5.6)

    # ── tolerance-sweep panel ─────────────────────────────────────────────
    ax = axes[5]
    tol_x = [t if t < 100 else 75 for t in TOLS]    # plot "any" at a finite x
    g = np.nanmean(res["sweep_ghg"][have], 0) * 100
    s = np.nanmean(res["sweep_ns"][have], 0) * 100
    ax.plot(tol_x, g, color="#D73027", lw=2.0, marker="o", ms=2.5, label="GHG")
    ax.plot(tol_x, s, color="#A50026", lw=2.0, marker="s", ms=2.5,
            label="Nutri-Score")
    ax.axvspan(0, 5, color="#4575B4", alpha=0.07)
    ax.annotate("near-exact", xy=(2.5, 4), fontsize=4.8, family=rb.MONO,
                color="#4575B4", ha="center")
    ax.axvline(TOL0, color=rb.MUTED, ls=":", lw=0.8)
    ax.annotate("'similar'", xy=(TOL0 + 1, 8), fontsize=4.8, family=rb.MONO,
                color=rb.MUTED)
    ax.set_title(f"How strict must macros be? (r = {R_FIXED})",
                 fontfamily=rb.SERIF, fontsize=8, fontweight="bold")
    ax.set_xlabel("macro tolerance — % of calories allowed to shift", fontsize=6)
    ax.set_ylabel("best-case reduction (%)", fontsize=6.5)
    ax.set_ylim(0, 100); ax.set_xlim(0, 78)
    ax.set_xticks([0, 10, 20, 40, 75])
    ax.set_xticklabels(["0", "10", "20", "40", "any"], fontsize=6)
    ax.legend(loc="lower right", fontsize=5.6)
    ax.grid(alpha=0.5)

    rb.serif_title(fig, "Flexibility while keeping the macros similar",
                   fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005, f"{int(have.sum()):,} dishes with a macro profile · "
             f"macro distance = total variation of protein/fat/carb calorie "
             f"shares · macro-matched curves require TV ≤ {int(TOL0)}",
             ha="center", va="bottom", family=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    rb.save(fig, "figures/fig7_macro_flexibility")


if __name__ == "__main__":
    main()
