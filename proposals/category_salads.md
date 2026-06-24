# Proposal P-salads (2026-05-03) — salad category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 1,703 canonicals containing whole-word token `salad` or `salads`.

**Method:** awk-filtered on whole-token match, sorted by `total_count` desc,
reviewed top ~250. Targeted greps for Spanish↔English pairs (`ensalada`/salad,
`pollo`/chicken, `mariscos`/seafood, `camaron`/shrimp, `aguacate`/avocado),
typos (`ceasar`/`cesar`→`caesar`, `cob`→`cobb`), filler `only`, plural→singular
gaps, synonym pairs (vegetable/vegetarian/veggie, garden vs house, chopped
cobb vs cobb), preparation modifiers, and dressing descriptors. Cross-checked
alias rows in `dish_aliases_v17.csv` for ambiguous candidates.

**Outputs:**
- `/proposals/category_salads.csv` — 5 merges + 9 judgment flags.
- `/proposals/category_salads.md` — this file.

**Rows touched if applied:**
- 5 merges → 4 destination clusters (`salad veggie`, `salad taco veggie`,
  `caesar chicken salad`, `salad seafood`).
- 0 plural→singular renames (all 6 `salads`-token canonicals were singletons
  with no singular sibling).
- 9 judgment flags surfaced for human review.

**Conservative carve-outs (explicitly NOT proposed):**
- `garden` vs `house salad` — playbook flags as judgment (garden potentially
  veggie-only; house potentially signature).
- `greek salad` kept distinct (specific dish per playbook).
- `chopped cobb salad` vs `cobb salad` — `chopped` is preparation modifier.
- `caesar classic salad` vs `caesar salad` — playbook excludes `classic`/
  `original` from filler-word merges.
- `caesar chicken salad` vs `caesar salad` — different protein.
- `bowl X salad` and `lunch X salad` not collapsed at canonical level.
- Different lettuce types (`arugula`, `romaine`, `kale`, `spinach`) kept
  separate.
- `gf`/`gluten free`/`gs` variants kept separate (dietary attribute).
- `vegan` NOT merged with `vegetarian`/`veggie`.
- `ahi` not merged with `tuna` (ahi = yellowfin specifically).
- Chain-branded caesar variants (`brisbane`, `sonoma`, `salanova`) kept
  distinct.
