#!/usr/bin/env python3
"""
build_archipelago_footprint.py — VARIANT B ("cartogram")

Same archipelago, but now an **area cartogram**: each island's *size is
proportional to its menu popularity* — the total number of menu listings
across all the dishes on it.  Burgers/pizza/wings swell into continents;
niche cuisines shrink to cays.  No dots, no contours — area alone carries
the signal.

Islands keep roughly their manifold positions, then a Dorling-style
repulsion nudges them apart so the bigger ones don't overlap their
neighbours.  Shapes are organic blobs scaled to hit each island's exact
target area.

Shares data, naming, parchment, chrome and fonts with build_archipelago.py.

Outputs (into map/): dish_archipelago_footprint.{png,pdf}, gazetteer_footprint.csv
"""
from __future__ import annotations

import csv
import math
import os

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

import build_archipelago as A   # reuse data, naming, cosmetics, fonts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = os.path.join(HERE, "dish_archipelago_footprint.png")
OUT_PDF = os.path.join(HERE, "dish_archipelago_footprint.pdf")
OUT_GAZ = os.path.join(HERE, "gazetteer_footprint.csv")

# how island area maps to popularity (log scale: area ∝ log of menu count)
LAND_FRAC = 0.34      # total island area as a fraction of the 1000² canvas
LOG_PAD = 0.6         # added to log10(menus) so the rarest isle has a small,
                      #   non-zero area — smooth, not a hard floor
DORLING_ITERS = 1100  # overlap-removal passes
DORLING_PAD = 17.0    # sea gap kept between islands
ANCHOR_PULL = 0.004   # how hard islands are tugged back to their true spot


def organic_blob(cx, cy, target_area, rng):
    """An organic island outline centred at (cx, cy) with exactly
    `target_area`."""
    th = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    rad = np.ones_like(th)
    for k in range(3, 8):
        rad += (0.17 / (k - 2)) * np.sin(k * th + rng.uniform(0, 2 * np.pi))
    rad = np.clip(rad, 0.55, 1.6)
    xy = np.column_stack([np.cos(th) * rad, np.sin(th) * rad])
    poly = Polygon(xy)
    s = math.sqrt(target_area / poly.area)
    return Polygon(xy * s + [cx, cy])


def dorling(pos, r, anchor):
    """Push overlapping island-circles apart; gently tug toward anchors."""
    pos = pos.copy()
    n = len(pos)
    for _ in range(DORLING_ITERS):
        for i in range(n):
            for j in range(i + 1, n):
                d = pos[j] - pos[i]
                dist = math.hypot(d[0], d[1]) or 1e-6
                need = r[i] + r[j] + DORLING_PAD
                if dist < need:
                    push = (need - dist) / 2
                    u = d / dist
                    pos[i] -= u * push
                    pos[j] += u * push
        pos += (anchor - pos) * ANCHOR_PULL
        pos[:, 0] = np.clip(pos[:, 0], r, 1000 - r)
        pos[:, 1] = np.clip(pos[:, 1], r, 1000 - r)
    return pos


def main():
    rng = np.random.default_rng(A.SEED)
    print("Loading manifold …")
    reg, nx, ny = A.load_regions()
    sup = A.merge_regions(reg)

    isles, names_by_isle = [], {}
    for cid, v in sup.items():
        if len(v) < A.MIN_ISLAND_PTS:
            continue
        coords = np.array([(x, y) for x, y, _, _ in v])
        counts = np.array([c for _, _, _, c in v])
        names_by_isle[cid] = [nm for _, _, nm, _ in v]
        isles.append(dict(cid=cid, n=len(v),
                          anchor=coords.mean(0), pop_sum=int(counts.sum()),
                          pop=float(np.log10(counts).mean())))
    ranked = A.ranked_tokens(names_by_isle)
    for d in isles:
        d["tokens"] = ranked[d["cid"]]
        d["area"] = d["pop_sum"]          # name priority = popularity
    A.assign_names(isles)

    # ── size each island: area ∝ log10(total menu appearances) ──
    lo = min(math.log10(d["pop_sum"]) for d in isles)

    def area_of(pop):                       # continuous log mapping, no floor
        return unit * (math.log10(pop) - lo + LOG_PAD)

    unit = 1.0
    unit = LAND_FRAC * 1_000_000 / sum(area_of(d["pop_sum"]) for d in isles)
    for d in isles:
        d["target_area"] = area_of(d["pop_sum"])
        d["r"] = math.sqrt(d["target_area"] / math.pi)

    anchor = np.array([d["anchor"] for d in isles])
    r = np.array([d["r"] for d in isles])
    print(f"  packing {len(isles)} islands (area ∝ menu popularity) …")
    pos = dorling(anchor.copy(), r, anchor)
    for d, p in zip(isles, pos):
        d["geom"] = organic_blob(p[0], p[1], d["target_area"], rng)
        d["area"] = d["geom"].area        # real area now (for label sizing)

    # ── figure ──
    fig = plt.figure(figsize=(7, 7.6), dpi=600)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-40, 1040); ax.set_ylim(1090, -90); ax.axis("off")
    ax.imshow(A.parchment((900, 900), rng), extent=(-40, 1040, 1090, -90),
              zorder=0, interpolation="bilinear", aspect="auto")
    for g in range(0, 1001, 100):
        ax.plot([g, g], [-90, 1090], color=A.SEPIA_LT, lw=0.3, alpha=0.16, zorder=1)
        ax.plot([-40, 1040], [g, g], color=A.SEPIA_LT, lw=0.3, alpha=0.16, zorder=1)

    # solid land fill, hand-drawn coastline + a faint inner shore line
    for d in isles:
        for pat in A.geom_to_patches(d["geom"], facecolor=A.LAND, edgecolor="none",
                                     alpha=1.0, zorder=3):
            ax.add_patch(pat)
    for d in isles:
        for poly in A.polys_of(d["geom"]):
            xy = np.asarray(poly.exterior.coords)
            wob = A.jitter_ring(xy, amp=min(2.0, d["r"] * 0.03), rng=rng)
            ax.plot(wob[:, 0], wob[:, 1], color=A.SEPIA, lw=0.9, alpha=0.9,
                    zorder=6, solid_capstyle="round")
        shore = d["geom"].buffer(-d["r"] * 0.07)
        for poly in A.polys_of(shore):
            if poly.is_empty:
                continue
            xy = np.asarray(poly.exterior.coords)
            ax.plot(xy[:, 0], xy[:, 1], color=A.SEPIA_LT, lw=0.4, alpha=0.45,
                    zorder=6)

    # labels, sized by island radius (greedy nudge to avoid collisions)
    placed = []

    def free(x, y, hw, hh):
        for px, py, phw, phh in placed:
            if abs(x - px) < hw + phw and abs(y - py) < hh + phh:
                return False
        return True

    for d in sorted(isles, key=lambda d: -d["r"]):
        if d["r"] < 11:
            continue
        cx, cy = d["geom"].representative_point().coords[0]
        big = d["r"] > 62
        fs = float(np.clip(d["r"] * 0.31, 5.0, 18.0))
        txt = " ".join(d["name"].upper()) if big else d["name"]
        hw, hh = len(txt) * fs * 0.30 + 4, fs * 0.8 + 3
        # try the centre, else nudge vertically until clear
        y = cy
        for off in (0, hh + 3, -(hh + 3), 2 * hh + 6, -(2 * hh + 6)):
            if free(cx, cy + off, hw, hh):
                y = cy + off
                break
        placed.append((cx, y, hw, hh))
        t = ax.text(cx, y, txt, ha="center", va="center", zorder=20,
                    fontproperties=A.F_HEAD if big else A.F_LABEL, fontsize=fs,
                    color="#3F2E16" if big else A.SEPIA)
        t.set_path_effects([A.pe.withStroke(linewidth=2.4, foreground=A.PAPER, alpha=0.85)])

    # size legend: reference islands drawn to scale, in open water
    def size_legend(ax):
        by = 1012
        ax.text(430, by - 58, "island area  ~  log of menus served",
                fontproperties=A.F_BODY, fontsize=7.5, color=A.SEPIA,
                ha="center", va="bottom", zorder=33)
        cursor = 360
        for pop, lab in [(1000, "1k"), (10000, "10k"), (100000, "100k")]:
            rr = math.sqrt(area_of(pop) / math.pi)
            cx = cursor + rr
            ax.add_patch(plt.Circle((cx, by), rr, facecolor=A.LAND,
                                    ec=A.SEPIA, lw=0.8, alpha=0.97, zorder=33))
            ax.text(cx, by, lab, fontproperties=A.F_LABEL, fontsize=6.2,
                    color=A.SEPIA_LT, ha="center", va="center", zorder=34)
            cursor += 2 * rr + 16

    A.add_chrome(ax, rng,
                 "80,768 dishes  ·  charted from the 195k menu-item manifold  ·  "
                 "each island sized by how often its dishes appear on menus",
                 "", "", "", legend_fn=size_legend)

    fig.savefig(OUT_PNG, dpi=600)
    fig.savefig(OUT_PDF)
    print(f"  wrote {OUT_PNG}\n  wrote {OUT_PDF}")

    with open(OUT_GAZ, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["isle", "n_dishes", "total_menu_count", "mean_log10_menu_count",
                    "centroid_x", "centroid_y"])
        for d in sorted(isles, key=lambda d: -d["pop_sum"]):
            c = d["geom"].representative_point()
            w.writerow([d["name"], d["n"], d["pop_sum"], round(d["pop"], 3),
                        round(c.x, 1), round(c.y, 1)])
    print(f"  wrote {OUT_GAZ}")


if __name__ == "__main__":
    main()
