"""Plot the distribution of canonical-dish total_count and dump quantiles."""

# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import csv
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

IN  = dpath("dish_canonical_summary_v6.csv")
PNG = dpath("dish_distribution.png")

counts = []
with open(IN) as f:
    for row in csv.DictReader(f):
        try:
            counts.append(int(row["total_count"]))
        except (ValueError, KeyError):
            pass
counts.sort()
n = len(counts)
total = sum(counts)
print(f"n_clusters: {n:,}    total restaurant-instances: {total:,}")

def pct(x): return counts[int(n * x) - 1]
print(f"\nquantiles:")
for q in [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999]:
    print(f"  p{int(q*1000)/10:>4}: {pct(q):>6}")
print(f"  max:  {counts[-1]:>6}")

# Cumulative-instance buckets
buckets = [(1,1), (2,2), (3,3), (4,5), (6,10), (11,20), (21,50), (51,100), (101,500), (501,1e9)]
print(f"\ncluster-count buckets (by total_count):")
print(f"  {'range':>10}  {'n_clusters':>11}  {'%clusters':>9}  {'sum_count':>10}  {'%instances':>10}")
for lo, hi in buckets:
    in_bucket = [c for c in counts if lo <= c <= hi]
    nb = len(in_bucket)
    sb = sum(in_bucket)
    pct_c = 100 * nb / n
    pct_i = 100 * sb / total
    label = f"{lo}" if lo == hi else (f"{lo}+" if hi >= 1e9 else f"{lo}-{int(hi)}")
    print(f"  {label:>10}  {nb:>11,}  {pct_c:>8.1f}%  {sb:>10,}  {pct_i:>9.1f}%")

# Top concentration
print(f"\ntop-N concentration (cumulative %instances):")
counts_desc = sorted(counts, reverse=True)
csum = np.cumsum(counts_desc)
for k in [10, 100, 1000, 5000, 10_000, 50_000, 100_000]:
    if k > n:
        continue
    print(f"  top {k:>7}: {100 * csum[k-1] / total:>5.1f}%")

# Plot — log-log rank-frequency (Zipf style)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ranks = np.arange(1, n + 1)
axes[0].loglog(ranks, counts_desc, ".", markersize=1.5, alpha=0.5, color="tab:blue")
axes[0].set_xlabel("rank (most-common dish = 1)")
axes[0].set_ylabel("total_count")
axes[0].set_title(f"Rank-frequency (log-log) — {n:,} canonical dishes")
axes[0].grid(True, alpha=0.3, which="both")

# Histogram of total_count (log y)
max_show = 50
hist_counts, edges = np.histogram(counts, bins=range(1, max_show + 2))
axes[1].bar(edges[:-1], hist_counts, color="tab:orange", edgecolor="black", linewidth=0.4)
axes[1].set_yscale("log")
axes[1].set_xlabel("total_count (truncated at 50)")
axes[1].set_ylabel("number of canonical dishes (log)")
axes[1].set_title(f"Distribution — {hist_counts[0]:,} singletons (count=1)")
axes[1].grid(True, alpha=0.3, which="both", axis="y")

plt.tight_layout()
plt.savefig(PNG, dpi=120)
print(f"\nwrote {PNG}")
