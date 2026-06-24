
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
import re
import html
from collections import Counter

DB = dpath("mydb.sqlite")

SIZE_WORDS = r"(?:extra\s*large|x[-\s]?large|xl|xxl|jumbo|grande|large|medium|regular|reg|small|sm|md|lg|mini|kids?|kid'?s|family|party|individual|single|double|triple|half|whole|full|personal|junior|jr|senior|sr|petite|tall|short|venti)"
QTY_WORDS = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"
# Pure measurement units only (NOT dish nouns like wings/tenders/nuggets/rolls/slices).
MEAS_UNITS = r"(?:oz|ounces?|lb|lbs|pounds?|inch|inches|qt|quart|gal|gallon|liter|ml)"
# Counter words paired with leading numbers ("8 pc.", "12 ct"). Stripped only when leading.
COUNT_UNITS = r"(?:pieces?|pcs?|piece|pc\.?|ct|count|pack)"

# Enumerations only: "#13 ", "1. ", "1) ", "A. ", "A) ". NOT bare "12 ".
LEAD_NUM = re.compile(r"^\s*(?:#\d+|\d+[.)]|[a-z][.)])\s+", re.I)
PAREN = re.compile(r"\([^)]*\)|\[[^\]]*\]")
SIZE_PAT = re.compile(rf"\b{SIZE_WORDS}\b", re.I)
# Leading "<number> [optional pc/ct/pack] " — strips count, leaves the dish noun.
# \b after qty-word so "ten" doesn't prefix-match "tenders".
LEAD_QTY_PAT = re.compile(rf"^\s*(?:\d+|{QTY_WORDS})\b\s*(?:{COUNT_UNITS})?\s*[-:.]?\s*", re.I)
# Embedded "<number> <measurement_unit>" — true units, safe to drop both
MEAS_PAT = re.compile(rf"\b(?:\d+(?:\.\d+)?|{QTY_WORDS})\s*-?\s*{MEAS_UNITS}\b", re.I)
NONALNUM = re.compile(r"[^a-z0-9 ]+")
WS = re.compile(r"\s+")
# Conservative: only articles, basic prepositions, conjunction, and "new".
# Removed (kept as differentiators): spicy/hot/cold/sweet/mild/savory, fresh/homemade/house/
# chef's/signature/classic/traditional/original/premium/deluxe/gourmet, special/combo/meal/
# plate/platter/dish/order/menu/item.
COMMON_NOISE = re.compile(r"\b(?:new|w/|with|and|the|a|an|of|in|on)\b", re.I)


def normalize(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = s.lower()
    s = LEAD_NUM.sub("", s)           # "#13", "1.", "A)"
    s = PAREN.sub(" ", s)              # (large), [vegan]
    s = LEAD_QTY_PAT.sub(" ", s)       # "5 pc.", "12 " — strip count, KEEP the dish noun
    s = MEAS_PAT.sub(" ", s)           # "8 oz", "11 inch"
    s = SIZE_PAT.sub(" ", s)           # large/small/jumbo/family/etc
    s = COMMON_NOISE.sub(" ", s)       # the/and/of/with/in/on/new
    s = NONALNUM.sub(" ", s)           # punctuation
    s = WS.sub(" ", s).strip()
    # sort tokens so "Pizza Margherita" == "Margherita Pizza"
    toks = sorted(s.split())
    return " ".join(toks)


# ─── Layer 4: infer dish format from menu.category ───
# Each entry: (regex, canonical_format_token). Order matters for diagnostics
# but we use unique-match-only logic so position only matters when multiple
# patterns hit different tokens.
CATEGORY_FORMAT_PATTERNS = [
    (re.compile(r"\bwraps?\b", re.I),                                    "wrap"),
    (re.compile(r"\b(subs?|hoagies?|heroes?|grinders?|po[' ]?boys?)\b", re.I), "sub"),
    (re.compile(r"\b(sandwich(?:es)?|deli|paninis?|melts?|sliders?)\b", re.I),  "sandwich"),
    (re.compile(r"\b(bowls?|poke)\b", re.I),                              "bowl"),
    (re.compile(r"\b(pizzas?|flatbreads?)\b", re.I),                      "pizza"),
    (re.compile(r"\b(calzones?|strombolis?)\b", re.I),                    "calzone"),
    (re.compile(r"\b(sushi|sashimi|nigiri|maki|temaki)\b", re.I),         "sushi"),
    (re.compile(r"\btacos?\b", re.I),                                     "taco"),
    (re.compile(r"\bburritos?\b", re.I),                                  "burrito"),
    (re.compile(r"\bquesadillas?\b", re.I),                               "quesadilla"),
    (re.compile(r"\bfajitas?\b", re.I),                                   "fajita"),
    (re.compile(r"\bsalads?\b", re.I),                                    "salad"),
    (re.compile(r"\b(pastas?|noodles?|pho|ramen|spaghetti|fettuccine|linguine|udon|soba)\b", re.I), "pasta"),
    (re.compile(r"\b(burgers?|cheeseburgers?|hamburgers?)\b", re.I),      "burger"),
    (re.compile(r"\bwings?\b", re.I),                                     "wings"),
    (re.compile(r"\b(ribs?|rib)\b", re.I),                                "ribs"),
    (re.compile(r"\b(curr(?:y|ies))\b", re.I),                            "curry"),
    (re.compile(r"\b(steaks?)\b", re.I),                                  "steak"),
    (re.compile(r"\b(soups?|chowders?|bisques?|stews?)\b", re.I),         "soup"),
]
# Plural→singular for known format tokens, so "Tuna Wraps" + Wraps → "tuna wrap"
# rather than "tuna wrap wraps".
FORMAT_TOKENS = {tok for _, tok in CATEGORY_FORMAT_PATTERNS}
_PLURAL_FORMAT = {}
for tok in FORMAT_TOKENS:
    _PLURAL_FORMAT[tok + "s"] = tok
    _PLURAL_FORMAT[tok + "es"] = tok
    if tok.endswith("y"):
        _PLURAL_FORMAT[tok[:-1] + "ies"] = tok


def format_from_category(cat: str) -> str | None:
    """Return the canonical format token if exactly one pattern matches the category."""
    if not cat:
        return None
    matches = set()
    for pat, tok in CATEGORY_FORMAT_PATTERNS:
        if pat.search(cat):
            matches.add(tok)
    if len(matches) == 1:
        return next(iter(matches))
    return None  # 0 or 2+ matches → ambiguous, skip


def normalize_with_format(name: str, category: str | None) -> str:
    """Normalize the dish name AND fold in the format token from menu.category."""
    base = normalize(name)
    fmt = format_from_category(category) if category else None
    if not fmt:
        return base
    # singularize any plural format-tokens already in the dish name
    base_toks = [_PLURAL_FORMAT.get(t, t) for t in base.split()]
    if fmt not in base_toks:
        base_toks.append(fmt)
    return " ".join(sorted(set(base_toks)))


EXCLUDE_FILE = dpath("unique_categories_to_exclude.csv")
MENU_CAT_EXCL = dpath("proposed_menu_category_excludes.csv")
MENU_CAT_AMBIG = dpath("proposed_menu_category_ambiguous.csv")


def load_exclude_tags() -> set[str]:
    """Read user's per-tag exclusion list (column B = 'x' marks excluded)."""
    import csv as _csv
    tags = set()
    with open(EXCLUDE_FILE) as f:
        r = _csv.reader(f)
        next(r, None)  # header
        for row in r:
            if len(row) >= 2 and row[1].strip().lower() == "x":
                tags.add(html.unescape(row[0]).strip())
    return tags


def load_excluded_menu_categories() -> set[str]:
    """Layer 2: menu.category exclusions = full excludes list + ambiguous list."""
    import csv as _csv
    cats = set()
    for path, cat_col in [(MENU_CAT_EXCL, 1), (MENU_CAT_AMBIG, 1)]:
        with open(path) as f:
            r = _csv.reader(f)
            next(r, None)
            for row in r:
                if len(row) > cat_col:
                    cats.add(row[cat_col].strip())
    cats.discard("")
    return cats


def excluded_restaurant_ids(con, exclude_tags: set[str]) -> set[int]:
    """Restaurants whose category list contains ANY excluded tag (exact match per tag)."""
    cur = con.cursor()
    cur.execute("SELECT id, category FROM restaurants WHERE category IS NOT NULL AND category != ''")
    bad = set()
    for rid, cat in cur:
        tags = {t.strip() for t in html.unescape(cat).split(",")}
        if tags & exclude_tags:
            bad.add(rid)
    return bad


def main():
    con = sqlite3.connect(DB)
    exclude_tags = load_exclude_tags()
    bad_ids = excluded_restaurant_ids(con, exclude_tags)
    bad_menu_cats = load_excluded_menu_categories()
    print(f"Layer 1 — excluded restaurant tags  : {len(exclude_tags)}")
    print(f"Layer 1 — excluded restaurants      : {len(bad_ids):,}")
    print(f"Layer 2 — excluded menu categories  : {len(bad_menu_cats):,}")

    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS _bad")
    cur.execute("CREATE TEMP TABLE _bad (id INTEGER PRIMARY KEY)")
    cur.executemany("INSERT INTO _bad VALUES (?)", ((i,) for i in bad_ids))

    cur.execute("DROP TABLE IF EXISTS _bad_cats")
    cur.execute("CREATE TEMP TABLE _bad_cats (cat TEXT PRIMARY KEY)")
    cur.executemany("INSERT OR IGNORE INTO _bad_cats VALUES (?)", ((c,) for c in bad_menu_cats))

    cur.execute("""
        SELECT m.name, m.category
        FROM menus m
        WHERE m.restaurant_id NOT IN (SELECT id FROM _bad)
          AND (m.category IS NULL OR m.category NOT IN (SELECT cat FROM _bad_cats))
    """)
    seen = Counter()
    n = 0
    empty = 0
    fmt_inferred = 0
    for name, category in cur:
        n += 1
        norm = normalize_with_format(name or "", category)
        if not norm:
            empty += 1
            continue
        if format_from_category(category):
            fmt_inferred += 1
        seen[norm] += 1
        if n % 500_000 == 0:
            print(f"  processed {n:,} rows, {len(seen):,} unique so far")

    print()
    print(f"total rows                  : {n:,}")
    print(f"empty after normalize       : {empty:,}")
    print(f"rows with category-format   : {fmt_inferred:,}")
    print(f"unique normalized           : {len(seen):,}")
    print()
    print("top 20 most common normalized dishes:")
    for k, v in seen.most_common(20):
        print(f"  {v:>7,}  {k}")

    # singletons = dishes that appear at only one restaurant (likely long-tail / unique)
    singletons = sum(1 for v in seen.values() if v == 1)
    print()
    print(f"singleton dishes (appear once): {singletons:,}")
    print(f"dishes appearing 2+ times    : {len(seen) - singletons:,}")

    # dump full sorted list to CSV for review
    import csv
    out = dpath("unique_dishes_mains_only.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["normalized_name", "count"])
        for name, cnt in seen.most_common():
            w.writerow([name, cnt])
    print(f"\nwrote full list to {out}")


if __name__ == "__main__":
    main()
