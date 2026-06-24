#!/usr/bin/env python3
"""SI figure — emission-factor source coverage BY IMPACT CATEGORY.

GHG draws on both databases (AGRIBALYSE v3.2 primary or SU-EATABLE LIFE
primary). The other impact categories (water, land, acidification,
eutrophication) are carried only by AGRIBALYSE — when a SU-EATABLE-primary
ingredient has them, they come from its secondary AGRIBALYSE match. So those
categories are attributed to AGRIBALYSE; ingredients with no AGRIBALYSE match
have no value ("no data").

Input : lca/ingredient_ef_table.csv + lca/data/ef_cache.json
Output: figures/figS_ef_by_category.{png,pdf}
"""
import csv, json, os, re, collections
import matplotlib.pyplot as plt
import rdylbu_style as rb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EF_TABLE = os.path.join(REPO, "lca", "ingredient_ef_table.csv")
CACHE = os.path.join(REPO, "lca", "data", "ef_cache.json")
FIRST = re.compile(r"\(([A-Za-z][^:()]*?):")

COL = {"AGRIBALYSE v3.2": rb.BLUE, "SU-EATABLE LIFE": rb.ORANGE, "no data": "#D9D9D9"}
CATS = [("GHG (kg CO₂e/kg)", "ghg_kgco2e_per_kg", True),
        ("Water (m³/kg)", "water_m3_per_kg", False),
        ("Land use (Pt/kg)", "land_pt_per_kg", False),
        ("Acidification", "acidification_per_kg", False),
        ("Eutrophication", "eutrophication_fw_per_kg", False)]


def ghg_source(r, entries):
    if r.get("unmatched", "").strip() == "True":
        return None
    m = FIRST.search((entries.get(r["ingredient"], {}) or {}).get("source_description", "") or "")
    s = m.group(1).strip() if m else r.get("primary_source", "").strip()
    return s if s in ("AGRIBALYSE v3.2", "SU-EATABLE LIFE") else None


def main():
    rb.apply()
    entries = json.load(open(CACHE))["entries"]
    rows = list(csv.DictReader(open(EF_TABLE)))

    data = {}  # category label -> {source: count}
    for label, col, is_ghg in CATS:
        c = collections.Counter()
        for r in rows:
            v = (r.get(col) or "").strip()
            has = v not in ("", "nan", "None")
            if not has:
                c["no data"] += 1
            elif is_ghg:
                c[ghg_source(r, entries) or "no data"] += 1
            else:
                # water/land/etc. only exist via an AGRIBALYSE match
                c["AGRIBALYSE v3.2"] += 1
        data[label] = c

    total = len(rows)
    order = ["AGRIBALYSE v3.2", "SU-EATABLE LIFE", "no data"]
    fig, ax = rb.subplots(1, 1, width="single", height=2.7)
    labels = [c[0] for c in CATS]
    y = range(len(labels))
    left = [0] * len(labels)
    for s in order:
        vals = [data[l].get(s, 0) for l in labels]
        ax.barh(list(y), vals, left=left, color=COL[s], edgecolor="white",
                linewidth=0.5, height=0.7, zorder=3, label=s)
        left = [a + b for a, b in zip(left, vals)]

    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontfamily=rb.SANS, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, total)
    # coverage % at the right edge (AGRIBALYSE+SU share)
    for i, l in enumerate(labels):
        cov = (data[l].get("AGRIBALYSE v3.2", 0) + data[l].get("SU-EATABLE LIFE", 0)) / total * 100
        ax.text(total * 1.01, i, f"{cov:.1f}% covered", va="center", ha="left",
                fontsize=6, family=rb.MONO, color=rb.MUTED)
    ax.set_xlim(0, total * 1.0)
    ax.set_xticks([0, 20000, 40000])
    ax.set_xticklabels(["0", "20k", "40k"], fontfamily=rb.MONO, fontsize=6)
    ax.set_xlabel("unique ingredients (of 54,266)", fontfamily=rb.SANS, fontsize=6.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=2)
    ax.legend(loc="lower right", frameon=False, fontsize=6, ncol=1,
              bbox_to_anchor=(1.0, -0.02), handlelength=1.1, handleheight=1.1)
    rb.serif_title(fig, "EF source coverage by impact category", y=1.0)
    fig.text(0.01, -0.03,
             "GHG comes from AGRIBALYSE v3.2 or SU-EATABLE LIFE; water, land, "
             "acidification and eutrophication are carried only by AGRIBALYSE "
             "(SU-EATABLE LIFE reports GHG only), so SU-EATABLE-primary ingredients "
             "get those four from a secondary AGRIBALYSE match or not at all.",
             ha="left", va="top", family=rb.MONO, fontsize=5.0, color=rb.MUTED, wrap=True)
    fig.subplots_adjust(left=0.26, right=0.80, top=0.86, bottom=0.20)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"figS_ef_by_category.{ext}"), dpi=300, bbox_inches="tight")
    print("wrote figS_ef_by_category.png / .pdf")
    for l in labels:
        print(f"  {l}: {dict(data[l])}")


if __name__ == "__main__":
    main()
