"""Stage 5.5 — assemble the static frontend data bundle.

Merges the upstream artifacts into exactly what phylogeny/site/ loads:

  site/data/tree.json     dendrogram with LLM clade labels merged onto
                          internal nodes; leaves enriched with the light
                          LCA fields the colour overlays need
  site/data/umap.json     2D manifold layout, points enriched the same way
  site/data/dishes/shard_<k>.json
                          per-dish recipe + full LCA detail, sharded by
                          cluster_id % N_SHARDS and lazy-loaded on click
  site/data/manifest.json build metadata (counts, timestamp, umap method)

Light overlay fields (ghg/water/land per kg, data-quality grade) are
copied onto every leaf and map point so the tool can recolour the whole
view without fetching any detail shard. Full detail is only fetched when
a dish is clicked.

Nothing here calls an API or a model — pure assembly, fast, re-runnable.

Usage:
  python3 export_site_data.py
"""
import csv
import json
import sys
import time
from pathlib import Path

sys.setrecursionlimit(1_000_000)

SCRIPT_DIR = Path(__file__).resolve().parent
PHYLO_DIR = SCRIPT_DIR.parent
REPO = PHYLO_DIR.parent
DATA_DIR = PHYLO_DIR / "data"
SITE_DATA = PHYLO_DIR / "site" / "data"

TREE_IN = DATA_DIR / "tree.json"
UMAP_IN = DATA_DIR / "umap.json"
CLADE_LABELS = PHYLO_DIR / "frozen" / "clade_labels.csv"
DISH_META = DATA_DIR / "dish_meta.csv"
RECIPES = REPO / "recipes" / "recipes.jsonl"
DISH_LCA = REPO / "lca" / "dish_lca.jsonl"
DISH_MACROS = REPO / "nutrition" / "dish_macros.jsonl"
DISH_NUTRISCORE = REPO / "nutrition" / "dish_nutriscore.jsonl"  # NUT-4
DISH_MEALHEALTH = REPO / "nutrition" / "dish_mealhealth.jsonl"  # MH-1
DISH_CLASSES = DATA_DIR / "dish_classes.csv"   # classify_dishes.py output

N_SHARDS = 256


def load_labels() -> dict[str, str]:
    if not CLADE_LABELS.exists():
        print("  WARN: no clade_labels.csv — tree exports unlabelled")
        return {}
    with open(CLADE_LABELS) as f:
        return {r["node_id"]: r["label"]
                for r in csv.DictReader(f) if r["label"]}


def walk(node, leaf_fn, internal_fn=None):
    """Depth-first visit; leaf_fn(node) on leaves, internal_fn(node) on the
    rest."""
    if node.get("leaf"):
        leaf_fn(node)
    else:
        if internal_fn:
            internal_fn(node)
        for ch in node.get("children", []):
            walk(ch, leaf_fn, internal_fn)


def main():
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "dishes").mkdir(exist_ok=True)

    # --- v1 dish set + idx→cluster_id map ---------------------------
    with open(DISH_META) as f:
        meta_rows = list(csv.DictReader(f))
    idx_to_cid = {int(r["idx"]): int(r["cluster_id"]) for r in meta_rows}
    v1_ids = set(idx_to_cid.values())
    print(f"{len(v1_ids):,} dishes in the v1 set")

    # --- recipe detail ----------------------------------------------
    print("collecting recipe detail ...")
    recipe = {}
    with open(RECIPES) as f:
        for line in f:
            d = json.loads(line)
            cid = d.get("cluster_id")
            if cid in v1_ids and not d.get("error"):
                recipe[cid] = d.get("ingredients", [])

    # --- nutrition detail (Stage 2b: dish_macros.jsonl) -------------
    # dish-level macros only — the per-ingredient nutrition breakdown is
    # left out to keep the shards lean (easy to add back if a per-
    # ingredient calorie view is wanted later)
    NUTRI_KEEP = ("n_servings", "energy_kcal_per_recipe", "protein_g_per_recipe",
                  "fat_g_per_recipe", "carb_g_per_recipe",
                  "energy_kcal_per_serving", "protein_g_per_serving",
                  "fat_g_per_serving", "carb_g_per_serving", "match_rate",
                  "unmatched")
    nutri = {}
    if DISH_MACROS.exists():
        print("collecting nutrition detail ...")
        with open(DISH_MACROS) as f:
            for line in f:
                d = json.loads(line)
                cid = d.get("cluster_id")
                if cid in v1_ids:
                    nutri[cid] = {k: d[k] for k in NUTRI_KEEP if k in d}
        print(f"  {len(nutri):,} dishes with nutrition")
    else:
        print(f"  WARN: {DISH_MACROS} not found — no nutrition in bundle")

    # --- nutrition quality (Stage 2b: dish_nutriscore.jsonl, Layer NUT-4)
    # Clark-et-al-2022 Nutri-Score per dish. We keep the 0-100 scaled score
    # (0 best .. 100 worst) and the A-E grade for the colour overlays, plus
    # a compact profile for the detail panel.
    nscore = {}
    if DISH_NUTRISCORE.exists():
        print("collecting nutri-score detail ...")
        with open(DISH_NUTRISCORE) as f:
            for line in f:
                d = json.loads(line)
                cid = d.get("cluster_id")
                if cid not in v1_ids:
                    continue
                q = d.get("nutriscore", {})
                nscore[cid] = {
                    "score_0to100": q.get("score_0to100"),
                    "score_1to5": q.get("score_1to5"),
                    "points": q.get("score"),
                    "grade": q.get("grade"),
                    "negative_points": q.get("negative_points"),
                    "positive_points": q.get("positive_points"),
                    "food_type": d.get("food_type"),
                    "fvn_pct": d.get("fvn_pct"),
                    "per_100g": d.get("per_100g"),
                }
        print(f"  {len(nscore):,} dishes with nutri-score")
    else:
        print(f"  WARN: {DISH_NUTRISCORE} not found — no nutri-score overlay")

    # --- health impact (Stage 2b: dish_mealhealth.jsonl, Layer MH-1) -
    # Koen's mealhealth ΔYLL per dish: years of life lost/gained if the
    # median US adult ate this dish daily for life, vs the US baseline
    # diet. We keep the signed lifetime ΔYLL + per-cause PAFs + the GBD
    # food-group grams for the detail panel; the overlay colours by years
    # LOST (negated below so red = worse, matching the other overlays).
    mhealth = {}
    if DISH_MEALHEALTH.exists():
        print("collecting mealhealth detail ...")
        with open(DISH_MEALHEALTH) as f:
            for line in f:
                d = json.loads(line)
                cid = d.get("cluster_id")
                if cid not in v1_ids:
                    continue
                mq = d.get("mealhealth")
                if not mq:
                    continue
                mhealth[cid] = {
                    "delta_yll_lifetime": mq.get("delta_yll_lifetime"),
                    "paf": mq.get("paf"),
                    "group_grams": d.get("group_grams"),
                    "meal_kcal": d.get("meal_kcal"),
                    "match_rate": d.get("match_rate"),
                }
        print(f"  {len(mhealth):,} dishes with mealhealth")
    else:
        print(f"  WARN: {DISH_MEALHEALTH} not found — no mealhealth overlay")

    # --- categorical classes (classify_dishes.py) -------------------
    classes = {}
    if DISH_CLASSES.exists():
        with open(DISH_CLASSES) as f:
            for r in csv.DictReader(f):
                classes[int(r["cluster_id"])] = r
        print(f"  {len(classes):,} dishes with cuisine/protein/carb classes")
    else:
        print(f"  WARN: {DISH_CLASSES} not found — run classify_dishes.py")

    # --- LCA detail (full, sharded) + light overlay fields ----------
    print("collecting LCA detail ...")
    KEEP = ("recipe_mass_g", "n_ingredients", "n_matched", "match_rate_count",
            "match_rate_mass", "ghg_kgco2e_per_recipe", "ghg_kgco2e_per_kg",
            "water_m3_per_recipe", "water_m3_per_kg", "land_pt_per_recipe",
            "land_pt_per_kg", "acidification_per_recipe",
            "eutrophication_fw_per_recipe", "ghg_mc", "data_quality_grade",
            "data_quality_score", "data_gaps", "unmatched", "ingredients")
    shards: dict[int, dict] = {}
    lite: dict[int, dict] = {}   # cid -> light overlay fields
    n_lca = 0
    with open(DISH_LCA) as f:
        for line in f:
            d = json.loads(line)
            cid = d.get("cluster_id")
            if cid not in v1_ids:
                continue
            cl = classes.get(cid, {})
            detail = {
                "cluster_id": cid,
                "canonical_name": d.get("canonical_name", ""),
                "top_raw_name": d.get("top_raw_name", ""),
                "cuisine_bucket": d.get("cuisine_bucket", ""),
                "cuisine": cl.get("cuisine", "Other"),
                "protein_type": cl.get("protein_type", "none"),
                "carb_type": cl.get("carb_type", "none"),
                "total_count": d.get("total_count", 0),
                "recipe": recipe.get(cid, []),
                "lca": {k: d[k] for k in KEEP if k in d},
                "nutrition": nutri.get(cid),
                "nutriscore": nscore.get(cid),
                "mealhealth": mhealth.get(cid),
            }
            shards.setdefault(cid % N_SHARDS, {})[str(cid)] = detail
            lite[cid] = {
                "ghg": d.get("ghg_kgco2e_per_kg"),
                "water": d.get("water_m3_per_kg"),
                "land": d.get("land_pt_per_kg"),
                "grade": d.get("data_quality_grade"),
            }
            n_lca += 1

    for k, bucket in shards.items():
        (SITE_DATA / "dishes" / f"shard_{k}.json").write_text(
            json.dumps(bucket))
    print(f"  {n_lca:,} dish details → {len(shards)} shards")

    # every overlay attribute the tree leaves / map points need, per dish
    def overlay_attrs(cid):
        li = lite.get(cid, {})
        nu = nutri.get(cid) or {}
        cl = classes.get(cid, {})
        nq = nscore.get(cid) or {}
        mq = mhealth.get(cid) or {}
        dy = mq.get("delta_yll_lifetime")
        return {
            "ghg": li.get("ghg"), "water": li.get("water"),
            "land": li.get("land"),
            "kcal": nu.get("energy_kcal_per_serving"),
            "protein": nu.get("protein_g_per_serving"),
            "fat": nu.get("fat_g_per_serving"),
            "carb": nu.get("carb_g_per_serving"),
            "nutriscore": nq.get("score_0to100"),   # 0 best .. 100 worst
            "grade": nq.get("grade"),                # A-E
            # ΔYLL negated → "years lost": higher = worse = red, like the rest
            "mealhealth": (round(-dy, 6) if dy is not None else None),
            "cuisine": cl.get("cuisine", "Other"),
            "protein_type": cl.get("protein_type", "none"),
            "carb_type": cl.get("carb_type", "none"),
        }

    # --- umap layout: load early so its region labels can also be
    #     attached to the matching tree leaves -----------------------
    umap = json.loads(UMAP_IN.read_text()) if UMAP_IN.exists() else {}
    idx_region = {p["idx"]: p.get("region", -1)
                  for p in umap.get("points", [])}

    # --- tree: merge clade labels, enrich leaves --------------------
    print("merging clade labels + enriching tree leaves ...")
    tree = json.loads(TREE_IN.read_text())
    labels = load_labels()
    applied = [0]

    def label_internal(node):
        if node["id"] in labels:
            node["label"] = labels[node["id"]]
            applied[0] += 1

    def enrich_leaf(node):
        node.update(overlay_attrs(node["cluster_id"]))
        node["region"] = idx_region.get(node["dish_idx"], -1)

    walk(tree, enrich_leaf, label_internal)
    (SITE_DATA / "tree.json").write_text(json.dumps(tree))
    print(f"  {applied[0]:,} clade labels applied")

    # --- umap: enrich each point ------------------------------------
    if umap:
        meta_by_idx = {int(r["idx"]): r for r in meta_rows}
        for p in umap.get("points", []):
            cid = idx_to_cid.get(p["idx"])
            m = meta_by_idx.get(p["idx"], {})
            p["cluster_id"] = cid
            p["name"] = m.get("canonical_name") or m.get("top_raw_name", "")
            p["cuisine_bucket"] = m.get("cuisine_bucket", "")
            p["total_count"] = int(m.get("total_count", 0) or 0)
            p["n_ingredients"] = int(m.get("n_ingredients", 0) or 0)
            p.update(overlay_attrs(cid))
        (SITE_DATA / "umap.json").write_text(json.dumps(umap))
        print(f"  umap.json ({umap.get('method', '?')}, "
              f"{umap.get('n', 0):,} points enriched)")

    missing = len(v1_ids) - n_lca
    if missing:
        print(f"  NOTE: {missing} v1 dishes had no LCA row")

    manifest = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_dishes": len(v1_ids),
        "n_dish_details": n_lca,
        "n_clade_labels": applied[0],
        "umap_method": umap.get("method", "none"),
        "n_shards": N_SHARDS,
    }
    (SITE_DATA / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"DONE — site bundle in {SITE_DATA}")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
