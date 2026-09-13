"""Run LossBench against the Z->ll muon file using, for each of SZ3/SPERR/
zstd-trunc, the best-compression Pareto-frontier point from the jet sweep in
each NRMSE decade 10^0 .. 10^-5 (see select_nrmse_targets.py's
best_at_order_of_magnitude, searched over the frontier so the result is
always a genuinely non-dominated config).

Configs are branch-specific (derived from the AnalysisJetsAuxDyn.pt/eta/phi
sweep in data/results.csv) and mapped onto the matching lep_pt/lep_eta/lep_phi
branches of the muon file. lep_e has no jet-sweep analogue and is left
uncompressed; the original file's lep_e is used as-is in the downstream mass
reconstruction (see case_study_find_the_z.ipynb).

Since one LossBench invocation applies a single compressor config to every
branch it's given, each (compressor, target) pair needs one invocation per
branch (their configs differ), with all three appended into the same
--decompFile.
"""

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from compute_pareto_frontiers import BRANCH_LABELS, frontier
from select_nrmse_targets import TARGETS, best_at_order_of_magnitude
from constants import MUONS_FILENAME, MUONS_TREENAME

# LossBench lives in a sibling repo, built against a self-contained
# conda-forge toolchain (see ~/LossBench/env.sh) since this machine has no
# system compiler/CMake/ROOT.
LOSSBENCH_PATH = str(Path.home() / "LossBench" / "build" / "lossbench")
LOSSBENCH_ENV_PREFIX = str(Path.home() / "local" / "micromamba" / "root" / "envs" / "lossbench")

OUTDIR = Path(__file__).resolve().parent / "case_study_data"
RESULTS_FILE = OUTDIR / "results.jsonl"
CONFIGS_FILE = OUTDIR / "lep_configs.csv"

LEP_MAP = {"pt": "lep_pt", "eta": "lep_eta", "phi": "lep_phi"}


def build_compressor_arg(compressor, row):
    if compressor == "sperr":
        # The jet sweep used sperr's bpp (bits-per-pixel) mode; "quality" is
        # the bpp value.
        return f"sperr:mode=bpp,quality={row['quality']:.6f}"
    if compressor == "sz3":
        # Pass every SZ3 option exactly as it was set for the matched sweep
        # row (cmprAlgo and errorBoundMode both varied across the sweep, so
        # a single "headline" parameter like relErrorBound isn't enough to
        # reproduce the configuration).
        int_fields = ["cmprAlgo", "errorBoundMode", "quantbinCnt", "blockSize",
                      "interpAlgo", "interpDirection", "interpAnchorStride"]
        float_fields = ["absErrorBound", "relErrorBound", "psnrErrorBound",
                         "l2normErrorBound", "interpAlpha", "interpBeta"]
        bool_fields = ["openmp", "lorenzo", "lorenzo2", "regression", "regression2"]
        parts = [f"{f}={int(round(row[f]))}" for f in int_fields]
        parts += [f"{f}={row[f]:.6f}" for f in float_fields]
        for f in bool_fields:
            val = row[f]
            b = val.strip().lower() in ("true", "1") if isinstance(val, str) else bool(val)
            parts.append(f"{f}={'true' if b else 'false'}")
        return "sz3:" + ",".join(parts)
    if compressor == "zstd-trunc":
        return f"zstd-trunc:truncBits={int(row['truncBits'])},compressionLevel={int(row['compressionLevel'])}"
    raise ValueError(compressor)


def build_configs():
    """Recompute the best-compression-per-decade Pareto-frontier matches
    directly from results.csv (full rows, not the lossy config_note text in
    nrmse_target_points.csv, which mislabels SZ3 rows that used absolute
    rather than relative error bounds), restricted to the three branches
    with a lep_* analogue.
    """
    df = pd.read_csv(REPO_ROOT / "data" / "results.csv")
    df["branch"] = df["branches"].map(BRANCH_LABELS)
    df = df[df["branch"].notna()]

    rows = []
    for (branch, compressor), group in df.groupby(["branch", "compressor"]):
        if branch not in LEP_MAP:
            continue
        front = frontier(group, "nrmse", higher_is_better=False)
        for target in TARGETS:
            row = best_at_order_of_magnitude(front, target)
            if row is None:
                continue
            rows.append({
                "target_nrmse": target,
                "branch": branch,
                "lep_branch": LEP_MAP[branch],
                "compressor": compressor,
                "chunk_size": int(row["chunk_size"]),
                "compressor_arg": build_compressor_arg(compressor, row),
                "achieved_nrmse": row["nrmse"],
                "compression_ratio": row["compression_ratio"],
            })
    return pd.DataFrame(rows).sort_values(["compressor", "target_nrmse", "branch"]).reset_index(drop=True)


def decomp_file_for(compressor, target):
    return OUTDIR / f"decomp_{compressor}_target{target:g}.root"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    configs = build_configs()
    configs.to_csv(CONFIGS_FILE, index=False)

    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()
    for compressor in configs["compressor"].unique():
        for target in configs["target_nrmse"].unique():
            f = decomp_file_for(compressor, target)
            if f.exists():
                f.unlink()

    env = os.environ.copy()
    env["PATH"] = f"{LOSSBENCH_ENV_PREFIX}/bin:" + env.get("PATH", "")
    env["LD_LIBRARY_PATH"] = f"{LOSSBENCH_ENV_PREFIX}/lib:" + env.get("LD_LIBRARY_PATH", "")

    for _, row in configs.iterrows():
        decomp_file = decomp_file_for(row["compressor"], row["target_nrmse"])
        cmd = [
            LOSSBENCH_PATH,
            "--inputFile", MUONS_FILENAME,
            "--tree", MUONS_TREENAME,
            "--branches", row["lep_branch"],
            "--chunkSize", str(row["chunk_size"]),
            "--compressor", row["compressor_arg"],
            "--resultsFile", str(RESULTS_FILE),
            "--decompFile", str(decomp_file),
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print("FAILED:", " ".join(cmd))
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)

    print(f"Ran {len(configs)} lossbench invocations OK.")
    print(f"Configs: {CONFIGS_FILE}")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
