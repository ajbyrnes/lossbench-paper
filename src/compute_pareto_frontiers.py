"""Compute the Pareto frontier for each (branch, metric, compressor) in the
rate-distortion dashboard and write the frontier points to a CSV.

A row is on the frontier if no other row for that branch/compressor beats it
on both compression ratio and the metric at once. Compression ratio is
always maximized; the metric direction depends on HIGHER_IS_BETTER. Null
psnr (an exact, lossless reconstruction) counts as the best possible value.

Mirrors the paretoFrontier() logic in src/main_results_dashboard.html so the
CSV matches the curves drawn there.
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = REPO_ROOT / "data" / "results.csv"
OUTPUT_CSV = REPO_ROOT / "data" / "pareto_frontiers.csv"

BRANCH_LABELS = {
    "AnalysisJetsAuxDyn.pt": "pt",
    "AnalysisJetsAuxDyn.eta": "eta",
    "AnalysisJetsAuxDyn.phi": "phi",
}

METRICS = {
    "psnr": True,
    "wasserstein_distance": False,
    "ks_statistic": False,
    "mse": False,
    "rel_error_avg": False,
    "nrmse": False,
    "compression_throughput_mbps": True,
    "decompression_throughput_mbps": True,
}


def config_note(row):
    if row["compressor"] == "sperr":
        return f"quality={row['quality']}"
    if row["compressor"] == "sz3":
        return f"relErrorBound={row['relErrorBound']:.1e}"
    if row["compressor"] == "zstd-trunc":
        return f"truncBits={int(row['truncBits'])}, level={int(row['compressionLevel'])}"
    return ""


def frontier(group, metric, higher_is_better):
    y = group[metric].to_numpy(dtype=float)
    eff_y = np.where(np.isnan(y), np.inf, y if higher_is_better else -y)
    order = np.lexsort((-eff_y, -group["compression_ratio"].to_numpy()))

    running_max = -np.inf
    keep = []
    for i in order:
        if eff_y[i] > running_max:
            keep.append(i)
            running_max = eff_y[i]

    return group.iloc[keep].sort_values("compression_ratio")


def main():
    df = pd.read_csv(RESULTS_CSV)
    df["config_note"] = df.apply(config_note, axis=1)
    df["branch"] = df["branches"].map(BRANCH_LABELS)

    rows = []
    for (branch, compressor), group in df.groupby(["branch", "compressor"]):
        for metric, higher_is_better in METRICS.items():
            front = frontier(group, metric, higher_is_better)
            for _, r in front.iterrows():
                rows.append({
                    "branch": branch,
                    "compressor": compressor,
                    "metric": metric,
                    "higher_is_better": higher_is_better,
                    "compression_ratio": r["compression_ratio"],
                    "metric_value": r[metric],
                    "chunk_size": r["chunk_size"],
                    "config_note": r["config_note"],
                })

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"wrote {len(out)} frontier points ({len(METRICS)} metrics x 3 branches x 3 compressors) to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
