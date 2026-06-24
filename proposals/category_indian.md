# Indian dish canonicals — proposed cleanup

Scanned ~4,378 canonicals in `dish_canonical_summary_v17.csv` containing any of:
`curry`, `curries`, `biryani`, `biriyani`, `tikka`, `tandoori`, `masala`,
`vindaloo`, `korma`, `karahi`. Reviewed the top ~500 by `total_count` and
spot-checked the long tail for spelling variants.

## High-confidence merges (apply directly)

- **navratan / navaratna / navarathan**: same Sanskrit word ("nine gems"). Two
  variants merge into `korma navratan` (cid 1312, n=139).
- **vindalu → vindaloo**: standard transliteration. `goat vindalu` (cid 12320)
  → `goat vindaloo` (cid 1367, n=92).
- **tika → tikka**: `chicken pizza tika` → `chicken pizza tikka` (cid 26719).
- **avakaya / avakai + biriyani / biryani**: same Telugu mango-pickle dish, two
  spelling axes. `avakaya biriyani` (cid 15521) → `avakai biryani` (cid 15643).

## High-confidence renames (plural→singular, no sibling)

- `tandoori vegetables` (cid 3374, 14) → `tandoori vegetable`
- `curries over rice veg` (cid 126737) → `curry over rice veg`
- `curries non over rice veg` (cid 150485) → `curry non over rice veg`

## Mass spelling-variant renames (biriyani / briyani → biryani)

~25 long-tail singletons rewrite `biriyani` / `briyani` token to `biryani` (no
existing biryani-spelling sibling, so straight rename). Plus `vindalu →
vindaloo` for 4 long-tail clusters.

## Flagged for judgment (no automatic action)

The bulk of the file is `flag` rows — patterns where a merge is plausible but
the playbook says BE CONSERVATIVE:

- **murgh / murg = chicken**: ~12 candidate merges (e.g. `murgh tikka` →
  `chicken tikka`). Playbook permits when modifiers exactly match. Listed for
  human review.
- **chana / channa / chickpea / chickpeas**: same legume across Hindi/English
  and plural; chana masala is a specific Punjabi-style dish, so kept distinct.
- **matar / mutter / mattar**: identical Hindi word for peas; multiple
  duplicate clusters.
- **kheema / keema / qeema**: minced-meat spelling variants — many low-count
  siblings.
- **chettinad / chettinadu**: South Indian regional adjective, same place.
- **mughlai / mughalai**: Mughal-style adjective spelling variant.
- **bhindi / okra**, **palak / saag**, **gobi / cauliflower**: Hindi/English
  pairs — kept separate per playbook (Hindi name IS the dish name).
- **kurma / korma**: kurma is also a distinct South Indian style — flag.
- **rawa / rava**: semolina spelling variant (1 cluster).
- **Marketing/descriptor words** (`aromatic`, `homestyle`, `tangy`, `savory`,
  `soulful`, `fusion`, `madness`, `lane spice`, `coastal`, `courtyard`):
  flagged for the chain-marketing-cleanup pass, not handled here.
- **Heat-level words** (`spicy`, `hot`): flagged but not auto-merged.

## Out of scope (kept distinct)

Different curry styles (madras / vindaloo / korma / panang / massaman) and
regional names (chettinad, goan, kerala, hyderabadi, peshawari) are kept
distinct. Different proteins are never merged. Format words (`wrap`,
`sandwich`, `roll`, `pizza`) are kept distinct as separate dish formats.
