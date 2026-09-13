#!/usr/bin/env python3
"""Generate LossBench --configFile JSON for a muon-branch sweep.

Mirrors the parameter grid in lossbench-experiments/scripts/write_config.py
(same CHUNK_SIZES/ERROR_BOUNDS/BITRATES/ITERATIONS) but points at the muon
file's lep_pt/lep_eta/lep_phi/lep_e branches instead of the jet branches, and
only covers sz3/sperr/zstd-trunc (the compressors built in this environment;
the original also covered mgard/zfpx/isabela/tucker, which aren't built here).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import MUONS_FILENAME, MUONS_TREENAME

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "data" / "muon-sweep-configs"

TREE_NAME = MUONS_TREENAME
ALL_BRANCHES = ["lep_pt", "lep_eta", "lep_phi", "lep_e"]

CHUNK_SIZES = [16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216]
ERROR_BOUNDS = [100, 10, 1, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6]
BITRATES = [2, 4, 8, 10, 12, 16, 20, 24, 26, 28, 30, 32]
MANTISSA_BITS = [2, 4, 8, 10, 12, 14, 16, 18, 20, 22]
ITERATIONS = 5

SZ3_ALGOS = [0, 1, 2, 3]  # 0=LORENZO_REG, 1=INTERP_LORENZO, 2=INTERP, 3=NOPRED


def write_config(config, filename):
    path = CONFIG_DIR / filename
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print(f"wrote {len(config['tests'])} tests to {path}")


def make_config(tests):
    return {
        "inputFile": MUONS_FILENAME,
        "tree": TREE_NAME,
        "branches": ALL_BRANCHES,
        "tests": tests,
    }


def trunc_sweep():
    tests = [
        {
            "compressor": "zstd-trunc",
            "options": {"compressionLevel": "5", "truncBits": str(tb)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS,
        }
        for tb in MANTISSA_BITS for c in CHUNK_SIZES
    ]
    write_config(make_config(tests), "zstd-trunc-sweep-config.json")


def sz3_sweep():
    abs_err_tests = [
        {
            "compressor": "sz3",
            "options": {"cmprAlgo": str(a), "errorBoundMode": "0", "absErrorBound": str(eb)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS,
        }
        for a in SZ3_ALGOS for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    rel_err_tests = [
        {
            "compressor": "sz3",
            "options": {"cmprAlgo": str(a), "errorBoundMode": "1", "relErrorBound": str(eb)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS,
        }
        for a in SZ3_ALGOS for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    write_config(make_config(abs_err_tests + rel_err_tests), "sz3-sweep-config.json")


def sperr_sweep():
    bitrate_tests = [
        {
            "compressor": "sperr",
            "options": {"bitrate": str(br)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS,
        }
        for br in BITRATES for c in CHUNK_SIZES
    ]
    pwe_tests = [
        {
            "compressor": "sperr",
            "options": {"pwe": str(pwe)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS,
        }
        for pwe in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    write_config(make_config(bitrate_tests + pwe_tests), "sperr-sweep-config.json")


def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    trunc_sweep()
    sz3_sweep()
    sperr_sweep()


if __name__ == "__main__":
    main()
