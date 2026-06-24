"""Flexibility-sphere computations on the dish manifold (shared by Fig 3 & 4).

Flexibility = a cosine radius r around a dish in the 384-D manifold. A diner
"willing to substitute within r" can pick any dish j with cosine distance
d(i,j) = 1 - <v_i, v_j> <= r (vectors are L2-normalised). We measure the
BEST-CASE improvement reachable inside that sphere, per metric.

Improvement orientation (from figdata.METRICS):
  better="lower"  -> improvement = (center - min_in_sphere) / center   (fraction, 0..1)
  better="higher" -> improvement =  max_in_sphere - center             (absolute units)

Honest regime: cosine distances compress, so beyond r~0.3 the sphere is a
large share of ALL dishes and "best in sphere" degenerates into "globally
best dish". Keep r small (default grid tops out at 0.30).

NaN-safe: dishes missing a metric never win a min/max; centers missing a
metric yield NaN improvement (dropped at aggregation).
"""
from __future__ import annotations

import numpy as np

BLOCK = 2000
DEFAULT_RADII = np.round(np.linspace(0.0, 0.30, 16), 3)  # step 0.02


def _dist_block(V, s, e):
    D = 1.0 - (V[s:e] @ V.T)
    np.clip(D, 0.0, None, out=D)
    rows = np.arange(e - s)
    D[rows, s + rows] = 0.0          # pin self-distance to exactly 0
    return D


def _macro_tv_block(M, s, e):
    """Total-variation macro distance (B x N), 0.5*sum|Δshare|, NaN-aware.
    NaN where either dish lacks a macro profile (so it fails any tolerance)."""
    tv = np.zeros((e - s, M.shape[0]), np.float64)
    for k in range(M.shape[1]):
        tv += np.abs(M[s:e, k][:, None] - M[None, :, k])
    return 0.5 * tv


def best_improvement(V, metrics: dict[str, np.ndarray], better: dict[str, str],
                     radii=DEFAULT_RADII, macro=None, macro_tol=None, block=BLOCK):
    """Per-center, per-radius best-case improvement for each metric.

    If `macro` (n,3 macro-share array) and `macro_tol` are given, candidates
    must also satisfy total-variation macro distance <= macro_tol.

    Returns dict with 'radii', 'neigh' (n,nr), and per metric an (n,nr) array
    of improvement (fraction for lower-better, absolute for higher-better).
    Centers with no qualifying neighbour (e.g. missing macro profile) -> NaN.
    """
    n, nr = V.shape[0], len(radii)
    imp = {k: np.full((n, nr), np.nan, np.float32) for k in metrics}
    neigh = np.zeros((n, nr), np.float32)
    cand = {}
    for k, arr in metrics.items():
        a = arr.astype(np.float64).copy()
        a[~np.isfinite(a)] = np.inf if better[k] == "lower" else -np.inf
        cand[k] = a[None, :]

    for s in range(0, n, block):
        e = min(s + block, n)
        D = _dist_block(V, s, e)
        macro_ok = None
        if macro is not None:
            tv = _macro_tv_block(macro, s, e)
            macro_ok = tv <= macro_tol     # NaN comparisons -> False
        centers = {k: metrics[k][s:e].astype(np.float64) for k in metrics}
        for ri, r in enumerate(radii):
            mask = D <= r
            if macro_ok is not None:
                mask = mask & macro_ok
            nb = mask.sum(1)
            neigh[s:e, ri] = nb
            empty = nb == 0
            for k in metrics:
                if better[k] == "lower":
                    best = np.where(mask, cand[k], np.inf).min(1)
                    c = centers[k]
                    with np.errstate(invalid="ignore", divide="ignore"):
                        v = (c - best) / c
                    v[~np.isfinite(centers[k]) | (c <= 0)] = np.nan
                else:
                    best = np.where(mask, cand[k], -np.inf).max(1)
                    c = centers[k]
                    v = best - c
                    v[~np.isfinite(c)] = np.nan
                v[empty] = np.nan          # no qualifying neighbour (e.g. no macro)
                imp[k][s:e, ri] = v
        print(f"[flex] centers {e}/{n}")
    return {"radii": np.asarray(radii), "neigh": neigh, **imp}


def best_pick_index(V, metric: np.ndarray, better: str, radius: float):
    """For each center, index of the best-in-sphere dish at a single radius.

    Used for alignment (Fig 4): pick the climate-optimal neighbour, then read
    its health metrics. Returns int array (n,), self if nothing better.
    """
    n = V.shape[0]
    pick = np.arange(n)
    a = metric.astype(np.float64).copy()
    a[~np.isfinite(a)] = np.inf if better == "lower" else -np.inf
    arow = a[None, :]
    for s in range(0, n, BLOCK):
        e = min(s + BLOCK, n)
        D = _dist_block(V, s, e)
        mask = D <= radius
        masked = np.where(mask, arow, np.inf if better == "lower" else -np.inf)
        pick[s:e] = masked.argmin(1) if better == "lower" else masked.argmax(1)
        print(f"[pick] centers {e}/{n}")
    return pick


def improvement_vs_tol(V, metric, better, radius, tols, macro, block=BLOCK):
    """At a fixed flexibility radius, per-center best-case improvement for each
    macro tolerance in `tols` (one block pass). Returns (n, len(tols)) array;
    fraction for lower-better, absolute for higher-better. NaN where no option."""
    n = V.shape[0]
    out = np.full((n, len(tols)), np.nan, np.float32)
    a = metric.astype(np.float64).copy()
    a[~np.isfinite(a)] = np.inf if better == "lower" else -np.inf
    arow = a[None, :]
    for s in range(0, n, block):
        e = min(s + block, n)
        D = _dist_block(V, s, e)
        tv = _macro_tv_block(macro, s, e)
        near = D <= radius
        c = metric[s:e].astype(np.float64)
        for ti, tol in enumerate(tols):
            mask = near & (tv <= tol)
            nb = mask.sum(1)
            if better == "lower":
                best = np.where(mask, arow, np.inf).min(1)
                with np.errstate(invalid="ignore", divide="ignore"):
                    v = (c - best) / c
                v[~np.isfinite(c) | (c <= 0)] = np.nan
            else:
                best = np.where(mask, arow, -np.inf).max(1)
                v = best - c
                v[~np.isfinite(c)] = np.nan
            v[nb == 0] = np.nan
            out[s:e, ti] = v
        print(f"[tol] centers {e}/{n}")
    return out


def best_picks(V, specs: dict[str, tuple], radius: float):
    """One block pass: for each center, the index of its best-in-sphere dish
    under each named criterion. specs = {name: (metric_array, better)}.
    Returns {name: int array (n,)}.
    """
    n = V.shape[0]
    rows_arr = {name: np.arange(n) for name in specs}
    prep = {}
    for name, (arr, better) in specs.items():
        a = arr.astype(np.float64).copy()
        a[~np.isfinite(a)] = np.inf if better == "lower" else -np.inf
        prep[name] = (a[None, :], better)
    for s in range(0, n, BLOCK):
        e = min(s + BLOCK, n)
        D = _dist_block(V, s, e)
        mask = D <= radius
        for name, (arow, better) in prep.items():
            fill = np.inf if better == "lower" else -np.inf
            masked = np.where(mask, arow, fill)
            rows_arr[name][s:e] = (masked.argmin(1) if better == "lower"
                                   else masked.argmax(1))
        print(f"[picks] centers {e}/{n}")
    return rows_arr


def aggregate(imp_nr: np.ndarray, weights: np.ndarray | None = None):
    """Column-wise mean + P25/P50/P75 across centers (NaN-dropped per radius)."""
    import figdata as fd
    nr = imp_nr.shape[1]
    mean = np.full(nr, np.nan)
    p = {q: np.full(nr, np.nan) for q in (25, 50, 75)}
    for ri in range(nr):
        col = imp_nr[:, ri]
        good = np.isfinite(col)
        if not good.any():
            continue
        v = col[good]
        w = (weights[good] if weights is not None else np.ones(good.sum()))
        mean[ri] = np.average(v, weights=w)
        for q in (25, 50, 75):
            p[q][ri] = fd.wquantile(v, w, q / 100.0)
    return mean, p[25], p[50], p[75]
