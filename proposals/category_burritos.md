# Burrito Category Cleanup Proposal

## Scope

- **Canonicals scanned:** 2,974 clusters whose canonical_name contains `burrito` or `burritos` as a whitespace token (out of 114,855 total).
- **Reviewed in detail:** Top 100 by `total_count` plus targeted greps for every Spanish↔English / abbreviation / plural pattern in the playbook. Long tail sampled.
- **Proposed actions:** 20 merges, 2 plural→singular renames, 7 judgment flags.

## Top-5 burrito canonicals (by count)

| cid    | canonical                | count |
|--------|--------------------------|-------|
| 84393  | bean burrito cheesy rice | 2,088 |
| 25455  | burrito fiesta veggie    | 1,972 |
| 663    | bean burrito             | 1,595 |
| 130306 | burrito chicken chipotle grilled ranch | 1,316 |
| 25468  | beefy burrito melt       | 1,314 |

## Merge themes

- **Spanish↔English protein/ingredient:** pollo→chicken (1632, 27707), queso→cheese (7655, 27041), carne→beef (3633), frijoles→bean (11821, 33963), camaron(es)→shrimp (5743, 27614), pescado→fish (8261, 36543).
- **Synonym (veggie):** vegetarian (1077), vegetable (2401), vegi (4824) all collapse into `burrito veggie` (802).
- **Article/preposition:** `de` and `con` dropped where they're the only difference; `pastor`/`burrito de pastor` merge to `al burrito pastor` (25938), matching the quesadilla precedent.
- **Missing token:** `asada burrito` (1173) → `asada burrito carne` (25749), exact replay of the quesadilla layer.
- **Abbreviation:** `barbecue burrito` (5343) → `bbq burrito` (2980); `bf burrito chicken` (26512) → `buffalo burrito chicken` (33041), keeping the spelled-out English canonical even though bf had higher count (matches v16→v17 quesadilla precedent).

## Renames (plural→singular, no singular sibling)

- 33639 `beef burritos cheese` → `beef burrito cheese`.
- 33640 `beans beef burritos` → `bean beef burrito` (also normalizes plural noun `beans`→`bean`).

## Held back as judgment

- `asado burrito pollo` (27097, 36): could merge to `burrito chicken grilled` (26177) but `asado` ≠ `asada` and the preparation may be distinct.
- `beef bf burrito` (26532, 56): canonical mixes `beef` and `bf` — looks dirty; needs alias-level audit before any action.
- `burrito carne guisada` (27441) and `burrito carne de` (27923): `carne guisada` is its own dish (stewed beef); `carne de …` looks truncated.
- `beef burrito chicken or` (86219, 24): the literal token `or` suggests combo/alias artifact — review aliases.
- `burritos de plato` (38928), `burritos carne de pollo` (131920): unclear singular target / mixed proteins.

## Explicitly **not** merged

- Different proteins (chicken vs beef vs shrimp), styles (wet/dry, breakfast, california, mexicano, supreme), and modifiers (`classic`, `original`) — all preserved per playbook.
- `quesarito`, `quesadilla burrito`, `chimichanga burrito` and other hybrid-format names left alone.
