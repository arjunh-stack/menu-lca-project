#!/usr/bin/env python3
"""SI figure — provenance of the ingredient emission factors.

Two panels: how many EF assignments come from each source database,
(a) by distinct ingredient string and (b) occurrence-weighted across all
recipe ingredient rows. Source recovered per ingredient from the LCA match
cache's source_description (the cache mislabels common cached hits as
"Local cache"; here every factor is attributed to its true database).

Input : lca/ingredient_ef_table.csv + lca/data/ef_cache.json
Output: figures/figS_ef_sources.{png,pdf}
"""
import csv, json, os, re, collections
import matplotlib.pyplot as plt
import rdylbu_style as rb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EF_TABLE = os.path.join(REPO, "lca", "ingredient_ef_table.csv")
CACHE = os.path.join(REPO, "lca", "data", "ef_cache.json")

# canonical source order + colours (on the RdYlBu palette, not a hot/cold metric)
ORDER = ["AGRIBALYSE v3.2", "SU-EATABLE LIFE", "Unmatched"]
COLOR = {"AGRIBALYSE v3.2": rb.BLUE, "SU-EATABLE LIFE": rb.ORANGE,
         "Unmatched": rb.MUTED}
FIRST = re.compile(r"\(([A-Za-z][^:()]*?):")


RECIPES = os.path.join(REPO, "experiment", "recipe_run", "recipes_for_downstream.jsonl")


def load():
    entries = json.load(open(CACHE))["entries"]
    by_ing, by_occ = collections.Counter(), collections.Counter()
    ef_src = {}
    for r in csv.DictReader(open(EF_TABLE)):
        if r.get("unmatched", "").strip() == "True":
            s = "Unmatched"
        else:
            m = FIRST.search((entries.get(r["ingredient"], {}) or {}).get("source_description", "") or "")
            s = m.group(1).strip() if m else r.get("primary_source", "").strip()
        if s not in ("AGRIBALYSE v3.2", "SU-EATABLE LIFE"):
            s = "Unmatched"           # fold tiny parse-glitch / blanks
        ef_src[r["ingredient"]] = s
        by_ing[s] += 1
        by_occ[s] += int(r.get("occurrences", 0) or 0)
    # mass-weighted: total grams of ingredients per source across all recipes
    by_mass = collections.Counter()
    for line in open(RECIPES):
        o = json.loads(line)
        for ing in (o.get("ingredients") or []):
            nm = (ing.get("ingredient") or "").strip().lower()
            by_mass[ef_src.get(nm, "Unmatched")] += float(ing.get("grams") or 0)
    return by_ing, by_occ, by_mass


def panel(ax, counts, title, unit, mass=False, show_y=True):
    total = sum(counts.values())
    vals = [counts.get(s, 0) for s in ORDER]
    y = range(len(ORDER))
    bars = ax.barh(y, vals, color=[COLOR[s] for s in ORDER],
                   edgecolor=rb.INK, linewidth=0.6, height=0.66, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(ORDER if show_y else [], fontfamily=rb.SANS, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals) * 1.18)
    for b, v in zip(bars, vals):
        lab = (f"{v/1000:,.0f} kg\n{v/total*100:.1f}%" if mass
               else f"{v:,}\n{v/total*100:.1f}%")
        ax.text(b.get_width() + max(vals) * 0.015, b.get_y() + b.get_height() / 2,
                lab, va="center", ha="left",
                fontsize=6.6, family=rb.MONO, color=rb.INK, linespacing=1.15)
    ax.set_title(title, fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold",
                 loc="left", pad=10)
    ax.text(0, 1.02, unit, transform=ax.transAxes, va="bottom", ha="left",
            fontsize=5.6, family=rb.MONO, color=rb.MUTED)
    ax.set_xticks([])
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(rb.INK)
    ax.tick_params(length=0)


def main():
    rb.apply()
    by_ing, by_occ, by_mass = load()
    fig, axes = rb.subplots(1, 3, width="double", height=2.7)
    panel(axes[0], by_ing,
          "a · By distinct ingredient",
          f"EF assignments · n = {sum(by_ing.values()):,} ingredients")
    panel(axes[1], by_occ,
          "b · By occurrence",
          f"ingredient rows · n = {sum(by_occ.values()):,}", show_y=False)
    panel(axes[2], by_mass,
          "c · By weight",
          f"total ingredient mass · {sum(by_mass.values())/1e6:,.0f} t",
          mass=True, show_y=False)
    rb.serif_title(fig, "Provenance of ingredient emission factors", y=1.0)
    fig.text(0.5, -0.02,
             "Each ingredient is matched to a life-cycle inventory in AGRIBALYSE v3.2 "
             "(France, ag+processing) or SU-EATABLE LIFE; unmatched = no defensible match "
             "(non-foods / specialty items). AGRIBALYSE leads by count but its share falls "
             "under occurrence- and mass-weighting as SU-EATABLE covers common, high-mass staples.",
             ha="center", va="top", family=rb.MONO, fontsize=5.0, color=rb.MUTED, wrap=True)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.74, bottom=0.14, wspace=0.28)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"figS_ef_sources.{ext}"),
                    dpi=300, bbox_inches="tight")
    print("wrote figS_ef_sources.png / .pdf")
    print("by ingredient:", dict(by_ing))
    print("by occurrence:", dict(by_occ))


if __name__ == "__main__":
    main()
