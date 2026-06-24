"""Figure 2 — The menu designer's opportunity (parallel menus).

A high-level infographic: today's menu on the left, a reimagined menu on the
right where each dish is swapped for a real, compositionally-similar dish from
its flexibility sphere that is BOTH lower-impact and healthier. Where a price
would sit, each item shows its carbon badge and a health grade — so the reader
sees that a greener, healthier menu is reachable without leaving the cuisine.

Swaps are automatic: for each dish we search its cosine neighbourhood (r<=R)
for the substitute that maximises combined GHG + health improvement while not
worsening either. All dishes, footprints, grades and swaps are real data.

Outputs: figures/fig2_menu_<archetype>.{pdf,png}
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

import figdata as fd
import rdylbu_style as rb

R = 0.20                      # flexibility radius allowed for a swap
GHG_SCALE = (0.5, 16.0)      # fixed colour scale for the carbon badge (kg/kg)
GRADE_COLOR = {"A": "#4575B4", "B": "#74ADD1", "C": "#FEE090",
               "D": "#F46D43", "E": "#A50026"}

# Archetype menus = lists of cluster_ids (curated from the real top dishes).
MENUS = {
    "subshop": ("The Sub Shop", [84406, 84404, 84424, 130325, 84432]),
    "pizzeria": ("The Pizzeria", [25524, 680, 670, 660, 785]),
}


def ghg_color(v):
    lo, hi = GHG_SCALE
    n = np.clip((np.log10(v) - np.log10(lo)) / (np.log10(hi) - np.log10(lo)), 0, 1)
    return rb.rdylbu_cmap(reverse=True)(n)   # high GHG -> red


def _search(near, df, i, same_cuisine):
    c = df.iloc[i]
    cg, cy, cz = c["ghg"], c["yll"], c["cuisine"]
    best, best_score = None, 0.0
    for j in near:
        r = df.iloc[j]
        g, y = r["ghg"], r["yll"]
        if not (np.isfinite(g) and np.isfinite(y)):
            continue
        if same_cuisine and r["cuisine"] != cz:
            continue
        if g >= cg * 0.9 or y < cy:          # must cut GHG >=10% and not hurt health
            continue
        score = (cg - g) / cg + max(0.0, (y - cy)) * 2.0
        if score > best_score:
            best, best_score = j, score
    return best


def find_swap(i, df, V, cid_rows):
    """Best win-win substitute for dish row i. Prefer same cuisine (keeps the
    reimagined menu coherent), fall back to any dish if none qualifies."""
    d = 1.0 - (V @ V[i])
    d[i] = np.inf
    near = np.where(d <= R)[0]
    if len(near) == 0:
        return None
    return _search(near, df, i, same_cuisine=True) or \
        _search(near, df, i, same_cuisine=False)


def chip(ax, x, y, w, h, text, facecolor, textcolor):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=facecolor, ec="none", transform=ax.transAxes,
                                zorder=3))
    ax.text(x + w / 2, y + h / 2, text, transform=ax.transAxes, ha="center",
            va="center", fontsize=5.6, family=rb.MONO, color=textcolor,
            zorder=4, fontweight="bold")


def dish_block(ax, x0, w, ytop, name, ghg, grade, align="left"):
    ha = "left" if align == "left" else "right"
    tx = x0 if align == "left" else x0 + w
    ax.text(tx, ytop, name, transform=ax.transAxes, ha=ha, va="top",
            fontsize=8.2, family=rb.SERIF, color=rb.INK)
    cy = ytop - 0.052
    gc = ghg_color(ghg)
    gtxt_col = "white" if np.mean(gc[:3]) < 0.6 else rb.INK
    cw, ch = 0.13, 0.034
    cx = x0 if align == "left" else x0 + w - cw - 0.135
    chip(ax, cx, cy - ch, cw, ch, f"{ghg:.1f} kg CO2e", gc, gtxt_col)
    hc = GRADE_COLOR.get(grade, "#999")
    htxt = "white" if grade in ("A", "D", "E") else rb.INK
    chip(ax, cx + cw + 0.012, cy - ch, 0.11, ch, f"Health {grade}", hc, htxt)


def render(key, df, V, cid_rows):
    title, cids = MENUS[key]
    rows = [cid_rows[c] for c in cids]
    swaps = [find_swap(i, df, V, cid_rows) for i in rows]

    fig, ax = rb.figure(width="double", height=6.4)
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    rb.serif_title(ax, "A greener, healthier menu — without leaving the cuisine",
                   fontsize=12, fontweight="bold")
    ax.text(0.25, 0.92, "TODAY", transform=ax.transAxes, ha="center",
            family=rb.MONO, fontsize=8, color=rb.MUTED, fontweight="bold")
    ax.text(0.78, 0.92, "REIMAGINED", transform=ax.transAxes, ha="center",
            family=rb.MONO, fontsize=8, color="#4575B4", fontweight="bold")
    ax.text(0.5, 0.965, title, transform=ax.transAxes, ha="center",
            family=rb.SERIF, fontsize=9, style="italic", color=rb.INK)
    ax.axvline(0.5, ymin=0.08, ymax=0.88, color=rb.GRID, lw=0.8)

    n = len(rows)
    top, bot = 0.85, 0.30
    ys = np.linspace(top, bot, n)
    tot = dict(g0=0, g1=0, better=0)
    for y, i, j in zip(ys, rows, swaps):
        c = df.iloc[i]
        dish_block(ax, 0.04, 0.40, y, c["top_raw_name"], c["ghg"],
                   c["nutriscore_grade"], "left")
        tot["g0"] += c["ghg"]
        if j is None:
            ax.text(0.78, y - 0.02, "(already optimal)", transform=ax.transAxes,
                    ha="center", va="top", fontsize=6, family=rb.MONO,
                    color=rb.MUTED)
            tot["g1"] += c["ghg"]
            continue
        s = df.iloc[j]
        dish_block(ax, 0.56, 0.40, y, s["top_raw_name"], s["ghg"],
                   s["nutriscore_grade"], "right")
        tot["g1"] += s["ghg"]
        tot["better"] += 1
        cut = (c["ghg"] - s["ghg"]) / c["ghg"] * 100
        ax.add_patch(FancyArrowPatch((0.455, y - 0.03), (0.545, y - 0.03),
                     transform=ax.transAxes, arrowstyle="-|>", mutation_scale=8,
                     color="#4575B4", lw=1.0, zorder=2))
        ax.text(0.5, y - 0.058, f"-{cut:.0f}% CO2e", transform=ax.transAxes,
                ha="center", va="top", fontsize=5.4, family=rb.MONO,
                color="#4575B4", fontweight="bold")

    # ── bottom summary ────────────────────────────────────────────────────
    red = (tot["g0"] - tot["g1"]) / tot["g0"] * 100
    ax.add_patch(FancyBboxPatch((0.04, 0.05), 0.92, 0.16,
                 boxstyle="round,pad=0.005,rounding_size=0.02", fc="#F4F7FB",
                 ec=rb.GRID, lw=0.8, transform=ax.transAxes, zorder=0))
    ax.text(0.20, 0.155, f"-{red:.0f}%", transform=ax.transAxes, ha="center",
            family=rb.SERIF, fontsize=22, fontweight="bold", color="#4575B4")
    ax.text(0.20, 0.085, "menu carbon\nfootprint", transform=ax.transAxes,
            ha="center", va="center", fontsize=6, family=rb.MONO, color=rb.MUTED)
    ax.text(0.55, 0.155, f"{tot['better']}/{n}", transform=ax.transAxes,
            ha="center", family=rb.SERIF, fontsize=22, fontweight="bold",
            color="#4575B4")
    ax.text(0.55, 0.085, "dishes made greener\n& at least as healthy",
            transform=ax.transAxes, ha="center", va="center", fontsize=6,
            family=rb.MONO, color=rb.MUTED)
    ax.text(0.81, 0.155, f"{tot['g0']:.0f}→{tot['g1']:.0f}",
            transform=ax.transAxes, ha="center", family=rb.SERIF, fontsize=16,
            fontweight="bold", color=rb.INK)
    ax.text(0.81, 0.085, "kg CO2e / kg\n(menu total)", transform=ax.transAxes,
            ha="center", va="center", fontsize=6, family=rb.MONO, color=rb.MUTED)

    ax.text(0.5, 0.015, f"Swaps drawn from each dish's flexibility sphere "
            f"(cosine r ≤ {R}) · real canonical dishes, footprints & "
            f"Nutri-Score grades from the 39k manifold", transform=ax.transAxes,
            ha="center", va="bottom", family=rb.MONO, fontsize=5.0,
            color=rb.MUTED)
    fig.tight_layout()
    rb.save(fig, f"figures/fig2_menu_{key}")


def main():
    rb.apply()
    df = fd.build()
    V = fd.vectors()
    cid_rows = {int(c): i for i, c in enumerate(df["cluster_id"].to_numpy())}
    for key in MENUS:
        render(key, df, V, cid_rows)


if __name__ == "__main__":
    main()
