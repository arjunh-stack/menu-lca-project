"""
C5 — Canonicalize menus.category in place. Idempotent.

Same approach as C4 for restaurants.category, but:
  - menus.category is a SINGLE label per row (not comma-separated), so no splitting
  - mapping is built from ALL menus rows (whole db) for consistency
  - update is applied to ALL rows in place

Then report:
  - total unique categories before/after, on whole db and on Layer-1-filtered subset.
"""

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
import html
import csv
import re
from collections import Counter, defaultdict

DB = dpath("mydb.sqlite")
EXCLUDE_FILE = dpath("unique_categories_to_exclude.csv")
MAPPING_OUT = dpath("menu_category_canonical_mapping.csv")


_BAD_CASE_ENTITY = re.compile(r"&(amp|quot|apos|lt|gt|nbsp);", re.IGNORECASE)
_ENTITY_MAP = {"amp": "&", "quot": '"', "apos": "'", "lt": "<", "gt": ">", "nbsp": " "}


def unescape_until_stable(s: str, max_iter: int = 5) -> str:
    for _ in range(max_iter):
        u = html.unescape(s)
        u = _BAD_CASE_ENTITY.sub(lambda m: _ENTITY_MAP[m.group(1).lower()], u)
        if u == s:
            return u
        s = u
    return s


def cluster_key(s: str) -> str:
    s = unescape_until_stable(s).strip().lower()
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"\s*\+\s*", " and ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _singularize_word(w: str) -> str:
    if len(w) < 4:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ches", "shes", "xes", "sses", "zes")):
        return w[:-2]
    if w.endswith("oes"):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def singular_key(s: str) -> str:
    return " ".join(_singularize_word(w) for w in s.split())


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

    # raw counts BEFORE
    cur.execute("SELECT COUNT(DISTINCT category) FROM menus WHERE category IS NOT NULL AND category != ''")
    before_raw = cur.fetchone()[0]

    # ---- build mapping from ALL menus.category ----
    cur.execute("SELECT category, COUNT(*) FROM menus WHERE category IS NOT NULL AND category != '' GROUP BY category")
    raw_counts = {cat: n for cat, n in cur}
    print(f"[C5] distinct raw menu categories : {len(raw_counts):,}")

    # Pass 1: cluster on cluster_key, canonical = most common (with html unescaped & trimmed)
    by_key = defaultdict(list)
    for tag, n in raw_counts.items():
        clean_form = unescape_until_stable(tag).strip()
        by_key[cluster_key(tag)].append((tag, clean_form, n))
    pass1 = {}  # raw → canonical_after_pass1
    canon1_count = Counter()
    for key, members in by_key.items():
        # rank canonicals by count desc, then alphabetic
        candidate_counts = Counter()
        candidate_form = {}
        for raw, clean_form, n in members:
            candidate_counts[clean_form] += n
            candidate_form.setdefault(clean_form, clean_form)
        winner = sorted(candidate_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
        for raw, _, n in members:
            pass1[raw] = winner
            canon1_count[winner] += n

    # Pass 2: singular/plural merge among canonicals
    by_sing = defaultdict(list)
    for canon, n in canon1_count.items():
        by_sing[singular_key(cluster_key(canon))].append((canon, n))
    canon_remap = {}
    for sing, members in by_sing.items():
        members.sort(key=lambda x: (-x[1], x[0]))
        winner = members[0][0]
        for canon, _ in members:
            canon_remap[canon] = winner

    final_map = {raw: canon_remap[c] for raw, c in pass1.items()}
    n_canonical = len(set(final_map.values()))
    print(f"[C5] after canonicalization       : {n_canonical:,}")

    # write mapping
    with open(MAPPING_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["raw_category", "canonical_category", "raw_count"])
        for raw in sorted(final_map, key=lambda x: (-raw_counts[x], x.lower())):
            w.writerow([raw, final_map[raw], raw_counts[raw]])
    print(f"[C5] wrote mapping to {MAPPING_OUT}")

    # ---- apply update in place (only where the value changes) ----
    cur.execute("SELECT rowid, category FROM menus WHERE category IS NOT NULL AND category != ''")
    todo = []
    for rid, cat in cur.fetchall():
        canon = final_map.get(cat)
        if canon is not None and canon != cat:
            todo.append((canon, rid))
    cur.executemany("UPDATE menus SET category = ? WHERE rowid = ?", todo)
    print(f"[C5] updated {len(todo):,} menu rows")
    con.commit()

    # ---- post-cleanup counts ----
    cur.execute("SELECT COUNT(DISTINCT category) FROM menus WHERE category IS NOT NULL AND category != ''")
    after_raw = cur.fetchone()[0]
    print(f"\n[result] distinct categories — whole db: {before_raw:,} → {after_raw:,}")

    # filtered (Layer 1) count
    bad = excluded_ids(con, load_exclude_tags())
    cur.execute("DROP TABLE IF EXISTS _bad")
    cur.execute("CREATE TEMP TABLE _bad (id INTEGER PRIMARY KEY)")
    cur.executemany("INSERT INTO _bad VALUES (?)", ((i,) for i in bad))
    cur.execute("""
        SELECT COUNT(DISTINCT category)
        FROM menus
        WHERE category IS NOT NULL AND category != ''
          AND restaurant_id NOT IN (SELECT id FROM _bad)
    """)
    filtered_count = cur.fetchone()[0]
    print(f"[result] distinct categories — Layer-1 filtered (real restaurants only): {filtered_count:,}")

    # top 30 in filtered set
    cur.execute("""
        SELECT category, COUNT(*) n
        FROM menus
        WHERE category IS NOT NULL AND category != ''
          AND restaurant_id NOT IN (SELECT id FROM _bad)
        GROUP BY category ORDER BY n DESC LIMIT 30
    """)
    print("\ntop 30 menu categories (filtered):")
    for cat, n in cur:
        print(f"  {n:>8,}  {cat}")


if __name__ == "__main__":
    main()
