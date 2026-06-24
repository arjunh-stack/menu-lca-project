#!/usr/bin/env python3
"""
build_archipelago.py — VARIANT A ("topo")

The 195k-dish manifold as an old-timey archipelago, with BROAD islands
and popularity *topography* (contour lines).

Pipeline
--------
1.  Load the merged 195k manifold (UMAP coords + dish metadata).
2.  Drop every dish listed on only one menu (total_count == 1).
3.  Take the precomputed UMAP semantic regions and **merge** neighbours
    (agglomerative on region centroids) into ~50 broad landmasses — the
    ISLAND_MERGE_DIST knob controls how broad.
4.  Draw an organic coastline around each landmass (buffer-union of its
    dots → smoothed blob); name it by its most distinctive dish token.
5.  Build a **popularity elevation field** (popular dishes pile into
    mountains) and draw it as hypsometric tint + sepia contour lines,
    clipped to land.  RdYlBu: red = popular/high, blue = rare/low.
6.  Render it aged: parchment sea, compass rose, cartouche, gazetteer.

Outputs (into map/): dish_archipelago_topo.{png,pdf}, gazetteer_topo.csv
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import Counter, defaultdict

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from scipy import ndimage
from shapely.affinity import scale as shp_scale
from shapely.geometry import MultiPolygon, MultiPoint, Point, Polygon
from shapely.ops import unary_union
from sklearn.cluster import AgglomerativeClustering

# ───────────────────────── config ──────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFOLD = os.path.join(ROOT, "experiment", "manifold_merged", "data")
META_CSV = os.path.join(MANIFOLD, "dish_meta.csv")
UMAP_JSON = os.path.join(MANIFOLD, "umap.json")

OUT_PNG = os.path.join(HERE, "dish_archipelago_topo.png")
OUT_PDF = os.path.join(HERE, "dish_archipelago_topo.pdf")
OUT_GAZ = os.path.join(HERE, "gazetteer_topo.csv")

# ── knobs ───────────────────────────────────────────────────────────
ISLAND_MERGE_DIST = 85   # centroid distance to fuse regions; bigger →
                         #   fewer, broader islands (60≈90, 85≈50, 120≈30)
MIN_ISLAND_PTS = 25      # smaller merged clumps become unnamed islets
MIN_LABEL_PTS = 130      # only isles at least this big get a name
ISLAND_SCALE = 0.93      # shrink each isle about its centroid so neighbours
                         #   sit slightly apart (1.0 = touching, lower = more sea)
TOPO_LEVELS = 9          # popularity contour lines
GRID = 600               # elevation-field raster resolution
SIGMA_POP = 5.0          # popularity-field smoothing (cells)
SEED = 7

# ColorBrewer 11-class RdYlBu (red = hot/high ... blue = cold/low)
RDYLBU = [
    "#A50026", "#D73027", "#F46D43", "#FDAE61", "#FEE090", "#FFFFBF",
    "#E0F3F8", "#ABD9E9", "#74ADD1", "#4575B4", "#313695",
]
RDYLBU_CMAP = LinearSegmentedColormap.from_list("rdylbu", RDYLBU, N=256)
HYPSO = RDYLBU_CMAP.reversed()         # low → blue, high → red

# aged-paper palette
PAPER, PAPER_DK = "#ECE0C2", "#D9C79E"
LAND = "#E7D7AC"
SEPIA, SEPIA_LT = "#5A4427", "#8A7350"
SEA_DEEP = "#C9B789"

STOP = set(
    "and or the with of a in on de la el to set combo plate platter side sides "
    "served fresh house special new style your choice add only all our two one "
    "half full small large reg regular".split()
)
GENERIC = set(
    "chicken sauce cheese fried grilled spicy bbq sweet hot classic crispy roll "
    "rolls bowl wrap sandwich salad soup dip plate meal combo".split()
)
PRETTIFY = {
    "nigiri": "Nigiri", "pho": "Pho", "pollo": "Pollo", "asada": "Asada",
    "pastor": "Pastor", "boneless": "Boneless Wing", "garden": "Garden Greens",
    "dog": "Hot Dogs", "mac": "Mac & Cheese", "mein": "Lo Mein",
    "belly": "Pork Belly",
}


# ──────────────────────── data + naming ────────────────────────────
def load_regions():
    """region_id -> list[(x, y, name, count)] for count>1 dishes,
    plus open-sea (region == -1) coords."""
    meta = {int(r["idx"]): r for r in csv.DictReader(open(META_CSV))}
    pts = json.load(open(UMAP_JSON))["points"]
    reg = defaultdict(list)
    nx, ny = [], []
    dropped = kept = 0
    for p in pts:
        m = meta.get(p["idx"])
        if not m:
            continue
        c = int(m["total_count"])
        if c <= 1:
            dropped += 1
            continue
        kept += 1
        if p["region"] == -1:
            nx.append(p["x"]); ny.append(p["y"])
        else:
            reg[p["region"]].append((p["x"], p["y"], m["canonical_name"], c))
    print(f"  kept {kept:,} dishes (count>1); dropped {dropped:,} single-listing")
    return reg, np.array(nx), np.array(ny)


def merge_regions(reg):
    """Fuse neighbouring regions into broad landmasses."""
    rids = sorted(reg)
    cent = np.array([[np.mean([t[0] for t in reg[r]]),
                      np.mean([t[1] for t in reg[r]])] for r in rids])
    cl = AgglomerativeClustering(n_clusters=None, linkage="average",
                                 distance_threshold=ISLAND_MERGE_DIST).fit(cent)
    sup = defaultdict(list)
    for rid, lab in zip(rids, cl.labels_):
        sup[int(lab)].extend(reg[rid])
    print(f"  merged {len(rids)} regions → {len(sup)} broad isles "
          f"(ISLAND_MERGE_DIST={ISLAND_MERGE_DIST})")
    return sup


def tokens(name):
    return {t for t in re.split(r"[^a-z]+", name.lower()) if len(t) > 2 and t not in STOP}


def ranked_tokens(names_by_isle):
    docfreq = Counter()
    for names in names_by_isle.values():
        seen = set()
        for nm in names:
            seen |= tokens(nm)
        for t in seen:
            docfreq[t] += 1
    N = len(names_by_isle)
    ranked = {}
    for cid, names in names_by_isle.items():
        cnt = Counter()
        for nm in names:
            for t in tokens(nm):
                cnt[t] += 1
        scored = sorted(
            ((cnt[t] * math.log((N + 1) / (docfreq[t] + 0.5)) *
              (0.25 if t in GENERIC else 1.0), t) for t in cnt), reverse=True)
        ranked[cid] = [t for _, t in scored[:6]] or ["terra"]
    return ranked


def assign_names(isles):
    used = set()
    for d in sorted(isles, key=lambda d: -d["area"]):
        pick = next((t for t in d["tokens"] if t not in used), d["tokens"][0])
        used.add(pick)
        d["name"] = PRETTIFY.get(pick, pick.title())


# ──────────────────── geometry: coastlines ─────────────────────────
def coastline(coords):
    n = len(coords)
    if n < 3:
        return None
    span = np.sqrt(np.ptp(coords[:, 0]) ** 2 + np.ptp(coords[:, 1]) ** 2)
    reach = float(np.clip(span / max(8, math.sqrt(n)) * 1.45, 7.0, 22.0))
    blob = unary_union([Point(x, y).buffer(reach, quad_segs=8) for x, y in coords])
    blob = blob.buffer(-reach * 0.40).buffer(reach * 0.52)
    if blob.is_empty:
        blob = MultiPoint([tuple(c) for c in coords]).buffer(reach)
    return blob.simplify(reach * 0.18)


def jitter_ring(xy, amp, rng):
    if len(xy) < 4:
        return xy
    noise = rng.normal(0, amp, len(xy))
    noise = np.convolve(np.r_[noise, noise[:5]], np.ones(5) / 5, "same")[: len(xy)]
    c = xy.mean(0)
    d = xy - c
    norm = np.linalg.norm(d, axis=1, keepdims=True)
    norm[norm == 0] = 1
    return xy + (d / norm) * noise[:, None]


def polys_of(geom):
    return geom.geoms if isinstance(geom, MultiPolygon) else [geom]


def compound_path(geoms):
    verts, codes = [], []
    for geom in geoms:
        for poly in polys_of(geom):
            if poly.is_empty:
                continue
            for ring in [poly.exterior, *poly.interiors]:
                xy = np.asarray(ring.coords)
                verts.extend(xy)
                codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2) + [MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def geom_to_patches(geom, **kw):
    for poly in polys_of(geom):
        if poly.is_empty:
            continue
        verts, codes = [], []
        for ring in [poly.exterior, *poly.interiors]:
            xy = np.asarray(ring.coords)
            verts.extend(xy)
            codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2) + [MplPath.CLOSEPOLY]
        yield PathPatch(MplPath(verts, codes), **kw)


# ───────────────────────── cosmetics ───────────────────────────────
def value_noise(shape, rng, octaves=5):
    h, w = shape
    field = np.zeros((h, w))
    for oct_ in range(1, octaves + 1):
        s = 2 ** oct_
        small = rng.normal(0, 1, (s, s))
        ys = np.clip(np.linspace(0, s - 1, h).astype(int), 0, s - 1)
        xs = np.clip(np.linspace(0, s - 1, w).astype(int), 0, s - 1)
        field += small[np.ix_(ys, xs)] / oct_
    return (field - field.min()) / (np.ptp(field) + 1e-9)


def parchment(shape, rng):
    h, w = shape
    field = value_noise(shape, rng)
    c0, c1 = np.array(to_rgb(PAPER)), np.array(to_rgb(PAPER_DK))
    img = c0[None, None] * (1 - field[..., None] * 0.55) + c1[None, None] * (field[..., None] * 0.55)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vig = np.clip(1 - 0.28 * np.clip(r - 0.5, 0, 1) ** 2 * 2, 0.72, 1)
    img *= vig[..., None]
    for _ in range(220):
        cy, cx = rng.integers(0, h), rng.integers(0, w)
        img[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2] *= rng.uniform(0.9, 0.97)
    return np.clip(img, 0, 1)


def compass_rose(ax, cx, cy, r):
    # the axes y-grid is flipped (north is up on screen), so subtract the
    # sin term to keep the long point and the "N" pointing upward
    for k in range(8):
        a = math.pi / 2 - k * math.pi / 4
        lng = r if k % 2 == 0 else r * 0.62
        x2, y2 = cx + lng * math.cos(a), cy - lng * math.sin(a)
        for sgn in (+1, -1):
            bx = cx + lng * 0.28 * math.cos(a + sgn * 0.13)
            by = cy - lng * 0.28 * math.sin(a + sgn * 0.13)
            ax.fill([cx, bx, x2], [cy, by, y2], color=SEPIA,
                    alpha=0.9 if sgn > 0 else 0, ec=SEPIA, lw=0.5, zorder=40)
    for rr in (r * 1.02, r * 1.08):
        ax.add_patch(plt.Circle((cx, cy), rr, fill=False, ec=SEPIA, lw=0.6, zorder=40))
    ax.text(cx, cy - r * 1.18, "N", ha="center", va="center",
            fontproperties=F_HEAD, fontsize=11, color=SEPIA, zorder=41)


# ───────────────────────── fonts ───────────────────────────────────
FONT_DIR = os.path.join(HERE, "fonts")


def _fp(fname):
    path = os.path.join(FONT_DIR, fname)
    fm.fontManager.addfont(path)
    return fm.FontProperties(fname=path)


F_TITLE = _fp("Cinzel[wght].ttf")
F_LABEL = _fp("IBMPlexSerif-Italic.ttf")
F_HEAD = _fp("IBMPlexSerif-SemiBold.ttf")
F_BODY = _fp("IBMPlexSerif-Regular.ttf")
F_MONO = _fp("IBMPlexMono-Regular.ttf")


# ───────────────────────── render ──────────────────────────────────
def flourish_rule(ax, xc, y, half, lw=1.0):
    """A thin divider rule with little diamond end-caps + centre stud."""
    ax.plot([xc - half, xc + half], [y, y], color=SEPIA, lw=lw, zorder=31,
            solid_capstyle="round")
    for mx, ms in ((xc - half, 4), (xc + half, 4), (xc, 5)):
        ax.plot([mx], [y], marker="D", ms=ms, color=SEPIA, zorder=31)


def add_chrome(ax, rng, subtitle, legend_lo, legend_hi, legend_cap, legend_fn=None):
    for inset, lw in ((0, 2.4), (16, 0.8)):
        ax.add_patch(plt.Rectangle((-40 + inset, -90 + inset), 1080 - 2 * inset,
                                   1180 - 2 * inset, fill=False, ec=SEPIA, lw=lw, zorder=30))
    ax.text(500, -50, "THE  CULINARY  ARCHIPELAGO", ha="center", va="center",
            fontproperties=F_TITLE, fontsize=19, color=SEPIA, zorder=31)
    flourish_rule(ax, 500, -29, 240)
    ax.text(500, -15, "a map of 80,768 menu dishes", ha="center", va="center",
            fontproperties=F_LABEL, fontsize=13, color=SEPIA_LT, zorder=31)
    ax.text(500, 1, subtitle, ha="center", va="center", fontproperties=F_MONO,
            fontsize=5.6, color=SEPIA_LT, zorder=31)
    compass_rose(ax, 120, 940, 52)
    sx, sy = 760, 980
    ax.plot([sx, sx + 200], [sy, sy], color=SEPIA, lw=1.4, zorder=31)
    for i in range(5):
        seg = [sx + i * 40, sx + (i + 1) * 40]
        if i % 2 == 0:
            ax.fill_between(seg, sy - 4, sy + 4, color=SEPIA, zorder=31)
        ax.plot([seg[0], seg[0]], [sy - 5, sy + 5], color=SEPIA, lw=0.8, zorder=31)
    ax.plot([sx + 200, sx + 200], [sy - 5, sy + 5], color=SEPIA, lw=0.8, zorder=31)
    ax.text(sx + 100, sy + 20, "leagues of flavour", ha="center", va="top",
            fontproperties=F_LABEL, fontsize=7, color=SEPIA_LT, zorder=31)
    if legend_fn is not None:
        legend_fn(ax)
        return
    # ── key: an un-boxed colour bar, centred along the bottom ──
    cx, top = 500, 1004
    ax.text(cx, top, legend_cap, ha="center", va="center", fontproperties=F_HEAD,
            fontsize=8.5, color=SEPIA, zorder=33)
    barw, barh = 210, 12
    barx, bary = cx - barw / 2, top + 16
    # fade the bar exactly like the map: HYPSO blended 50/50 with the land
    # tone, so the key matches the hypsometric tint on the islands
    grad = HYPSO(np.linspace(0, 1, 256))[:, :3]
    faded = (0.5 * grad + 0.5 * np.array(to_rgb(LAND)))[None, :, :]
    ax.imshow(faded, extent=(barx, barx + barw, bary + barh, bary),
              aspect="auto", zorder=33)
    ax.add_patch(plt.Rectangle((barx, bary), barw, barh, fill=False, ec=SEPIA,
                               lw=0.7, zorder=34))
    ax.text(barx - 6, bary + barh / 2, legend_lo, ha="right", va="center",
            fontproperties=F_BODY, fontsize=7, color=SEPIA, zorder=33)
    ax.text(barx + barw + 6, bary + barh / 2, legend_hi, ha="left", va="center",
            fontproperties=F_BODY, fontsize=7, color=SEPIA, zorder=33)
    ax.text(cx, bary + barh + 16, "the higher the land, the more often it is on menus",
            ha="center", va="center", fontproperties=F_LABEL, fontsize=6,
            color=SEPIA_LT, zorder=33)


def _overlaps(x, y, hw, hh, placed):
    return any(abs(x - px) < hw + phw and abs(y - py) < hh + phh
               for px, py, phw, phh in placed)


def place_labels(ax, isles):
    """Place island names, nudging to dodge already-placed labels instead of
    silently dropping them. Returns the list of occupied label boxes so the
    hamlet/landmark labels can avoid them too."""
    placed = []
    labeled = 0
    for d in sorted(isles, key=lambda d: -d["area"]):
        if d["n"] < MIN_LABEL_PTS:
            continue
        rp = d["geom"].representative_point()
        big = d["area"] > 9000
        fs = float(np.clip(3.0 + d["area"] ** 0.5 * 0.085, 4.6, 15.0))
        txt = " ".join(d["name"].upper()) if big else d["name"]
        # width from the STRING ACTUALLY DRAWN (spaced caps are far wider);
        # bold head face also runs wider per glyph than the italic label face.
        char_w = 0.52 if big else 0.34
        hw, hh = len(txt) * fs * char_w + 14, fs * 0.95 + 6
        # try the representative point first, then sweep outward on rings whose
        # radius grows in absolute map units (not the label's own size) so a
        # small label can clear a much larger neighbour like "HAM".
        spot = None
        cands = [(0.0, 0.0)]
        for rad in (14, 26, 40, 58, 80, 108):
            for k in range(12):
                a = math.pi / 2 + k * math.pi / 6
                cands.append((rad * math.cos(a), rad * 1.05 * math.sin(a)))
        for dx, dy in cands:
            x, y = rp.x + dx, rp.y + dy
            if not _overlaps(x, y, hw, hh, placed):
                spot = (x, y)
                break
        if spot is None:
            if not big:
                continue                 # small label can't fit → leave unnamed
            spot = (rp.x, rp.y)          # keep the big landmass labels regardless
        x, y = spot
        placed.append((x, y, hw, hh))
        t = ax.text(x, y, txt, ha="center", va="center", zorder=20,
                    fontproperties=F_HEAD if big else F_LABEL, fontsize=fs,
                    color="#3F2E16" if big else SEPIA)
        t.set_path_effects([pe.withStroke(linewidth=2.2, foreground=PAPER, alpha=0.85)])
        labeled += 1
    print(f"  labelled {labeled} isles")
    return placed


def add_hamlets(ax, allx, ally, allnm, placed):
    HAMLETS = {"Gator Hole": ("gator", "alligator"), "Frog Cove": ("frog",),
               "Escargot Point": ("escargot", "snail"), "Oxtail Bay": ("oxtail",)}
    fs = 4.6
    for label, keys in HAMLETS.items():
        spots = [(x, y) for x, y, nm in zip(allx, ally, allnm)
                 if any(k in nm.lower() for k in keys)]
        if len(spots) < 3:
            continue
        cx, cy = np.mean(spots, axis=0)
        ax.plot(cx, cy, marker=(8, 2, 0), ms=4, color=SEPIA, zorder=21)
        hw, hh = len(label) * fs * 0.32 + 4, fs * 0.95 + 3
        # candidate label anchors around the marker; centre of the text box is
        # offset from the anchor by ±hw depending on alignment
        cands = [(7, 0, "left"), (-7, 0, "right"), (7, -11, "left"),
                 (-7, -11, "right"), (7, 11, "left"), (-7, 11, "right"),
                 (0, -13, "center"), (0, 13, "center")]
        ax_pt, ha = (cx + 7, cy), "left"
        for dx, dy, align in cands:
            bx = cx + dx + (hw if align == "left" else -hw if align == "right" else 0)
            by = cy + dy
            if not _overlaps(bx, by, hw, hh, placed):
                ax_pt, ha = (cx + dx, cy + dy), align
                placed.append((bx, by, hw, hh))
                break
        ht = ax.text(ax_pt[0], ax_pt[1], label, ha=ha, va="center", zorder=21,
                     fontproperties=F_LABEL, fontsize=fs, color=SEPIA)
        ht.set_path_effects([pe.withStroke(linewidth=1.6, foreground=PAPER, alpha=0.9)])


def main():
    rng = np.random.default_rng(SEED)
    print("Loading manifold …")
    reg, nx, ny = load_regions()
    sup = merge_regions(reg)

    # build island records
    isles = []
    names_by_isle = {}
    for cid, v in sup.items():
        if len(v) < MIN_ISLAND_PTS:
            continue
        coords = np.array([(x, y) for x, y, _, _ in v])
        geom = coastline(coords)
        if geom is None or geom.is_empty:
            continue
        geom = shp_scale(geom, ISLAND_SCALE, ISLAND_SCALE, origin="centroid")
        names = [nm for _, _, nm, _ in v]
        counts = np.array([c for _, _, _, c in v])
        names_by_isle[cid] = names
        isles.append(dict(cid=cid, n=len(v), geom=geom, area=geom.area,
                          pop=float(np.log10(counts).mean()), coords=coords))
    ranked = ranked_tokens(names_by_isle)
    for d in isles:
        d["tokens"] = ranked[d["cid"]]
    assign_names(isles)
    print(f"  drawing {len(isles)} isles")

    # popularity elevation field (log-count-weighted density)
    wx, wy, ww = [], [], []
    for v in sup.values():
        for x, y, _, c in v:
            wx.append(x); wy.append(y); ww.append(math.log10(c))
    wx, wy, ww = np.array(wx), np.array(wy), np.array(ww)
    ix = np.clip((wx / 1000 * GRID).astype(int), 0, GRID - 1)
    iy = np.clip((wy / 1000 * GRID).astype(int), 0, GRID - 1)
    popw = np.zeros((GRID, GRID))
    np.add.at(popw, (iy, ix), ww)
    elev = ndimage.gaussian_filter(popw, SIGMA_POP)
    cc = (np.arange(GRID) + 0.5) / GRID * 1000.0
    Xc, Yc = np.meshgrid(cc, cc)

    # ── figure ──
    fig = plt.figure(figsize=(7, 7.6), dpi=600)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-40, 1040); ax.set_ylim(1090, -90); ax.axis("off")
    ax.imshow(parchment((900, 900), rng), extent=(-40, 1040, 1090, -90),
              zorder=0, interpolation="bilinear", aspect="auto")
    for g in range(0, 1001, 100):
        ax.plot([g, g], [-90, 1090], color=SEPIA_LT, lw=0.3, alpha=0.16, zorder=1)
        ax.plot([-40, 1040], [g, g], color=SEPIA_LT, lw=0.3, alpha=0.16, zorder=1)
    if len(nx):
        ax.scatter(nx, ny, s=0.7, c=SEA_DEEP, alpha=0.28, linewidths=0, zorder=2)

    # land fill
    for d in isles:
        for pat in geom_to_patches(d["geom"], facecolor=LAND, edgecolor="none",
                                   alpha=0.97, zorder=3):
            ax.add_patch(pat)

    # popularity topography, clipped to land
    clip = PathPatch(compound_path([d["geom"] for d in isles]),
                     transform=ax.transData, fc="none", ec="none", zorder=3)
    ax.add_patch(clip)
    land_vals = elev[elev > elev.max() * 0.02]
    levels = np.linspace(np.percentile(land_vals, 40), elev.max(), TOPO_LEVELS)
    cf = ax.contourf(Xc, Yc, elev, levels=levels, cmap=HYPSO, alpha=0.5,
                     extend="both", zorder=4)
    cf.set_clip_path(clip)
    cl = ax.contour(Xc, Yc, elev, levels=levels, colors=SEPIA,
                    linewidths=0.4, alpha=0.55, zorder=5)
    cl.set_clip_path(clip)

    # coastlines (hand-drawn wobble)
    for d in isles:
        for poly in polys_of(d["geom"]):
            xy = np.asarray(poly.exterior.coords)
            wob = jitter_ring(xy, amp=min(1.6, d["area"] ** 0.5 * 0.02), rng=rng)
            ax.plot(wob[:, 0], wob[:, 1], color=SEPIA, lw=0.8, alpha=0.88,
                    zorder=6, solid_capstyle="round")

    placed = place_labels(ax, isles)
    sx_all = [x for v in sup.values() for (x, _, _, _) in v]
    sy_all = [y for v in sup.values() for (_, y, _, _) in v]
    nm_all = [nm for v in sup.values() for (_, _, nm, _) in v]
    add_hamlets(ax, sx_all + list(nx), sy_all + list(ny),
                nm_all + [""] * len(nx), placed)

    add_chrome(ax, rng,
               "charted from the 195k menu-item manifold",
               "rare", "popular", "DISH  POPULARITY")

    fig.savefig(OUT_PNG, dpi=600)
    fig.savefig(OUT_PDF)
    print(f"  wrote {OUT_PNG}\n  wrote {OUT_PDF}")

    with open(OUT_GAZ, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["isle", "n_dishes", "mean_log10_menu_count", "centroid_x", "centroid_y"])
        for d in sorted(isles, key=lambda d: -d["n"]):
            c = d["geom"].representative_point()
            w.writerow([d["name"], d["n"], round(d["pop"], 3), round(c.x, 1), round(c.y, 1)])
    print(f"  wrote {OUT_GAZ}")


if __name__ == "__main__":
    main()
