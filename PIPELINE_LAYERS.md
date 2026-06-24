# Pipeline layers — dish-deduplication pipeline reference

Compact overview of every cleaning + filtering layer applied to the Kaggle SQLite menu database. For full details and audit-file references, see `DATA_CLEANING.md`.

## Dish-count progression

| Layer | What it does | Resulting count |
|---|---|---|
| **Source** | Raw `restaurants` table | 63,469 restaurants |
| **Source** | Raw `menus` table | 5,117,217 rows |
| **C1** | Null one bizarre `price_range` value | (no row delta) |
| **C2** | HTML-unescape text columns idempotently | 528,175 row updates |
| **C3** | Add numeric `menus.price_usd` (parsed from "9.99 USD") | 5,117,217 rows populated |
| **C4** | Canonicalize `restaurants.category` tag list | 380 → 365 distinct tags |
| **C5** | Canonicalize `menus.category` (whole-db) | 73,048 → 62,394 distinct |
| **Layer 1** | Drop restaurants by user-marked exclusion tags (87 tags: pharmacies, grocery, dessert/bar/etc.) | 63,469 → 45,109 restaurants; menus 5,117,217 → 3,286,489 |
| **Layer 2** | Drop non-mains menu sections (drinks/desserts/sides/sauces/kids/catering, 17,209 distinct categories) | menus 3,286,489 → 1,659,202 |
| **Layer 3** | Conservative dish-name normalization (case, html, sizes, qty, sort tokens) | 288,307 distinct names |
| **Layer 4** | Infer dish format from `menus.category` (Tuna + Wraps section → `tuna wrap`) | 297,383 distinct |
| **Layer 5** | Heuristic flagger — drop pure marketing/instruction/single-token rows | 296,140 → 285,011 |
| **Layer 6** | Lenient per-row LLM classification (30 parallel agents) | 276,431 |
| **Layer 7** | Strict "recipe-test" LLM re-classification (30 parallel agents, "when in doubt → DROP") | 195,949 |
| **Layer 8** | Mechanical drop of long/repeat-token fragments | 195,551 |
| **Layer 9** | Hybrid alias clustering (fuzz.ratio bucketed by token count) | 165,655 canonical dishes |
| **Layer 10** | Curated synonym dictionary (sub/hoagie/grinder, prawn/shrimp, etc.) | 164,823 |
| **Layer 11A** | Heuristic drop of bare ingredients + redundant numbered variants | 163,211 |
| **Layer 11B** | LLM strict-pass on the "digit-but-no-match" review pile (3 parallel agents) | 153,007 |
| **Layer 12** | Token-based drop of side/snack/appetizer/combo/à-la-carte indicators | 149,244 |
| **Layer 13** | Strip floating single-letter tokens (apostrophe-s, BMT acronyms, w/) | 148,181 |
| **Layer 14** | LLM-judged long-tail merges (token-overlap → Gemini Flash YES/NO, round 1) | 124,800 |
| **Layer 15** | Strip Subway/chain marketing tokens (`footlong`, `pro`) | 124,712 |
| **Layer 16** | Drop canonicals containing `meal` / `dinner` (combo-deal labels) | 122,897 |
| **Layer 17** | Second LLM long-tail merge pass (post-15/16 candidates → Gemini Flash) | 117,154 |
| **Layer 18** | sub↔sandwich relaxed LLM pass (skeleton-equal pairs) | 115,348 |
| **Layer 18B** | *(reverted)* — over-relaxed prompt produced false merges (`eggplant parmesan` ≠ `eggplant parmesan sub`) | n/a |
| **Layer 19** | Drop bare-format canonicals (`sandwich sub`, `burger`, `plate taco`) | 115,320 |
| **Layer 20** | LLM keep/drop on over-tokenized singleton fragments (≥5 tokens, no allowlist noun) | 114,920 |
| **Layer 21** | Drop add-on canonicals (`add chicken`, `add avocado burrito`) | 114,873 |
| **Layer 22** | Strip artifact doubled tokens (preserve `mahi mahi`, `bang bang`, etc.) | 114,865 |
| **Layer 23** | Targeted quesadilla cleanup (Spanish↔English, plural→singular, bf→buffalo) | 114,855 |
| **Layer 24** | Parallel-agent multi-category cleanup (11 categories, 1,130 high-confidence merges/renames) | 113,925 |
| **Layer 25** | Recipe-test cross-screen: Gemini Flash + DeepSeek v4 Pro asked "could a chef Google this exact name and find a real recipe?" → 33,620 drops + 1,072 rescues | **79,590 canonical dishes** |

## Final reconstructed table (`menu_dishes.sqlite`)

Current `menu_dishes.sqlite` was reconstructed from v18 aliases on 2026-05-06:

- **1,126,856** rows of `(restaurant, menu_item, canonical_dish)`
- **42,557** distinct restaurants
- **107,581** distinct canonical dishes appearing in actual menu data
- **2,678** distinct zip codes

**After rebuild against v19** (pending — `build_dish_index.py` still
points at `dish_aliases_v18.csv`; updating to `_v19.csv` is a one-line
change):

- v19 canonicals: 79,590
- v19 canonicals with menu rows after rebuild: **75,325** (the actionable dataset vocabulary)
- v19 canonicals with no menu row (vocab orphans): 4,258
- canonicals currently in `menu_dishes.sqlite` that Layer 25 dropped from v19: 32,256

The 4,258 v19 vocab orphans are normalizer-key drift across layers
(Layer 22 diagnostic), down from 6,344 under v18 because Layer 25's
recipe-test screen dropped many of the orphans as non-dishes anyway.

---

## Layer details

### Cleaning (C1–C5) — in-place db modifications

Idempotent. Implemented in `clean_db.py` and `clean_menu_categories.py`.

- **C1** — Set one anomalous `price_range = '$$$$$$$$$$$$$$$$$'` to NULL (Schlotzsky's Deli, Port Arthur TX).
- **C2** — HTML-unescape `restaurants.category`, `menus.name`, `menus.description` until idempotent. Handles double-encoding (`&amp;amp;`) and wrong-cased entities (`&Amp;`).
- **C3** — Add `menus.price_usd REAL` parsed from `"9.99 USD"` text. 5.1M rows populated.
- **C4** — Canonicalize the comma-separated `restaurants.category` tag list. 380 → 365 distinct tags. Mapping in `category_canonical_mapping.csv`.
- **C5** — Canonicalize `menus.category` (single label per row). 73,048 → 62,394 distinct whole-db. 713,216 row updates. Mapping in `menu_category_canonical_mapping.csv`.

### Layer 1 — Exclude restaurants by user-marked category tags

**Source:** `dedup.py:load_exclude_tags`. User reviewed all 380 unique tags and marked 87 to exclude (pharmacies, grocery, liquor, beauty, retail, dessert/coffee/snack-only spots, bars).
**Effect:** 63,469 → 45,109 restaurants; menus 5,117,217 → 3,286,489.

### Layer 2 — Exclude non-main-dish menu sections

**Source:** `dedup.py:load_excluded_menu_categories`. Two user-approved lists totaling 17,209 distinct menu categories: drinks, desserts, sides, sauces, kids menus, delivery-app surfaced sections, catering bundles, plus ambiguous combos/salads/soups/sushi/specials.
**Effect:** menus 3,286,489 → 1,659,202.

### Layer 3 — Fuzzy dish-name normalization

**Source:** `dedup.py:normalize`. HTML-unescape → lowercase → strip leading enumerations → remove parenthetical content → strip `<num> [pc/ct/pack]` (keeps the dish noun) → remove `<num> <unit>` → remove size words → remove safe filler (and/with/the/a/of/in/on) → strip non-alphanumeric → collapse whitespace → **alphabetize tokens**. The token-sort step makes word order meaningless.

### Layer 4 — Infer dish format from `menus.category`

**Source:** `dedup.py:format_from_category`. Match category against format-keyword regexes (`wrap`, `sub`, `sandwich`, `bowl`, `pizza`, `taco`, `burrito`, `quesadilla`, etc.). If exactly one matches, append the format token; if 0 or 2+, skip. Singularize plurals during fold-in.
**Effect:** 660,175 rows had a format token inferred; distinct names 288,307 → 297,383.

### Layer 5 — Heuristic flagger

**Source:** `flag_non_dishes.py` → `apply_dish_flags.py`. Drops single-token junk from a curated list (`meal`, `pack`, `combo`, `plate`, `box`, `your`, `own`, …), multi-word combos where every token is junk, and "build/pick/make/create + your/own" instruction patterns.
**Effect:** 297,383 → 285,011 (1,243 dropped).

### Layer 6 — Lenient per-row LLM classification

**Source:** 30 parallel `Agent` calls each with ~9,500 rows. Verdicts: keep / drop with reason (`drink`, `dessert`, `side`, `snack`, `sauce`, `bulk`, `deal`, `instruction`, `ingredient`, `fragment`, `marketing`). Tie-breaker: "when in doubt → keep".
**Effect:** 285,011 → 276,431.

### Layer 7 — Strict LLM re-classification

**Source:** 30 parallel agents with strict "recipe test" rubric — keep only if a chef could Google-search the exact name and find a real recognizable dish. Tie-breaker: "when in doubt → DROP".
**Effect:** 276,431 → 195,949.

### Layer 8 — Drop pathological long/repeat-token fragments

**Source:** `drop_long_fragments.py`. Drop if token count > 12, OR any single token appears ≥ 3 times, OR ≥ 2 distinct tokens each appear ≥ 2 times.
**Effect:** 195,949 → 195,551.

### Layer 9 — Alias clustering (collapse misspellings & variants)

**Source:** `cluster_aliases.py`. Sort by frequency desc → bucket by token count → within each bucket, greedy fuzzy-clustering with `rapidfuzz.fuzz.ratio` ≥ 90 → highest-count wins canonical.
**Effect:** 195,551 → 165,655 canonical dishes.

### Layer 10 — Curated synonym dictionary

**Source:** `synonyms.csv` (manual) → `validate_synonyms.py` (preview impact) → `apply_synonyms.py` (rewrite tokens, then group + merge).
**APPLY entries:** sub/hoagie/grinder/poboy, pancake/flapjack/hotcake, prawn→shrimp, gamba→shrimp, hamburger→burger, fettuccini/fettucini→fettuccine, linguini→linguine, spagetti→spaghetti, panini variants, gyros→gyro, aubergine→eggplant, calamari→squid, escargot→snail, frites→fries.
**REJECTED:** wedge→sub (false positives in salad wedge / potato wedges), po→sub (`ma po tofu`!), boy→sub, hero→sub, cheeseburger→burger.
**Effect:** 165,655 → 164,823.

### Layer 11A — Bare ingredients + redundant numbered variants

**Source:** `flag_ingredients_and_numbers.py` → `apply_ingredients_and_numbers.py`. Drops bare proteins (`catfish`, `brisket`, `red snapper`, `prime rib`), redundant `<num> X` ↔ `X` collapses, `by <pricing>` fragments.
**Effect:** 164,823 → 163,211.

### Layer 11B — LLM strict pass on digit-with-no-match review pile

**Source:** 3 parallel agents on 10,779 names with digits but no clean number-strip match. Recognized intrinsic-number dishes (`chicken 65`, `7 layer dip`, `4 cheese pizza`, `5 spice chicken`).
**Effect:** 163,211 → 153,007 (10,204 dropped).

### Layer 12 — Token-based side/snack/combo drop

**Source:** `flag_sides_combos.py`. Drop any cluster containing: `snack/snacks, side/sides, appetizer/appetizers/starter/starters, topping/toppings, combo/combos, carte` (alphabetized "à la carte"). NOT in drop set: `sauce/dip/plain/extra` (over-merge risk).
**Effect:** 153,007 → 149,244.

### Layer 13 — Strip floating single-letter tokens

**Source:** `clean_single_letters.py`. 8,982 canonicals with apostrophe-s splits (`burger dave s`), BLT/BMT acronym splits (`b l t wrap`), `w/` leftovers. Strip → re-sort → merge if matches existing canonical, else rename.
**Effect:** 149,244 → 148,181 (959 merge + 7,919 rename + 104 drop).

### Layer 14 — LLM-judged long-tail merges (round 1)

**Source:** `find_merge_candidates.py` (token-overlap candidate gen, 128,388 pairs) → `judge_merge_candidates.py` (async OpenRouter Gemini Flash, 50 concurrency, ~660 pairs/sec) → `apply_judged_merges.py`. 30,243 YES → 23,381 unique singletons absorbed.
**Effect:** 148,181 → 124,800.

### Layer 15 — Strip chain marketing tokens

**Source:** `clean_chain_marketing.py`. Strip `footlong` / `pro` (Subway terms). 121 canonicals → 88 merge + 33 rename.
**Effect:** 124,800 → 124,712.

### Layer 16 — Drop `meal` / `dinner` canonicals

**Source:** `drop_meal_dinner.py`. Drop combo-deal labels (`chicken meal mixed`, `meal whopper`, `chicken dinner`, `dinner roasted turkey`). 1,815 dropped (1,134 dinner / 669 meal / 7 meals / 5 dinners). NOT in drop set: `lunch`, `breakfast`, `platter`, `special`.
**Effect:** 124,712 → 122,897.

### Layer 17 — Second LLM long-tail merge pass

**Source:** `find_merge_candidates_v2.py` → `judge_merge_candidates_v2.py` → `apply_judged_merges_v2.py`. 69,346 candidate pairs against v9 → 6,404 YES → 5,743 unique singletons absorbed.
**Effect:** 122,897 → 117,154.

### Layer 18 — sub↔sandwich relaxed LLM pass

**Source:** `find_sub_sandwich_pairs.py` (skeleton-equal candidate gen, 2,411 pairs) → `judge_sub_sandwich_pairs.py` (relaxed prompt: "Subway calls them subs, others call same item a sandwich; default YES") → `apply_sub_sandwich_merges.py`. 1,806 YES merges.
**Effect:** 117,154 → 115,348.

### Layer 18B — *(REVERTED)*

Attempted re-judge of L18's 605 NO verdicts with stricter prompt. 517 new merges unlocked, but model overcorrected — collapsed `eggplant parmesan` (over noodles) with `eggplant parmesan sub` (on bread), `chicken grilled` plate with `chicken grilled sandwich`, etc. **Reverted in full**; the right approach for future would be a curated allowlist of intrinsically-sandwich dish names (BLT, cheeseburger, philly cheesesteak, reuben, cubano, gyro).

### Layer 19 — Drop bare-format canonicals

**Source:** `drop_bare_format.py`. Drop canonicals whose tokens are a subset of `{sub, sandwich, wrap, bowl, burger, pizza, taco, burrito, salad, soup, plate}` with ≤2 tokens.
**Effect:** 115,348 → 115,320 (28 dropped, 8,492 menu rows).

### Layer 20 — LLM keep/drop on over-tokenized singleton fragments

**Source:** `flag_long_singletons.py` → `judge_long_singletons.py` → `apply_long_singleton_drops.py`. Singletons (count=1) with ≥5 tokens AND no token in a curated allowlist of recognizable dish nouns. Strict LLM with international-aware prompt: "KEEP regional/ethnic dishes you may not recognize personally."
**Effect:** 115,320 → 114,920 (807 flagged → 407 KEEP, 400 DROP).

### Layer 21 — Drop add-on canonicals

**Source:** `drop_addons.py`. Drop any canonical with `add` / `adds` / `addon` / `addons` token (`add chicken`, `add avocado burrito`, `add my order to utensils`).
**Effect:** 114,920 → 114,873 (47 dropped, 191 menu rows).

### Layer 22 — Strip artifact doubled tokens

**Source:** `clean_doubled_tokens.py`. 1,012 canonicals with doubled tokens. PRESERVE_DOUBLED allowlist for legit repetitions: `mahi`, `huli`, `dan`, `bang`, `peri`, `boom`, `shabu`, `yum`, `lau`, `chop`, `pon`, `woo`, `kko`, `kee`, `mao`, `kai`, `gai`, etc.
**Effect:** 114,873 → 114,865 (854 rename + 8 merge + 0 drop; 150 preserved unchanged). Big index-time win: 1,849 previously-unreachable menu rows now match (they had been hitting `lookup_key`'s `set()` dedup against doubled-token aliases).

### Layer 23 — Targeted quesadilla cleanup

**Source:** `clean_quesadillas.py`. Hand-curated 10 merges + 4 plural-renames + 1 abbreviation (`bf`/`buffalo`).
- Spanish→English: `pollo`/`chicken`, `queso`/`cheese`.
- Article omission: `pastor`/`al pastor`, `asada`/`carne asada`.
- Synonyms: `vegetable`/`vegetarian`/`veggie`.
- Plural: `brisket quesadillas`/`brisket quesadilla`.
**Effect:** 114,865 → 114,855.

Introduced the **`rename_preserved` mechanic**: when renaming a "self" alias, both the new and old alias_name are kept as alias rows (under the same cluster_id) so raw menu rows that normalize to the old form still find a canonical at index time. Adopted as the standard rename pattern from L23 forward.

### Layer 24 — Parallel-agent multi-category cleanup

**Source:** 11 read-only sub-agents in parallel, one per category. Each produces `proposals/category_<name>.csv`. Aggregated via `aggregate_proposals.py` (validates + buckets by confidence). Applied via `apply_categories.py` (cycle-aware: renames first, then merges with redirect-on-rename-collision).
**Categories:** tacos, burritos, mexican_misc (enchilada/tostada/torta/tamale/sopes), mexican_small (fajita/empanada/flauta/nachos), pizza, pasta, wings, asian_noodles, indian, salads, sushi.
**Total proposals:** 3,847 → 1,130 high-confidence applied → 930 net merges + 36 renames.
**Top per-category yields:** sushi 452 (`X roll sushi` ≡ `X roll`), asian_noodles 289 (`pasta` menu-section noise), tacos 71, mexican_misc 55, burritos/pizza 21 each, pasta/mexican_small 17 each, wings 10, indian 8, salads 5.
**Effect:** 114,855 → **113,925 canonical dishes**.

**2,418 medium-confidence + 198 judgment items held back** for opt-in user review (`proposals/aggregated_medium.csv`, `proposals/aggregated_judgment.csv`).

---

## File-naming convention

Snapshot pairs at each transformation layer:
- `dish_aliases_v<N>.csv` — long table: `canonical_name, alias_name, alias_count, cluster_id, method`
- `dish_canonical_summary_v<N>.csv` — one row per cluster: `cluster_id, canonical_name, n_aliases, total_count`

Versions: v1 (Layer 9) → v2 (L10) → v3 (L11A) → v4 (L11B) → v5 (L12) → v6 (L13) → v7 (L14) → v8 (L15) → v9 (L16) → v10 (L17) → v11 (L18) → v12 (L19) → v13 (L20) → *(v14 reserved for the reverted L18B)* → v15 (L21) → v16 (L22) → v17 (L23) → v18 (L24) → **v19 (L25, current)**.

The reconstruction script `build_dish_index.py` reads the latest alias key + applies Layers 1+2+3+4+10 to raw `mydb.sqlite` to produce `menu_dishes.csv` / `menu_dishes.sqlite`.

### Layer 25 — Recipe-test cross-screen via two independent LLMs

**Source:** `screen_recipe_test.py` (run twice — once Gemini Flash, once
DeepSeek v4 Pro) → `compare_recipe_screens_v2.py` (3-way verdict
comparator with bucket assignment) → `find_drop_rescues.py` /
`judge_rescues_gemini.py` (rescue pass for "real dish hiding inside
long-form name") → `apply_recipe_drops.py`.

**Rule:** each canonical asked "could a chef Google this exact name and
find a real, repeatable recipe?" Both models return KEEP/DROP + reason.
Bucket → action:
- BOTH_KEEP → keep
- BOTH_DROP → drop
- PRO_VETO (gemini KEEP, pro DROP) → drop, UNLESS in `RESCUE_CANONICALS`
  (verified chain item) OR pro_reason in {obscure/unknown/unrecognized}
  AND total_count ≥ 3 (protects ethnic dishes the larger model doesn't
  recognize)
- PRO_RESCUE (gemini DROP, pro KEEP) → keep
- HAS_ERROR → keep

**Effect:** 113,925 → 79,590. **33,620 dropped + 1,072 rescued.**

**Drop-reason distribution** (final applied set, top reasons):
- `dish` (Pro determined "not a real dish"): 8,037
- `gibberish`: 7,920
- `vague`: 6,851
- `possessive` (e.g. `burger dave`, `dave thomas burger`): 3,595
- `combo` (combo-plate labels): 3,299
- `regional` (model-unrecognized regional): 1,688
- `generic` (e.g. `tenders`, `bone wings`): 1,565
- `addon`, `code`, `branded`: <300 each

**Top-count drops** (illustrative of what this layer actually catches):
- cluster_id 0 `tenders` (810) — generic
- cluster_id 668 `chicken mixed` (1,497) — vague
- cluster_id 25463 `burger dave` (1,469) — possessive
- cluster_id 683 `bone wings` (1,006) — generic/nonexistent
- cluster_id 25488 `bowl meat mozza` (1,093) — pro_veto vague

**Frozen verdicts:** `recipe_screen_gemini.csv` (113,925 rows),
`recipe_screen_deepseek.csv` (30,879 — re-screen of Gemini DROPs),
`recipe_screen_deepseek_keeps.csv` (82,606 — re-screen of Gemini
KEEPs), `dish_rescue_judgments.csv` (1,072), `recipe_drops_applied.csv`
(33,620). All checked in.
