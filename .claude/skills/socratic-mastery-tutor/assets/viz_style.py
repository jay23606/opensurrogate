"""Shared matplotlib style for every session figure, so the whole course looks like one book.

Usage in any figure script:
    import sys; sys.path.insert(0, "<engine skill>/assets")   # or copy this file next to the script
    from viz_style import setup, PAL, save
    setup()
    fig, ax = plt.subplots(figsize=FIG["single"])
    ...
    save(fig, "figures/fig01_signal.png")

Palette is Okabe-Ito (colour-blind safe). For chart-form / palette guidance beyond this file, use the
`dataviz` skill. Rules baked in: labelled axes with units, no chartjunk, dpi 200, tight layout.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAL = {
    "blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00",
    "purple": "#CC79A7", "sky": "#56B4E9", "yellow": "#F0E442", "black": "#000000", "grey": "#7F7F7F",
}
CYCLE = [PAL[k] for k in ("blue", "orange", "green", "red", "purple", "sky", "grey")]
FIG = {"single": (6.4, 3.8), "wide": (7.6, 3.6), "square": (4.8, 4.4), "tall": (6.4, 5.6), "panel2": (7.6, 3.4)}


def setup():
    plt.rcParams.update({
        "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight",
        "font.size": 10.5, "axes.titlesize": 11.5, "axes.labelsize": 10.5, "legend.fontsize": 9,
        "axes.prop_cycle": matplotlib.cycler(color=CYCLE),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "lines.linewidth": 1.8, "mathtext.fontset": "cm", "font.family": "serif",
        "image.cmap": "viridis", "figure.constrained_layout.use": True,
    })


def save(fig, path):
    fig.savefig(path)
    plt.close(fig)
    print("saved", path)
