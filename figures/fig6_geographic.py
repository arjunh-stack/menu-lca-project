"""Figure 6 — Geographic equity of impact & nutrition.

Do more-affluent areas have access to lower-impact, healthier dishes? We have
no income data, so we use each ZIP's mean menu price as an affluence proxy and
ask how the dishes actually served there score on impact and health.

Per real menu row (menu_dishes.sqlite) we join the dish's GHG / Nutri-Score /
ΔYLL (from the 39k manifold, by canonical name), aggregate to the ZIP, keep
ZIPs with >= MIN_ROWS priced+scored rows, and:
  (A) map ZIPs over the continental US, coloured by mean Nutri-Score
      (red = less healthy food environment).
  (B-D) ZIP-level scatter of affluence (mean price) vs mean GHG / Nutri-Score
      / ΔYLL, with a weighted Spearman ρ.

Outputs: figures/fig6_geographic.{pdf,png}
"""
from __future__ import annotations

import os
import sqlite3
from collections import defaultdict

import numpy as np

import json

import figdata as fd
import rdylbu_style as rb

MIN_ROWS = 40           # ZIPs need this many priced+scored menu rows
CACHE = os.path.join(rb.FIG_DIR, "_zip_agg.npz")
STATES_GEOJSON = os.path.join(rb.FIG_DIR, "data", "us_states.geojson")
US = dict(lng=(-125, -66), lat=(24, 50))   # continental extent


def draw_states(ax):
    """Draw US state boundaries from a bundled GeoJSON (no geopandas)."""
    if not os.path.exists(STATES_GEOJSON):
        return
    gj = json.load(open(STATES_GEOJSON))
    for feat in gj["features"]:
        geom = feat["geometry"]
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        for poly in polys:
            for ring in poly:
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                ax.plot(xs, ys, color="#9AA5B1", lw=0.4, zorder=1)


def aggregate():
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=True)
        return {k: z[k] for k in z.files}
    df = fd.build()
    # canonical name -> metrics (manifold dishes only)
    name2 = {r.canonical_name: (r.ghg, r.nutriscore, r.yll)
             for r in df.itertuples()}
    acc = defaultdict(lambda: dict(price=[], ghg=[], ns=[], yll=[],
                                   lat=[], lng=[]))
    con = sqlite3.connect(fd.MENUDB)
    q = ("select zip_code, lat, lng, price_usd, canonical_dish from menu_dishes "
         "where price_usd is not null and price_usd>0 and zip_code is not null")
    for zip_code, lat, lng, price, name in con.execute(q):
        m = name2.get(name)
        if not m or not np.isfinite(m[0]):
            continue
        a = acc[zip_code]
        a["price"].append(price); a["ghg"].append(m[0])
        a["ns"].append(m[1]); a["yll"].append(m[2])
        if lat and lng:
            a["lat"].append(lat); a["lng"].append(lng)
    con.close()

    rows = []
    for zc, a in acc.items():
        if len(a["price"]) < MIN_ROWS or not a["lat"]:
            continue
        rows.append((np.median(a["price"]), np.nanmean(a["ghg"]),
                     np.nanmean(a["ns"]), np.nanmean(a["yll"]),
                     np.median(a["lat"]), np.median(a["lng"]), len(a["price"])))
    arr = np.array(rows, float)
    out = dict(price=arr[:, 0], ghg=arr[:, 1], ns=arr[:, 2], yll=arr[:, 3],
               lat=arr[:, 4], lng=arr[:, 5], n=arr[:, 6])
    np.savez(CACHE, **out)
    return out


def wspearman(x, y, w):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    mx = np.average(rx, weights=w); my = np.average(ry, weights=w)
    cov = np.average((rx - mx) * (ry - my), weights=w)
    sx = np.sqrt(np.average((rx - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((ry - my) ** 2, weights=w))
    return cov / (sx * sy)


def scatter_panel(ax, z, key, label, better):
    x = z["price"]; y = z[key]; w = z["n"]
    ax.scatter(x, y, s=np.clip(w / 8, 2, 40), c="#9E9E9E", alpha=0.25, lw=0)
    # binned weighted median trend
    edges = fd.wquantile(x, w, np.linspace(0, 1, 9))
    edges = np.unique(edges)
    cx, md = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        s = (x >= a) & (x <= b)
        if s.sum() < 10:
            continue
        cx.append(np.average(x[s], weights=w[s]))
        md.append(fd.wquantile(y[s], w[s], 0.5))
    color = "#D73027" if better == "lower" else "#313695"
    ax.plot(cx, md, color=color, lw=1.8, marker="o", ms=2.5)
    rho = wspearman(x, y, w)
    ax.annotate(rf"$\rho$ = {rho:+.2f}", xy=(0.96, 0.93),
                xycoords="axes fraction", ha="right", va="top",
                family=rb.MONO, fontsize=6.5, fontweight="bold")
    ax.set_xlabel("ZIP mean price ($, affluence proxy)", fontsize=6)
    ax.set_ylabel(label, fontsize=6)
    ax.set_title(label, fontfamily=rb.SERIF, fontsize=8, fontweight="bold")
    ax.grid(alpha=0.5)
    return rho


def main():
    rb.apply()
    z = aggregate()
    print(f"[geo] {len(z['price'])} ZIPs with >= {MIN_ROWS} priced+scored rows")

    fig, axes = rb.subplots(2, 2, width="double", height=6.0)
    (axMap, axB), (axC, axD) = axes

    # ── A: US map coloured by mean Nutri-Score (red = less healthy) ───────
    m = (z["lng"] > US["lng"][0]) & (z["lng"] < US["lng"][1]) & \
        (z["lat"] > US["lat"][0]) & (z["lat"] < US["lat"][1])
    ns = z["ns"][m]
    lo, hi = np.percentile(ns, [5, 95])
    norm = np.clip((ns - lo) / (hi - lo or 1), 0, 1)
    cmap = rb.rdylbu_cmap(reverse=True)         # high Nutri-Score -> red (worse)
    draw_states(axMap)
    axMap.scatter(z["lng"][m], z["lat"][m], s=np.clip(z["n"][m] / 6, 3, 60),
                  c=cmap(norm), alpha=0.85, lw=0, rasterized=True, zorder=2)
    axMap.set_title("Food-environment health by ZIP\n(red = less healthy)",
                    fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold")
    axMap.set_xlim(*US["lng"]); axMap.set_ylim(*US["lat"])
    axMap.set_aspect(1.25)
    axMap.set_xticks([]); axMap.set_yticks([])
    axMap.grid(False)
    for sp in axMap.spines.values():
        sp.set_visible(False)

    scatter_panel(axB, z, "ghg", "Mean GHG (kg CO₂e/kg)", "lower")
    scatter_panel(axC, z, "ns", "Mean Nutri-Score (0–100)", "lower")
    scatter_panel(axD, z, "yll", r"Mean $\Delta$YLL (yrs gained)", "higher")

    rb.serif_title(fig, "Geographic equity of dish impact & nutrition",
                   fontsize=11, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005, f"{len(z['price']):,} US ZIP codes · ≥{MIN_ROWS} "
             f"priced menu rows each · dish metrics joined from the 39k "
             f"manifold · affluence proxied by ZIP mean price",
             ha="center", va="bottom", family=rb.MONO, fontsize=5.2,
             color=rb.MUTED)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    rb.save(fig, "figures/fig6_geographic")


if __name__ == "__main__":
    main()
