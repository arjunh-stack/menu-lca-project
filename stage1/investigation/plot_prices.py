"""Plot the distribution of menus.price_usd (post-C3 cleaning, post-Layer-1 filter)."""

# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import sqlite3
import csv
import html
import numpy as np
import matplotlib.pyplot as plt

DB = dpath("mydb.sqlite")
EXCLUDE_FILE = dpath("unique_categories_to_exclude.csv")
OUT = dpath("price_distribution.png")


def load_exclude_tags():
    tags = set()
    with open(EXCLUDE_FILE) as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) >= 2 and row[1].strip().lower() == "x":
                tags.add(html.unescape(row[0]).strip())
    return tags


def excluded_ids(con, exclude):
    cur = con.cursor()
    cur.execute("SELECT id, category FROM restaurants WHERE category IS NOT NULL AND category != ''")
    bad = set()
    for rid, cat in cur:
        tags = {t.strip() for t in cat.split(",")}
        if tags & exclude:
            bad.add(rid)
    return bad


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # filtered set (Layer 1)
    bad = excluded_ids(con, load_exclude_tags())
    cur.execute("DROP TABLE IF EXISTS _bad")
    cur.execute("CREATE TEMP TABLE _bad (id INTEGER PRIMARY KEY)")
    cur.executemany("INSERT INTO _bad VALUES (?)", ((i,) for i in bad))
    cur.execute("SELECT price_usd FROM menus WHERE restaurant_id NOT IN (SELECT id FROM _bad) AND price_usd IS NOT NULL")
    prices = np.fromiter((r[0] for r in cur), dtype=np.float64)

    # all rows
    cur.execute("SELECT price_usd FROM menus WHERE price_usd IS NOT NULL")
    all_prices = np.fromiter((r[0] for r in cur), dtype=np.float64)

    print(f"filtered (Layer 1) prices : {len(prices):,}")
    print(f"all prices                : {len(all_prices):,}")

    def stats(p, label):
        q = np.percentile(p, [1, 25, 50, 75, 95, 99])
        print(f"{label}: min={p.min():.2f}  max={p.max():.2f}  mean={p.mean():.2f}  median={q[2]:.2f}")
        print(f"  pct: 1%={q[0]:.2f}  25%={q[1]:.2f}  50%={q[2]:.2f}  75%={q[3]:.2f}  95%={q[4]:.2f}  99%={q[5]:.2f}")
        print(f"  zeros={int((p == 0).sum()):,}  negatives={int((p < 0).sum()):,}  > $100={int((p > 100).sum()):,}")

    stats(prices, "filtered")
    stats(all_prices, "all     ")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # Top-left: linear scale, 0-50
    ax = axes[0, 0]
    ax.hist(prices[(prices >= 0) & (prices <= 50)], bins=100, color="#1f77b4", edgecolor="white", linewidth=0.3)
    ax.set_title(f"Menu prices $0–$50 (linear y) — {((prices>=0)&(prices<=50)).sum():,} items")
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Count")
    ax.axvline(np.median(prices), color="red", linestyle="--", linewidth=1, label=f"median ${np.median(prices):.2f}")
    ax.axvline(np.mean(prices),   color="orange", linestyle="--", linewidth=1, label=f"mean ${np.mean(prices):.2f}")
    ax.legend()

    # Top-right: same range, log y (shows the $0 spike + long tail honestly)
    ax = axes[0, 1]
    ax.hist(prices[(prices >= 0) & (prices <= 50)], bins=100, color="#1f77b4", edgecolor="white", linewidth=0.3)
    ax.set_yscale("log")
    ax.set_title("Menu prices $0–$50 (log y)")
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Count (log)")

    # Bottom-left: full range with log y
    ax = axes[1, 0]
    ax.hist(prices[prices >= 0], bins=200, color="#2ca02c", edgecolor="white", linewidth=0.3)
    ax.set_yscale("log")
    ax.set_title(f"Full range $0–${prices.max():.0f} (log y) — long tail")
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Count (log)")

    # Bottom-right: percentile / CDF view
    ax = axes[1, 1]
    sorted_p = np.sort(prices[prices >= 0])
    cdf = np.arange(1, len(sorted_p) + 1) / len(sorted_p)
    ax.plot(sorted_p, cdf, color="#9467bd")
    ax.set_xlim(0, 60)
    ax.set_title("CDF (cumulative share of items ≤ price)")
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Cumulative share")
    for pct in [0.5, 0.75, 0.95]:
        v = np.quantile(sorted_p, pct)
        ax.axhline(pct, color="grey", linewidth=0.5, linestyle=":")
        ax.axvline(v, color="grey", linewidth=0.5, linestyle=":")
        ax.text(v + 0.5, pct - 0.03, f"{int(pct*100)}% ≤ ${v:.2f}", fontsize=9)

    fig.suptitle(f"Menu price distribution — {len(prices):,} items from {63469 - len(bad):,} restaurants (post Layer-1 filter)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT, dpi=130, bbox_inches="tight")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
