"""Precompute the per-dish context that feeds the recipe pipeline.

For each canonical dish (cluster_id), find:
  - `top_raw_name`: the most-frequent raw_menu_name across restaurants
    (ties broken by shortest length — prefers clean generic forms like
    "Italian Sub" over brand-specific "Italian B.M.T.® 6 Inch Regular Sub").
  - `cuisine_bucket`: the structural-reference bucket from
    structural_references.CATEGORY_MAP, picked by counting bucket hits
    across each restaurant's comma-separated category tags.

Inputs:
  menu_dishes.sqlite              (raw_menu_name, restaurant_category, canonical_dish)
  stage1/snapshots/dish_canonical_summary_v19.csv  (cluster_id, canonical_name, total_count) — current head, post-Layer-25

Output:
  recipes/dish_context.csv
    columns: cluster_id, canonical_name, top_raw_name, cuisine_bucket,
             n_rows, n_restaurants, total_count
"""
import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from structural_references import _TIERS

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "menu_dishes.sqlite"
SUMMARY = ROOT / "stage1" / "snapshots" / "dish_canonical_summary_v19.csv"
OUT = Path(__file__).resolve().parent / "dish_context.csv"


def load_canonical_to_cluster():
    """Map canonical_name -> (cluster_id, total_count) from the summary CSV."""
    m = {}
    with open(SUMMARY) as f:
        for row in csv.DictReader(f):
            m[row["canonical_name"]] = (int(row["cluster_id"]), int(row["total_count"]))
    return m


def bucket_for_tags(category_str: str | None) -> str | None:
    """Scan tags by tier priority; return the highest-priority bucket match
    or None if no tag matches any tier. Mirrors structural_references.
    bucket_from_category but returns None instead of "default" so the
    aggregation step can distinguish no-signal from default-signal."""
    if not category_str:
        return None
    tags = [t.strip().lower() for t in category_str.split(",")]
    for tier in _TIERS:
        for tag in tags:
            if tag in tier:
                return tier[tag]
    return None


def main():
    print(f"loading {SUMMARY.name}...")
    canon_map = load_canonical_to_cluster()
    print(f"  {len(canon_map):,} canonical dishes")

    print(f"streaming {DB.name}...")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT canonical_dish, raw_menu_name, restaurant_category, restaurant_id
        FROM menu_dishes
        WHERE canonical_dish IS NOT NULL
    """)

    name_counts: dict[str, Counter] = defaultdict(Counter)
    bucket_counts: dict[str, Counter] = defaultdict(Counter)
    row_count: Counter = Counter()
    restaurant_ids: dict[str, set] = defaultdict(set)

    n = 0
    for row in cursor:
        canon = row["canonical_dish"]
        raw = row["raw_menu_name"]
        cat = row["restaurant_category"]
        rid = row["restaurant_id"]

        if raw:
            name_counts[canon][raw] += 1
        # Always vote: tier-matching tag → its bucket; no match → "default".
        # This protects sandwich-chain dishes (mostly tag-silent restaurants)
        # from getting pulled into a niche bucket by a handful of crossover
        # restaurants tagged differently.
        bucket_counts[canon][bucket_for_tags(cat) or "default"] += 1
        row_count[canon] += 1
        if rid is not None:
            restaurant_ids[canon].add(rid)

        n += 1
        if n % 200_000 == 0:
            print(f"  {n:,} rows ({len(name_counts):,} canonicals seen)")
    conn.close()
    print(f"  total rows scanned: {n:,}")
    print(f"  distinct canonicals seen: {len(name_counts):,}")

    print(f"writing {OUT.name}...")
    n_with_cluster = 0
    n_missing_cluster = 0
    n_with_bucket = 0
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "cluster_id", "canonical_name", "top_raw_name", "cuisine_bucket",
            "n_rows", "n_restaurants", "total_count",
        ])
        for canon, names in name_counts.items():
            # most-frequent name, ties broken by shortest length
            top_raw, _ = max(names.items(), key=lambda kv: (kv[1], -len(kv[0])))
            buckets = bucket_counts.get(canon)
            cuisine = buckets.most_common(1)[0][0] if buckets else "default"
            if buckets:
                n_with_bucket += 1
            cluster_info = canon_map.get(canon)
            if cluster_info is None:
                n_missing_cluster += 1
                cluster_id = ""
                total_count = ""
            else:
                cluster_id, total_count = cluster_info
                n_with_cluster += 1
            w.writerow([
                cluster_id,
                canon,
                top_raw,
                cuisine,
                row_count[canon],
                len(restaurant_ids[canon]),
                total_count,
            ])

    print(f"  rows with cluster_id:  {n_with_cluster:,}")
    print(f"  rows missing cluster_id (in DB but not in summary): {n_missing_cluster:,}")
    print(f"  rows with non-default cuisine bucket: {n_with_bucket:,}")
    # FILTERING_LOG entry is maintained manually — this script is re-runnable
    # and would otherwise append duplicates each run.


if __name__ == "__main__":
    main()
