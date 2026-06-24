"""Figure 2 — Real restaurant menus, scored.

Instead of inventing menus, we pull two ACTUAL restaurant menus from the
dataset (menu_dishes.sqlite — real items, real prices) and add the two numbers
a menu never shows: each dish's carbon footprint and a health grade. Items are
sorted greenest-first and colour-coded, so a diner can see at a glance which
item on the menu they're already looking at is the better choice — and the
footer shows the saving from the menu's worst pick to its best.

This keeps every item inside one coherent real menu (no cross-cuisine swaps).

Outputs: figures/fig2_real_menu.{pdf,png}
"""
from __future__ import annotations

import sqlite3

import numpy as np
from matplotlib.patches import FancyBboxPatch

import figdata as fd
import rdylbu_style as rb

GHG_SCALE = (0.5, 16.0)
GRADE_COLOR = {"A": "#4575B4", "B": "#74ADD1", "C": "#FEE090",
               "D": "#F46D43", "E": "#A50026"}
# (restaurant_id, clean display name, max items)
RESTAURANTS = [(461, "Five Guys", 9), (692, "Sbarro", 9)]


def ghg_color(v):
    lo, hi = GHG_SCALE
    n = np.clip((np.log10(v) - np.log10(lo)) / (np.log10(hi) - np.log10(lo)), 0, 1)
    return rb.rdylbu_cmap(reverse=True)(n)


def load_menu(rid, df_by_name, cap):
    con = sqlite3.connect(fd.MENUDB)
    rows = con.execute(
        "select raw_menu_name, price_usd, canonical_dish from menu_dishes "
        "where restaurant_id=? and price_usd>0", (rid,)).fetchall()
    con.close()
    seen, items = set(), []
    for raw, price, canon in rows:
        if canon in seen or canon not in df_by_name.index:
            continue
        seen.add(canon)
        r = df_by_name.loc[canon]
        if not np.isfinite(r["ghg"]):
            continue
        items.append(dict(name=raw, price=price, ghg=float(r["ghg"]),
                          grade=r["nutriscore_grade"], ns=float(r["nutriscore"])))
    items.sort(key=lambda d: d["ghg"])
    if len(items) > cap:                       # keep a spread across the range
        idx = np.linspace(0, len(items) - 1, cap).round().astype(int)
        items = [items[i] for i in idx]
    return items


def chip(ax, x, y, w, h, text, fc, tc):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.003,rounding_size=0.01", fc=fc, ec="none",
                 transform=ax.transAxes, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, transform=ax.transAxes, ha="center",
            va="center", fontsize=5.3, family=rb.MONO, color=tc, zorder=4,
            fontweight="bold")


def render_menu(ax, items, name):
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.0, 0.97, name, transform=ax.transAxes, family=rb.SERIF,
            fontsize=11, fontweight="bold", va="top")
    ax.text(0.0, 0.915, "real menu · sorted greenest → heaviest",
            transform=ax.transAxes, family=rb.MONO, fontsize=5.2,
            color=rb.MUTED, va="top")

    # badness for the colour strip = blend of within-menu GHG rank & Nutri-Score
    g = np.array([it["ghg"] for it in items])
    s = np.array([it["ns"] for it in items])
    gb = (np.log10(g) - np.log10(g).min()) / (np.ptp(np.log10(g)) or 1)
    sb = (s - s.min()) / (np.ptp(s) or 1)
    bad = 0.55 * gb + 0.45 * sb
    strip_cmap = rb.rdylbu_cmap(reverse=True)

    top, bot = 0.85, 0.16
    ys = np.linspace(top, bot, len(items))
    gap = (top - bot) / max(len(items) - 1, 1)
    for y, it, b in zip(ys, items, bad):
        ax.add_patch(FancyBboxPatch((0.0, y - gap * 0.30), 0.018, gap * 0.62,
                     boxstyle="square,pad=0", fc=strip_cmap(b), ec="none",
                     transform=ax.transAxes, zorder=3))
        ax.text(0.035, y, it["name"][:30], transform=ax.transAxes, va="center",
                family=rb.SERIF, fontsize=7.3, color=rb.INK)
        ax.text(1.0, y, f"${it['price']:.2f}", transform=ax.transAxes,
                va="center", ha="right", family=rb.MONO, fontsize=6.6,
                color=rb.INK)
        gc = ghg_color(it["ghg"])
        gtc = "white" if np.mean(gc[:3]) < 0.6 else rb.INK
        chip(ax, 0.035, y - gap * 0.42, 0.20, gap * 0.30,
             f"{it['ghg']:.1f} kg CO2e", gc, gtc)
        hc = GRADE_COLOR[it["grade"]]
        htc = "white" if it["grade"] in ("A", "D", "E") else rb.INK
        chip(ax, 0.245, y - gap * 0.42, 0.115, gap * 0.30,
             f"Health {it['grade']}", hc, htc)

    best, worst = items[0], items[-1]
    cut = (worst["ghg"] - best["ghg"]) / worst["ghg"] * 100
    ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 0.1,
                 boxstyle="round,pad=0.004,rounding_size=0.015", fc="#F4F7FB",
                 ec=rb.GRID, lw=0.7, transform=ax.transAxes, zorder=0))
    ax.text(0.5, 0.05,
            f"Pick the {best['name'][:18]} over the {worst['name'][:18]}:  "
            f"-{cut:.0f}% carbon, {worst['grade']}→{best['grade']}",
            transform=ax.transAxes, ha="center", va="center", family=rb.MONO,
            fontsize=5.3, color="#4575B4", fontweight="bold")


def main():
    rb.apply()
    df = fd.build().set_index("canonical_name")
    fig, axes = rb.subplots(1, 2, width="double", height=5.6)
    for ax, (rid, name, cap) in zip(axes, RESTAURANTS):
        render_menu(ax, load_menu(rid, df, cap), name)
    rb.serif_title(fig, "Real menus, scored: which item is actually better?",
                   fontsize=12, fontweight="bold", y=1.0)
    fig.text(0.5, 0.005, "Actual restaurant menus & prices from the dataset · "
             "colour strip = combined carbon + Nutri-Score (red = worse) · "
             "kg CO2e per kg · health grade A–E",
             ha="center", va="bottom", family=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    rb.save(fig, "figures/fig2_real_menu")


if __name__ == "__main__":
    main()
