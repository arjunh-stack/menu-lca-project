"""RdYlBu design system for matplotlib (Arjun Hausner, V1.0 2026).

Local re-implementation of the `rdylbu_mpl` kit referenced in the design
system PDF (the kit is not pip-installable on this machine). Registers the
ColorBrewer 11-class RdYlBu palette, an `rdylbu` diverging colormap, the IBM
Plex font stack (bundled in figures/fonts/), and Tufte-ish rcParams.

Usage:
    import rdylbu_style as rb
    rb.apply()
    fig, ax = rb.figure(width="single")   # 3.5in ; "double" -> 7in
    ax.plot(...)
    rb.save(fig, "figures/my_plot")        # writes .pdf + .png at 300 dpi

Rules baked in (design system, non-negotiable):
  1. Red = hot/high, blue = cold/low, yellow (#FFFFBF) = zero/midpoint.
  2. Endpoints (#A50026 / #313695) are reserved for extremes; default series
     use RED/BLUE (#D73027 / #4575B4).
  3. No hues outside the ramp — differentiate via neutrals, weight, shape.
"""
from __future__ import annotations

import glob
import os

import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.colors import LinearSegmentedColormap

# ── 11-class ColorBrewer RdYlBu ───────────────────────────────────────────
RAMP = [
    "#A50026", "#D73027", "#F46D43", "#FDAE61", "#FEE090", "#FFFFBF",
    "#E0F3F8", "#ABD9E9", "#74ADD1", "#4575B4", "#313695",
]
# Semantic named tokens
HOT_EXTREME = RAMP[0]    # #A50026  "off the chart" hot
RED = RAMP[1]            # #D73027  default hot/high series
ORANGE = RAMP[2]         # #F46D43
SAND = RAMP[3]           # #FDAE61
ZERO = RAMP[5]           # #FFFFBF  yellow = zero/midpoint ONLY
SKY = RAMP[7]            # #ABD9E9
BLUE = RAMP[9]           # #4575B4  default cold/low series
COLD_EXTREME = RAMP[10]  # #313695  "off the chart" cold

# Neutrals (the only non-ramp values allowed: grayscale for chrome/text)
INK = "#1A1A1A"
GRID = "#D9D9D9"
MUTED = "#6E6E6E"

# Discrete categorical order: alternate warm/cool away from the endpoints,
# so adjacent categories stay distinct without using #A50026/#313695.
CATEGORICAL = [RED, BLUE, ORANGE, SKY, SAND, RAMP[8], "#B0451F", RAMP[6]]

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SERIF = "IBM Plex Serif"   # display, headings, stat numbers
SANS = "IBM Plex Sans"     # body, axis/tick labels, captions
MONO = "IBM Plex Mono"     # eyebrows, numbers, annotations

WIDTHS = {"single": 3.5, "double": 7.0}  # Nature column widths (inches)

_applied = False


def _register_fonts() -> bool:
    """Add the bundled Plex TTFs to matplotlib's font manager. Returns True
    if at least the sans family registered."""
    for path in glob.glob(os.path.join(FONT_DIR, "*.ttf")):
        try:
            fm.fontManager.addfont(path)
        except Exception:
            pass
    have = {f.name for f in fm.fontManager.ttflist}
    return SANS in have


def rdylbu_cmap(reverse: bool = False) -> LinearSegmentedColormap:
    """Continuous diverging RdYlBu colormap (red=high, blue=low)."""
    cols = RAMP[::-1] if reverse else RAMP
    name = "rdylbu_r" if reverse else "rdylbu"
    return LinearSegmentedColormap.from_list(name, cols, N=256)


def apply() -> None:
    """Install palette colormaps, fonts, and Tufte-ish rcParams globally."""
    global _applied
    have_plex = _register_fonts()

    for cm in (rdylbu_cmap(False), rdylbu_cmap(True)):
        try:
            mpl.colormaps.register(cm, force=True)
        except Exception:
            pass

    serif_stack = ([SERIF] if have_plex else []) + ["DejaVu Serif", "serif"]
    sans_stack = ([SANS] if have_plex else []) + ["DejaVu Sans", "sans-serif"]
    mono_stack = ([MONO] if have_plex else []) + ["DejaVu Sans Mono", "monospace"]

    mpl.rcParams.update({
        # fonts — body text is sans; titles set serif explicitly per-figure
        "font.family": "sans-serif",
        "font.sans-serif": sans_stack,
        "font.serif": serif_stack,
        "font.monospace": mono_stack,
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "figure.titlesize": 11,
        # color / ink
        "text.color": INK,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
        # tufte-ish chrome: no top/right spines, light grid
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.9,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,   # embed TrueType (editable text in Illustrator)
        "ps.fonttype": 42,
    })
    _applied = True
    if not have_plex:
        print("[rdylbu] WARNING: IBM Plex not found; using DejaVu fallback.")


def figure(width: str = "single", height: float | None = None, **kw):
    """Create a fig/ax at a Nature column width (3.5 or 7 inches).

    width: "single" (3.5in) or "double" (7in), or a float in inches.
    height: inches; defaults to width / golden-ratio.
    """
    if not _applied:
        apply()
    w = WIDTHS.get(width, width) if isinstance(width, str) else float(width)
    h = height if height is not None else w / 1.618
    import matplotlib.pyplot as plt
    return plt.subplots(figsize=(w, h), **kw)


def subplots(nrows=1, ncols=1, width="double", height=None, **kw):
    """Multi-panel figure at a fixed Nature column width."""
    if not _applied:
        apply()
    w = WIDTHS.get(width, width) if isinstance(width, str) else float(width)
    h = height if height is not None else w * (nrows / max(ncols, 1)) * 0.8
    import matplotlib.pyplot as plt
    return plt.subplots(nrows, ncols, figsize=(w, h), **kw)


def serif_title(ax_or_fig, text: str, **kw):
    """Set a title in IBM Plex Serif (display face)."""
    kw.setdefault("fontfamily", SERIF)
    if hasattr(ax_or_fig, "suptitle"):
        return ax_or_fig.suptitle(text, **kw)
    return ax_or_fig.set_title(text, **kw)


FIG_DIR = os.path.dirname(os.path.abspath(__file__))


def save(fig, path_stem: str, formats=("pdf", "png")) -> list[str]:
    """Save a figure as both vector (pdf) and raster (png). Relative stems
    resolve against the figures/ directory (and a leading 'figures/' is
    stripped) so scripts save correctly from any cwd."""
    if not os.path.isabs(path_stem):
        stem = path_stem[len("figures/"):] if path_stem.startswith("figures/") else path_stem
        path_stem = os.path.join(FIG_DIR, stem)
    out = []
    for ext in formats:
        p = f"{path_stem}.{ext}"
        fig.savefig(p)
        out.append(p)
    print("[saved]", ", ".join(out))
    return out


if __name__ == "__main__":
    apply()
    print("Plex registered:", _register_fonts())
    print("colormap:", rdylbu_cmap().name)
    print("widths:", WIDTHS)
