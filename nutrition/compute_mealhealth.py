"""compute_mealhealth.py — Per-dish health-impact (ΔYLL) for every
canonical dish, via Koen van Greevenbroek's `mealhealth` package. The
mealhealth analogue of `compute_nutriscore.py`.

What it computes
----------------
For each dish in `nutrition/dish_macros.jsonl` (one row per cluster_id,
with a per-ingredient breakdown carrying fdc_id + grams + scaled kcal), we:

  1. Classify every ingredient into one of the seven GBD risk-factor food
     groups (or "other") via `gbd_classify` (fdc_id -> group, with a
     string fallback for unmatched ingredients).
  2. Sum each group's grams over the recipe and divide by ``n_servings``
     so the unit is **one served dish = one meal**.
  3. Apply the mass-basis conversions mealhealth's curves require
     (see docs/food_groups.md): whole_grains & legumes -> dry/uncooked
     weight, red & processed meat -> raw retail weight. Conversions are
     applied per-ingredient and ONLY when the matched FDC description
     indicates a cooked/hydrated state, since some ingredients are already
     supplied dry (flour) or raw. Fruits/vegetables/nuts are fresh
     as-eaten and need no conversion. (Logged in FILTERING_LOG.md.)
  4. Take the meal's total energy as ``energy_kcal_per_serving`` (already
     summed over matched ingredients in dish_macros).
  5. Call ``mealhealth.assess_meal(meal, meal_kcal, "USA", mode="median")``
     — the individual-lifetime ΔYLL for the median US adult who eats this
     dish every day for the rest of their life, substituted into the US
     baseline diet at constant calories.

Sign convention: delta_yll_total > 0 ⇒ years GAINED, < 0 ⇒ years LOST.

Basis note: per-serving grams use matched ingredients only; unmatched
ingredients (~1–2 % of mass) contribute neither group mass nor kcal. We
record ``match_rate`` per dish so low-coverage dishes can be filtered.

Outputs
-------
  nutrition/dish_mealhealth.jsonl          every dish (full detail)
  nutrition/dish_mealhealth_manifold.csv   the 39,166-dish phylogeny
                                           manifold (joined to dish_meta,
                                           idx-aligned to umap.json).

Usage:
  python3 nutrition/compute_mealhealth.py
  python3 nutrition/compute_mealhealth.py --no-manifold --workers 4
"""
import argparse
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gbd_classify as gc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"

DEFAULT_MACROS = HERE / "dish_macros.jsonl"
GBD_TABLE = DATA / "ingredient_gbd.csv"
DISH_META = ROOT / "phylogeny" / "data" / "dish_meta.csv"

OUT_JSONL = HERE / "dish_mealhealth.jsonl"
OUT_MANIFOLD = HERE / "dish_mealhealth_manifold.csv"

COUNTRY = "USA"
MODE = "median"  # individual-lifetime ΔYLL for the median adult
CAUSES = ("CHD", "Stroke", "T2DM", "CRC")

# --- mass-basis conversion (docs/food_groups.md) ------------------------
# Applied only to ingredients whose matched FDC description shows a
# cooked/hydrated state; foods supplied dry (flour) or raw are left as-is.
COOKED_MARKERS = ("cook", "boil", "roast", "braise", "grill", "broil",
                  "fried", "baked", "bake,", "steam", "stew", "canned",
                  "simmer", "prepared", "drained", "moist heat", "dry heat")
GRAIN_DRY_FACTOR = 0.45    # cooked grains ≈ 0.45 × dry
LEGUME_DRY_FACTOR = 0.40   # cooked legumes ≈ 0.40 × dry
MEAT_RAW_FACTOR = 1.0 / 0.7  # cooked meat ≈ 0.7 × raw  →  raw = cooked / 0.7

# worker-global, populated by _init
_GBD: dict[str, str] = {}


def load_gbd(path: Path) -> dict[str, str]:
    with open(path) as f:
        return {r["fdc_id"]: r["gbd_group"] for r in csv.DictReader(f)}


def _basis_convert(group: str, grams: float, desc: str) -> float:
    """Convert as-used grams to the GBD input basis for `group`."""
    cooked = any(m in desc for m in COOKED_MARKERS)
    if group == "whole_grains" and cooked:
        return grams * GRAIN_DRY_FACTOR
    if group == "legumes" and cooked:
        return grams * LEGUME_DRY_FACTOR
    if group in ("red_meat", "processed_meat") and cooked:
        return grams * MEAT_RAW_FACTOR
    return grams


def build_meal(d: dict, gbd: dict) -> tuple[dict, float, float, float] | None:
    """Return (meal_grams_per_serving, meal_kcal, matched_mass, total_mass)
    for one dish, or None if it has no usable mass."""
    mass = float(d.get("recipe_mass_g") or 0.0)
    if mass <= 0:
        return None
    n_serv = float(d.get("n_servings") or 1) or 1.0

    groups: dict[str, float] = {}
    matched_mass = 0.0
    for ing in d.get("ingredients", []):
        grams = float(ing.get("grams") or 0.0)
        if grams <= 0:
            continue
        fid = ing.get("fdc_id")
        desc = (ing.get("matched_fdc") or "").lower()
        if fid and fid in gbd:
            matched_mass += grams
            g = gbd[fid]
        else:
            g = gc.classify_name(ing.get("ingredient", ""))
        if g == "other":
            continue
        groups[g] = groups.get(g, 0.0) + _basis_convert(g, grams, desc)

    # per-serving, drop zero/near-zero groups
    meal = {k: round(v / n_serv, 3) for k, v in groups.items()
            if v / n_serv >= 0.05}
    meal_kcal = float(d.get("energy_kcal_per_serving") or 0.0)
    return meal, meal_kcal, matched_mass, mass


def _init(gbd_path: str) -> None:
    global _GBD
    _GBD = load_gbd(Path(gbd_path))


def assess_one(d: dict) -> dict | None:
    """Worker: classify + assess a single dish. Returns the output record."""
    import mealhealth as mh
    built = build_meal(d, _GBD)
    if built is None:
        return None
    meal, meal_kcal, matched_mass, mass = built
    n_serv = float(d.get("n_servings") or 1) or 1.0

    rec = {
        "cluster_id": d.get("cluster_id"),
        "canonical_name": d.get("canonical_name"),
        "cuisine_bucket": d.get("cuisine_bucket"),
        "n_servings": d.get("n_servings"),
        "meal_kcal": round(meal_kcal, 1),
        "match_rate": round(matched_mass / mass, 4),
        "group_grams": meal,
    }

    if meal_kcal <= 0:
        rec["mealhealth"] = None
        rec["error"] = "no_kcal"
        return rec
    try:
        r = mh.assess_meal(meal, meal_kcal, COUNTRY, mode=MODE,
                           include_processed_meat=True)
        rec["mealhealth"] = {
            "mode": MODE,
            "delta_yll_lifetime": round(r.delta_yll_total, 6),
            "per_meal_marginal_yll": mh.per_meal_marginal(r),
            "paf": {c: round(r.delta_paf_total.get(c, 0.0), 5) for c in CAUSES},
            "f": round(r.f, 4),
            "warnings": list(getattr(r, "warnings", []) or []),
        }
    except Exception as e:  # keep the dish, record the failure
        rec["mealhealth"] = None
        rec["error"] = f"{type(e).__name__}: {e}"
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--macros", default=str(DEFAULT_MACROS))
    ap.add_argument("--out", default=str(OUT_JSONL))
    ap.add_argument("--workers", type=int, default=0,
                    help="process pool size (0 = os.cpu_count()-1)")
    ap.add_argument("--no-manifold", action="store_true")
    args = ap.parse_args()

    if not GBD_TABLE.exists():
        sys.exit(f"ERROR: {GBD_TABLE} missing — run gbd_classify.py first")

    import os
    workers = args.workers or max(1, (os.cpu_count() or 2) - 1)

    dishes = []
    with open(args.macros) as f:
        for line in f:
            line = line.strip()
            if line:
                dishes.append(json.loads(line))
    print(f"loaded {len(dishes):,} dishes; assessing with {workers} workers "
          f"({COUNTRY}, mode={MODE}) …")

    results: dict[int, dict] = {}
    n = n_skip = n_err = 0
    yll_sum = 0.0
    with open(args.out, "w") as fout, \
            ProcessPoolExecutor(max_workers=workers, initializer=_init,
                                initargs=(str(GBD_TABLE),)) as ex:
        for out in ex.map(assess_one, dishes, chunksize=200):
            if out is None:
                n_skip += 1
                continue
            fout.write(json.dumps(out) + "\n")
            results[out["cluster_id"]] = out
            n += 1
            if out.get("mealhealth"):
                yll_sum += out["mealhealth"]["delta_yll_lifetime"]
            else:
                n_err += 1
    print(f"wrote {args.out}  ({n:,} dishes; {n_skip} skipped no-mass; "
          f"{n_err} without an assessment)")
    assessed = n - n_err
    if assessed:
        print(f"  mean ΔYLL (lifetime, median adult): {yll_sum/assessed:+.4f} yr "
              f"(>0 gained, <0 lost), over {assessed:,} assessed dishes")

    if args.no_manifold:
        return
    if not DISH_META.exists():
        print(f"  WARN: {DISH_META} not found — skipping manifold CSV")
        return

    with open(DISH_META) as f:
        meta_rows = list(csv.DictReader(f))
    cols = ["idx", "cluster_id", "canonical_name", "cuisine_bucket",
            "n_servings", "meal_kcal",
            "g_fruits", "g_vegetables", "g_whole_grains", "g_legumes",
            "g_nuts_seeds", "g_red_meat", "g_processed_meat",
            "delta_yll_lifetime", "per_meal_marginal_yll",
            "paf_CHD", "paf_Stroke", "paf_T2DM", "paf_CRC", "match_rate"]
    g_order = ["fruits", "vegetables", "whole_grains", "legumes",
               "nuts_seeds", "red_meat", "processed_meat"]
    n_join = n_miss = 0
    with open(OUT_MANIFOLD, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in meta_rows:
            cid = int(r["cluster_id"])
            o = results.get(cid)
            if o is None:
                n_miss += 1
                continue
            mh_ = o.get("mealhealth") or {}
            gg = o.get("group_grams", {})
            paf = mh_.get("paf", {}) if mh_ else {}
            w.writerow([
                r["idx"], cid, o["canonical_name"], o["cuisine_bucket"],
                o.get("n_servings"), o.get("meal_kcal"),
                *[gg.get(g, 0) for g in g_order],
                mh_.get("delta_yll_lifetime", "") if mh_ else "",
                mh_.get("per_meal_marginal_yll", "") if mh_ else "",
                *[paf.get(c, "") for c in CAUSES],
                o.get("match_rate"),
            ])
            n_join += 1
    print(f"wrote {OUT_MANIFOLD}  ({n_join:,} manifold dishes; "
          f"{n_miss} in dish_meta without an assessment)")


if __name__ == "__main__":
    main()
