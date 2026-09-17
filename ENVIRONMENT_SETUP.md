# Environment Setup Notes

How LossBench got built and working on this machine, starting from a
completely bare Ubuntu 24.04 container: no C/C++ compiler, no CMake, no ROOT,
no SZ3/SPERR, and no `sudo` password to install any of it via `apt`. Everything
below was done in user space, without root, using `~/local/micromamba` as a
self-contained toolchain.

## Why not just `apt install`

The container had `sudo` in principle (user is in the `sudo` group) but no
password available non-interactively, so `apt-get install` was a dead end.
Separately, ROOT isn't packaged in Ubuntu's own repos at all — it would need
to be built from source (slow, many dependencies) or fetched as a prebuilt
binary. `nlohmann-json3-dev` also didn't resolve in the local apt cache.

## Approach: a conda-forge toolchain in user space

[conda-forge](https://conda-forge.org/) ships prebuilt packages for
everything the build needs — a C++20 compiler, CMake, and ROOT itself (with
its own CMake config files) — all installable without root via
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html),
a single static binary.

### 1. Install micromamba

```bash
mkdir -p ~/local/micromamba && cd ~/local/micromamba
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest -o micromamba.tar.bz2
```

The container also had no `bzip2` binary to extract the `.tar.bz2`, so the
archive was extracted with Python's built-in `bz2`/`tarfile` modules instead:

```bash
python3 -c "
import tarfile
with tarfile.open('micromamba.tar.bz2', 'r:bz2') as t:
    t.extract('bin/micromamba', '.')
"
chmod +x bin/micromamba
```

### 2. Create the build environment

```bash
export MAMBA_ROOT_PREFIX=~/local/micromamba/root
~/local/micromamba/bin/micromamba create -y -n lossbench -c conda-forge \
    root cmake make cxx-compiler c-compiler nlohmann_json zstd pkg-config git
```

This pulled in CMake 4.4.3, GCC 15.3.0, and ROOT 6.40.04 (plus zstd,
nlohmann_json, and pkg-config), all resolvable via `find_package`/
`pkg_check_modules` once the environment's prefix is on `CMAKE_PREFIX_PATH`.
The resulting environment lives at
`~/local/micromamba/root/envs/lossbench`.

### 3. Build SZ3 from source

Not on conda-forge, so built and installed straight into the same
environment prefix:

```bash
ENV_PREFIX=~/local/micromamba/root/envs/lossbench
export PATH="$ENV_PREFIX/bin:$PATH"

git clone --depth 1 https://github.com/szcompressor/SZ3.git ~/local/src/SZ3
cd ~/local/src/SZ3
cmake -S . -B build \
    -DCMAKE_INSTALL_PREFIX="$ENV_PREFIX" \
    -DCMAKE_PREFIX_PATH="$ENV_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON
cmake --build build -j"$(nproc)"
cmake --install build
```

This installs `SZ3Config.cmake` into `$ENV_PREFIX/lib/cmake/SZ3`, which is
exactly what LossBench's `find_package(SZ3 QUIET)` looks for.

### 4. Build SPERR from source

Same pattern. SPERR has no CMake package config of its own (LossBench finds
it with `find_library`/`find_path` instead), so it just needs its `.so` and
headers to land under the environment prefix:

```bash
git clone --depth 1 https://github.com/NCAR/SPERR.git ~/local/src/SPERR
cd ~/local/src/SPERR
cmake -S . -B build \
    -DCMAKE_INSTALL_PREFIX="$ENV_PREFIX" \
    -DCMAKE_PREFIX_PATH="$ENV_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_UNIT_TESTS=OFF \
    -DBUILD_CLI_UTILITIES=OFF \
    -DUSE_OMP=OFF
cmake --build build -j"$(nproc)"
cmake --install build
```

### 5. Configure and build LossBench itself

```bash
export LD_LIBRARY_PATH="$ENV_PREFIX/lib:$LD_LIBRARY_PATH"
cd ~/LossBench
cmake -S src -B build \
    -DCMAKE_PREFIX_PATH="$ENV_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

The configure log confirmed exactly the intended set of backends:

```
-- SZ3 found - enabling SZ3 compressor
-- ZFP not found - ZFP compressor disabled
-- SPERR found - enabling SPERR compressor
-- SZp not found - SZp compressor disabled
-- ZFP-X not found - ZFP-X compressor disabled
-- MGARD not found - MGARD compressor disabled
-- TuckerMPI not found - Tucker compressor disabled
-- ISABELA not found - ISABELA compressor disabled
```

zstd (required, not optional) was found via `pkg-config`. `--list-compressors`
on the built binary shows `zstd`, `zstd-trunc`, `sz3`, `sperr`, plus the
always-on histogram baselines (`uniform-histogram`, `quantile-histogram`,
`quantile-residual`).

Verified against real data by running all three compressors against the
PHYSLITE and muon ROOT files already in `lossbench-paper/data/` and checking
the compression ratios/PSNR came back sane.

### 6. A bug found along the way

Building it was only half the problem — the very first real use (reproducing
the Z-mass case study, which needs decompressed data lined up event-for-event
with the original file) turned up an off-by-one in
`src/root-utils/root-utils.cpp`: every vector-branch reader called
`TTreeReader::SetEntry(0)` to validate branch setup, then immediately started
its main loop with `while (reader.Next())` — which advances *past* entry 0,
silently dropping it from every read (compression, decompFile output,
everything downstream). Fixed by inserting `reader.Restart()` after the
validation check, in all four places the pattern appeared, then rebuilding.
This means every sweep result collected before the fix (this repo's existing
`data/*-sweep/results.jsonl` files) excluded entry 0 of each branch —
immaterial for aggregate statistics over 100k+ entries, but worth knowing.

### 7. Convenience script

`~/LossBench/env.sh` puts the toolchain on `PATH`/`LD_LIBRARY_PATH` for any
future shell:

```bash
source ~/LossBench/env.sh
./build/lossbench --list-compressors
```

## Summary of what lives where

| Thing | Location |
|---|---|
| micromamba binary | `~/local/micromamba/bin/micromamba` |
| conda-forge env (ROOT, CMake, GCC, zstd, nlohmann_json) | `~/local/micromamba/root/envs/lossbench` |
| SZ3 source + build | `~/local/src/SZ3` |
| SPERR source + build | `~/local/src/SPERR` |
| LossBench source | `~/LossBench/src` |
| LossBench build output | `~/LossBench/build/lossbench` |
| Env activation shortcut | `~/LossBench/env.sh` |
