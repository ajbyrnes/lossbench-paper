"""Figure 1 — PHYSLITE composition (motivation).

Caption draft: Lossless (ZSTD) compression of PHYSLITE branches by
category, aggregated over a 100-file random sample of real ATLAS Run 2
pp collision data (data15/16_13TeV, ~657 GB uncompressed). Pale bars
show uncompressed size; solid bars show size after lossless compression.
Four-vector components (jet/muon pt, eta, phi, m, e) shrink far less
under lossless compression than other continuous floats or discrete/
metadata branches, motivating lossy compression targeted at kinematics.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

FIG_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIG_DIR.parent.parent

sys.path.insert(0, str(REPO_ROOT))
from plotting_style import BRANCH_CATEGORY_COLORS, BRANCH_CATEGORY_LABELS, set_style

CATEGORY_ORDER = ["four_vector_component", "continuous_float", "other"]
BYTES_PER_GB = 1e9


def load_category_totals():
    df = pd.read_csv(FIG_DIR / "branch_metadata.csv")
    df = df[df["file"].str.contains("DAOD")]  # jets/PHYSLITE rows only
    totals = df.groupby("branch_category")[["compressed_bytes", "uncompressed_bytes"]].sum()
    totals["size_reduction_pct"] = (1 - totals["compressed_bytes"] / totals["uncompressed_bytes"]) * 100
    return totals.loc[CATEGORY_ORDER]


def plot(totals, ax):
    y = range(len(totals))
    for yi, category in zip(y, totals.index):
        color = BRANCH_CATEGORY_COLORS[category]
        uncompressed_gb = totals.loc[category, "uncompressed_bytes"] / BYTES_PER_GB
        compressed_gb = totals.loc[category, "compressed_bytes"] / BYTES_PER_GB
        reduction_pct = totals.loc[category, "size_reduction_pct"]

        ax.barh(yi, uncompressed_gb, height=0.6, color=color, alpha=0.3, zorder=2)
        ax.barh(yi, compressed_gb, height=0.3, color=color, zorder=3)
        ax.text(
            uncompressed_gb * 1.15, yi, f"−{reduction_pct:.0f}%",
            va="center", ha="left", fontsize=9, color=color, fontweight="bold",
        )

    ax.set_yticks(list(y))
    ax.set_yticklabels([BRANCH_CATEGORY_LABELS[c] for c in totals.index])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("Size (GB, log scale)")
    ax.set_xlim(right=ax.get_xlim()[1] * 3)  # headroom for reduction-% labels
    ax.grid(True, axis="x", zorder=0)
    ax.grid(False, axis="y")

    uncompressed_handle = plt.Rectangle((0, 0), 1, 1, color="0.4", alpha=0.3)
    compressed_handle = plt.Rectangle((0, 0), 1, 1, color="0.4")
    ax.legend(
        [uncompressed_handle, compressed_handle],
        ["Uncompressed", "Lossless-compressed (ZSTD)"],
        loc="upper right", frameon=False,
    )


def main():
    set_style()
    totals = load_category_totals()

    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    plot(totals, ax)
    fig.tight_layout()

    fig.savefig(FIG_DIR / "fig1_physlite_composition.pdf")
    fig.savefig(FIG_DIR / "fig1_physlite_composition.png", dpi=200)


if __name__ == "__main__":
    main()
