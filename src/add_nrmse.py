"""Add an NRMSE column to data/results.csv.

RMSE = sqrt(mse) (the existing per-config "mse" column is already the mean
squared error over reconstructed values). NRMSE normalizes RMSE by the
dynamic range (max - min) of the original, lossless branch values, read
once per branch from the reference PHYSLITE file:

    NRMSE = sqrt(mse) / (max(branch) - min(branch))
"""

import sys
from pathlib import Path

import awkward as ak
import pandas as pd
import uproot

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import JETS_FILENAME, JETS_TREENAME

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = REPO_ROOT / "data" / "results.csv"


def branch_ranges(branch_names):
    tree = uproot.open(JETS_FILENAME)[JETS_TREENAME]
    ranges = {}
    for name in branch_names:
        values = ak.flatten(tree[name].array(), axis=None)
        ranges[name] = float(ak.max(values)) - float(ak.min(values))
    return ranges


def main():
    df = pd.read_csv(RESULTS_CSV)
    ranges = branch_ranges(df["branches"].unique())
    df["nrmse"] = df["mse"] ** 0.5 / df["branches"].map(ranges)
    df.to_csv(RESULTS_CSV, index=False)
    print(f"branch ranges: {ranges}")
    print(f"wrote nrmse column for {len(df)} rows to {RESULTS_CSV}")


if __name__ == "__main__":
    main()
