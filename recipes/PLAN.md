# Recipes pipeline — porting plan

**Scope.** Dish name → recipe, where *recipe* = `[{ingredient, grams}, ...]`.
That's it. No species identification, no emissions mapping, no LCA. LCA is
a later step on top of this output.

## Source: `../menu-project/ingredient_pipeline.py`

That one file (1,136 lines) is where the production logic lives. We need a
small slice of it. Everything else in the sibling repo is either
benchmark-only, study-only, or downstream of recipes.

### What we actually need (from `ingredient_pipeline.py`)

| Symbol                                                  | Lines (approx) | Purpose                                                   |
| ------------------------------------------------------- | -------------- | --------------------------------------------------------- |
| `STRUCTURAL_REFERENCES` dict                            | \~160          | the grams-first few-shot examples, one per cuisine bucket |
| `CATEGORY_MAP` + `get_structural_reference()`           | \~25           | cuisine tag → which reference to use                      |
| `build_ingredient_prompt()`                             | \~25           | wraps the user prompt with the structural reference       |
| `parse_json_response()` + `parse_ingredient_response()` | \~40           | JSON-fence stripping + grams→proportion computation       |
| `call_openrouter()` shape                               | \~40           | request payload format, retry on 429/5xx                  |

Total real code being ported: **\~300 lines** of the 1,136. The rest of
`ingredient_pipeline.py` we drop:

* Synonym dictionary + `get_canonical`/`synonym_match`/`fuzzy_ingredient_match`
  (used only by the benchmark scripts for scoring against TheMealDB).

* Species step (`build_species_prompt`, `parse_species_response`) — that's
  the second LLM call we're cutting.

* SQLite queries + CLI shell + threaded executor — we feed canonical dishes
  from this repo's CSVs, not raw `menus` rows, and we use async like the rest
  of this repo.

### What we drop entirely

`emissions.py`, `unit_converter.py`, `ground_truth_recipes.py`, every
`benchmark_*.py`, `run_*.py`, `study_*/`, `METHODOLOGY.md`, `mydb.sqlite`,
all output figures.

## What changes when we port

1. **Input.** Original took `(menu_name, menu_desc, restaurant_category)` row
   from `menus`. We feed canonical dishes from
   `dish_canonical_summary_v18.csv` (`cluster_id`, `canonical_name`,
   `total_count`).

2. **Concurrency.** Async/httpx with semaphore + resumeable CSV writer —
   same shape as `screen_keeps_deepseek.py`. Replaces the threaded
   `requests.Session` from the original.

3. **Output.** JSONL keyed by `cluster_id` so it joins cleanly against
   `dish_canonical_summary_v18.csv`. One row per dish, with an `ingredients`
   list inside.

## Open questions for you

**Q1 — Dish-name text fed to the LLM.**
Canonical name is token-sorted (`alfredo chicken pasta`). Aliases are not.

* (a) feed canonical name as-is — simplest, may degrade quality.

* (b) join to `dish_aliases_v18.csv` and feed the highest-count alias
  ("Chicken Alfredo Pasta") — more natural, one extra step.

**Q2 — Cuisine context.**
The structural reference picker (`CATEGORY_MAP`) needs a cuisine tag. The
benchmarks showed this was the only prompt-engineering change that helped.

* (a) always use the `"default"` reference.

* (b) precompute a representative cuisine per canonical dish from the
  `restaurants.category` tags of restaurants that serve it (one-time
  aggregation against `menu_dishes.sqlite`).

* (c) let the LLM pick from the dish name (extra call, probably overkill).

**Q3 — Run scope on first pass.**
Full 113K dishes (\~\$35 at DeepSeek v3 rates, \~75 min at 25/s), or a
validation slice first (top 500 by count, \~10 min, eyeball outputs)?
Recommend validation first.

## Proposed folder layout

```
recipes/
├── PLAN.md                  (this file)
├── pipeline.py              (async runner, prompt builder, parser, resumeable writer)
└── structural_references.py (the few-shot examples + cuisine→bucket map)
```

Two source files. `structural_references.py` is data-only; `pipeline.py` is
control flow. Output drops into this folder later (`recipes_v1.jsonl`).

## Execution order (once greenlit)

1. Extract `structural_references.py` from `ingredient_pipeline.py`.
2. Write `pipeline.py`: async client, prompt builder, JSON parser,
   resumeable JSONL writer keyed by `cluster_id`.
3. Validate on a small slice — eyeball 20 outputs.
4. Run the full canonical dish set.

LCA is a separate next step and is not in this folder yet.
