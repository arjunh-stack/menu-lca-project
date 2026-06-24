"""Monte Carlo uncertainty propagation for per-recipe LCA totals.

Triangular over (ef_min, ef_recommended, ef_max) per ingredient,
normal over mass (default σ = 15 % of mean). Aggregates per simulation
and returns mean/median/std/p5/p25/p75/p95 plus per-ingredient variance
contribution.

Ported verbatim from
../reverse-recipe/uncertainty_propagation/monte_carlo.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class Ingredient:
    """Single ingredient: mass + EF uncertainty bounds (kg CO2e / kg).

    Used as input to monte_carlo_propagation. Generalizes cleanly to
    water/land impacts: just pass the per-impact (min, recommended, max)
    in place of CO2e bounds.
    """
    name: str
    mass_g: float
    ef_recommended: float
    ef_min: float
    ef_max: float


def monte_carlo_propagation(
    ingredients: Sequence[Ingredient],
    n_simulations: int = 10_000,
    mass_uncertainty_pct: float = 0.15,
    seed: int | None = None,
) -> dict:
    """Run Monte Carlo propagation and return summary statistics.

    Returns
    -------
    dict with: n_simulations, mean, median, std, p5, p25, p75, p95,
    ci_90, ci_95, histogram_data, per_ingredient_variance_contribution.

    Notes
    -----
    Mass distribution is normal(mean=mass_g, std=mass_uncertainty_pct*mass_g).
    Mass can technically go negative for high uncertainty / small means;
    no clipping is applied here (matches reverse-recipe behavior). For
    headline numbers this is negligible at the 15% default.
    """
    rng = np.random.default_rng(seed)
    n_ing = len(ingredients)
    samples = np.empty((n_simulations, n_ing))

    for i, ing in enumerate(ingredients):
        if ing.ef_min == ing.ef_max:
            ef = np.full(n_simulations, ing.ef_recommended)
        else:
            ef = rng.triangular(
                left=ing.ef_min,
                mode=ing.ef_recommended,
                right=ing.ef_max,
                size=n_simulations,
            )
        mass_std = ing.mass_g * mass_uncertainty_pct
        mass = rng.normal(loc=ing.mass_g, scale=mass_std, size=n_simulations)
        samples[:, i] = (mass / 1000.0) * ef

    totals = samples.sum(axis=1)
    p5, p25, p50, p75, p95 = np.percentile(totals, [5, 25, 50, 75, 95])
    p2_5, p97_5 = np.percentile(totals, [2.5, 97.5])

    total_var = float(np.var(totals, ddof=1))
    variance_contribution: dict[str, float] = {}
    for i, ing in enumerate(ingredients):
        ing_var = float(np.var(samples[:, i], ddof=1))
        variance_contribution[ing.name] = (
            ing_var / total_var if total_var > 0 else 0.0
        )

    return {
        "n_simulations": n_simulations,
        "mean": float(np.mean(totals)),
        "median": float(p50),
        "std": float(np.std(totals, ddof=1)),
        "p5": float(p5),
        "p25": float(p25),
        "p75": float(p75),
        "p95": float(p95),
        "ci_90": (float(p5), float(p95)),
        "ci_95": (float(p2_5), float(p97_5)),
        "per_ingredient_variance_contribution": variance_contribution,
    }
