"""Combine the per-compressor sweep results into a single CSV.

Reads data/{sperr,sz3,zstdtrunc}-sweep/results.jsonl (one JSON object per
trial, with config/results/system fields nested) and writes a flat
data/results.csv, one row per trial. Leaf field names are unique across
the three top-level sections in every sweep, so nesting is flattened
without prefixes (e.g. "truncBits", "psnr", "wasserstein_distance").
"""

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_CSV = DATA_DIR / "results.csv"

SWEEP_DIRS = ["sperr-sweep", "sz3-sweep", "zstdtrunc-sweep"]


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


def main():
    rows = [row for sweep_dir in SWEEP_DIRS for row in load_sweep(sweep_dir)]
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"wrote {len(df)} rows, {len(df.columns)} columns to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
