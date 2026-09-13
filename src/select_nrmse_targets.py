"""For each of the order-of-magnitude categories NRMSE ~ 10^0..10^-5, pick
the best-compression Pareto-frontier point for every (branch, compressor).

A config belongs to category 10^k if floor(log10(nrmse)) == k, i.e. its
NRMSE falls in the half-open decade [10^k, 10^(k+1)). Within each
(branch, compressor, category), we take the point with the highest
compression ratio anywhere in that decade, searched over the Pareto
frontier (not the raw sweep) so the result is always a genuinely
non-dominated config rather than an off-frontier point that happens to
land in the decade.

If a (branch, compressor)'s frontier never has a point in a given decade,
that category has no row and is dropped.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compute_pareto_frontiers import BRANCH_LABELS, config_note, frontier

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = REPO_ROOT / "data" / "results.csv"
OUTPUT_CSV = REPO_ROOT / "data" / "nrmse_target_points.csv"

TARGETS = [10 ** k for k in range(0, -6, -1)]  # 1, 0.1, 0.01, 0.001, 0.0001, 0.00001


def best_at_order_of_magnitude(group, target):
    exponent = round(np.log10(target))
    positive = group[group["nrmse"] > 0]
    if positive.empty:
        return None
    in_decade = positive[np.floor(np.log10(positive["nrmse"])) == exponent]
    if in_decade.empty:
        return None
    return in_decade.loc[in_decade["compression_ratio"].idxmax()]


def main():
    df = pd.read_csv(RESULTS_CSV)
    df["config_note"] = df.apply(config_note, axis=1)
    df["branch"] = df["branches"].map(BRANCH_LABELS)

    rows = []
    for (branch, compressor), group in df.groupby(["branch", "compressor"]):
        front = frontier(group, "nrmse", higher_is_better=False)
        for target in TARGETS:
            row = best_at_order_of_magnitude(front, target)
            if row is None:
                continue
            rows.append({
                "target_nrmse": target,
                "branch": branch,
                "compressor": compressor,
                "achieved_nrmse": row["nrmse"],
                "compression_ratio": row["compression_ratio"],
                "chunk_size": row["chunk_size"],
                "config_note": row["config_note"],
            })

    out = pd.DataFrame(rows).sort_values(["target_nrmse", "branch", "compressor"])
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"wrote {len(out)} rows ({len(TARGETS)} targets x 3 branches x 3 compressors) to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
