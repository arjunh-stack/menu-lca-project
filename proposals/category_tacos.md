# Taco category cleanup proposals

Scanned all 5,490 canonicals containing the token `taco` or `tacos` in `dish_canonical_summary_v17.csv`. Sampled the top ~300 by count and pattern-scanned the rest for known playbook patterns.

## Summary counts

- **Merges (high confidence):** 48
- **Merges (judgment):** 1
- **Renames (high confidence):** 23
- **Renames (judgment):** 1
- **Total proposals:** 73

## Top 5 merges by source count

1. `de pollo taco` (102) → `chicken taco` (655) — Spanish→English: pollo = chicken
2. `de pescado tacos` (166) → `fish taco` (951) — Spanish→English + 'de' + plural
3. `pollo taco` (134) → `chicken taco` (655) — Spanish→English
4. `carnitas de taco` (122) → `carnitas taco` (505) — 'de' preposition drop
5. `asada carne de taco` (114) → `asada carne taco` (347) — 'de' preposition drop (already alphabetized form of `taco de carne asada`)

## Patterns observed

- **Spanish→English protein/ingredient translations:** pollo→chicken, pescado→fish, camaron(es)→shrimp, aguacate→avocado, frijoles→bean, papa→potato, puerco→pork, queso→cheese, huevo→egg, jamon→ham. ~21 merges.
- **Spanish 'de' preposition drops:** very heavy in this category. `X de taco` / `de X taco` are token-sorted variants of `taco de X` and should collapse onto plain `X taco`. ~14 merges.
- **'al pastor' vs 'pastor':** article omission. Merged `pastor taco`, `de pastor taco`, and `al order pastor taco` into `al pastor taco`.
- **Filler 'style':** merged `al pastor street style taco` into `al pastor street taco`.
- **Plural→singular:** 23 plural canonicals where no singular sibling exists (e.g., `breakfast tacos`, `al carbon tacos`, `shrimp spicy tacos`, `chicken ranchero tacos`, `baja fish tacos`). One special case (`mahi mahi tacos`) merged into `mahi taco` since `mahi` and `mahi mahi` are equivalent.
- **English/Spanish offal duplicates:** `taco tongue`, `beef taco tongue`, and `de lengua taco tongue` merged into `lengua taco` (the established higher-count term).

## Judgment / risky items held back

- **`carne de taco` (cid 29457, count 20):** `carne` alone is ambiguous — could be plain beef OR shorthand for `carne asada`. Renamed to drop `de` only, NOT merged into either `beef taco` or `asada carne taco`.
- **`fish shrimp taco` (9):** ambiguous — could mean a combo platter or either-or. Tentatively merged into `shrimp taco` but flagged judgment.
- **`asado pollo taco` (49), `guisado pollo taco` (17):** distinct cooking methods (`asado` = roasted, `guisado` = stewed). Kept separate.
- **`picadillo taco` vs `beef ground taco`:** picadillo is a specific seasoned-hash style, not just ground beef. Kept separate.
- **`papa taco` vs `potato taco` vs `de papa tacos`:** papa→potato handled, but other compound forms left for later.
- **`nopales` vs `nopalitos`:** different size of cactus paddle, regionally distinct words. Kept separate.
- **`bf` (buffalo) abbreviation:** present (10+ clusters at low counts) but always combined with breakfast tokens (`bf chorizo egg`) — context suggests `bf` here means "breakfast", not "buffalo". Held back; needs clarification.
- **`queso shrimpico taco` (45):** unusual artifact, possibly a real menu name. Not touched.
- **`huevos rancheros taco`, `chorizo con huevo taco` etc.:** `con huevo` and `huevo` patterns abundant; only handled the simplest two cases (`huevo taco`, `chorizo huevo taco`). Many `con huevo X taco` variants left untouched to avoid over-merging breakfast composites.
