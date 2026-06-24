# Proposal P-pasta (2026-05-03) — pasta category cleanup proposals

**Status:** PROPOSED (not yet applied).
**Input:** `dish_canonical_summary_v17.csv` (114,855 canonicals).
**Scope:** 7,665 canonicals containing whole-word `pasta` / `pastas`. Reviewed top ~300 by `total_count` plus targeted greps.

**Method:** awk-filtered on whole-token match, sorted by count desc, then targeted greps for: Thai romanization variants (`pad`/`phad`, `lad na`/`nah rad`, `woonsen`/`woon sen`), Italian↔English food terms (`parmigiana`/`parmesan`, `pollo`/`chicken`, `formaggio`/`cheese`, `funghi`/`mushroom`, `melanzane`/`eggplant`, `salsiccia`/`sausage`, `gamberi(etti)`/`shrimp`), abbreviations (`mac`/`macaroni`, `veg`/`vegetable`), synonyms (`vegetable`/`vegetarian`/`veggie`), and known typos (`fettucine`, `lasagne`, `gnochi`, `leanguini`, `padthai`, `lomein`). Cross-checked aliases for ambiguous cases.

**Outputs:**
- `/proposals/category_pasta.csv` — 30 merges + 13 judgment/info flags.

**Rows touched if applied:**
- 30 merge sources collapsed into ~17 destination clusters spanning Thai romanization (`pad`/`phad`, `woon sen`), Italian/English (`parmigiana`≡`parmesan`), abbreviations (`mac`/`macaroni`, `veg`/`vegetable`), synonym pairs (`veggie`/`vegetable`/`vegetarian`).
- Top three by source count: `chicken parmigiana pasta` (158) → `chicken parmesan pasta`; `noodle pad pasta thai` (142) → `pad pasta thai`; `eggplant parmesan pasta` (126) → `eggplant parmigiana pasta`.
- Italian/Spanish food-term variants (`pollo`, `formaggio`, `funghi`, `melanzane`, `salsiccia`, `gamberi`) appear only in tiny clusters (≤16 count) — below review threshold, skipped.

**Conservative carve-outs (NOT proposed):**
- Pasta shapes distinct: penne, ziti, rigatoni, tortellini, tortelloni (size variant of tortellini per playbook), fettuccine, linguine, cavatappi, manicotti, cannelloni, ravioli, gnocchi, bucatini.
- Sauces distinct: pesto, alfredo, marinara, vodka, bolognese, carbonara, puttanesca, aglio olio, pomodoro, arrabiata, scampi, piccata, rosa, sorrentina.
- Proteins distinct: chicken, shrimp, beef, pork, seafood, lobster, crab, salmon, clams, sausage, meatballs.
- `chicken parmesan pasta spaghetti` and `eggplant parmigiana pasta spaghetti` NOT merged into generic parm pasta — `spaghetti` specifies shape.
- Filler `classic`/`original`/`signature`/`special`/`plain` not removable per playbook.
- `marinara pasta` vs `marinara pasta sauce` flagged not merged — `sauce` borderline content token.
- `lomein` concatenated, `fettucine` single-c, `padthai` concatenated — only 1-count canonicals, below threshold.
