"""Combine the per-compressor muon sweep results into a single CSV, then add
an NRMSE column.

Reads data/muon-{sperr,sz3,zstdtrunc}-sweep/results.jsonl (one JSON object per
trial) and writes a flat data/muon_results.csv, one row per trial, mirroring
combine_sweep_results.py + add_nrmse.py for the jet sweep.

NRMSE = sqrt(mse) / (max(branch) - min(branch)), with the branch range read
from the muon file itself (not the jet file).
"""

import json
import sys
from pathlib import Path

import awkward as ak
import pandas as pd
import uproot

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import MUONS_FILENAME, MUONS_TREENAME

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_CSV = DATA_DIR / "muon_results.csv"

SWEEP_DIRS = ["muon-sperr-sweep", "muon-sz3-sweep", "muon-zstdtrunc-sweep"]


def flatten(d):
    flat = {}
    for k, v in d.items():
        if isinstance(v, dict):
            flat.update(flatten(v))
        else:
            flat[k] = v
    return flat


def load_sweep(sweep_dir):
    rows = []
    with open(DATA_DIR / sweep_dir / "results.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(flatten(json.loads(line)))
    return rows


def branch_ranges(branch_names):
    tree = uproot.open(MUONS_FILENAME)[MUONS_TREENAME]
    ranges = {}
    for name in branch_names:
        values = ak.flatten(tree[name].array(), axis=None)
        ranges[name] = float(ak.max(values)) - float(ak.min(values))
    return ranges


def main():
    rows = [row for sweep_dir in SWEEP_DIRS for row in load_sweep(sweep_dir)]
    df = pd.DataFrame(rows)

    ranges = branch_ranges(df["branches"].unique())
    df["nrmse"] = df["mse"] ** 0.5 / df["branches"].map(ranges)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"branch ranges: {ranges}")
    print(f"wrote {len(df)} rows, {len(df.columns)} columns to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
