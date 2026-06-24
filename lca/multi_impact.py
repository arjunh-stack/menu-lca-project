"""Multi-impact lookup against AGRIBALYSE by LCI Name.

Given an AGRIBALYSE 'LCI Name' (the string returned as
`matched_lci_name` from matcher.match_ingredient), return all impact
categories: climate change, water use, land use, eutrophication,
acidification, etc.

Slim port of ../reverse-recipe/impact_categories/multi_impact.py. The
underlying CSV columns are French; this module exposes English keys.

Scope note (D3): AGRIBALYSE's per-category values are cradle-to-retail
in synthese, while the climate_change values in `aggregate_recipe`
intentionally use the ag+processing-only column (`co2e_ag_proc`, via
agribalyse_loader) to stay cradle-to-farm-gate for the headline GHG
number. Water and land use are reported as-is from synthese because
AGRIBALYSE doesn't publish per-stage water/land breakdowns — these
include consumer-side ratios that are small for most ingredients.
Flagged as a v1 limitation in PLAN.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from agribalyse_loader import load_agribalyse, COL_CO2E_AG_PROC  # type: ignore  # noqa: E402

# ── French → English column mapping ─────────────────────────────────────

IMPACT_COLUMN_MAP: dict[str, str] = {
    "Changement climatique": "climate_change",
    "Appauvrissement de la couche d'ozone": "ozone_depletion",
    "Rayonnements ionisants": "ionizing_radiation",
    "Formation photochimique d'ozone": "photochemical_ozone_formation",
    "Particules fines": "particulate_matter",
    "Effets toxicologiques sur la santé humaine : substances non-cancérogènes": "human_toxicity_non_carcinogenic",
    "Effets toxicologiques sur la santé humaine : substances cancérogènes": "human_toxicity_carcinogenic",
    "Acidification terrestre et eaux douces": "acidification",
    "Eutrophisation eaux douces": "eutrophication_freshwater",
    "Eutrophisation marine": "eutrophication_marine",
    "Eutrophisation terrestre": "eutrophication_terrestrial",
    "Écotoxicité pour écosystèmes aquatiques d'eau douce": "freshwater_ecotoxicity",
    "Utilisation du sol": "land_use",
    "Épuisement des ressources eau": "water_use",
    "Épuisement des ressources énergétiques": "resource_use_energy",
    "Épuisement des ressources minéraux": "resource_use_minerals",
}

IMPACT_UNITS: dict[str, str] = {
    "climate_change": "kg CO2 eq / kg",
    "ozone_depletion": "kg CFC-11 eq / kg",
    "ionizing_radiation": "kBq U235 eq / kg",
    "photochemical_ozone_formation": "kg NMVOC eq / kg",
    "particulate_matter": "disease incidence / kg",
    "human_toxicity_non_carcinogenic": "CTUh / kg",
    "human_toxicity_carcinogenic": "CTUh / kg",
    "acidification": "mol H+ eq / kg",
    "eutrophication_freshwater": "kg P eq / kg",
    "eutrophication_marine": "kg N eq / kg",
    "eutrophication_terrestrial": "mol N eq / kg",
    "freshwater_ecotoxicity": "CTUe / kg",
    "land_use": "Pt / kg",
    "water_use": "m³ world eq / kg",
    "resource_use_energy": "MJ / kg",
    "resource_use_minerals": "kg Sb eq / kg",
}

# Headline metrics this project actually consumes (kept tight on purpose).
HEADLINE_KEYS = ("climate_change", "water_use", "land_use",
                 "eutrophication_freshwater", "acidification")


def get_multi_impact(lci_name: str) -> dict[str, float] | None:
    """Return all impact categories for an AGRIBALYSE LCI Name.

    The `climate_change` value here is overridden with the
    cradle-to-farm-gate (ag+processing) value to stay consistent with
    the matcher's recommended EF.
    """
    df = load_agribalyse()
    row = df[df["LCI Name"].str.strip() == lci_name.strip()]
    if row.empty:
        return None
    row = row.iloc[0]

    impacts: dict[str, float] = {}
    for fr_col, en_key in IMPACT_COLUMN_MAP.items():
        val = row.get(fr_col)
        impacts[en_key] = float(val) if val is not None and pd.notna(val) else 0.0

    ag_proc = row.get(COL_CO2E_AG_PROC)
    if ag_proc is not None and pd.notna(ag_proc):
        impacts["climate_change"] = float(ag_proc)
    return impacts


def get_impact_with_units(lci_name: str) -> dict[str, dict] | None:
    impacts = get_multi_impact(lci_name)
    if impacts is None:
        return None
    return {k: {"value": v, "unit": IMPACT_UNITS.get(k, "?")} for k, v in impacts.items()}


def aggregate_recipe(ingredients: list[dict]) -> dict[str, float]:
    """Sum impacts across a recipe, weighted by mass.

    Parameters
    ----------
    ingredients : list of dict
        Each dict has keys 'lci_name' (str) and 'mass_kg' (float).
        Ingredients without an lci_name are skipped (not summed in).

    Returns
    -------
    dict[str, float]
        Per-category totals, keyed by English names. Categories where
        every ingredient is missing data sum to 0.0.
    """
    totals: dict[str, float] = {k: 0.0 for k in IMPACT_COLUMN_MAP.values()}
    for ing in ingredients:
        lci = ing.get("lci_name")
        if not lci:
            continue
        mass_kg = float(ing.get("mass_kg", 0.0))
        impacts = get_multi_impact(lci)
        if impacts is None:
            continue
        for k, v in impacts.items():
            totals[k] += mass_kg * v
    return totals
