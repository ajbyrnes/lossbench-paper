# LossBench CHEP 2026 — Figure Specification

Handoff doc for producing the seven figures in the LossBench paper. Target venue is IOP conference proceedings (CHEP 2026), 8-page limit.

## Global conventions

Apply to every figure unless a figure's spec overrides.

- **Backend**: matplotlib. Save both `.pdf` (for LaTeX) and `.png` (for slides/preview).
- **Sizing**: IOP proceedings is single-column full-width ~6.3 in. Use `figsize=(6.3, h)` for full-width figures and `figsize=(3.1, h)` for half-width. Height per figure noted below.
- **Fonts**: matplotlib default serif to match LaTeX body; 9 pt tick labels, 10 pt axis labels, 10 pt legend. No title inside the axes — use LaTeX `\caption{}` instead.
- **Colors**: consistent per-compressor palette across every figure it appears in.
  - SZ3: `#0072B2` (blue)
  - ZFP: `#D55E00` (vermillion)
  - SPERR: `#009E73` (green)
  - zstd-trunc: `#CC79A7` (magenta)
  - R(D) bound: black, dashed
- **Markers**: circle SZ3, square ZFP, triangle SPERR, diamond zstd-trunc. Marker size 4–5.
- **Grid**: light gray, `alpha=0.3`, behind data.
- **Legends**: inside axes when space allows, `frameon=False`, no title.
- **Log axes**: use `LogLocator` and format ticks as `10^n` where relevant (compression ratio, EMD often).
- **File naming**: `fig{N}_{shortname}.{pdf,png}` — e.g., `fig1_physlite_composition.pdf`.
- **Layout**: each figure gets its own `src/fig{N}/` directory holding that figure's script(s), any figure-specific data-prep code, and its rendered `.pdf`/`.png` output side by side. Shared code (`plotting_style.py`) stays at the repo root and is imported via `sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))` from within `src/fig{N}/`. Shared infra used across figures (e.g. `certs/` for remote data access) also stays at the repo root.

## Data sources

- `results.jsonl` — 792-row zstd-trunc sweep across jet pt/eta/phi. Fields include chunk size, truncBits, compressionLevel, PSNR, EMD (Wasserstein), KS statistic, quantile shifts, compression ratio.
- `branch_stats.csv` (or equivalent) — PHYSLITE per-branch `GetTotBytes` / `GetZipBytes`.
- SZ3, ZFP, SPERR run outputs — **pending Phase 1**. Figures that depend on these should be built to accept the same schema as `results.jsonl` so they render as soon as data lands.
- R(D) bound estimates — **pending Phase 1**. Build the overlay as a separate function that reads a bound curve from CSV, so it can be swapped in without touching the Pareto code.

## Figures

### Figure 1 — PHYSLITE composition (motivation)

**Purpose**: establish that kinematics is the bucket that compresses poorly under lossless schemes, motivating lossy compression on those branches specifically.

- **Type**: horizontal stacked bar, or grouped bar. One row per bucket: {four-vectors, other continuous floats, discrete/metadata}.
- **X-axis**: bytes (log scale if the buckets span orders of magnitude; linear if not).
- **Two bars per bucket**: uncompressed (`GetTotBytes`) and lossless-compressed (`GetZipBytes`). Or a single bar showing compressed size with a marker for uncompressed.
- **Annotation**: per-bucket lossless compression ratio as text at end of bar.
- **Data**: `branch_stats.csv`. Bucketing logic: four-vectors = branches matching `*_pt`, `*_eta`, `*_phi`, `*_m`, `*_e`; discrete/metadata = integer types, bit-packed flags, event-level scalars; other continuous = everything else float-typed.
- **Size**: full-width, ~3.0 in tall.

### Figure 2 — Rate-distortion bound methodology (schematic + worked example)

**Purpose**: make the bound estimation procedure explicit so a reviewer can evaluate it. This is where the paper earns the right to overlay R(D) on Pareto plots.

- **Panel A (left)**: schematic of the bound estimation pipeline. Boxes: raw branch → quantization at distortion level D → empirical entropy H(D) → point on R(D) curve. Arrow flow. Text-only, no data.
- **Panel B (right)**: worked example on jet pt. X-axis: distortion D (in whatever units matches your EMD estimate). Y-axis: estimated H(D), bits/value. Curve is the empirical bound; individual quantization operating points as markers along it.
- **Size**: full-width, ~2.8 in tall. Two-panel layout via `plt.subplots(1, 2)`.
- **Blocked on**: R(D) methodology finalization (Phase 1). Build the plotting code now against a stub CSV.

### Figure 3 — Pareto frontier + R(D) overlay per branch (CENTERPIECE)

**Purpose**: the headline claim. SZ3 approaches the empirical R(D) bound; other compressors sit further from it.

- **Type**: small multiples, 1×3 or 1×4. One subplot per branch: jet pt, jet eta, jet phi, (optionally jet m).
- **X-axis**: rate (bits/value, or compression ratio — pick one and stick with it across every figure). Log scale likely.
- **Y-axis**: distortion (EMD as primary — see Figure 4 for the justification). Log scale likely.
- **Per subplot**:
  - Scatter of all configurations per compressor, faint (`alpha=0.3`).
  - Pareto-optimal points per compressor, bold, connected by a stepped line.
  - R(D) bound curve overlaid in black dashed.
- **Legend**: shared across subplots, placed above or to the right — not repeated in each panel.
- **Size**: full-width, ~3.0 in tall for 1×3; ~2.5 in for 1×4.
- **Blocked on**: SZ3/ZFP/SPERR runs + R(D) bound. Build against stub data now.

### Figure 4 — Metric disagreement (PSNR vs distribution metrics)

**Purpose**: evidence that PSNR and distribution metrics rank configurations differently, motivating EMD as the primary distortion metric for downstream physics.

- **Type**: two options, pick one after seeing the data:
  - (a) Scatter of configurations, x = PSNR rank, y = EMD rank. Off-diagonal points are disagreements. Color by compressor.
  - (b) Pareto frontier of a single branch drawn twice, once with y = PSNR, once with y = EMD, side by side. Configurations that are Pareto-optimal under one metric but dominated under the other are highlighted.
- **Preference**: (b) is more concrete and directly interpretable. Start there.
- **Size**: full-width, ~3.0 in tall.
- **Data**: `results.jsonl` — zstd-trunc alone is enough for a first pass; ideally include all four compressors once Phase 1 data lands.

### Figure 5 — Chunk-size × error-bound decomposition

**Purpose**: shows the interior of the sweep — how compression ratio (or distortion) varies over the two-axis configuration space per compressor. Explains *why* the Pareto frontier looks the way it does.

- **Type**: heatmap grid, one heatmap per compressor. 2×2 layout for four compressors.
- **X-axis**: chunk size (1 KB → 1 MB, log-spaced).
- **Y-axis**: error bound (for SZ3/ZFP/SPERR) or truncBits (for zstd-trunc). Use a consistent color scale across all four panels if possible; separate scales if the ranges are wildly different (note this in the caption).
- **Color**: compression ratio, or EMD — pick one. Compression ratio is easier to interpret for a physics audience.
- **Size**: full-width, ~4.5 in tall for 2×2.
- **Blocked on**: SZ3/ZFP/SPERR runs. Build against `results.jsonl` for the zstd-trunc panel first.

### Figure 6 — Z→ℓℓ mass reconstruction validation

**Purpose**: physics-level check that Pareto-optimal compression configurations don't distort downstream observables.

- **Type**: two options:
  - (a) Overlaid mass histograms — uncompressed truth vs a few operating points along the Pareto frontier (e.g., low-rate, mid-rate, high-rate).
  - (b) Bias and resolution of reconstructed Z mass vs compression ratio, one point per operating point along the frontier. Two panels: bias on top, resolution on bottom, shared x-axis.
- **Preference**: (a) is visually compelling and honest; (b) is more quantitative. If space allows, do both as a two-panel figure.
- **Size**: full-width, ~3.0 in tall for single-panel; ~4.5 in for two-panel.
- **Blocked on**: reconstruction pipeline on decompressed outputs. Confirm status.

### Figure 7 — LossBench architecture schematic (optional)

**Purpose**: visualize the five-dimension framing and two-output architecture. Only include if space allows and if it clarifies more than the prose alone.

- **Type**: block diagram. Text and boxes, no data.
- **Recommended tool**: draw in TikZ directly in the LaTeX source, not matplotlib. Skip for now; revisit after figures 1–6 are done.

## Priority order

1. **Figure 1** (motivation) — data on hand, sets the plotting style, definitely in the paper.
2. **Figure 4** (metric disagreement) — data on hand from `results.jsonl`, load-bearing for the metrics contribution.
3. **Figure 3** (Pareto + R(D)) — build the scaffolding against stub data; wire up real data as Phase 1 lands.
4. **Figure 5** (chunk × error heatmaps) — same as Figure 3, scaffold first.
5. **Figure 2** (R(D) methodology) — scaffold; blocked on methodology finalization.
6. **Figure 6** (Z→ℓℓ validation) — blocked on reconstruction pipeline.
7. **Figure 7** (architecture) — optional, defer.

## Deliverables

For each figure, produce:

1. A standalone Python script `make_fig{N}_{shortname}.py` in `src/fig{N}/` that reads the relevant data file(s) and writes its output alongside itself.
2. The rendered `.pdf` and `.png`, written into that same `src/fig{N}/` directory.
3. A one-paragraph caption draft as a comment at the top of the script — Aim will edit into final caption prose during paper writing.

A shared `plotting_style.py` module holds the color/marker dicts, `set_style()` function, and any helpers (Pareto-frontier extraction, log-tick formatters). Every figure script imports from it.