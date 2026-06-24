"""Unified per-dish data table for the figure series.

Joins every per-dish metric onto the 39,166-dish manifold order (the row
order of phylogeny/data/dish_vectors.npy, via dish_meta.csv `idx`), so any
figure can pull a single tidy DataFrame and, when needed, line it up with the
manifold vectors by `idx`.

Sources (all keyed on cluster_id):
  phylogeny/data/dish_meta.csv            idx, cluster_id, names, total_count
  phylogeny/data/dish_classes.csv         cuisine, protein_type, carb_type (15 cuisines)
  lca/dish_lca.jsonl                      ghg/water/land per-kg, quality grade
  nutrition/dish_nutriscore_manifold.csv  nutriscore_0to100, grade
  nutrition/dish_mealhealth_manifold.csv  delta_yll_lifetime
  menu_dishes.sqlite                      price_usd (mean per canonical dish)

Metric orientation matters and is declared once in METRICS:
  better="lower"  -> GHG, water, land, NutriScore (lower 0-100 = healthier)
  better="higher" -> delta_yll (years gained > 0 is good)
"""
from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "phylogeny", "data", "dish_meta.csv")
VECTORS = os.path.join(ROOT, "phylogeny", "data", "dish_vectors.npy")
CLASSES = os.path.join(ROOT, "phylogeny", "data", "dish_classes.csv")
LCA = os.path.join(ROOT, "lca", "dish_lca.jsonl")
NUTRISCORE = os.path.join(ROOT, "nutrition", "dish_nutriscore_manifold.csv")
MEALHEALTH = os.path.join(ROOT, "nutrition", "dish_mealhealth_manifold.csv")
MACROS = os.path.join(ROOT, "nutrition", "dish_macros.jsonl")
MENUDB = os.path.join(ROOT, "menu_dishes.sqlite")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_dish_table.parquet")

# Central metric registry — label, unit, column, orientation, palette color, group.
# Colors come only from the RdYlBu ramp (no greens / new hues).
METRICS = {
    "ghg":        dict(col="ghg",        label="GHG emissions",   unit="kg CO₂e / kg",
                       better="lower", color="#D73027", group="impact", log=True),
    "water":      dict(col="water",      label="Freshwater use",  unit="m³ / kg",
                       better="lower", color="#4575B4", group="impact", log=True),
    "land":       dict(col="land",       label="Land use",        unit="Pt / kg",
                       better="lower", color="#F46D43", group="impact", log=True),
    "nutriscore": dict(col="nutriscore", label="Nutri-Score",     unit="0–100, lower = healthier",
                       better="lower", color="#A50026", group="health", log=False),
    "yll":        dict(col="yll",        label=r"Health ($\Delta$YLL)", unit="lifetime years gained / meal",
                       better="higher", color="#313695", group="health", log=False),
}
IMPACT_METRICS = [k for k, v in METRICS.items() if v["group"] == "impact"]
HEALTH_METRICS = [k for k, v in METRICS.items() if v["group"] == "health"]

# Cuisines worth showing (drop tiny / non-cuisine buckets to taste at plot time)
CUISINE_ORDER = ["American", "Mexican", "Italian", "Japanese", "Chinese", "Indian",
                 "Asian", "Mediterranean", "Latin American", "Thai", "Vietnamese",
                 "Korean", "European", "African", "Other"]


def _read_jsonl_map(path: str, fields: dict[str, str]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            cid = d.get("cluster_id")
            if cid is None:
                continue
            out[int(cid)] = {dst: d.get(src) for dst, src in fields.items()}
    return out


def _mean_price() -> dict[str, float]:
    """Mean menu price_usd per canonical_dish name."""
    con = sqlite3.connect(MENUDB)
    acc: dict[str, list] = defaultdict(list)
    for name, p in con.execute(
        "select canonical_dish, price_usd from menu_dishes "
        "where price_usd is not null and price_usd > 0"
    ):
        acc[name].append(p)
    con.close()
    # robust central tendency: median resists $0.01 / catering-platter outliers
    return {k: float(np.median(v)) for k, v in acc.items()}


def build(rebuild: bool = False) -> pd.DataFrame:
    """Assemble (and cache) the per-dish table, row-aligned to dish_meta/idx."""
    if os.path.exists(CACHE) and not rebuild:
        return pd.read_parquet(CACHE)

    meta = pd.read_csv(META)  # idx, cluster_id, canonical_name, top_raw_name, cuisine_bucket, total_count, n_ingredients
    classes = pd.read_csv(CLASSES).set_index("cluster_id")  # cuisine, protein_type, carb_type

    lca = _read_jsonl_map(LCA, {
        "ghg": "ghg_kgco2e_per_kg", "water": "water_m3_per_kg", "land": "land_pt_per_kg",
        "ghg_per_recipe": "ghg_kgco2e_per_recipe", "recipe_mass_g": "recipe_mass_g",
        "quality_grade": "data_quality_grade",
    })
    nutri = {}
    ns = pd.read_csv(NUTRISCORE)
    for _, r in ns.iterrows():
        nutri[int(r["cluster_id"])] = {
            "nutriscore": r.get("nutriscore_0to100"), "nutriscore_grade": r.get("grade")}
    mh = {}
    mhd = pd.read_csv(MEALHEALTH)
    for _, r in mhd.iterrows():
        mh[int(r["cluster_id"])] = {"yll": r.get("delta_yll_lifetime"),
                                    "meal_kcal": r.get("meal_kcal")}
    macros = _read_jsonl_map(MACROS, {
        "kcal_serving": "energy_kcal_per_serving",
        "protein_serving": "protein_g_per_serving",
        "fat_serving": "fat_g_per_serving",
        "carb_serving": "carb_g_per_serving",
        "n_servings": "n_servings"})
    price = _mean_price()

    rows = []
    for _, m in meta.iterrows():
        cid = int(m["cluster_id"])
        cls = classes.loc[cid] if cid in classes.index else None
        rec = dict(
            idx=int(m["idx"]), cluster_id=cid,
            canonical_name=m["canonical_name"], top_raw_name=m["top_raw_name"],
            total_count=int(m["total_count"]),
            cuisine=(cls["cuisine"] if cls is not None else None),
            protein_type=(cls["protein_type"] if cls is not None else None),
            carb_type=(cls["carb_type"] if cls is not None else None),
            price=price.get(m["canonical_name"]),
        )
        rec.update(lca.get(cid, {}))
        rec.update(nutri.get(cid, {}))
        rec.update(mh.get(cid, {}))
        rec.update(macros.get(cid, {}))
        rows.append(rec)

    df = pd.DataFrame(rows).set_index("idx").sort_index()
    for c in ["ghg", "water", "land", "nutriscore", "yll", "price",
              "ghg_per_recipe", "recipe_mass_g", "kcal_serving",
              "protein_serving", "fat_serving", "carb_serving", "meal_kcal"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df.to_parquet(CACHE)
    return df


def wquantile(v: np.ndarray, w: np.ndarray, q) -> float | np.ndarray:
    """Weighted quantile(s) via the cumulative-weight CDF. q may be scalar/array."""
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return np.interp(q, cw, v)


def vectors() -> np.ndarray:
    """The 39,166 x 384 L2-normalised manifold vectors (row idx-aligned to build())."""
    return np.load(VECTORS).astype(np.float32)


def metric_series(df: pd.DataFrame, key: str) -> pd.Series:
    """Clean numeric series for a metric (drops non-finite; for log metrics drops <=0)."""
    m = METRICS[key]
    s = df[m["col"]]
    s = s[np.isfinite(s)]
    if m["log"]:
        s = s[s > 0]
    return s


if __name__ == "__main__":
    df = build(rebuild=True)
    print("rows:", len(df))
    print("columns:", list(df.columns))
    for k, m in METRICS.items():
        s = metric_series(df, k)
        print(f"  {k:11s} n={len(s):6d}  "
              f"min={s.min():.4g} med={s.median():.4g} max={s.max():.4g}")
    print("price coverage:", int(df['price'].notna().sum()), "/", len(df))
    print("cuisines:", df['cuisine'].value_counts().to_dict())
