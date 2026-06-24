# Mexican Miscellaneous (enchilada / tostada / torta / tamale / sopes)

Source: `dish_canonical_summary_v17.csv` (114,855 clusters). Filter: any token in `{enchilada, enchiladas, tostada, tostadas, torta, tortas, tamale, tamales, sopes}` as a whole word in `canonical_name`.

## Per-subcategory cluster counts

| Subcategory | Clusters |
|---|---|
| enchilada/enchiladas | 1,398 |
| tostada/tostadas | 531 |
| torta/tortas | 716 |
| tamale/tamales | 302 |
| sopes | 80 |
| **Total scanned** | **~3,027** |

Reviewed top 50–60 of each (plus targeted greps for known patterns); deeper tail rows are mostly singletons or rare combos out of scope for high-confidence merges.

## Top-5 sample merges (all high confidence)

1. `de enchiladas pollo` (cid 27073, n=54) → `chicken enchiladas` (cid 844, n=415) — Spanish→English: pollo=chicken; `de` is filler.
2. `de enchiladas queso` (cid 27077, n=58) → `cheese enchiladas` (cid 810, n=497) — queso=cheese.
3. `de pollo torta` (cid 26956, n=43) + `pollo torta` (cid 1816, n=43) → `chicken torta` (cid 1099, n=153).
4. `pastor torta` (cid 1422, n=90) + `de pastor torta` (cid 28042, n=21) → `al pastor torta` (cid 26172, n=92).
5. `enchiladas verdes` absorbs `enchiladas green` (cid 1377, n=85), `enchiladas red` (cid 2587, n=23) and `enchiladas rojo` (cid 69371, n=1) go to `enchiladas rojas` (cid 1095, n=150).

## Patterns applied
- Spanish↔English: `pollo`/`chicken`, `queso`/`cheese`, `carne`/`beef`, `camaron`/`shrimp`, `pescado`/`fish`, `jamon`/`ham`, `bistec`/`steak`, `pierna`/`leg`, `huevo`/`egg`, `lengua`/`tongue` (merge — same body part), `puerco`/`pork`, `gallina`/`chicken`, `papa`/`potato`, `verde`/`green`, `rojo`/`rojas`/`red`, `suizas`/`swiss`.
- Article filler: `de` consistently dropped before the alphabetized noun.
- Style equivalence: `breaded` = `milanesa`; `bistec` = `steak`.
- Synonym group: `vegetable`/`vegetarian`/`vegan` → `veggie` (per quesadilla-playbook precedent for vegan; flagged medium-confidence).
- Plural→singular rename only where no singular sibling exists (a few `tostadas`, `tamales` cases).

## Unusual / one-off patterns
- Several `de X Y` clusters where Y is also the english equivalent of X (e.g. `chicken de pollo tostadas`, `cheese de queso sopes`) — clearly merged tokens that survived dedup; flagged for clean rename.
- `de pollo puerco tamales` ambiguous (chicken+pork combo vs typo) — held back as low-confidence.
- `as enchiladas norte` is `enchiladas norteñas` mangled by tokenizer dropping `ñ`; proposed rename, medium confidence.

## Held back (flagged, NOT merged)
- Regional/style names: `enchiladas suizas`, `rancheras`, `poblanas`, `potosinas`, `tapatias`, `texanas`, `michoacanas`, `huastecas` — all distinct regional dishes.
- Distinct ingredients/cuts: `lengua torta`, `cabeza torta`, `torta tripa`, `tinga tostada`, `barbacoa`, `birria` — kept separate per playbook.
- Sauce-distinguished dishes: `enchiladas mole`, `chicken enchiladas mole`, `cream enchiladas sour` — different sauces stay separate.
- `sweet tamale` vs `tamale` — sweet tamales are distinct.
- Cooking-method modifiers (`grilled`, `smoked`, `shredded`) preserved when they are the sole distinguishing token.

Total proposed actions: ~80 rows in `category_mexican_misc.csv` (mix of merges, renames, and explicit KEEP flags for transparency).
