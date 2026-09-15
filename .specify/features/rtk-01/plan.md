# Plan: RTK-01 — RTK native compression engine and PyO3 bridge

## Approach

Build `rtk/` as the standalone PyO3 cdylib (maturin) and wire the existing `reference/gateway/rtk_bridge.py` import-or-fallback pattern into the gateway pipeline after route selection; align the bridge to the crate's dict contract (messages key, strategy, target_ratio, min_tokens); record compression metrics (strategy, token counts, ratio, tokens saved, duration) into run metadata and ledger-adjacent events; keep the Python `compression.py` as the documented fallback path and prove both paths pass the same contract tests.

## Components

- `rtk/Cargo.toml (noerelay-compact cdylib, pyo3)`
- `rtk/src/lib.rs (estimate_tokens_rust, dedup/prune/auto/compress_messages_rust)`
- `rtk/pyproject.toml (maturin build)`
- `reference/gateway/rtk_bridge.py (import-or-fallback bridge)`
- `reference/gateway/compression.py (documented Python fallback)`
- `tests/test_compression.py, tests/test_compression_cache.py, tests/test_compression_profiler.py`

## Risks

- PyO3 version skew between rtk (0.21) and the workspace (0.29) breaks the build; keep rtk standalone or pin a compatible pyo3.
- Stale `rtk/target/` artifacts from a previous machine path mislead the build.
- Native and fallback paths drift, so a fixture passes one path but not the other.
