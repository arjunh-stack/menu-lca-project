# Pizza category cleanup — proposals

**Scope:** 6,796 canonicals containing `pizza`/`pizzas` in `dish_canonical_summary_v17.csv`. Reviewed top 300 by `total_count` and ran token-normalized pair detection across the full set.

## Findings

Pizza is wide and menu-distinct — most variation is real (toppings, crust, region, chain branding). High-confidence merges are limited to spelling/abbreviation/plural normalizations mirroring L23 quesadilla precedent.

### Auto-merge (19 high-confidence)

- **Spelling/typo:** `margarita` → `margherita`; `peperoni…` → `pepperoni…`; `proscuitto` → `prosciutto` (1 pair).
- **Abbreviation `barbeque`/`barbecue` → `bbq`** (5 pairs; biggest is 159-count `barbeque chicken pizza` → 1,347-count `bbq chicken pizza`).
- **Plural/singular `lover` ↔ `lovers`** (7 pairs). Direction follows the larger-count target — note `lover pizza veggie` (484) and `lover pepperoni pizza` (478) win over their `lovers …` siblings, while `lovers meat pizza` (793) wins over `lover meat pizza` (576).
- **Token compound `meatlovers` → `meat lovers`** (3 clusters; "Meat Lovers" alphabetizes to `lovers meat`).
- **Filler word `only`** (1 cluster, parity with quesadilla L23): `cheese only pizza` (35) → `cheese pizza` (1,904).

### Rename (2)

`mushroom pizza proscuitto` (5) and `arugula baby fig pickled pizza proscuitto` (1) — typo fix; no `prosciutto` sibling to merge into.

### Judgment flags (4 — surface, do not auto-apply)

- `cheese pizza plain` (58) vs `cheese pizza` (1,904): "plain" is menu-dependent.
- `funghi pizza` (37) vs `mushroom pizza` (65): trattorias keep `funghi` deliberately.
- `melanzane pizza` (5): no plain `eggplant pizza` target exists.
- `pizza prosciutto` (34): IS the canonical for plain prosciutto pizza.

### Explicitly NOT merged (per playbook)

Crust/style variants (thin, deep dish, flatbread, stuffed, original crust, chicago, sicilian, NY style); chain-branded pies (magnifico, motherlode, extramostbestest, BJ favorite, cowboy); `cheezy` (Casey's branding) vs `cheesy`; `mexican pizza` (Taco Bell) vs `pizza`.

### `pizzas` plural

Only 2 plural-`pizzas` clusters exist (count 1 each, both noisy) — no rename warranted.

**Outputs:** `/proposals/category_pizza.csv` (19 merges + 2 renames + 4 judgment flags).
