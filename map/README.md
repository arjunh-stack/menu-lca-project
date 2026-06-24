# 🗺️ The Culinary Archipelago — a map of dishes

A for-fun cartographic reimagining of the dish manifold: coherent clumps
of related dishes (burgers, wings, pizza, sushi, ramen…) become **broad
islands** on an old-timey archipelago chart — hand-drawn coastlines,
compass rose, cartouche, gazetteer.

There are **two variants** of how popularity is drawn — compare and pick:

| variant | how popularity shows up | files |
|---------|-------------------------|-------|
| **A — topo** | popularity is *elevation*: contour lines + hypsometric tint, popular clusters rise into red mountains | `dish_archipelago_topo.png` / `.pdf` |
| **B — cartogram** | popularity is *island area*, on a **log scale**: each island's area grows with `log(menu appearances)`, so popularity is legible without one island dwarfing the rest. Dorling-style packing keeps them from overlapping; no dots | `dish_archipelago_footprint.png` / `.pdf` |

![topo](dish_archipelago_topo.png)
![footprint](dish_archipelago_footprint.png)

## Shared pipeline

- **Source:** the merged **195k-dish manifold** (`experiment/manifold_merged/`) —
  UMAP coords (`umap.json`) + dish metadata (`dish_meta.csv`).
- **Filter:** dishes listed on **only one menu** (`total_count == 1`) are
  dropped (114,448 of them) → **80,768 dishes** charted. This is a
  render-time subset for legibility, not a pipeline filter, so it is
  intentionally not logged in `FILTERING_LOG.md`.
- **Broad islands:** the manifold's dense core is too connected to carve
  with plain spatial clustering, so we take the precomputed UMAP semantic
  `region`s (540 of them) and **merge neighbours** (agglomerative on
  region centroids, `ISLAND_MERGE_DIST`) into ~50 broad landmasses.
- **Names:** TF-IDF over each island's dish names picks its most
  *distinctive* token → "Burger", "Pizza", "Wings", "Enchiladas"…
  Duplicate names auto-diversify to each island's next-best token.
- **Colour:** ColorBrewer **RdYlBu** — red = popular/hot, blue = rare/cold
  (per the RdYlBu design system).
- **Easter eggs:** dishes that hide *inside* a bigger island get tiny
  hamlet labels — **Gator Hole** (alligator dishes in the Cajun/seafood
  island), Escargot Point, Frog Cove, Oxtail Bay.

## Outputs

`dish_archipelago_topo.{png,pdf}`, `dish_archipelago_footprint.{png,pdf}`
(both 7 in wide @ 600 dpi → 4200 px), plus `gazetteer_topo.csv` /
`gazetteer_footprint.csv` (index of every named island).

## Rebuild

```bash
python3 map/build_archipelago.py            # variant A (topo)
python3 map/build_archipelago_footprint.py  # variant B (footprint)
```

Fonts are bundled in `map/fonts/` (IBM Plex Serif/Mono + Cinzel) so the
render is reproducible without installing anything.

## Tweakables

Shared knobs live at the top of `build_archipelago.py`:

- `ISLAND_MERGE_DIST` — bigger → fewer, broader islands (60 ≈ 90 isles,
  85 ≈ 50, 120 ≈ 30).
- `MIN_LABEL_PTS` — smallest island that gets a name.
- `TOPO_LEVELS`, `SIGMA_POP` — topography detail/smoothing (variant A).
- `LAND_FRAC`, `LOG_PAD`, `DORLING_PAD` (in `..._footprint.py`) — total
  land area, how much the rarest isle still shows under the log mapping,
  and the sea gap kept between islands (variant B).
