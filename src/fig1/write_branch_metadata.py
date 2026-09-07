import csv
import time
from pathlib import Path

import uproot

from constants import MUONS_FILENAME, MUONS_TREENAME, JETS_TREENAME
from remote_files import configure_ssl_for_cern, sample_physlite_urls

OUTPUT_CSV = Path(__file__).resolve().parent / "branch_metadata.csv"

# eospublic rate-limits bursts of requests; back off and retry on transient
# failures (429s, dropped connections) instead of aborting the whole sample.
REQUEST_DELAY_SECONDS = 0.5
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 10


def open_tree_with_retry(url, treename):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return uproot.open(url)[treename]
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = RETRY_BACKOFF_SECONDS * attempt
            print(f"  retry {attempt}/{MAX_RETRIES} after error ({e}); waiting {wait}s")
            time.sleep(wait)


def is_four_vector_component(branchname):
    four_vector_elements = ["m", "pt", "eta", "phi"]
    return any(branchname.endswith(elem) for elem in four_vector_elements)


def is_continuous_float(branch):
    return "float" in branch.typename and not is_four_vector_component(branch.name)


def write_branch_metadata(branchname, branch, writer):
    try:
        writer.writerow([
            branchname,
            branch.file,
            branch.tree,
            branch.typename,
            branch.num_entries,
            branch.compression,
            branch.compressed_bytes,
            branch.uncompressed_bytes,
            branch.compression_ratio,
            "continuous_float" if is_continuous_float(branch) else "four_vector_component" if is_four_vector_component(branchname) else "other",
        ])
    except Exception as e:
        print(f"Error processing branch {branchname}: {e}")


def main():
    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "branchname",
            "file",
            "tree",
            "typename",
            "num_entries",
            "compression",
            "compressed_bytes",
            "uncompressed_bytes",
            "compression_ratio",
            "branch_category"
        ])

        configure_ssl_for_cern()
        jet_urls = sample_physlite_urls()
        for i, url in enumerate(jet_urls):
            print(f"[{i + 1}/{len(jet_urls)}] reading branch metadata from {url}")
            try:
                jet_tree = open_tree_with_retry(url, JETS_TREENAME)
            except Exception as e:
                print(f"  giving up on {url}: {e}")
                continue
            for branchname, branch in jet_tree.items():
                write_branch_metadata(branchname, branch, writer)
            time.sleep(REQUEST_DELAY_SECONDS)

        muon_tree = uproot.open(MUONS_FILENAME)[MUONS_TREENAME]
        for branchname, branch in muon_tree.items():
            write_branch_metadata(branchname, branch, writer)


if __name__ == "__main__":
    main()
