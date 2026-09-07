"""Helpers for pulling branch-level metadata from remote PHYSLITE files
without downloading them, using atlasopenmagic (file discovery) + uproot
(metadata-only reads over HTTPS range requests).
"""

import os
import random
import tempfile

import certifi

from constants import (
    ATLASOPENMAGIC_DATASET_KEY,
    ATLASOPENMAGIC_PROTOCOL,
    ATLASOPENMAGIC_RELEASE,
    ATLASOPENMAGIC_SKIM,
    CERN_GRID_ROOT_CA,
)

_ca_bundle_path = None


def configure_ssl_for_cern():
    """Point SSL_CERT_FILE/REQUESTS_CA_BUNDLE at certifi's bundle plus the
    CERN Grid root CA, so requests to eospublic.cern.ch verify correctly.
    Additive only (widens trust, doesn't disable verification). Idempotent.
    """
    global _ca_bundle_path
    if _ca_bundle_path is not None:
        return _ca_bundle_path

    with open(certifi.where(), "rb") as f:
        certifi_bundle = f.read()
    with open(CERN_GRID_ROOT_CA, "rb") as f:
        cern_root_ca = f.read()

    fd, path = tempfile.mkstemp(suffix=".pem", prefix="cern_ca_bundle_")
    with os.fdopen(fd, "wb") as f:
        f.write(certifi_bundle)
        f.write(cern_root_ca)

    os.environ["SSL_CERT_FILE"] = path
    os.environ["REQUESTS_CA_BUNDLE"] = path
    _ca_bundle_path = path
    return path


def sample_physlite_urls(n=None, seed=None):
    """Return a reproducible random sample of remote PHYSLITE file URLs
    from the real (non-MC) Run 2 pp collision data catalog. No files are
    downloaded by this call.
    """
    import atlasopenmagic as aom

    from constants import REMOTE_SAMPLE_SEED, REMOTE_SAMPLE_SIZE

    n = REMOTE_SAMPLE_SIZE if n is None else n
    seed = REMOTE_SAMPLE_SEED if seed is None else seed

    aom.set_release(ATLASOPENMAGIC_RELEASE)
    urls = aom.get_urls(
        ATLASOPENMAGIC_DATASET_KEY,
        skim=ATLASOPENMAGIC_SKIM,
        protocol=ATLASOPENMAGIC_PROTOCOL,
        cache=False,
    )
    return random.Random(seed).sample(urls, n)
