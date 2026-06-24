"""
In-place cleaning of mydb.sqlite. Idempotent — safe to re-run.

Operations (each = one Cleaning Layer):
  C1  NULL the one bizarre restaurants.price_range row ($$$$$$$$$$$$$$$$$)
  C2  HTML-unescape restaurants.category, menus.name, menus.description
  C3  Add menus.price_usd REAL column, populate from "X.XX USD" → X.XX
  C4  Canonicalize restaurants.category (case/entity/punctuation/singular-plural dedup)

Outputs:
  - mydb.sqlite (modified in place)
  - category_canonical_mapping.csv (raw tag → canonical, for review)
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
MAPPING_OUT = dpath("category_canonical_mapping.csv")


def cluster_key(tag: str) -> str:
    """Lowercase, html-unescape, &/+ → and, collapse whitespace."""
    s = html.unescape(tag).strip().lower()
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"\s*\+\s*", " and ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _singularize_word(w: str) -> str:
    """Singularize a single token. Handles -ies, -es (after sibilants), -s."""
    if len(w) < 4:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"             # parties → party
    if w.endswith(("ches", "shes", "xes", "sses", "zes")):
        return w[:-2]                    # sandwiches → sandwich, boxes → box
    if w.endswith("oes"):
        return w[:-2]                    # tomatoes → tomato
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]                    # burgers → burger
    return w


def singular_key(s: str) -> str:
    return " ".join(_singularize_word(w) for w in s.split())


_BAD_CASE_ENTITY = re.compile(r"&(amp|quot|apos|lt|gt|nbsp);", re.IGNORECASE)
_ENTITY_MAP = {"amp": "&", "quot": '"', "apos": "'", "lt": "<", "gt": ">", "nbsp": " "}


def unescape_until_stable(s: str, max_iter: int = 5) -> str:
    """Some entities are double-encoded (&amp;amp;) or wrong-cased (&Amp;)."""
    for _ in range(max_iter):
        u = html.unescape(s)
        u = _BAD_CASE_ENTITY.sub(lambda m: _ENTITY_MAP[m.group(1).lower()], u)
        if u == s:
            return u
        s = u
    return s


def build_canonical_mapping(con) -> dict[str, str]:
    cur = con.cursor()
    cur.execute("SELECT category FROM restaurants WHERE category IS NOT NULL AND category != ''")
    raw_counts = Counter()
    for (cat,) in cur:
        for t in html.unescape(cat).split(","):
            t = t.strip()
            if t:
                raw_counts[t] += 1

    # Pass 1: cluster by cluster_key, pick most-common original spelling as canonical
    by_key = defaultdict(list)
    for tag, n in raw_counts.items():
        by_key[cluster_key(tag)].append((tag, n))
    pass1 = {}  # raw_tag → canonical_after_pass1
    canon1_count = Counter()
    for key, members in by_key.items():
        members.sort(key=lambda x: (-x[1], x[0]))
        canonical = members[0][0]
        for tag, n in members:
            pass1[tag] = canonical
            canon1_count[canonical] += n

    # Pass 2: merge singular/plural pairs (within canonicals only)
    by_sing = defaultdict(list)
    for canon, n in canon1_count.items():
        by_sing[singular_key(cluster_key(canon))].append((canon, n))
    canon_remap = {}  # canonical_after_pass1 → final_canonical
    for sing, members in by_sing.items():
        members.sort(key=lambda x: (-x[1], x[0]))
        winner = members[0][0]
        for canon, _ in members:
            canon_remap[canon] = winner

    final = {raw: canon_remap[c] for raw, c in pass1.items()}
    return final, raw_counts


def write_mapping_csv(mapping: dict[str, str], counts: Counter):
    with open(MAPPING_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["raw_tag", "canonical_tag", "raw_count"])
        for raw in sorted(mapping, key=lambda x: (-counts[x], x.lower())):
            w.writerow([raw, mapping[raw], counts[raw]])


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # ---- C1: bizarre price_range ----
    cur.execute("SELECT id, name FROM restaurants WHERE price_range = '$$$$$$$$$$$$$$$$$'")
    rows = cur.fetchall()
    for rid, name in rows:
        print(f"[C1] nulling price_range for restaurant id={rid}: {name}")
    cur.execute("UPDATE restaurants SET price_range = NULL WHERE price_range = '$$$$$$$$$$$$$$$$$'")
    print(f"[C1] {cur.rowcount} row(s) updated")

    # ---- C2: HTML-unescape text columns ----
    # restaurants.category
    cur.execute("SELECT id, category FROM restaurants WHERE category LIKE '%&%;%'")
    todo = [(unescape_until_stable(c), i) for i, c in cur.fetchall()]
    cur.executemany("UPDATE restaurants SET category = ? WHERE id = ?", todo)
    print(f"[C2] restaurants.category: unescaped {len(todo)} rows")

    # menus.name — match by rowid (no PK, no unique key)
    cur.execute("SELECT rowid, name FROM menus WHERE name LIKE '%&%;%'")
    todo = [(unescape_until_stable(n), rid) for rid, n in cur.fetchall() if unescape_until_stable(n) != n]
    cur.executemany("UPDATE menus SET name = ? WHERE rowid = ?", todo)
    print(f"[C2] menus.name: unescaped {len(todo)} rows")

    # menus.description
    cur.execute("SELECT rowid, description FROM menus WHERE description LIKE '%&%;%'")
    todo = [(unescape_until_stable(d), rid) for rid, d in cur.fetchall() if unescape_until_stable(d) != d]
    cur.executemany("UPDATE menus SET description = ? WHERE rowid = ?", todo)
    print(f"[C2] menus.description: unescaped {len(todo)} rows")

    con.commit()

    # ---- C3: price_usd column ----
    cur.execute("PRAGMA table_info(menus)")
    cols = {row[1] for row in cur.fetchall()}
    if "price_usd" not in cols:
        cur.execute("ALTER TABLE menus ADD COLUMN price_usd REAL")
        print("[C3] added column menus.price_usd REAL")
    else:
        print("[C3] menus.price_usd already exists")

    # All prices end in ' USD' (verified). Strip suffix and cast.
    # Using SQL is fastest; non-USD or unparseable rows stay NULL.
    cur.execute("""
        UPDATE menus
        SET price_usd = CAST(REPLACE(price, ' USD', '') AS REAL)
        WHERE price IS NOT NULL AND price LIKE '% USD'
    """)
    n_set = cur.rowcount
    cur.execute("SELECT COUNT(*) FROM menus WHERE price_usd IS NULL")
    n_null = cur.fetchone()[0]
    print(f"[C3] populated price_usd on {n_set:,} rows; {n_null:,} remain NULL")

    con.commit()

    # ---- C4: canonicalize categories ----
    mapping, raw_counts = build_canonical_mapping(con)
    write_mapping_csv(mapping, raw_counts)
    print(f"[C4] wrote canonical mapping ({len(mapping)} raw → "
          f"{len(set(mapping.values()))} canonical) to {MAPPING_OUT}")

    cur.execute("SELECT id, category FROM restaurants WHERE category IS NOT NULL AND category != ''")
    updates = []
    changed = 0
    for rid, cat in cur.fetchall():
        original = cat  # already html-unescaped above
        tags = [t.strip() for t in original.split(",") if t.strip()]
        seen = []
        for t in tags:
            c = mapping.get(t, t)
            if c not in seen:
                seen.append(c)
        new_cat = ", ".join(seen)
        if new_cat != original:
            updates.append((new_cat, rid))
            changed += 1
    cur.executemany("UPDATE restaurants SET category = ? WHERE id = ?", updates)
    print(f"[C4] updated {changed:,} restaurants with canonicalized category strings")

    con.commit()
    con.close()
    print("done.")


if __name__ == "__main__":
    main()
