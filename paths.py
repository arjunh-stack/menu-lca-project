"""Repo-root anchor + canonical data-file location map.

This module is the single source of truth for *where every Stage-1 data
file lives* after the directory reorg. Every Stage-1 script resolves its
data files through `dpath("<file>")`, which locates the file relative to
*this* file's directory rather than via any hardcoded absolute path.
That removes the last hardcoded-absolute-path reproducibility gap: clone
anywhere, run from anywhere, and paths still resolve.

`paths.py` lives at the repo root and is also the sentinel scripts walk
up to find the root (see the bootstrap header in each script).

Layout
------
  <root>/                    docs, config, build_dish_index.py, dedup.py,
                             mydb.sqlite, menu_dishes.{sqlite,csv}
  <root>/stage1/snapshots/   versioned alias chain + frozen Layer-10 input
  <root>/stage1/frozen/      non-deterministic LLM verdicts (replay inputs)
  <root>/stage1/intermediate/ deterministic outputs / audit / scratch
  <root>/stage1/scripts/     the pipeline-layer scripts
  <root>/stage1/investigation/ trace / test / plot one-offs
  <root>/logs/               run logs
  <root>/chunks*/, proposals/  unchanged (frozen LLM verdicts, see
                             .gitignore note — kept at root by design)
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

SNAPSHOTS    = os.path.join(ROOT, "stage1", "snapshots")
FROZEN       = os.path.join(ROOT, "stage1", "frozen")
INTERMEDIATE = os.path.join(ROOT, "stage1", "intermediate")
SCRIPTS      = os.path.join(ROOT, "stage1", "scripts")
INVESTIGATION = os.path.join(ROOT, "stage1", "investigation")
LOGS         = os.path.join(ROOT, "logs")

# ── Data-file → bucket map ────────────────────────────────────────────
# Exact basenames take priority; then longest matching prefix. A name
# that matches nothing here stays at the repo root (covers mydb.sqlite,
# menu_dishes.*, .env.openrouter, and every path that points into an
# unchanged dir such as chunks*/, proposals/, recipes/, lca/, docs/).

_EXACT: dict[str, str] = {}
_PREFIX: list[tuple[str, str]] = []  # (prefix, bucket), checked longest-first


def _reg_exact(bucket: str, *names: str) -> None:
    for n in names:
        _EXACT[n] = bucket


def _reg_prefix(bucket: str, *prefixes: str) -> None:
    for p in prefixes:
        _PREFIX.append((p, bucket))


# snapshots — the replayable versioned alias chain + frozen L10 input
_reg_exact(
    SNAPSHOTS,
    "dish_aliases.csv", "dish_canonical_summary.csv",
    "synonyms.csv", "synonym_merges.csv", "synonym_validation.csv",
)
_reg_prefix(SNAPSHOTS, "dish_aliases_v", "dish_canonical_summary_v")

# frozen — non-deterministic LLM verdicts replayed by apply_*.py
_reg_exact(
    FROZEN,
    "candidate_judgments.csv", "candidate_judgments_v2.csv",
    "llm_merges_applied.csv", "llm_merges_applied_v2.csv",
    "sub_sandwich_judgments.csv", "sub_sandwich_merges_applied.csv",
    "long_singleton_judgments.csv",
    "recipe_screen_gemini.csv", "recipe_screen_deepseek.csv",
    "recipe_screen_deepseek_keeps.csv",
    "recipe_screen_deepseek_keeps_missing.csv",
    "recipe_drops_applied.csv",
    "dish_rescue_judgments.csv", "dish_rescue_decisions.json",
    "dish_rescue_data.json",
    "dish_review_decisions.json", "dish_review_data.json",
    "dish_review.html",
    "category_canonical_mapping.csv", "menu_category_canonical_mapping.csv",
    "review_classified_merged.csv",
)
_reg_prefix(FROZEN, "recipe_screen_deepseek_keeps_shard")

# intermediate — deterministic outputs / audit / scratch
_reg_exact(
    INTERMEDIATE,
    "category_changes.csv", "chain_marketing_changes.csv",
    "doubled_token_changes.csv", "quesadilla_changes.csv",
    "single_letter_changes.csv",
    "merge_candidates.csv", "merge_candidates_v2.csv",
    "sub_sandwich_candidates.csv", "long_singleton_flags.csv",
    "recipe_screen_compare.csv", "recipe_screen_compare_v2.csv",
    "recipe_screen_review_samples.md", "recipe_screen_review_v2.md",
    "ingredients_and_numbers_review.csv",
    "unique_categories.csv", "unique_categories_to_exclude.csv",
    "proposed_menu_category_excludes.csv",
    "proposed_menu_category_ambiguous.csv",
    "restaurants_filtered.csv", "candidate_judgments.csv.bak",
    "dish_distribution.png", "price_distribution.png",
)
_reg_prefix(INTERMEDIATE, "dropped_", "unique_dishes")

_PREFIX.sort(key=lambda kv: -len(kv[0]))  # longest prefix wins


def bucket_for(name: str) -> str | None:
    """Return the absolute bucket dir for a bare *basename*, or None if
    the file stays at the repo root. `name` must have no path separator."""
    if name in _EXACT:
        return _EXACT[name]
    for prefix, bucket in _PREFIX:
        if name.startswith(prefix):
            return bucket
    return None


def dpath(rel: str) -> str:
    """Resolve a repo-relative reference to its real absolute path.

    `rel` is whatever followed the old hardcoded
    `.../menu-item-impact/` prefix — usually a bare data-file basename,
    sometimes a path into an unchanged dir (e.g. ``recipes/dish_context.csv``
    or ``chunks/chunk_01.csv``). Files that moved resolve into their
    stage1 bucket; everything else resolves under the repo root."""
    rel = rel.lstrip("/")
    if "/" not in rel:
        bucket = bucket_for(rel)
        if bucket is not None:
            return os.path.join(bucket, rel)
    return os.path.join(ROOT, rel)


if __name__ == "__main__":
    # Quick audit: print the resolved map for review.
    print(f"ROOT = {ROOT}")
    for label, d in [
        ("SNAPSHOTS", SNAPSHOTS), ("FROZEN", FROZEN),
        ("INTERMEDIATE", INTERMEDIATE), ("SCRIPTS", SCRIPTS),
        ("INVESTIGATION", INVESTIGATION), ("LOGS", LOGS),
    ]:
        print(f"{label:14s} = {d}")
