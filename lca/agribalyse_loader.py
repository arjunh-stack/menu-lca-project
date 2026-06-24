"""AGRIBALYSE loader — merges agriculture+processing CO2e from
agribalyse_detail_etape.csv into agribalyse_synthese.csv.

Cradle-to-farm-gate scope (D3): ag+processing only, no packaging/transport/
retail/consumer-use. Avoids double-counting if/when stage adders are
introduced downstream.

Ported verbatim from ../reverse-recipe/data/agribalyse_loader.py.
"""

import os
import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "agribalyse")
_SYNTHESE_CSV = os.path.join(_DATA_DIR, "agribalyse_synthese.csv")
_DETAIL_CSV = os.path.join(_DATA_DIR, "agribalyse_detail_etape.csv")

_COL_AG = "Changement climatique - Agriculture"
_COL_PROC = "Changement climatique - Transformation"

COL_CO2E_AG_PROC = "co2e_ag_proc"
COL_CO2E_TOTAL = "Changement climatique"

_df_cache: pd.DataFrame | None = None


def load_agribalyse() -> pd.DataFrame:
    """Load AGRIBALYSE synthese with merged ag+processing CO2e column.

    Returns DataFrame with all original synthese columns plus
    'co2e_ag_proc' (kg CO2e / kg, cradle-to-farm-gate scope).
    """
    global _df_cache
    if _df_cache is not None:
        return _df_cache

    if not os.path.exists(_SYNTHESE_CSV):
        _df_cache = pd.DataFrame()
        return _df_cache

    df = pd.read_csv(_SYNTHESE_CSV)

    if os.path.exists(_DETAIL_CSV):
        detail = pd.read_csv(_DETAIL_CSV, low_memory=False,
                             usecols=["LCI Name", _COL_AG, _COL_PROC])
        detail[_COL_AG] = pd.to_numeric(detail[_COL_AG], errors="coerce").fillna(0)
        detail[_COL_PROC] = pd.to_numeric(detail[_COL_PROC], errors="coerce").fillna(0)
        detail[COL_CO2E_AG_PROC] = detail[_COL_AG] + detail[_COL_PROC]
        detail = detail.drop_duplicates(subset="LCI Name", keep="first")

        df = df.merge(
            detail[["LCI Name", COL_CO2E_AG_PROC]],
            on="LCI Name",
            how="left",
        )
        df[COL_CO2E_AG_PROC] = df[COL_CO2E_AG_PROC].fillna(df[COL_CO2E_TOTAL])
    else:
        df[COL_CO2E_AG_PROC] = df[COL_CO2E_TOTAL]

    _df_cache = df
    return _df_cache
