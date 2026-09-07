"""Shared style for all LossBench paper figures (see todo.md "Global conventions")."""

import matplotlib.pyplot as plt

# Okabe-Ito colorblind-safe palette, consistent across every figure.
COMPRESSOR_COLORS = {
    "SZ3": "#0072B2",
    "ZFP": "#D55E00",
    "SPERR": "#009E73",
    "zstd-trunc": "#CC79A7",
}
COMPRESSOR_MARKERS = {
    "SZ3": "o",
    "ZFP": "s",
    "SPERR": "^",
    "zstd-trunc": "D",
}
RD_BOUND_STYLE = {"color": "black", "linestyle": "--"}

# Branch-category palette for Figure 1 (PHYSLITE composition), drawn from
# the same Okabe-Ito set. Four-vector components are highlighted since
# they're the paper's headline poorly-compressing bucket.
BRANCH_CATEGORY_COLORS = {
    "four_vector_component": "#D55E00",
    "continuous_float": "#0072B2",
    "other": "#009E73",
}
BRANCH_CATEGORY_LABELS = {
    "four_vector_component": "Four-vector\ncomponents",
    "continuous_float": "Other continuous\nfloats",
    "other": "Discrete /\nmetadata",
}


def set_style():
    plt.rcParams.update({
        "font.family": "serif",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.labelsize": 10,
        "legend.fontsize": 10,
        "axes.grid": True,
        "grid.color": "0.5",
        "grid.alpha": 0.3,
        "axes.axisbelow": True,
    })
