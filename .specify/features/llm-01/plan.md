# Plan: LLM-01 — Two-model local plane, GPU priority, and quant benchmark

## Approach

Extend the model catalog in `src/noerelay/models.py` with `gpt-oss-20b` (three quants) and tier metadata (fast/hard) plus VRAM guidance; fix `_recommend_split` in `src/noerelay/provision.py` so the display/primary GPU receives the larger tensor share (e.g. 15,10 on the reference host instead of 10,15); add a benchmark runner that loads each quant and records tokens/s, TTFT, VRAM, and a quality proxy into `evidence/`; expose the supported-model list through the catalog and the CLI.

## Components

- `src/noerelay/models.py (MODEL_CATALOG, tier/VRAM metadata)`
- `src/noerelay/provision.py (_recommend_split, _pick_model, _pick_ctx)`
- `src/noerelay/system_info.py (GPU detection, display GPU flag)`
- `benchmarks/ (task sets for the local benchmark)`
- `evidence/ (recorded per-quant benchmark artifact)`

## Risks

- Split weighting regresses to favoring the secondary GPU on hosts with different VRAM order.
- Benchmark artifacts are not reproducible (missing build tag, ctx, or seed).
- Catalog metadata drifts from what the provisioner actually loads.
