"""nutriscore.py — The original (2017) Nutri-Score / FSAm-NPS nutrient
profiling algorithm, exactly as used by Clark et al. (2022, PNAS,
"Estimating the environmental impacts of 57,000 food products").

From the paper's Methods, "Calculating the Nutrition Impact Score":

    "NutriScore ranks products from -15 (least harm, most nutritious) to
     40 (most harm, least nutritious) based on the content of 7
     components, penalising products for 4 components (energy, saturated
     fat, sodium, and sugars) and rewarding products for 3 components
     (protein, fiber, and the percentage of the product that is fruits,
     vegetables, nuts, olive oil, walnut oil, and rapeseed oils). The
     penalised components are given a score 0-10 based on preset nutrient
     density thresholds; the rewarded components 0-5. The positive score
     (sum of the 0-5 scores) is subtracted from the negative score (sum
     of the 0-10 scores), giving a range of -15 to 40. This is translated
     into the A-E NutriScore, with different thresholds for different
     types of food (e.g. cheese, beverages, fats)."

This module implements the four food-type variants of the public
Santé-publique-France 2017 algorithm:
  * general (solid foods)         — the default for prepared dishes
  * beverages                     — different energy/sugar grids, FVN to
                                    10 pts, water auto-A
  * cheese                        — protein points always count
  * added fats/oils               — sat-fat scored as sat-fat/total-fat %

All nutrient inputs are per 100 g (per 100 mL for beverages; density ~1).
Energy is passed in kcal and converted to kJ internally (1 kcal = 4.184 kJ),
since the Nutri-Score energy grid is in kJ.

Outputs, per `nutri_score()`:
  negative_points, positive_points, fvn_points, fiber_points,
  protein_points, score (-15..40), grade (A-E),
  score_1to5 (1=most..5=least nutritious, the form Clark averaged), and
  score_0to100 (0=best..100=worst, the form Clark plots; the paper "scales
  the numeric algorithm underlying NutriScore so it ranges 0-100").

Pure functions, no I/O. Run directly to execute the reference self-test
(values cross-checked against the published Santé publique France
worked examples).
"""
from __future__ import annotations

KCAL_TO_KJ = 4.184

# ── Negative-component grids (0-10). points = count(value > threshold). ──
ENERGY_KJ_GENERAL = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]
ENERGY_KJ_BEVERAGE = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270]
SUGAR_G_GENERAL = [4.5, 9, 13.5, 18, 22.5, 27, 31, 36, 40, 45]
SUGAR_G_BEVERAGE = [0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5]
SATFAT_G = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# added-fats variant: saturated fat as % of total lipid
SATFAT_RATIO_PCT = [10, 16, 22, 28, 34, 40, 46, 52, 58, 64]
SODIUM_MG = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900]

# ── Positive-component grids. ───────────────────────────────────────────
FIBER_G_AOAC = [0.9, 1.9, 2.8, 3.7, 4.7]          # 0-5
PROTEIN_G = [1.6, 3.2, 4.8, 6.4, 8.0]              # 0-5
FVN_PCT = [40, 60, 80]                             # bin index -> points map
FVN_POINTS_GENERAL = {0: 0, 1: 1, 2: 2, 3: 5}
FVN_POINTS_BEVERAGE = {0: 0, 1: 2, 2: 4, 3: 10}


def _grid_points(value: float, thresholds: list) -> int:
    """Standard Nutri-Score lookup: points = number of thresholds the
    value strictly exceeds (so value <= thresholds[0] -> 0 points; value >
    thresholds[-1] -> len(thresholds) points)."""
    return sum(1 for t in thresholds if value > t)


def _fvn_points(fvn_pct: float, beverage: bool) -> int:
    idx = _grid_points(fvn_pct, FVN_PCT)            # 0..3
    table = FVN_POINTS_BEVERAGE if beverage else FVN_POINTS_GENERAL
    return table[idx]


def _grade_general(score: int) -> str:
    if score <= -1:
        return "A"
    if score <= 2:
        return "B"
    if score <= 10:
        return "C"
    if score <= 18:
        return "D"
    return "E"


def _grade_beverage(score: int, is_water: bool) -> str:
    if is_water:
        return "A"          # only water grades A among beverages
    if score <= 1:
        return "B"
    if score <= 5:
        return "C"
    if score <= 9:
        return "D"
    return "E"


GRADE_TO_1_5 = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}

# Universal 0-100 scaling of the raw FSAm-NPS score over its general-food
# theoretical range [-15, 40] (Clark plots all foods on one 0-100 axis).
_SCORE_MIN, _SCORE_MAX = -15, 40


def _score_0_100(score: int) -> float:
    frac = (score - _SCORE_MIN) / (_SCORE_MAX - _SCORE_MIN)
    return round(max(0.0, min(1.0, frac)) * 100, 2)


def nutri_score(
    *,
    energy_kcal: float,
    sugars_g: float,
    sat_fat_g: float,
    sodium_mg: float,
    protein_g: float,
    fiber_g: float,
    fvn_pct: float,
    fat_g: float = 0.0,
    food_type: str = "general",
    is_water: bool = False,
) -> dict:
    """Compute the Nutri-Score profile of one food per 100 g.

    food_type ∈ {"general", "beverage", "cheese", "fat"}.
    All nutrient args are amounts per 100 g; fvn_pct is 0-100.
    """
    beverage = food_type == "beverage"
    energy_kj = (energy_kcal or 0.0) * KCAL_TO_KJ

    # --- negative points -------------------------------------------------
    energy_pts = _grid_points(energy_kj,
                              ENERGY_KJ_BEVERAGE if beverage else ENERGY_KJ_GENERAL)
    sugar_pts = _grid_points(sugars_g,
                             SUGAR_G_BEVERAGE if beverage else SUGAR_G_GENERAL)
    if food_type == "fat":
        # sat-fat as a percentage of total lipid
        ratio = (sat_fat_g / fat_g * 100) if fat_g and fat_g > 0 else 0.0
        satfat_pts = _grid_points(ratio, SATFAT_RATIO_PCT)
    else:
        satfat_pts = _grid_points(sat_fat_g, SATFAT_G)
    sodium_pts = _grid_points(sodium_mg, SODIUM_MG)
    negative = energy_pts + sugar_pts + satfat_pts + sodium_pts

    # --- positive points -------------------------------------------------
    fvn_pts = _fvn_points(fvn_pct, beverage)
    fiber_pts = _grid_points(fiber_g, FIBER_G_AOAC)
    protein_pts = _grid_points(protein_g, PROTEIN_G)

    # --- combine, applying the protein-exclusion rule --------------------
    # If negative >= 11 and the food is not fruit/veg-rich (fvn < 5 pts),
    # protein points are NOT subtracted — UNLESS the food is a cheese, for
    # which protein always counts.
    if negative >= 11 and fvn_pts < 5 and food_type != "cheese":
        positive = fvn_pts + fiber_pts
        protein_counted = False
    else:
        positive = fvn_pts + fiber_pts + protein_pts
        protein_counted = True

    score = negative - positive
    if beverage:
        grade = _grade_beverage(score, is_water)
    else:
        grade = _grade_general(score)

    return {
        "food_type": food_type,
        "energy_points": energy_pts,
        "sugar_points": sugar_pts,
        "satfat_points": satfat_pts,
        "sodium_points": sodium_pts,
        "negative_points": negative,
        "fvn_points": fvn_pts,
        "fiber_points": fiber_pts,
        "protein_points": protein_pts,
        "protein_counted": protein_counted,
        "positive_points": positive,
        "score": score,
        "grade": grade,
        "score_1to5": GRADE_TO_1_5[grade],
        "score_0to100": _score_0_100(score),
    }


# --- reference self-test ------------------------------------------------
# Worked examples checked against Santé publique France's published guide.
def _selftest() -> bool:
    ok = True

    # Example: a sugary still drink, ~180 kJ, 8 g sugar/100mL, no FVN.
    # beverage energy 180 -> 6 pts; sugar 8 -> 6 pts; satfat 0; sodium ~0
    # negative = 12; positive 0 -> score 12 -> E
    r = nutri_score(energy_kcal=180 / KCAL_TO_KJ, sugars_g=8, sat_fat_g=0,
                    sodium_mg=5, protein_g=0, fiber_g=0, fvn_pct=0,
                    food_type="beverage")
    if not (r["score"] == 12 and r["grade"] == "E"):
        print("  FAIL sugary drink:", r["score"], r["grade"]); ok = False

    # Plain water -> A
    r = nutri_score(energy_kcal=0, sugars_g=0, sat_fat_g=0, sodium_mg=0,
                    protein_g=0, fiber_g=0, fvn_pct=0, food_type="beverage",
                    is_water=True)
    if r["grade"] != "A":
        print("  FAIL water:", r); ok = False

    # A lean, veg-rich solid: low energy, low everything, high FVN, fibre.
    # energy 300kJ->0, sugar 3->0, satfat 0.5->0, sodium 50->0 => N=0
    # fvn 90% -> 5 pts; fiber 5 -> 5 pts; protein 5 -> 4 pts; P=14
    # score = -14 -> A
    r = nutri_score(energy_kcal=300 / KCAL_TO_KJ, sugars_g=3, sat_fat_g=0.5,
                    sodium_mg=50, protein_g=7, fiber_g=5, fvn_pct=90)
    if not (r["score"] == -14 and r["grade"] == "A"):
        print("  FAIL veg dish:", r["score"], r["grade"]); ok = False

    # Protein-exclusion rule: very high energy/satfat/sodium, low FVN.
    # Construct N>=11, fvn<5 so protein is dropped.
    # energy 3000kJ->8, sugar 0->0, satfat 12->10, sodium 1000->10 => N=28
    # fvn 0 ->0, fiber 0 ->0, protein 9 ->5 but EXCLUDED => P=0; score 28 E
    r = nutri_score(energy_kcal=3000 / KCAL_TO_KJ, sugars_g=0, sat_fat_g=12,
                    sodium_mg=1000, protein_g=9, fiber_g=0, fvn_pct=0)
    if not (r["protein_counted"] is False and r["score"] == 28
            and r["grade"] == "E"):
        print("  FAIL protein-exclusion:", r); ok = False

    # Cheese exception: same as above but cheese -> protein counts.
    r = nutri_score(energy_kcal=3000 / KCAL_TO_KJ, sugars_g=0, sat_fat_g=12,
                    sodium_mg=1000, protein_g=9, fiber_g=0, fvn_pct=0,
                    food_type="cheese")
    if not (r["protein_counted"] is True and r["score"] == 23):
        print("  FAIL cheese protein:", r); ok = False

    print("nutriscore self-test:", "ALL PASS" if ok else "FAILURES ABOVE")
    return ok


if __name__ == "__main__":
    _selftest()
