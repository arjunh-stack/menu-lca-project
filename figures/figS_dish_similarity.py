#!/usr/bin/env python3
"""SI figure — dish-to-dish similarity, two views.

a) cosine similarity of the recipe embeddings the manifold is laid out from.
b) actual ingredient overlap between each dish and its nearest neighbour,
   split into TYPE (Jaccard of ingredient sets) and AMOUNT (shared mass
   fraction). Random-pair baselines shown for reference.

Input : figures/_dish_sim.npz
Output: figures/figS_dish_similarity.{png,pdf}
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import rdylbu_style as rb

HERE = os.path.dirname(os.path.abspath(__file__))


def med_line(ax, arr, col, label_y=0.96, fmt="{:.2f}"):
    m = float(np.median(arr))
    ax.axvline(m, color=col, ls="--", lw=0.9, zorder=5)
    ax.text(m, ax.get_ylim()[1] * label_y, " median " + fmt.format(m),
            color=col, fontsize=6, family=rb.MONO, ha="left", va="top")


def main():
    rb.apply()
    z = np.load(os.path.join(HERE, "_dish_sim.npz"))
    fig, (axc, axi) = rb.subplots(2, 1, width="single", height=5.2)

    # --- panel a: cosine similarity ---------------------------------
    bins = np.linspace(0.2, 1.0, 81)
    axc.hist(z["rand"], bins=bins, density=True, color=rb.BLUE, alpha=0.85,
             edgecolor="white", linewidth=0.2, label="Random dish pairs")
    axc.hist(z["nn"], bins=bins, density=True, color=rb.RED, alpha=0.80,
             edgecolor="white", linewidth=0.2, label="Nearest neighbour")
    med_line(axc, z["rand"], rb.BLUE)
    med_line(axc, z["nn"], rb.RED)
    axc.set_xlim(0.2, 1.0)
    axc.set_xlabel("cosine similarity of recipe embedding", fontfamily=rb.SANS, fontsize=7.5)
    axc.set_ylabel("density", fontfamily=rb.SANS, fontsize=7.5)
    axc.legend(loc="upper left", frameon=False, fontsize=6.5, handlelength=1.2)
    axc.set_title("a · Embedding similarity (manifold layout)",
                  fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold", loc="left", pad=6)

    # --- panel b: actual ingredient overlap, nearest neighbour ------
    b2 = np.linspace(0, 1.0, 51)
    axi.hist(z["nn_jac"], bins=b2, density=True, color=rb.RAMP[8], alpha=0.8,
             edgecolor="white", linewidth=0.2, label="Type (which ingredients)")
    axi.hist(z["nn_mass"], bins=b2, density=True, color=rb.ORANGE, alpha=0.75,
             edgecolor="white", linewidth=0.2, label="Amount (shared mass)")
    med_line(axi, z["nn_jac"], rb.RAMP[9])
    med_line(axi, z["nn_mass"], rb.RAMP[2])
    axi.set_xlim(0, 1.0)
    axi.set_xlabel("ingredient overlap with nearest neighbour", fontfamily=rb.SANS, fontsize=7.5)
    axi.set_ylabel("density", fontfamily=rb.SANS, fontsize=7.5)
    axi.legend(loc="upper left", frameon=False, fontsize=6.5, handlelength=1.2)
    axi.set_title("b · Actual ingredient overlap (nearest neighbour)",
                  fontfamily=rb.SERIF, fontsize=8.5, fontweight="bold", loc="left", pad=6)
    rj, rm = np.median(z["rnd_jac"]), np.median(z["rnd_mass"])
    axi.text(0.03, 0.55,
             f"random-pair baseline:\ntype {rj:.0%} · amount {rm:.0%}",
             transform=axi.transAxes, fontsize=6, family=rb.MONO,
             color=rb.MUTED, ha="left", va="top")

    for ax in (axc, axi):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=6.5)

    rb.serif_title(fig, "Dish-to-dish compositional similarity", y=1.0)
    fig.text(0.5, -0.015,
             "110,261 dishes. Embedding cosine (a) ranks compositional likeness but is not a "
             "% of shared recipe; (b) shows what a dish actually shares with its closest match — "
             "a median 62% of ingredient types and 83% of mass (random pairs: 9% / 1%).",
             ha="center", va="top", family=rb.MONO, fontsize=5.0, color=rb.MUTED, wrap=True)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.92, bottom=0.10, hspace=0.42)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"figS_dish_similarity.{ext}"), dpi=300, bbox_inches="tight")
    print("wrote figS_dish_similarity.png / .pdf")


if __name__ == "__main__":
    main()
