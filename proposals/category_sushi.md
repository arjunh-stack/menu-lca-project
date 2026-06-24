# Sushi/Sashimi/Maki/Nigiri/Roll cleanup

Scanned 5,834 canonicals containing `sushi`/`sashimi`/`nigiri`/`maki`/`roll`/`rolls`; focused on the top ~300 by count.

## Proposed merges (455, all high-confidence)

| Pattern | # | Example |
|---|---|---|
| Redundant `sushi` token in named rolls | 433 | `california roll sushi` (476) → `california roll` (481) |
| `philly` → `philadelphia` | 6 | `philly roll` (113) → `philadelphia roll` (281) |
| `cali` → `california` | 5 | `cali roll` (8) → `california roll` |
| Spring rolls: `vegetable`/`veggie`/`vegetarian` | 3 | `rolls spring veggie` (45) → `roll spring vegetable` (77) |
| Tokenization `yellow tail` = `yellowtail` | 8 | `roll tail yellow` (39) → `roll yellowtail` (161) |

The dominant rule: when a canonical already names a sushi roll (philadelphia, california, dragon, spider, rainbow, alaska, caterpillar, etc.), the trailing `sushi` token is just a category tag and merges with the bare cluster. Restricted to canonicals containing `roll`/`rolls`/`nigiri`/`maki` so that sashimi-context combos are NOT merged.

## Held back as judgment (50 flags, low confidence)

- **Bare-roll ambiguity** — `hawaiian roll` (bread), `chicken roll`, `lobster roll`, `egg roll` (Chinese), `bacon roll`, `kimchi roll`, `bulgogi roll`, `sausage roll`, `pumpkin/banana/apple/strawberry roll` (dessert), `cheese cream roll`, `pickle/mushroom/carrot/bamboo/panko/crispy/fried/alfredo roll`. Sushi version exists, but bare may include non-sushi items.
- **`crab` / `crabmeat` / `crab meat` roll** — likely synonyms.
- **maki redundancy** — `maki roll`, `maki sushi`, `maki roll sushi`, `kappa maki` vs `kappa maki sushi`, `futomaki roll` vs `futomaki sushi`. `maki` = "roll" in Japanese.

## Explicitly NOT merged

- `sashimi` (33) vs `sashimi sushi` (147) — bare sashimi vs sashimi+sushi combo.
- `tuna roll` vs `spicy tuna roll` (different — spicy mayo).
- `temaki`, `hosomaki`, `futomaki` kept distinct.
- Spring roll vs summer roll, fried vs fresh.
- Anything with `cream cheese` token vs without.
