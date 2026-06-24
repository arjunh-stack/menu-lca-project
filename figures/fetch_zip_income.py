"""Fetch ACS median household income (B19013) per ZIP, cached to data/.

Source: Census Reporter API (no key needed), ACS 2024 5-year, ZCTA level.
We only request the ZIPs that actually appear in menu_dishes (valid 5-digit),
batched to stay under the API's per-request geo limit. Result cached so the
figure build never re-hits the network.

Output: figures/data/zip_income.csv  (zip, median_hh_income)
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import ssl
import time
import urllib.request

import certifi

import figdata as fd

SSL_CTX = ssl.create_default_context(cafile=certifi.where())

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.join(OUT_DIR, "zip_income.csv")
API = "https://api.censusreporter.org/1.0/data/show/latest"
BATCH = 80


def valid_zips():
    con = sqlite3.connect(fd.MENUDB)
    rows = con.execute("select distinct zip_code from menu_dishes "
                       "where zip_code is not null").fetchall()
    con.close()
    zips = sorted({z[0] for z in rows if re.fullmatch(r"\d{5}", str(z[0]))})
    print(f"  {len(zips)} valid 5-digit ZIPs in menu_dishes")
    return zips


def fetch_batch(zips):
    geo = ",".join(f"86000US{z}" for z in zips)
    url = f"{API}?table_ids=B19013&geo_ids={geo}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh) menu-impact-research/1.0",
        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
        payload = json.load(r)
    out = {}
    for geoid, blob in payload.get("data", {}).items():
        z = geoid.split("US")[-1]
        est = blob.get("B19013", {}).get("estimate", {}).get("B19013001")
        if est is not None and est >= 0:
            out[z] = float(est)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    zips = valid_zips()
    # resume from cache so reruns only fill gaps
    inc = {}
    if os.path.exists(OUT):
        for r in csv.DictReader(open(OUT)):
            if r["median_hh_income"]:
                inc[r["zip"]] = float(r["median_hh_income"])
        print(f"  resuming with {len(inc)} cached")
    todo = [z for z in zips if z not in inc]
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        for attempt in range(5):
            try:
                got = fetch_batch(batch)
                inc.update(got)
                break
            except Exception as e:
                print(f"    batch {i//BATCH} attempt {attempt+1} failed: {e}")
                time.sleep(1.5 * (attempt + 1))
        print(f"  processed {min(i+BATCH, len(todo))}/{len(todo)} new  "
              f"(total {len(inc)} with income)")
        time.sleep(0.5)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip", "median_hh_income"])
        for z in sorted(inc):
            w.writerow([z, int(inc[z])])
    print(f"  wrote {OUT}  ({len(inc)} ZIPs with income)")


if __name__ == "__main__":
    main()
