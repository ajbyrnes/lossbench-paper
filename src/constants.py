from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

JETS_FILENAME = str(REPO_ROOT / "data" / "DAOD_PHYSLITE.37019878._000009.pool.root.1")
MUONS_FILENAME = str(REPO_ROOT / "data" / "ODEO_FEB2025_v0_2muons_data15_periodD.2muons.root")

JETS_TREENAME = "CollectionTree;1"
MUONS_TREENAME = "analysis"

# atlasopenmagic: real Run 2 pp collision data (not MC), 2024 research release.
# key "data" is the collision-data entry (no generator/cross-section metadata).
ATLASOPENMAGIC_RELEASE = "2024r-pp"
ATLASOPENMAGIC_DATASET_KEY = "data"
ATLASOPENMAGIC_SKIM = "noskim"
ATLASOPENMAGIC_PROTOCOL = "https"

# Number of DAOD_PHYSLITE files to sample for branch-metadata collation.
# Branch composition (typenames, per-branch compression ratios) is stable
# across files, so a modest sample is enough to estimate dataset-wide totals.
REMOTE_SAMPLE_SIZE = 100
REMOTE_SAMPLE_SEED = 42

# CERN's EOS-hosted open data uses the CERN Grid CA, which isn't in the
# default OS/Python trust store. This repo pins the (public, long-lived)
# root cert so HTTPS verification succeeds without disabling it.
CERN_GRID_ROOT_CA = str(REPO_ROOT / "certs" / "cern_grid_root_ca.pem")