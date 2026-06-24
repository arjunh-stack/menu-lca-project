"""ISO 14044 pedigree-matrix data quality scoring.

Ported from ../reverse-recipe/data_quality/pedigree.py with minimal
changes: same five Weidema & Wesnæs indicators, same A–F letter-grade
bins. Source-database list (AGRIBALYSE, SU-EATABLE, Poore) matches our
matcher's source-of-truth (lca/matcher.py + ef_cache.json).

Public API:
    score_ingredient(ingredient: dict) -> dict
    score_product(ingredients: list[dict]) -> dict

The ingredient dict shape expected:
    name: str
    confidence: "high" | "medium" | "low" | "very_low"
    method: str   (e.g. "hybrid_query_expansion_wider_uncertainty")
    n_matches: int
    source: str   (the cache's source_description with DB names embedded)
    co2e: float   (recommended GHG EF, used as CO2e-weight in product avg)
"""
from __future__ import annotations

import re
from typing import Any


# Database-quality metadata. Lower number = better.
_DB_COMPLETENESS: dict[str, int] = {
    "AGRIBALYSE":  1,   # ~15k products, well sampled
    "SU-EATABLE":  2,   # 324 products, meta-analysis of 841 publications
    "Poore":       2,   # 1530-study meta-analysis, 38,700 farms
}

_DB_TEMPORAL: dict[str, int] = {
    "AGRIBALYSE":  1,   # v3.2, 2023
    "SU-EATABLE":  2,   # 2020
    "Poore":       2,   # 2018
}

_DB_GEOGRAPHIC: dict[str, int] = {
    "AGRIBALYSE":  3,   # France-centric; we apply it to US dishes (R3 boundary)
    "SU-EATABLE":  2,   # global meta-analysis
    "Poore":       2,   # global meta-analysis
}

_DB_PATTERNS: list[tuple[str, str]] = [
    (r"AGRIBALYSE", "AGRIBALYSE"),
    (r"SU-EATABLE", "SU-EATABLE"),
    (r"Poore",      "Poore"),
]


def _parse_sources(source_str: str) -> list[str]:
    """Extract recognised database keys from a source description string."""
    found: list[str] = []
    for pattern, key in _DB_PATTERNS:
        if re.search(pattern, source_str, re.IGNORECASE):
            found.append(key)
    return found


def _score_reliability(confidence: str, method: str, n_matches: int,
                      sources: list[str]) -> int:
    """Score 1-5 based on how the data was obtained."""
    n_sources = len(sources)
    if n_sources >= 3:
        return 1
    if n_sources == 2:
        return 2
    if n_sources == 1:
        return 3
    if "llm" in method.lower() or "reasoning" in method.lower():
        return 4
    return 5


def _score_completeness(sources: list[str], method: str) -> int:
    if not sources:
        return 5 if "llm" in method.lower() else 4
    return min(_DB_COMPLETENESS.get(s, 4) for s in sources)


def _score_temporal(sources: list[str], method: str) -> int:
    if not sources:
        return 4 if "llm" in method.lower() else 5
    return min(_DB_TEMPORAL.get(s, 4) for s in sources)


def _score_geographic(sources: list[str], method: str) -> int:
    """Geographic match. Assumes US consumer (R3 of top-level PLAN)."""
    if not sources:
        return 5
    return min(_DB_GEOGRAPHIC.get(s, 4) for s in sources)


def _score_technological(confidence: str, method: str, n_matches: int) -> int:
    """How well the matched LCI represents the actual ingredient."""
    if confidence == "high" and n_matches >= 3:
        return 1
    if confidence == "high":
        return 2
    if confidence == "medium":
        return 3
    if "llm" in method.lower():
        return 4
    return 5


def _average(*scores: int) -> float:
    return sum(scores) / len(scores)


def _letter_grade(score: float) -> str:
    if score <= 1.5: return "A"
    if score <= 2.5: return "B"
    if score <= 3.5: return "C"
    if score <= 4.5: return "D"
    return "F"


def score_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    name = ingredient["name"]
    confidence = ingredient.get("confidence") or "low"
    method = ingredient.get("method") or ""
    n_matches = ingredient.get("n_matches", 0) or 0
    source_str = ingredient.get("source") or ""

    sources = _parse_sources(source_str)

    reliability   = _score_reliability(confidence, method, n_matches, sources)
    completeness  = _score_completeness(sources, method)
    temporal      = _score_temporal(sources, method)
    geographic    = _score_geographic(sources, method)
    technological = _score_technological(confidence, method, n_matches)

    avg = _average(reliability, completeness, temporal, geographic, technological)

    return {
        "name": name,
        "reliability":   reliability,
        "completeness":  completeness,
        "temporal":      temporal,
        "geographic":    geographic,
        "technological": technological,
        "average": round(avg, 2),
        "grade":   _letter_grade(avg),
        "sources_detected": sources,
    }


def score_product(ingredients: list[dict[str, Any]]) -> dict[str, Any]:
    """CO2e-weighted product-level pedigree. Returns overall grade + gaps."""
    if not ingredients:
        return {
            "overall_grade": "F",
            "overall_score": 5.0,
            "per_ingredient": [],
            "data_gaps": [],
        }

    per_ingredient = [score_ingredient(ing) for ing in ingredients]

    # Weighted average by CO2e contribution (the ingredient that drives the
    # impact deserves the most weight in the overall data-quality score).
    total_co2e = sum(ing.get("co2e", 0.0) or 0.0 for ing in ingredients)
    if total_co2e > 0:
        weighted_sum = sum(
            pi["average"] * (ing.get("co2e", 0.0) or 0.0)
            for pi, ing in zip(per_ingredient, ingredients)
        )
        overall = weighted_sum / total_co2e
    else:
        overall = sum(pi["average"] for pi in per_ingredient) / len(per_ingredient)

    data_gaps: list[dict[str, Any]] = []
    for pi, ing in zip(per_ingredient, ingredients):
        if pi["grade"] in ("D", "F"):
            pct = (round(100 * (ing.get("co2e", 0.0) or 0.0) / total_co2e, 1)
                   if total_co2e > 0 else 0.0)
            data_gaps.append({
                "ingredient": pi["name"],
                "grade": pi["grade"],
                "co2e_share_pct": pct,
            })

    return {
        "overall_grade": _letter_grade(overall),
        "overall_score": round(overall, 2),
        "per_ingredient": per_ingredient,
        "data_gaps": data_gaps,
    }
