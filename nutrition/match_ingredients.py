"""match_ingredients.py — Match every unique recipe-ingredient string to a
USDA FoodData Central food + its per-100 g macros. (Stage 2b, step 3.)

Collects the unique ingredient strings from a recipes JSONL file, matches
each once (concurrently) via fdc_matcher, and writes one row per unique
ingredient to nutrition/ingredient_fdc_table.csv. aggregate_macros.py then
joins that table back onto recipes by ingredient name.

Architecture mirrors lca/match_ingredients.py — dedupe first, match the
unique set once. Idempotent: fdc_matcher caches every result in
data/fdc_match_cache.json, so a re-run (or a later full run after a
validation-slice run) only matches ingredients not seen before.

Usage:
  python3 match_ingredients.py                                  # recipes_validation.jsonl (500-dish slice)
  python3 match_ingredients.py --recipes ../recipes/recipes.jsonl  # full ~75k run
  python3 match_ingredients.py --concurrency 30
"""
import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdc_matcher  # type: ignore  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_RECIPES = ROOT / "recipes" / "recipes_validation.jsonl"
DEFAULT_OUT = HERE / "ingredient_fdc_table.csv"
ENV_FILE = ROOT / ".env.openrouter"

OUT_COLS = [
    "ingredient", "occurrences",
    "fdc_id", "matched_description", "source",
    "energy_kcal", "protein_g", "fat_g", "carb_g",
    "confidence", "method", "unmatched",
]


def load_api_key() -> str:
    import os
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key.strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(f"OPENROUTER_API_KEY not found in env var or {ENV_FILE}")


def collect_unique_ingredients(recipes_path: Path) -> list[tuple[str, int]]:
    """Return [(name, occurrence_count)] sorted by count desc. First-seen
    casing is kept for the name; the lowercased key is dedup-only."""
    seen: dict[str, tuple[str, int]] = {}
    n_recipes = 0
    with open(recipes_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("error"):
                continue
            n_recipes += 1
            for ing in r.get("ingredients", []):
                raw = (ing.get("ingredient") or "").strip()
                if not raw:
                    continue
                key = raw.lower()
                if key in seen:
                    nm, n = seen[key]
                    seen[key] = (nm, n + 1)
                else:
                    seen[key] = (raw, 1)
    print(f"  {n_recipes:,} recipes -> {len(seen):,} unique ingredient strings")
    return sorted(seen.values(), key=lambda nc: -nc[1])


def match_one(name: str, api_key: str) -> dict:
    """Wrap fdc_matcher so a single failure can't kill the batch."""
    try:
        return fdc_matcher.match_ingredient(name, api_key=api_key)
    except Exception as e:
        return {
            "ingredient": name, "fdc_id": None, "matched_description": None,
            "source": None, "energy_kcal": None, "protein_g": None,
            "fat_g": None, "carb_g": None, "confidence": "none",
            "method": f"exception:{type(e).__name__}", "unmatched": True,
        }


def write_csv(out_path: Path, ingredients: list[tuple[str, int]],
              results: dict[str, dict]) -> None:
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        for name, occ in ingredients:
            r = results.get(name.lower(), {})
            w.writerow({
                "ingredient": name,
                "occurrences": occ,
                "fdc_id": r.get("fdc_id"),
                "matched_description": r.get("matched_description"),
                "source": r.get("source"),
                "energy_kcal": r.get("energy_kcal"),
                "protein_g": r.get("protein_g"),
                "fat_g": r.get("fat_g"),
                "carb_g": r.get("carb_g"),
                "confidence": r.get("confidence"),
                "method": r.get("method"),
                "unmatched": r.get("unmatched", True),
            })


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipes", default=str(DEFAULT_RECIPES),
                   help=f"recipes JSONL (default: {DEFAULT_RECIPES.name})")
    p.add_argument("--out", default=str(DEFAULT_OUT),
                   help="output CSV path (default: ingredient_fdc_table.csv)")
    p.add_argument("--concurrency", type=int, default=20,
                   help="max concurrent LLM calls (default: 20)")
    args = p.parse_args()

    api_key = load_api_key()
    print(f"loading {args.recipes} ...")
    ingredients = collect_unique_ingredients(Path(args.recipes))

    print("warming model + embedding index + macro table + cache ...")
    fdc_matcher.warm()

    print(f"matching with concurrency={args.concurrency} ...")
    results: dict[str, dict] = {}
    t0 = last = time.time()
    n_done = n_ok = n_unmatched = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(match_one, name, api_key): name
                for name, _ in ingredients}
        for fut in as_completed(futs):
            name = futs[fut]
            r = fut.result()
            results[name.lower()] = r
            n_done += 1
            if r.get("unmatched"):
                n_unmatched += 1
            else:
                n_ok += 1
            # Periodic cache flush so a killed long run stays resumable —
            # a re-run skips every ingredient already in the cache.
            if n_done % 250 == 0:
                fdc_matcher.save_cache()
            if time.time() - last > 5:
                el = time.time() - t0
                rate = n_done / el if el else 0
                eta = (len(futs) - n_done) / rate if rate else 0
                print(f"  {n_done:>5d}/{len(futs)}  ({n_ok} ok, "
                      f"{n_unmatched} unmatched)  rate={rate:.1f}/s  "
                      f"eta={eta:.0f}s", flush=True)
                last = time.time()

    fdc_matcher.save_cache()
    print(f"\ndone in {time.time() - t0:.0f}s "
          f"({n_ok} matched, {n_unmatched} unmatched)")

    out_path = Path(args.out)
    write_csv(out_path, ingredients, results)
    print(f"wrote {out_path}  ({len(ingredients):,} unique ingredients)")

    # Coverage weighted by how often each ingredient appears.
    total_occ = sum(occ for _, occ in ingredients)
    matched_occ = sum(occ for nm, occ in ingredients
                      if not results.get(nm.lower(), {}).get("unmatched", True))
    print(f"  occurrence-weighted match rate: "
          f"{matched_occ / total_occ:.1%}  ({matched_occ:,}/{total_occ:,})")


if __name__ == "__main__":
    main()
