# Mexican-small category proposals (fajita / fajitas / flauta / flautas / empanada / empanadas / nachos)

Scanned 2,612 canonicals containing any target token in `dish_canonical_summary_v17.csv`. Reviewed top ~150 by `total_count`. Followed `clean_quesadillas.py` precedent.

## High-confidence merges (Spanish→English / article omission / plural)
17 clusters collapse into 9 destination clusters:

- Fajita protein duplicates → `chicken fajita` (698): cids 26450 `de fajitas pollo` (116), 2880 `fajita pollo` (19).
- Fajita protein duplicates → `beef fajita` (815): cids 27480 `de fajitas res` (26), 28096 `carne de fajita` (25), 7024 `carne fajita` (4), 132669 `beef de fajitas res` (8).
- 3162 `camarones fajita` (26) → 715 `fajita shrimp`.
- Nachos protein → `chicken nachos` (1052): cids 4229 `nachos pollo` (12), 30331 `de nachos pollo` (11).
- 2399 `nachos supremos` (23) → 1155 `nachos supreme` (Spanish plural→English).
- 25886 `de flautas pollo` (154) → 871 `chicken flautas`.
- Empanada chicken → `chicken empanada` (2054): cids 28302 `de empanada pollo` (23), 5198 `empanada pollo` (8).
- Empanada beef → `beef empanada` (2578): cids 30315 `carne de empanada` (14), 33345 `de empanada res` (9).
- 8938 `camarones empanada` (5) → 5578 `empanada shrimp`.

## Medium confidence
- 31844 `de empanada queso` (12) → 4519 `empanada queso` (article omission only; both stay Spanish-form because no English `cheese empanada` base cluster exists).
- 1903 `fajita vegetable` (73) and 1365 `fajita vegetarian` (172) → 1121 `fajita veggie` (synonym, per quesadilla precedent cid 1743/1444).

## Renames (plural→singular, no merge target)
- 31170 `beef fajitas lb` (14) → `beef fajita lb`. Singular sibling `chicken fajita lb` (cid 31171) exists; 6 of 14 raw aliases already use singular form.

## Judgment / NOT merging (flagged)
- 26566 `asada carne fajita` (61): carne asada is a specific cut/preparation, not generic beef fajita.
- 90831 `carne de fajita pollo` (16): aliases reveal `carne O pollo` combo plate — keep separate.
- 27852 `carne con nachos` (19): "carne" unmodified is ambiguous; conservatively keep.
- 1029 `loaded nachos`, 1174 `nachos super`, 1280 `nachos ultimate`, 2460 `deluxe nachos`: per playbook, marketing/loaded labels are NOT merged into `nachos supreme`.
- 84973 `beef ground nachos seasoned` (48) vs 25889 `beef ground nachos` (143): "seasoned" is descriptive, borderline filler — kept per playbook (no `regular`/`classic` style merges).
- 3677 `empanada pechuga` (11): pechuga = chicken breast (specific cut) vs generic chicken empanada — flagged for human review.

## Counts
- 17 high-confidence merges + 3 medium-confidence merges = 20 merges proposed.
- 1 plural→singular rename.
- 7 judgment-only rows for human review.
