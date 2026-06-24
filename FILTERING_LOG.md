# FILTERING_LOG

Each layer documents a step that filtered, excluded, or normalized data in the
deduplicated dish-canonical pipeline. Append in chronological order.

---

## Proposal P-pizza (2026-05-03) — pizza category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 6,796 canonicals whose `canonical_name` contains the token `pizza` or `pizzas`.

**Method:** scanned top 300 by `total_count`; ran token-normalized pair detection
across the full 6,796 set with these normalizations:
`lover→lovers`, `peperoni→pepperoni`, `proscuitto→prosciutto`, `cheezy→cheesy`,
`margarita→margherita`, `barbeque|barbecue→bbq`, `meatlovers→meat lovers`,
`pizzas→pizza`. Same-token-set groups were surfaced as merge candidates.

**Outputs:**
- `/proposals/category_pizza.csv` — 19 merges + 2 renames + 4 judgment flags.
- `/proposals/category_pizza.md` — summary.

**Rows that will be touched if applied:**
- 19 merge sources collapsed into 14 distinct targets.
- 2 typo renames (no sibling to merge into).
- 4 judgment-flag pairs surfaced for human review (no auto-action).

**Conservative carve-outs (explicitly NOT proposed):**
- crust/format/style variants (thin, deep dish, sicilian, NY style, flatbread, chicago, stuffed, original crust) kept separate.
- chain-branded pies (magnifico, motherlode, extramostbestest, BJ favorite, cowboy, etc.) kept separate.
- `cheezy` (Casey's branding) vs `cheesy` kept separate.
- `mexican pizza` (Taco Bell) kept distinct from `pizza`.
- Italian/English funghi/mushroom and melanzane/eggplant flagged as judgment, not merged.

---

## Proposal P-mexican-misc (2026-05-03) — enchilada/tostada/torta/tamale/sopes proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** ~3,027 canonicals whose `canonical_name` contains any of these whole-word tokens:
`enchilada, enchiladas, tostada, tostadas, torta, tortas, tamale, tamales, sopes`.

**Per-subcategory cluster counts:**
- enchilada/enchiladas: 1,398
- tostada/tostadas: 531
- torta/tortas: 716
- tamale/tamales: 302
- sopes: 80

**Method:** filtered with `grep -E ',[^,]*\b(token)\b[^,]*,'` then sorted by total_count
desc and reviewed top 50–60 per subcategory plus targeted greps for known patterns
(Spanish↔English duplicates, `de X` article omissions, plural↔singular siblings,
verde/rojo color-sauce variants, milanesa↔breaded, lengua↔tongue, etc.).

**Outputs:**
- `/proposals/category_mexican_misc.csv` — ~60 merges + ~10 renames + ~15 explicit KEEP flags.
- `/proposals/category_mexican_misc.md` — summary.

**Conservative carve-outs (explicitly NOT proposed):**
- Regional style names: `suizas`, `rancheras`, `poblanas`, `potosinas`, `tapatias`,
  `texanas`, `michoacanas`, `huastecas` — distinct regional dishes per playbook.
- Distinct cuts/preparations: `lengua`, `cabeza`, `tripa`, `tinga`, `barbacoa`, `birria`.
- Sauce-differentiated dishes: `mole`, `sour cream`, `verde` vs `rojo` (color-sauce
  variants of same protein kept separate per playbook).
- Sweet vs savory: `sweet tamale` distinct from plain tamale.
- Cooking method modifiers when they are the sole distinguishing token (`grilled`,
  `smoked`, `shredded`).
- Ambiguous combo tokens like `de pollo puerco tamales` (chicken+pork or typo?) —
  flagged low confidence.

---

## Proposal P-burritos (2026-05-03) — burrito category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 2,974 canonicals whose `canonical_name` contains the token `burrito` or `burritos`.

**Method:** scanned top 100 by `total_count`; ran targeted token-presence greps
for every Spanish↔English pair, abbreviation, synonym, and plural pattern in the
playbook (pollo/chicken, queso/cheese, carne/beef, frijoles/bean,
camaron(es)/shrimp, pescado/fish, aguacate/avocado, cebolla/onion, arroz/rice,
pastor/al pastor, vegetable/vegetarian/vegi → veggie, bbq/barbecue, bf/buffalo,
de/con article-drop, plural→singular). Long tail sampled.

**Outputs:**
- `/proposals/category_burritos.csv` — 20 merges + 2 renames + 7 judgment flags.
- `/proposals/category_burritos.md` — summary.

**Rows that will be touched if applied:**
- 20 merge sources collapsed into 9 distinct targets (chicken, cheese, beef, bean, shrimp, fish, veggie, al pastor, asada carne, bbq, buffalo).
- 2 plural→singular renames (no singular sibling).
- 7 judgment flags surfaced for manual review (asado pollo, beef-bf mixed cluster, carne guisada, carne de truncated, beef-or-chicken combo artifact, burritos de plato, mixed carne/pollo).

**Conservative carve-outs (explicitly NOT proposed):**
- Different proteins (chicken vs beef vs shrimp vs fish) kept separate.
- Style/format variants kept separate: `breakfast`, `california`, `wet`/`dry`, `mexicano`, `supreme`, `quesarito`, `chimichanga burrito`, `quesadilla burrito`, `bowl burrito`, `loco`, `monster`, `homewrecker`, etc.
- `burrito carne guisada` (stewed beef) kept separate from plain beef burrito.
- bf→buffalo merge keeps the spelled-out English canonical even though bf cluster has higher count, matching the v16→v17 quesadilla precedent.

---

## Proposal P-mexican-small (2026-05-03) — fajita/flauta/empanada/nachos proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 2,612 canonicals whose `canonical_name` contains any whole-word token from
`fajita, fajitas, flauta, flautas, empanada, empanadas, nachos`.

**Method:** awk-filtered the four CSV columns on whole-token match, sorted by
`total_count` desc, reviewed top ~150 plus targeted greps for protein duplicates
(pollo/chicken, res/carne/beef, camarones/shrimp, queso/cheese), article-omission
patterns (`de X`), Spanish plurals (`supremos`→`supreme`), and synonym pairs
(`vegetable`/`vegetarian`/`veggie`). Cross-checked alias rows in
`dish_aliases_v17.csv` for ambiguous candidates (e.g., `carne con nachos`,
`carne de fajita pollo` combo plate, `empanada pechuga` cut-spec).

**Outputs:**
- `/proposals/category_mexican_small.csv` — 17 high-confidence merges + 3 medium
  merges + 1 rename + 7 judgment flags.
- `/proposals/category_mexican_small.md` — summary.

**Rows that will be touched if applied:**
- 17 high-confidence merges collapse into 8 destination clusters
  (`chicken fajita`, `beef fajita`, `fajita shrimp`, `chicken nachos`,
  `nachos supreme`, `chicken flautas`, `chicken empanada`, `beef empanada`,
  `empanada queso`, `empanada shrimp`).
- 3 medium-confidence merges into `fajita veggie` (vegetable/vegetarian synonym).
- 1 plural→singular rename (`beef fajitas lb` → `beef fajita lb`).

**Conservative carve-outs (explicitly NOT proposed):**
- `asada carne fajita` kept distinct from `beef fajita` — carne asada is a
  specific cut/preparation.
- `carne de fajita pollo` flagged as combo plate (`carne O pollo`) per aliases.
- `loaded nachos`, `nachos super`, `nachos ultimate`, `deluxe nachos` kept
  separate from `nachos supreme` per playbook (loaded vs basic distinction).
- `beef ground nachos seasoned` kept separate from `beef ground nachos`
  (descriptive modifier, borderline filler).
- `empanada pechuga` (chicken-breast cut) flagged for review vs `chicken empanada`.
- `de empanada queso` merged only into `empanada queso` (not translated to
  `cheese empanada` because no English-form base cluster exists).

---

## Proposal P-tacos (2026-05-03) — taco category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 5,490 canonicals whose `canonical_name` contains the token `taco` or `tacos`.

**Method:** awk-filtered on whole-token match, sorted by `total_count` desc,
reviewed top ~300 plus targeted greps for the standard playbook patterns:
Spanish→English protein/ingredient pairs (pollo/chicken, pescado/fish,
camaron[es]/shrimp, aguacate/avocado, frijoles/bean, papa/potato, puerco/pork,
queso/cheese, huevo/egg, jamon/ham), Spanish 'de' preposition drops
(`X de taco`, `de X taco`), article omission (`pastor` vs `al pastor`),
filler words (`style`, `order`), and pluralization gaps. Cross-checked
candidate target clusters' existence and counts in the summary.

**Outputs:**
- `/proposals/category_tacos.csv` — 48 high-confidence merges + 1 judgment merge
  + 23 high-confidence renames + 1 judgment rename.
- `/proposals/category_tacos.md` — summary.

**Rows that will be touched if applied:**
- 49 merge sources collapse into ~25 destination clusters
  (`chicken taco`, `fish taco`, `shrimp taco`, `avocado taco`, `bean taco`,
  `potato taco`, `pork taco`, `cheese taco`, `egg taco`, `chorizo egg taco`,
  `ham taco`, `al pastor taco`, `al pastor street taco`, `carnitas taco`,
  `barbacoa taco`, `birria taco`, `bistec taco`, `lengua taco`, `taco tripa`,
  `taco tripitas`, `taco trompo`, `buche taco`, `cabeza taco`,
  `asada carne taco`, `fajita taco`, `picadillo taco`, `chicharron taco`,
  `salmon taco`, `mahi taco`, `street taco`).
- 23 plural→singular renames where no singular sibling cluster exists.

**Conservative carve-outs (explicitly NOT proposed):**
- `asado pollo taco` and `guisado pollo taco` kept distinct from `chicken taco`
  (cooking methods: roasted, stewed).
- `picadillo taco` kept distinct from `beef ground taco` (specific seasoned-hash
  style, not just ground beef).
- `nopales taco` and `nopalitos taco` kept distinct (regional/size variants).
- `bf` abbreviation NOT mapped to `buffalo` here — context (`bf chorizo egg`,
  `bf egg potato`, etc.) suggests `bf` = "breakfast" in taco contexts, opposite
  of the quesadilla case. Held back; needs clarification.
- `carne de taco` (cid 29457) renamed to `carne taco` only (drop `de`); NOT
  merged into `beef taco` or `asada carne taco` because `carne` alone is
  ambiguous.
- `fish shrimp taco` flagged judgment — could be combo or either-or.
- `queso shrimpico taco` (45) untouched — possible legitimate menu name.
- `con huevo X taco` breakfast composites left mostly untouched to avoid
  over-merging multi-ingredient breakfast tacos.
- Format modifiers (`soft`, `crispy`, `crunchy`, `hard shell`, `puffy`,
  `rolled`, `street`) kept as distinguishing per playbook.
- Sauces/salsa modifiers (`verde`, `roja`, `chipotle`, `buffalo`, `bbq`) kept
  distinguishing.
- `supreme` kept as distinguishing (specific "with extras" variant).

---

## Proposal P-indian (2026-05-03) — Indian category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 4,378 canonicals whose `canonical_name` contains any whole-word token from
`curry, curries, biryani, biriyani, biriani, briyani, tikka, tika, tandoori,
tandori, masala, vindaloo, vindalu, korma, karahi`.

**Method:** awk-filtered on whole-token match, sorted by `total_count` desc,
reviewed top ~500 plus targeted greps for spelling axes documented in the
playbook: `biryani/biriyani/biriani/briyani`, `tikka/tika`, `tandoori/tandori`,
`vindaloo/vindalu`, `panneer/paneer`. Plus opportunistic checks for
`navratan/navaratna/navarathan`, `matar/mutter/mattar`, `kheema/keema/qeema`,
`chana/channa/chickpea(s)`, `mughlai/mughalai`, `chettinad/chettinadu`,
`avakai/avakaya/aavakai/avakkai`, `gobi/gobhi`, `rava/rawa`, `kurma/korma`,
plus the `murgh/murg = chicken` Hindi-English overlap.

**Outputs:**
- `/proposals/category_indian.csv` — 4 high-confidence merges + 22 medium-conf
  renames (no sibling) + 3 high-conf plural→singular renames + ~50 judgment flags.
- `/proposals/category_indian.md` — summary.

**Rows that will be touched if applied:**
- 4 high-confidence merges (navratan/navaratna/navarathan unification,
  vindalu→vindaloo, tika→tikka, avakaya biriyani→avakai biryani).
- 22 medium-confidence pure renames where the spelling-corrected canonical has
  no existing sibling cluster (mostly `biriyani`/`briyani`→`biryani` and
  `vindalu`→`vindaloo` long-tail singletons).
- 3 plural→singular renames (`tandoori vegetables`, two `curries → curry`).

**Conservative carve-outs (explicitly NOT proposed; flagged for human review):**
- `murgh/murg` ↔ `chicken` substitution: ~12 candidate merges flagged but not
  auto-applied (playbook permits when modifiers exactly match, but Hindi name
  may carry stylistic specificity).
- `chana/channa` ↔ `chickpea(s)`: same legume but `chana masala` is a specific
  Punjabi dish-name — kept separate.
- `bhindi`/`okra`, `palak`/`saag`, `aloo`/`potato`, `gosht`/`meat`,
  `dahi`/`yogurt` — Hindi-name-is-the-dish-name rule preserved.
- Regional adjective spelling variants (`chettinad/chettinadu`,
  `mughlai/mughalai`) flagged for unification but not auto-merged because some
  clusters lack siblings to merge into.
- `kurma` vs `korma`: also a distinct South Indian dish style — flag, don't
  merge.
- `matar/mutter/mattar` (peas) and `kheema/keema/qeema` (minced meat) spelling
  variants flagged but require coordinated mass-rename pass.
- Different curry styles (`madras`, `vindaloo`, `korma`, `panang`, `massaman`,
  `goan`, `kerala`, `chettinad`, `hyderabadi`, `peshawari`) kept distinct per
  playbook.
- Heat-level descriptors (`spicy`, `hot`, `mild`) flagged not auto-merged.
- Marketing/descriptor adjectives (`aromatic`, `homestyle`, `tangy`, `savory`,
  `soulful`, `fusion`, `madness`, `coastal`, `courtyard`) flagged for the
  chain-marketing-cleanup pass.
- Format words (`wrap`, `sandwich`, `roll`, `pizza`, `burger`, `taco`) kept
  distinct as separate dish formats per existing convention.

---

## Proposal P-salads (2026-05-03) — salad category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 1,703 canonicals whose `canonical_name` contains the whole-word
token `salad` or `salads`.

**Method:** awk-filtered on whole-token match, sorted by `total_count` desc,
reviewed top ~250 plus targeted greps for Spanish↔English pairs (`ensalada`/
salad, `pollo`/chicken, `mariscos`/seafood, `camaron`/shrimp, `aguacate`/
avocado), typos (`ceasar`/`cesar`→`caesar`, `cob`→`cobb`), filler `only`,
plural→singular gaps (`salads`-token canonicals — all 6 were singletons with no
singular siblings), synonym pairs (`vegetable`/`vegetarian`/`veggie`, garden
vs house, chopped cobb vs cobb), preparation modifiers, and dressing
descriptors. Cross-checked alias rows in `dish_aliases_v17.csv` for ambiguous
candidates.

**Outputs:**
- `/proposals/category_salads.csv` — 5 merges + 9 judgment flags.
- `/proposals/category_salads.md` — summary.

**Rows that will be touched if applied:**
- 5 merge sources collapse into 4 destination clusters
  (`salad veggie`, `salad taco veggie`, `caesar chicken salad`,
  `salad seafood`).
- 0 plural→singular renames (none of the 6 `salads`-plural canonicals had a
  matching singular sibling).
- 9 judgment flags surfaced for human review (no auto-action).

**Conservative carve-outs (explicitly NOT proposed):**
- `garden salad` vs `house salad` — playbook flags as judgment (garden
  potentially veggie-only, house potentially signature).
- `greek salad` kept distinct from generic salads (specific dish per playbook).
- `chopped cobb salad` vs `cobb salad` — `chopped` is preparation modifier.
- `caesar classic salad` vs `caesar salad` — playbook explicitly excludes
  `classic` / `original` from filler-word merges.
- `caesar chicken salad` vs `caesar salad` — different protein, different dish.
- `bowl X salad` and `lunch X salad` left separate at canonical level.
- Different lettuce types (`arugula`, `romaine`, `kale`, `spinach`) kept
  separate per playbook.
- `gf` / `gluten free` / `gs` variants kept separate (dietary attribute).
- `vegan` NOT merged with `vegetarian`/`veggie` — strictly different.
- `ahi` not merged with `tuna` (ahi = yellowfin specifically).
- Chain-branded caesar variants (`brisbane`, `sonoma`, `salanova`) kept
  distinct.

---

## Proposal P-pasta (2026-05-03) — pasta category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 7,665 canonicals whose `canonical_name` contains the whole-word
token `pasta` or `pastas`.

**Method:** awk-filtered top ~300 by `total_count`, then targeted greps for
Thai romanization variants (`pad`/`phad`, `lad na`/`nah rad`, `woonsen`/`woon
sen`), Italian↔English food terms (`parmigiana`/`parmesan`, `pollo`/`chicken`,
`formaggio`/`cheese`, `funghi`/`mushroom`, `melanzane`/`eggplant`,
`salsiccia`/`sausage`, `gamberi(etti)`/`shrimp`), abbreviations (`mac`/`macaroni`,
`veg`/`vegetable`), synonyms (`vegetable`/`vegetarian`/`veggie`), and known
typos (`fettucine`, `lasagne`, `gnochi`, `leanguini`, `padthai`, `lomein`).

**Outputs:**
- `/proposals/category_pasta.csv` — 30 merges + 13 judgment/info flags.
- `/proposals/category_pasta.md` — summary.

**Rows that will be touched if applied:**
- 30 merge sources collapsed into ~17 destination clusters spanning Thai
  romanization (`pad`/`phad`, `woon sen`), Italian/English equivalents
  (`parmigiana`≡`parmesan`), abbreviations (`mac`/`macaroni`, `veg`/`vegetable`),
  and synonym pairs (`veggie`/`vegetable`/`vegetarian`).
- Highest-impact merges by source count: `chicken parmigiana pasta` (158) →
  `chicken parmesan pasta`; `noodle pad pasta thai` (142) → `pad pasta thai`;
  `eggplant parmesan pasta` (126) → `eggplant parmigiana pasta`.

**Conservative carve-outs (explicitly NOT proposed):**
- Pasta shapes kept distinct: penne, ziti, rigatoni, tortellini, tortelloni
  (size variant of tortellini per playbook), fettuccine, linguine, cavatappi,
  manicotti, cannelloni, ravioli, gnocchi, bucatini.
- Sauces kept distinct: pesto, alfredo, marinara, vodka, bolognese, carbonara,
  puttanesca, aglio olio, pomodoro, arrabiata, scampi, piccata, rosa, sorrentina.
- Proteins kept distinct: chicken, shrimp, beef, pork, seafood, lobster, crab,
  salmon, clams, sausage, meatballs.
- `chicken parmesan pasta spaghetti` (26) and `eggplant parmigiana pasta
  spaghetti` (9) NOT merged into the generic parm pasta clusters — `spaghetti`
  specifies shape.
- Filler-word `classic`/`original`/`signature`/`special`/`plain` NOT removable
  per playbook (`only` is the sole filler precedent).
- `marinara pasta` vs `marinara pasta sauce` flagged not merged — `sauce` is a
  borderline content token.
- Italian/Spanish food-term variants (`pollo`, `formaggio`, `funghi`,
  `melanzane`, `salsiccia`, `gamberi`) appear only in ≤16-count clusters —
  below review threshold.
- `lomein` concatenated (top 14 count), `fettucine` single-c, `padthai`
  concatenated — only 1-count canonicals, below threshold; will surface in
  singleton/tokenization layer.

---

---

## Proposal P-sushi (2026-05-03) — sushi/sashimi/maki/nigiri/roll category cleanup proposals

**Inputs:** `dish_canonical_summary_v17.csv` (114,855 clusters).
**Scope:** 5,834 canonicals containing any of `sushi` / `sashimi` / `nigiri` /
`maki` / `roll` / `rolls`. Focused on the top ~300 by `total_count`.

**Method:**
1. Token-set comparison after stripping the `sushi` token: matched 494 pairs
   where `X` and `X sushi` both exist as canonicals.
2. For pairs where the bare canonical contains `roll`/`rolls`/`nigiri`/`maki`
   AND no non-sushi-suggestive modifier (see carve-outs), proposed merge with
   reason "redundant sushi token".
3. Hand-curated synonym lists for `philly`/`philadelphia`, `cali`/`california`,
   `vegetable`/`veggie`/`vegetarian` (spring rolls), and tokenization variants
   `yellow tail` (alphabetized 2-token) ↔ `yellowtail`.
4. Ambiguous bare-roll cases (bread, sandwich, Korean, dessert) left as
   judgment flags.

**Outputs:**
- `/proposals/category_sushi.csv` — 455 merges + 50 judgment flags.
- `/proposals/category_sushi.md` — summary.

**Rows that will be touched if applied:**
- 455 merges collapsing 455 source clusters into ~370 destination clusters.
- Highest-impact: `california roll sushi` (476) → `california roll` (481);
  `roll spicy sushi tuna` (388) → `roll spicy tuna` (434);
  `roll shrimp sushi tempura` (292) → `roll shrimp tempura` (324);
  `philadelphia roll sushi` (240) → `philadelphia roll` (281);
  `philly roll` (113) → `philadelphia roll` (281).

**Conservative carve-outs (explicitly NOT proposed):**
- `sashimi` (33) NOT merged with `sashimi sushi` (147) — bare sashimi is raw
  fish only, while `X sashimi sushi` denotes a sashimi+sushi combo platter.
  Same for `combination sashimi` vs `combination sashimi sushi`,
  `lunch sashimi` vs `lunch sashimi sushi`, etc.
- `tuna roll` vs `spicy tuna roll` kept distinct (per playbook — spicy mayo).
- `temaki`, `hosomaki`, `futomaki` kept distinct from generic `maki` (size
  variants per playbook).
- Bare-roll clusters that may not be sushi were FLAGGED, not merged:
  `hawaiian roll` (bread), `chicken roll`, `beef roll`, `lobster roll`
  (sandwich), `egg roll` (Chinese), `bacon roll`, `kimchi roll`, `bulgogi roll`,
  `sausage roll`, `pumpkin/banana/apple/strawberry roll` (dessert),
  `cheese cream roll`, `pickle roll`, `mushroom roll`, `carrot roll`,
  `bamboo roll`, `panko roll`, `crispy roll`, `fried roll`, `alfredo roll`,
  `cabbage roll`, etc.
- maki redundancy (`maki` already means "roll" in Japanese, so `maki roll`,
  `maki sushi`, `maki roll sushi`, `kappa maki sushi` vs `kappa maki`,
  `futomaki roll` vs `futomaki sushi` — flagged for human judgment.
- `crab roll` / `crabmeat roll` / `crab meat roll` flagged (likely synonyms
  but not auto-merged).
- Spring roll: `vietnamese spring roll` vs `summer roll` kept distinct (fried
  vs fresh).
- `rolls spring` (115) NOT renamed to "spring rolls" — token order is
  alphabetized by design; rename out of scope here.

---

## Proposal P-asian-noodles (2026-05-03) — Asian noodles cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 4,782 canonicals whose `canonical_name` contains a whole-word token
in {`noodle`, `noodles`, `mein`, `ramen`, `pho`, `udon`, `soba`, `pad`}.

**Method:** Token-level (whitespace-split) matching, then groupwise dedup by a
"cleanest form" function that drops the noise token `pasta`, expands
`lomein`→`lo mein` / `chowmein`→`chow mein`, and normalizes Thai
romanization `phad`→`pad`. Within each clean-form group the highest-count
cluster survives; others merge in. Singular/plural `noodle`/`noodles`
treated separately. Vietnamese protein words (`ga`, `bo`, `tom`, `rau`,
`chay`) checked against English-protein paired clusters.

**Outputs:**
- `/proposals/category_asian_noodles.csv` — 368 merges + 2,510 renames.
- `/proposals/category_asian_noodles.md` — summary.

**Rows that will be touched if applied:**
- 368 merges collapse 368 source clusters into existing cleaner clusters,
  consolidating ~4,512 menu rows. Highest-impact:
  `chicken lo mein pasta` (421) → `chicken lo mein` (639);
  `pad pasta thai` (766) ↔ `pad thai` (214) (clean = `pad thai`);
  `lo mein pasta shrimp` (370) → `lo mein shrimp` (584);
  `beef lo mein pasta` (258) → `beef lo mein` (559);
  `lo mein pasta vegetable` (296) → `lo mein vegetable` (516);
  `ew pad pasta see` (442) ↔ `ew pad see` (77) (clean = `ew pad see`);
  `beef chow mein pasta` (83) → `beef chow mein` (407);
  `chow mein pasta shrimp` (9) → `chow mein shrimp` (451).
- 2,510 standalone renames (medium confidence) strip `pasta` from canonicals
  whose clean form has no paired cluster — same systematic noise rule;
  ~12,836 menu rows affected. Top examples: `drunken noodles pasta` (279)
  → `drunken noodles`; `noodle pasta rice singapore` (202) →
  `noodle rice singapore`; `buttered noodles pasta` (104) →
  `buttered noodles`.
- Vietnamese protein merges: `ga pho`(1) → `chicken pho`(21);
  `chay pho`(5) → `pho vegetarian`(10).
- Singular/plural top: `drunken noodle`(66) → `drunken noodles`(279);
  `noodle rice singapore`(202) ← `noodles rice singapore`(58) (note:
  merged into singular here because singular has higher count after
  pasta-strip).

**Conservative carve-outs (explicitly NOT proposed):**
- Different broth/sauce ramens (`miso ramen`, `tonkotsu ramen`,
  `shoyu ramen`, `shio ramen`) kept distinct.
- `udon`, `soba`, `ramen` as noodle TYPES never merged with each other
  per playbook.
- Different Thai dishes kept distinct: `pad thai`, `pad see ew`,
  `pad kee mao` (drunken noodles), `pad woon sen` (glass noodle),
  `pad ped`, `pad pak`, `pad prik`, `pad phet`.
- Different proteins (chicken/beef/shrimp/pork/tofu/seafood/duck/lobster)
  always kept distinct.
- Thai protein words `gai` (chicken), `goong` (shrimp), `moo` (pork) — all
  appearances in noodle scope are 1-count singletons with no paired
  English-protein cluster, so no merges proposed; will surface in a
  singleton/tokenization layer.
- `chicken noodle soup` (29) NOT merged with `chicken noodle pasta soup`
  (58) — wait, this IS a proposed merge (pasta noise drop). Verified safe:
  the canonical `chicken noodle soup` already exists separately.
- `noodle pad thai` (13) and `noodle pasta phad thai` (26) merge into
  `noodle pad pasta thai` (142) cluster, which then renames to
  `noodle pad thai` — chained pasta-strip + phad→pad.
- Single-letter / 1-count phonetic singletons like `ph pho`, `pad th`,
  `ka pad pao`, `gra pad prow` not unioned with their longer correct
  forms (would need fuzzy/LLM judgment).
- The previous P-pasta layer proposed `noodle pad pasta thai`(142) →
  `pad pasta thai`(766). This layer goes further: both clean to `pad thai`.
  If P-pasta has already been applied, P-asian-noodles will redirect the
  combined cluster to `pad thai`.

---

## Proposal P-wings (2026-05-03) — wings/tenders category cleanup proposals

**Status:** PROPOSED (not yet applied to alias/summary tables).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 2,007 canonicals whose `canonical_name` contains the token `wing`,
`wings`, `tender`, or `tenders`.

**Method:** scanned top ~280 by `total_count`; ran token-substitution checks
across the full 2,007 set for: `barbecue|barbeque|barbq → bbq`, `wing → wings`
(singular→plural), `tender → tenders`, `smokey → smoky`, `finger(s) → tender(s)`,
`strip(s) → tender(s)`. Spot-checked aliases under each candidate cluster to
verify intent before proposing.

**Outputs:**
- `/proposals/category_wings.csv` — 9 merges + 3 renames + 22 judgment flags.
- `/proposals/category_wings.md` — summary.

**Rows that will be touched if applied:**
- 9 merge sources collapsed into 7 distinct targets (`barbecue wings` and
  `barbeque wing` both → `bbq wings`; the rest are 1-to-1).
- 3 spelling renames (smokey → smoky; no merge sibling exists).
- 22 judgment flags for human review (no auto-action).

**Conservative carve-outs (explicitly NOT proposed):**
- `bone` (bone-in) vs `boneless` — real format distinction, kept separate.
- `traditional wings` (1,375) kept distinct from generic wings — `traditional`
  is the brand-standard bone-in indicator.
- Brand-name singletons preserved: `handcrafted tenders` (2,573, Raising Cane's),
  `golden tenders` (305, Popeyes), `wicked wings` (176, KFC), `fried kentucky
  wings` (416, KFC), `bj original wings`, `hooters original style wings`,
  `kookaburra platter wings`.
- `tenders` alone (cluster_id 0, count 810) and `crispy tenders` (223) NOT
  auto-merged into `chicken tenders` (1,886) despite likely identity — flagged
  as high-impact judgment because bare `tenders` could include steak/beef
  variants, and `crispy tenders` is a frequent brand menu line (Popeyes etc.).
- `chicken crispy tenders` (362) — token-sorted "crispy chicken tenders" —
  flagged not merged; cluster has already absorbed `chicken ribs tenders`
  via fuzzy.
- `only wings` (81) NOT merged — no plain `wings` canonical exists; the
  natural target would be `traditional wings` but that conflates plain wings
  with the bone-in indicator.
- BWW-style `things` clusters (`boneless things wings`, `things traditional
  wings`, `boneless buffalo things wings`, `buffalo things traditional wings`)
  — `things` appears to be a brand artifact ("Wild Things") preserved in raw
  text; not merged.
- `wing wings` and `X wing wings` clusters — double-token raw-text artifacts;
  flagged but not merged (some are real BWW menu items like "Wing Box Combo").
- `tenders wings` / `or tenders wings` combo platters kept distinct.
- `naked wings` vs `plain wings` (both unsauced) flagged — subtle distinction
  (`naked` sometimes also = unbreaded).
- `bone less wings` / `bone less wing wings` (space-typo for `boneless`)
  flagged — proper destination is `boneless wings`, not `bone wings`, but the
  clusters are dirty and need alias-level audit.
- Specific sauces / heat levels / cuts (`all drums`, `all flappers`,
  `cauliflower wings`, `beyond piece tenders`) preserved.
- `chicken sandwich tender` and other `... sandwich tender` clusters kept
  distinct — these are tender-sandwiches, not tenders.

**No `bf → buffalo` matches found** in this slice — that abbreviation pattern
was already cleaned for the wings/tenders subset (or never appeared); the
quesadilla-layer precedent fired only on `bf chicken quesadilla`.


---
---

## Layer 25-prep (2026-05-11) — dish-context precompute for recipe pipeline

**Status:** APPLIED. Side input for the recipe-generation pipeline (`recipes/`).
**Input:** `menu_dishes.sqlite` (1,126,856 rows) + `dish_canonical_summary_v18.csv` (113,911 canonicals).
**Output:** `recipes/dish_context.csv` (107,579 rows).

**Method:** group `menu_dishes` by `canonical_dish`. For each canonical record:
- `top_raw_name`: most-frequent `raw_menu_name` (ties → shortest length); prefers
  clean generic forms like "Italian Sub" over brand-specific
  "Italian B.M.T.® 6 Inch Regular Sub".
- `cuisine_bucket`: modal vote across all restaurants serving the dish.
  Each restaurant votes via `recipes/structural_references.bucket_from_category`,
  which uses **priority tiers** (ingredient → cuisine → diet → dessert) and falls
  back to `"default"` when no tier matches. Tag-silent restaurants (american /
  sandwiches / fast food) vote "default" so they can't be dominated by a handful
  of cross-listing burger places.

**CATEGORY_MAP revision** — significant departure from the menu-project original:
- DROPPED tags that mismatch the underlying structural reference shapes:
  `healthy`, `salad`, `salads` (mapped to vegetarian which has 0% protein — wrong
  for meal-salads); `mexican`, `tacos`, `burritos` (mapped to beef but span
  beef/chicken/pork/bean/fish); `indian` (mapped to vegetarian but US Indian is
  mostly meat curries); `vegetarian`, `vegetarian friendly` (too noisy — restaurants
  tagged "Vegetarian" still serve meat curries).
- CHANGED: `thai` from seafood → chicken (the chicken bucket's second reference
  *is* Pad See Ew).
- ADDED: `noodles, vietnamese, korean, caribbean, fried chicken` → chicken;
  `bbq` → beef.

**Distribution:**
| Bucket | Canonicals | Notes |
|---|---:|---|
| default | 35,165 | sandwich/American chains + dishes spanning proteins |
| chicken | 27,479 | Asian noodle/rice shape + wings |
| beef    | 18,757 | burgers + steak + bbq |
| seafood | 13,185 | sushi/seafood/Japanese |
| pasta   | 12,271 | Italian/pizza/pasta |
| vegetarian | 724 | strict vegan-only |

**Rows touched:**
- Distinct canonicals seen in DB: 107,581
- Joined to cluster_id via summary CSV: 107,579
- Missing from summary (alias-key drift, see PIPELINE_LAYERS final-table note): 2

---

## Layer LCA-1 (2026-05-11) — ingredient → emission-factor matching (validation slice)

**Status:** APPLIED on validation slice. New pipeline step in `lca/`.
**Input:** `recipes/recipes_validation.jsonl` (500 recipes, 6,049 ingredient rows).
**Output:** `lca/ingredient_ef_table.csv` (533 unique ingredient strings).

**Method:** Port of `../reverse-recipe/`'s hybrid matcher into `lca/matcher.py`:
synonym dict → sentence-transformer embedding search (all-MiniLM-L6-v2)
across AGRIBALYSE v3.2 (~15k products, ag+processing CO2e scope) and
SU-EATABLE LIFE (324 products) → keyword-based Poore & Nemecek candidates
→ DeepSeek v3 LLM disambiguation → uncertainty widening via P&N cross-source
values + ±30% floor. Multi-impact (water, land, eutrophication,
acidification) joined per matched AGRIBALYSE LCI Name. Cache:
`lca/data/ef_cache.json`.

**Concurrency:** ThreadPoolExecutor with 20 workers; LLM calls via raw
`httpx` POSTs (repo convention; matches `recipes/pipeline.py`). First run
~220s; cache-warm re-runs ~12s.

**Decisions baked in** (from `lca/PLAN.md`):
- D1 AGRIBALYSE-first (preferred for `recommended` value when an exact
  AGRIBALYSE match exists).
- D3 Cradle-to-farm-gate: GHG uses `co2e_ag_proc` column
  (agriculture+processing, from `agribalyse_detail_etape`); water/land
  taken from synthese as-is (no per-stage breakdown available — v1
  limitation).
- D4 No pre-normalization — raw recipe-LLM ingredient strings fed
  directly to the matcher.

**Rows touched:**
- Unique ingredient strings: 533
- Matched: 532 (99.8%)
- Unmatched after retry: 1 (`smoking wood chips`, correctly rejected — not food)
- With AGRIBALYSE multi-impact: 528 (99.1%)
- With only SU-EATABLE/P&N (no water/land): 4 (`croissants`, `tilapia fillet`,
  `chocolate chips`, `yeast`)

**Headline sanity-check** (recommended kg CO₂e/kg; (min, max) after widening):
- chicken breast: 4.84 (3.39, 9.30) — AGRIBALYSE "Chicken, breast, without skin, raw"
- ground beef: 44.22 (30.95, 99.50) — between P&N's dairy-herd (32.9) and beef-herd (99.5)
- cheddar cheese: 5.66 (3.96, 23.90) — AGRIBALYSE 5.66; widened to P&N's 23.9
- eggs: 1.51 (1.06, 4.70) — AGRIBALYSE; widened to P&N's 4.7
- olive oil: 0.60 (0.42, 5.90) — AGRIBALYSE ag+proc only; widened to P&N's 5.9
- salmon fillet: 4.19 (2.93, 12.60) — AGRIBALYSE farmed salmon; widened to P&N farmed-fish
- shrimp: 18.29 (7.04, 26.50) — AGRIBALYSE cooked shrimp; widened to P&N's 26.5
- rice: 1.61 (1.13, 4.50) — AGRIBALYSE raw; widened to P&N's 4.5
- tomato: 0.32 (0.22, 2.10) — AGRIBALYSE raw; widened to P&N's 2.1

**Known quirks** (none blocking):
- Singular/plural duplicates still present (`egg`/`eggs`, `bell pepper`/`bell peppers`):
  same matched LCI, near-identical numbers. D4 deliberately skips pre-norm.
- Spice catch-all: `black pepper`, `cumin`, `paprika` all matched to AGRIBALYSE's
  spice entry (7.53 kg CO₂e/kg, 688 Pt/kg land). Per-recipe impact small because
  spice masses are tiny (~2 g).
- `capers` matched the composite "Anchovy, fillets, rolled with capers" — not
  ideal but quantitatively close (0.94 kg/kg).
- `ranch dressing` initially failed with an LLM JSON parse error; resolved
  cleanly on retry to "Salad dressing, prepacked" (1.76 kg/kg). Suggests
  adding a JSON-parse retry pass would harden the matcher (future).

---

## Layer LCA-2 (2026-05-11) — per-recipe aggregation + Monte Carlo (validation slice)

**Status:** APPLIED on validation slice. New pipeline step in `lca/`.
**Input:** `recipes/recipes_validation.jsonl` (500 recipes) ×
`lca/ingredient_ef_table.csv` (533 ingredient EFs).
**Output:** `lca/dish_lca_validation.jsonl` (500 rows, one per cluster_id).
**Runtime:** 2 s for 500 recipes × 10 000 MC draws (~314 recipes/s).

**Method:** Pure in-process arithmetic (`lca/aggregate_lca.py`). For each
recipe:
1. For each ingredient, look up EF row by lowercased name. Skip if
   unmatched (1 case: "smoking wood chips" in 1 recipe).
2. Compute per-ingredient (mass_kg × ef) for GHG, water, land,
   acidification, eutrophication (freshwater).
3. Sum to per-recipe totals; also compute per-kg-of-recipe rates.
4. Run 10k-draw triangular Monte Carlo over (ghg_min, ghg_recommended,
   ghg_max) per ingredient with normal(σ=15%) mass noise → report
   p5/p25/p50/p75/p95 + per-ingredient variance contribution
   (top-5 variance drivers).

**Scope reminder** (per `lca/PLAN.md` decisions):
- D2: Full MC on GHG. Water/land are *point estimates* — AGRIBALYSE
  doesn't publish ranges for those columns; no scope uncertainty
  synthesized in v1.
- D3: Cradle-to-farm-gate. GHG uses AGRIBALYSE ag+processing CO2e column.
  Water/land taken from synthese as-is (full lifecycle in AGRIBALYSE for
  those categories — v1 limitation).

**Distribution across the 500-dish slice:**
| Metric                  | p10   | median | p90    | max     |
|-------------------------|------:|-------:|-------:|--------:|
| GHG kg CO₂e / recipe    | 1.58  | 4.36   | 17.23  | 30.3    |
| GHG kg CO₂e / kg recipe | 1.68  | 3.23   | 13.81  | 25.3    |
| Water m³ / recipe       | 1.22  | 2.71   | 7.66   | 109.5   |
| Land Pt / recipe        | 99    | 277    | 1160   | 2020    |

The 90/10 GHG ratio (~11×) reflects the meat-vs-veg spread well:
beef-heavy dishes (steak, brisket, bacon cheeseburger) cluster at the
top; vegetable-only dishes (Veggie Delite, broccoli, mixed vegetables,
black beans) at the bottom.

**MC right-skew observation:** 463/500 recipes have MC mean > point
estimate. This is the expected effect of P&N cross-source widening
pulling the upper tail higher than the AGRIBALYSE ag+proc-only mode
(e.g., chicken: mode 4.84, max 9.3 from P&N poultry). Reading: the
*expected* footprint integrating scope uncertainty is systematically
higher than the AGRIBALYSE-only point estimate.

**Spot-check — Chicken Tikka Masala** (cluster_id 25561, n=473 menus):
- 1634 g recipe → 4.45 kg CO₂e (2.72 kg/kg)
- Hotspot: chicken breast 600 g = 2.90 kg CO₂e (65% of total),
  heavy cream + butter + yogurt = 23%, everything else <2%.
- Water 2.12 m³ (chicken 1.49 m³ = 70%, onion 0.11 m³, tomato 0.11 m³).
- Land 300 Pt (chicken 201 Pt, dairy 55 Pt combined).
- MC variance drivers: chicken 92%, heavy cream 3%, tomato puree 2% —
  matches intuition (the dominant contributor is also the most
  uncertain because of P&N's broader poultry value).

**Files added:**
- `lca/aggregate_lca.py` — script
- `lca/dish_lca_validation.jsonl` — 500 rows of per-recipe LCA results

Next step (gated on user go-ahead per PLAN.md execution order): the same
script will run unchanged on the full canonical-dish recipe set once
`recipes/recipes.jsonl` exists for all 107k dishes.

---
---

## Layer 25 (2026-05-11) — recipe-test cross-screen via two independent LLMs

**Status:** APPLIED. Produced v19 head.
**Input:** `dish_canonical_summary_v18.csv` (113,925 canonicals) + `dish_aliases_v18.csv`.
**Output:** `dish_canonical_summary_v19.csv` (79,590) + `dish_aliases_v19.csv` + `recipe_drops_applied.csv` (33,620 audited drops).

**Method:** Every canonical asked by two independent LLMs (`temperature=0`):
"could a chef Google this exact name and find a real, repeatable recipe?"
KEEP/DROP binary verdicts → 3-way bucket assignment in `compare_recipe_screens_v2.py`:

| Bucket | Action |
|---|---|
| BOTH_KEEP | keep |
| BOTH_DROP | drop |
| PRO_VETO (gemini KEEP, pro DROP) | drop, UNLESS in `RESCUE_CANONICALS` (verified chain item by web search) OR pro_reason ∈ {obscure, unknown, unrecognized} ∧ total_count ≥ 3 (protects ethnic dishes Pro doesn't recognize) |
| PRO_RESCUE (gemini DROP, pro KEEP) | keep |
| HAS_ERROR | keep |

**Rescue pass:** `find_drop_rescues.py` + `judge_rescues_gemini.py`
(1,072 rescues) — for "real dish hiding inside long-form name" cases
where canonical tokens are a strict superset of an existing keeper.

**Models:**
- Gemini 2.0 Flash (`google/gemini-2.0-flash-001`), 113,925 verdicts → `recipe_screen_gemini.csv`
- DeepSeek v4 Pro (`deepseek/deepseek-v4-pro`), 30,879 re-screen of Gemini DROPs → `recipe_screen_deepseek.csv`
- DeepSeek v4 Pro KEEPs re-screen, 4 shards, 82,606 rows → `recipe_screen_deepseek_keeps.csv`
- Gemini rescue judge → `dish_rescue_judgments.csv`

**Drop-reason distribution (final applied set, 33,620 rows):**
| Reason | Count |
|---|---:|
| dish (Pro: "not a real dish") | 8,037 |
| gibberish | 7,920 |
| vague | 6,851 |
| possessive (e.g. `burger dave`) | 3,595 |
| combo (combo-plate labels) | 3,299 |
| regional (model-unrecognized regional) | 1,688 |
| generic (e.g. `tenders`, `bone wings`) | 1,565 |
| addon, code, branded | <300 each |

**Effect on row counts:**
- Canonical vocabulary: 113,925 → 79,590 (−34,335)
- Aliases retained: ~v18's count minus aliases pointing to dropped canonicals
- `menu_dishes.sqlite` impact (pending rebuild): 32,256 canonicals currently mapped to menu rows will be dropped; ~75,325 canonicals retain menu rows after rebuild.

**Frozen verdict CSVs (R10):** all five outputs above committed at repo
root. Re-runs replay deterministically via `apply_recipe_drops.py`.

**Open follow-up:** `build_dish_index.py` still hardcodes
`dish_aliases_v18.csv` (line 46). Update to `_v19.csv` and rebuild
`menu_dishes.sqlite` to bring downstream stages onto v19. Validation
slice impact: 23/500 dishes in `recipes/recipes_validation.jsonl` are
v18 cluster_ids dropped in v19 (`tenders`, `chicken mixed`, `burger
dave`, etc.) — orphan in v19, suggest regenerating the slice as top-
500-of-v19 before any cross-stage spot-check.

---

## Layer NUT-1 (2026-05-21) — FDC port + ingredient → macros matching (validation slice)

**Status:** APPLIED on validation slice. New pipeline step in `nutrition/`.
**Inputs:** USDA FoodData Central bulk CSVs (SR Legacy, FNDDS/Survey,
Foundation) under `nutrition/data/`; `recipes/recipes_validation.jsonl`
(500 recipes, 6,038 ingredient rows).
**Outputs:** `nutrition/data/fdc_macro_table.csv` (13,602 foods),
`nutrition/data/fdc_descriptions.csv`, `nutrition/data/embeddings/*.npy`,
`nutrition/ingredient_fdc_table.csv` (533 unique ingredient strings).

**Port step** (`port_fdc_data.py`) — filtering / normalization applied:
- Three FDC sources joined to `food_nutrient.csv`; four nutrients pulled
  per 100 g: energy (kcal), protein (g), total fat (g), carbohydrate (g).
- Nutrient-id scheme differs by source — SR Legacy + Foundation key on the
  standard nutrient `id` (1008/1003/1004/1005); FNDDS keys on the legacy
  `nutrient_nbr` (208/203/204/205). Verified against each source's
  `nutrient.csv`.
- **Foundation forensic-row filter (PLAN D1):** `foundation/food.csv`
  carries ~88k rows but only 469 are real foundation foods; the other
  ~87.5k are chain-of-custody rows (`sample_food` 4,079, `sub_sample_food`
  75,055, `market_acquisition` 7,577, `agricultural_acquisition` 810).
  Filtered to `data_type == 'foundation_food'` → 469.
- **No-energy drop:** foods with no usable energy value (true Energy kcal,
  then Atwater Specific, then Atwater General all absent) are dropped —
  unusable for a macro lookup. Dropped: 0 SR Legacy, 1 FNDDS, 91 of 469
  Foundation. Final macro table: 7,793 SR Legacy + 5,431 FNDDS + 378
  Foundation = 13,602.

**Match step** (`match_ingredients.py` + `fdc_matcher.py`):
sentence-transformer embedding search (all-MiniLM-L6-v2) over the 13,602
FDC descriptions → DeepSeek v3 (`deepseek/deepseek-chat-v3-0324`,
temperature 0) picks the single best entry, applying a cooked-vs-raw
preference rule (PLAN D3). Cache: `nutrition/data/fdc_match_cache.json`.
ThreadPoolExecutor, 8 workers; first run ~56s, cache-warm re-runs ~5s.

**Rows touched:**
- Unique ingredient strings: 533
- Matched: 514 (96.4% of unique; 98.9% occurrence-weighted, 5,971/6,038)
- Unmatched: 19 — `pizza dough` (×20), `oil` (×7), and 17 specialty
  spices/aromatics or non-foods (`mirin`, `nori sheet`, `garam masala`,
  `Sichuan peppercorns`, `liquid smoke`, `smoking wood chips`, `dried corn
  husks`, …). Spices carry negligible mass; `smoking wood chips` / `dried
  corn husks` are correctly rejected (not eaten).

**Headline sanity-check** (matched FDC entry; per-100 g kcal):
- grilled chicken breast → "Chicken breast, grilled without sauce, skin
  eaten" [FNDDS] 206 kcal — cooked-form rule fired correctly.
- boiled white rice → "Rice, white, cooked, as ingredient" [FNDDS] 130 kcal.
- cheddar cheese → "Cheese, cheddar" [Foundation] 408 kcal.
- all-purpose flour → "Flour, wheat, all-purpose, enriched, unbleached"
  [Foundation] 358 kcal.
- ketchup → "Ketchup" [FNDDS] 109 kcal.

**Known quirks** (none blocking):
- **`pizza dough` is a genuine FDC coverage gap.** FDC has no plain
  pizza-dough / raw-crust entry — only composite pizzas and branded
  refrigerated doughs. The matcher correctly rejects the composite-pizza
  candidates rather than mis-matching; pizza per-recipe totals undercount
  (e.g. `margherita pizza` lands at match_rate 0.57). A manual proxy
  (bread dough ≈ 270 kcal/100 g) is a candidate fix — flagged, not applied.
- `asiago cheese` matched "Cheese, fontina" (medium confidence) — close
  hard-cheese proxy, ~equivalent macros.
- Two matcher bugs found and fixed during the validation run:
  (1) transient OpenRouter failures were mislabeled `llm_rejected_all`
  *and cached* as permanent — now distinguished (`llm_call_failed`,
  never cached, retried on re-run); (2) the LLM occasionally 0-indexed
  its candidate pick — the parser now treats a returned `0` as the first
  candidate. Post-fix the unmatched set dropped from 29 → 19.

---

## Layer NUT-2 (2026-05-21) — per-recipe macro aggregation (validation slice)

**Status:** APPLIED on validation slice. `nutrition/aggregate_macros.py`.
**Input:** `recipes/recipes_validation.jsonl` × `ingredient_fdc_table.csv`.
**Output:** `nutrition/dish_macros.jsonl` (500 dishes).

**Method:** pure in-process arithmetic — per ingredient, `contribution =
per_100g_value × grams / 100`, summed over the recipe. Per-serving =
per-recipe ÷ 4 (PLAN D4: recipe step prompts for a 4-serving recipe).
`match_rate` is ingredient-mass-weighted (matched grams / total grams).

**Results:**
- Mean ingredient-mass match rate: 98.3%.
- Fully matched dishes (`match_rate` ≥ 0.999): 433 / 500.
- Mean per-recipe macros (4 servings): 2,313 kcal / 156 g protein /
  124 g fat / 144 g carb → 578 kcal/serving.

**Validation checks:**
- **Atwater consistency:** `|4·protein + 9·fat + 4·carb − energy_kcal| /
  energy_kcal` — median 0.9%, mean 1.1% across 500 dishes. Confirms the
  macro extraction and gram-scaled summation are internally correct.
- **Energy density:** kcal/g median 1.85, range 0.30–5.00 — all
  physically plausible (watery soups low, fatty dishes high).
- **Spot dishes (kcal/serving):** grilled cheese 374, Caesar salad 698,
  chicken wings 899, pad thai 503, fried rice 590, pancakes 450 — all
  within published ranges. `margherita pizza` 195 is a known undercount
  (pizza-dough gap above).

**Next:** STOP per PLAN D7 — await go-ahead before the full ~75k-recipe
run (`--recipes recipes/recipes.jsonl` on both scripts; cache makes the
match step incremental).

---

## Layer NUT-3 (2026-05-21) — full nutrition run (all 75,324 recipes)

**Status:** APPLIED to the full recipe set (go-ahead given). Run executed
on a remote Mac mini via `nutrition/run_on_mini.sh` (rsync the pre-built
FDC artifacts + scripts, tmux + venv, chained match → aggregate);
`nutrition/fetch_from_mini.sh` pulled the outputs back.
**Input:** `recipes/recipes.jsonl` (75,325 recipes; 1 error row skipped).
**Outputs:** `nutrition/ingredient_fdc_table.csv` (12,103 unique
ingredient strings), `nutrition/dish_macros.jsonl` (75,324 dishes,
~229 MB — gitignored, reconstructable).

**Dedup:** the 75,324 recipes' ingredient lists collapse to 12,103 unique
ingredient strings; each is matched exactly once (recipes sharing an
ingredient never re-query it).

**Match-step config:** DeepSeek v3 disambiguation, concurrency 10.
OpenRouter rate-limited the run to a steady ~4.5 calls/s; full match
step ~45 min. The bread-dough proxy for `pizza dough` (Layer NUT-1
"known quirks") was applied — `_MANUAL_OVERRIDES` in `fdc_matcher.py`.

**Rows touched:**
- Unique ingredient strings: 12,103
- Matched: 11,166 (92.3% of unique; **98.2% occurrence-weighted**)
- Unmatched: 937 — a long tail of specialty spices / condiments
  (`garam masala` ×3,067, `mirin` ×1,353, `nori sheets` ×1,015,
  `gochujang` ×615, `Sichuan peppercorns` ×461, `kaffir lime leaves`
  ×344, …) plus generic `oil` (×2,198). Spices carry negligible recipe
  mass, so the dish-level impact is small (see match rate below).

**Per-dish results (`dish_macros.jsonl`, 75,324 dishes):**
- Mean ingredient-mass match rate: **98.6%**.
- Fully matched dishes (`match_rate` ≥ 0.999): 60,787 / 75,324 (80.7%).
- Dishes with <50% match: 240 — mostly rotisserie-chicken dishes
  (`whole chicken` unmatched) and a few steak/pasta dishes.
- Mean per-recipe macros (4 servings): 2,220 kcal / 143 g protein /
  117 g fat / 150 g carb → **555 kcal / 36 P / 29 F / 37 C per serving**.

**Validation checks:**
- **Atwater consistency:** `|4P + 9F + 4C − kcal| / kcal` — median 0.9%,
  mean 1.3% across all 75,324 dishes. Confirms the arithmetic at scale.
- **Energy density:** kcal/g median 1.66, p1 0.59, p99 3.46 — all
  physically plausible. Only 3 dishes outside 0.05–9.1 kcal/g, all
  beverages (still water 0.0, Inca Kola, café de olla — correctly near-
  zero-calorie liquids).

**Post-run override pass (applied same day).** Four high-frequency
ingredients the embedding/LLM step missed despite real FDC entries
existing were added to `_MANUAL_OVERRIDES` and the match + aggregate
steps re-run (instant — all other ingredients cache-hit, no LLM calls):

| Ingredient | → FDC entry (fdc_id) |
|---|---|
| `oil` (×2,198) | Oil, soybean, salad or cooking (171411) |
| `whole chicken` | Chicken, broilers/fryers, meat and skin, cooked, roasted (171450) |
| `filet mignon` | Beef, tenderloin, steak, choice, cooked, broiled (168722) |
| `jasmine rice` | Rice, white, long-grain, regular, enriched, cooked (168878) |

Effect on `dish_macros.jsonl`: mean ingredient-mass match rate
98.6% → **99.0%**; fully matched dishes 60,787 → **62,712**; dishes
with <50% match 240 → **153**. Atwater consistency unchanged (0.9%
median). Mean per serving: 559 kcal / 36 P / 30 F / 38 C.

**Remaining follow-ups (quality tail, non-blocking):**
- `fettuccine`, `pancetta`, and a long tail of specialty
  spices/condiments (`garam masala`, `mirin`, `gochujang`, …) still
  unmatched — spices carry negligible mass, the 153 remaining low-match
  dishes are a thin tail.
- `nori sheet` / `nori sheets` singular-plural duplicate — harmless
  (both unmatched), but indicative; D6-style pre-normalization is
  deliberately skipped (mirrors LCA Layer LCA-1).

---

## Layer NUT-4 (2026-05-28) — per-dish Nutri-Score (Clark et al. 2022)

**Goal.** Compute the Nutri-Score / FSAm-NPS nutrition-quality score for
every dish, using the algorithm Clark et al. (2022, PNAS, "Estimating the
environmental impacts of 57,000 food products") used for their Nutrition
Impact Score — the original (2017) Santé-publique-France formula:
4 negative components scored 0–10 (energy, sugars, saturated fat, sodium)
and 3 positive 0–5 (protein, fibre, fruit/veg/legume/nut/qualifying-oil
%); score = Σnegative − Σpositive ∈ [−15, 40]; → A–E grade → Clark's 1–5
scale (A=1…E=5) and 0–100 scaled score.

**Inputs / new code (`nutrition/`).**
- `port_fdc_micronutrients.py` → `data/fdc_micronutrient_table.csv`
  (13,694 FDC foods): per-100 g saturated fat (id 1258 / nbr 606), total
  sugars (2000→1063 / 269), fibre (1079 / 291), sodium (1093 / 307), plus
  the FDC food-category tag. Same three sources / id-scheme split as the
  macro port (NUT-1).
- `fvn_classify.py` → `data/ingredient_fvn.csv`: the FVN% positive
  component (no nutrient row exists for it) estimated per ingredient.
- `nutriscore.py`: the algorithm (4 food-type variants), reference
  self-test passes.
- `compute_nutriscore.py` → `dish_nutriscore.jsonl` (75,323 dishes) and
  `dish_nutriscore_manifold.csv` (**39,166** phylogeny-manifold dishes,
  `idx`-aligned to `phylogeny/data/umap.json`; 0 missing).

**Normalisation / estimation choices (the filtering this layer records):**
1. **Per-100 g basis.** Nutrient density = Σ(matched-ingredient
   contribution) / `recipe_mass_g` × 100. Numerator runs over *matched*
   ingredients, denominator is *total* recipe mass → unmatched
   ingredients are treated as nutrient-free. Energy cross-checks exactly
   vs `dish_macros` (e.g. grilled cheese 369.86 = 1494.2 / 404 × 100).
2. **Absent FDC nutrient → 0.** A food with no fibre/sugars/sat-fat row
   contributes 0 — matches Nutri-Score's "absent positive = 0 points"
   convention and is conservative for negatives. Non-zero presence in the
   FDC table: sat-fat 90%, sodium 96%, sugars 66%, fibre 61%.
3. **FVN% estimation.** Each ingredient classified fruit / vegetable /
   legume / nut / qualifying-oil / none via FDC food-category prior +
   curated description keywords, then summed by mass share. *Exclusions
   that win first* (per the official FSAm-NPS rule): starchy roots/tubers
   (potato, **sweet potato**, cassava, yam, plantain, tapioca) do NOT
   count as vegetables; only **olive / rapeseed-canola / walnut** oils
   count (sunflower, vegetable-NFS, sesame, palm, soybean excluded);
   soy sauce, plant-based milks, juice *drinks*, spices & herbs excluded.
   28-case self-test guards the rules. ~31% of FDC foods qualify; manifold
   `fvn_pct==0` for only 2.6% of dishes.
4. **Food-type variant detection.** Default **general**. Beverage only by
   conservative whole-word, **non-alcoholic** drink terms (Clark excluded
   alcohol) with a solid-food guard list — after de-bugging substring
   collisions ("platter"→latte, "shaken"→shake, "margarita pizza"→
   cocktail), **0 beverages survive in the manifold** (a prepared-dish
   corpus has no standalone soft drinks; all "shaken" hits are Vietnamese
   shaking-beef, correctly general). Cheese (40) / added-fat (12) variants
   fire when one ingredient is >50% of mass (cream-cheese spreads, paneer,
   butter-sauce dishes) — cheese keeps protein points; fat scores sat-fat
   as a % of total lipid.

**Coverage.** Mean `fdc_match_rate_mass` = 0.991; only 63 manifold dishes
< 0.50 (kept, flagged via the column for downstream filtering).

**Validation (manifold, n=39,166).** Grade mix A 24.6 / B 29.2 / C 23.7 /
D 20.7 / E 1.8 %; points min −12, median 2, max 30. Most nutritious:
tofu/bean/vegan dishes (FVN 80–97%, fibre 5–8 g) at −12. Least: butter/
caramel/fried-wing dishes (sat-fat 30–41 g, Na ~1 g) at +30, grade E.
Mean 1–5 by cuisine bucket: vegetarian 2.02 < chicken 2.16 < seafood 2.45
< pasta 2.94 < beef 3.02 — reproduces Clark's plant-vs-meat nutrition
gradient. The known Nutri-Score quirk (oily fish/salmon graded D because
the N≥11 rule drops its protein points) reproduces faithfully.

**Known limitations.** (a) Per-ingredient FDC nutrients are US (FDC), not
UK (Clark used McCance & Widdowson) — chosen for consistency with the
existing macro/LCA pipeline. (b) FVN% is a rule-based ingredient estimate,
not an LLM screen — the swappable, highest-uncertainty input; herbs like
cilantro fall to `none` (negligible mass). (c) Original 2017 algorithm
(matches Clark), not the 2022/2023 revision. (d) 0–100 scaling uses the
general-food range [−15, 40] for all foods, as Clark plots one axis.

## Layer MH-1 (2026-06-04) — per-dish health impact (mealhealth / GBD ΔYLL)

**What.** Applied Koen van Greevenbroek's `mealhealth` package
(github.com/Sustainable-Solutions-Lab/mealhealth, v0.1.0) to every
canonical dish, recipe → mealhealth directly (NutriScore is *not* an
intermediate). `mealhealth.assess_meal()` substitutes a meal into a
country baseline diet at constant calories and returns the change in
diet-attributable **years of life lost** (ΔYLL) via GBD relative-risk
dose–response curves. Country = USA, mode = `median` (individual-lifetime
ΔYLL for the median adult eating the dish daily for life). Sign: ΔYLL > 0
⇒ years gained, < 0 ⇒ lost. Code: `nutrition/gbd_classify.py`,
`nutrition/compute_mealhealth.py`. Outputs `dish_mealhealth.jsonl`
(75,323) + `dish_mealhealth_manifold.csv` (39,166, dish_meta-joined).

**Classification → 7 GBD groups.** `gbd_classify.py` maps each FDC food
(fdc_id, via `ingredient_gbd.csv`, 13,694 foods) to one of fruits /
vegetables / whole_grains / legumes / nuts_seeds / red_meat /
processed_meat, else `other`. The four shared groups delegate to the
Nutri-Score FVN classifier (oil/none → other); the two NutriScore never
modelled get dedicated rules, **processed_meat checked before red_meat**
(cured pork is processed, not unprocessed) and a meat-alternative veto
(soy/tofu/tempeh → legumes, other plant patties → other). whole_grains
requires an explicit whole-grain marker — **refined grains (white bread/
rice, all-purpose flour, plain pasta) deliberately fall to `other`** and
act through calories only, matching GBD (whole-grain is the risk factor,
not total grain). 35-case self-test passes. 53.2% of FDC foods land in a
risk group.

**Mass-basis normalization (mealhealth requirement, docs/food_groups.md).**
Group masses must match the curves' native basis. Applied per-ingredient,
**only when the matched FDC description shows a cooked/hydrated state**
(markers: cook/boil/roast/braise/grill/broil/fried/baked/steam/stew/
canned/…), since some ingredients are already dry (flour) or raw:
whole_grains ×0.45 and legumes ×0.40 (cooked→dry); red_meat &
processed_meat ×1/0.7 (cooked→raw retail). Fruits/vegetables/nuts are
fresh as-eaten, no conversion. **This is the highest-uncertainty step**
(recipe grams don't carry an explicit cooked/raw flag; cooked-state is
inferred from the FDC match string).

**Meal unit + calories.** One *served dish* = one meal: group grams summed
over the recipe ÷ `n_servings`; `meal_kcal` = `energy_kcal_per_serving`
from dish_macros. Groups < 0.05 g/serving dropped. Unmatched ingredients
(~1% mass) contribute neither group mass nor kcal — `match_rate` recorded
per dish (mean 0.990; 1,317 dishes < 0.80).

**Skips.** 1 dish no recipe mass; 1 (`acqua panna still water`, cluster
119957) no kcal → no assessment (water; correctly un-scored). Both kept in
the jsonl with `mealhealth: null` + an `error` field.

**Validation (n=75,322 assessed).** ΔYLL mean −0.213 yr, median −0.026,
range −4.95…+0.56. Net-harmful 64.7% / net-beneficial 35.3%. Worst:
all-meat pizza, prime-rib, ribeye, deep-fried cheeseburger (red+processed
meat dominated). Best: arepas & veggie sandwiches (whole grains + fruit +
veg + legumes). Group prevalence in manifold-assessed dishes: vegetables
95.8%, fruits 43.0%, red_meat 27.8%, legumes 14.5%, processed_meat 13.9%,
nuts_seeds 11.4%, whole_grains 2.0% (low by design — most restaurant
grains are refined → other); 1.6% have no risk group (kcal-only impact).
Face-valid red-meat/processed-meat gradient.

**Known limitations.** (a) mealhealth models 7 food groups × 4 diseases
(CHD/Stroke/T2DM/CRC) only — **no sodium** (the largest GBD dietary risk
factor; Koen's proposed extension, for which our NUT-4 per-dish sodium is
the input), no SSB/fibre/calcium/PUFA/trans-fat. (b) Everything outside
the 7 groups collapses into `meal_kcal`, so dishes differing only in oil/
cheese/refined-flour score identically except via calories — coarse by
design. (c) Cooked→dry/raw basis inferred from FDC strings, not a true
preparation flag (see above). (d) GBD baseline = US population diet;
ΔYLL is "eat this dish *instead of* the average US diet, daily, for life".
