# Spec: RTK-01 — RTK native compression engine and PyO3 bridge

> Work package `RTK-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PY-EVAL`, `ROLE-RUST` · Depends on: `CTX-01`

## Problem

Ship the Rust-native context condenser (`noerelay-compact` in `rtk/`) as the authoritative compression engine for the Python gateway, with a Maturin/PyO3 bridge and a documented Python fallback, so compression is fast, deterministic, and auditable (NR-RTK-001, NR-RTK-002).

## Goals

- Produce a buildable `noerelay-compact` native module from `rtk/` (maturin, pyo3).
- Route gateway compression through the native bridge with a null-signal fallback.
- Record per-pass compression metrics with protected-node preservation.
- Keep the Python fallback behaviorally equivalent for the shared contract tests.

## Non-goals

- No changes to the Rust gateway core in this package (the bridge is the Python-side surface).
- No new compression strategies beyond dedup/prune/summarize/auto already defined.

## Requirements

- `NR-RTK-001` — Context compression MUST be provided by a Rust-native engine (`noerelay-compact`) exposed to the Python gateway through a PyO3/Maturin bridge, and the bridge MUST degrade to a documented Python fallback when the native module is unavailable.
  - Acceptance: The bridge returns native results when the module is built and a null signal that triggers the documented fallback otherwise; both paths pass the same compression contract tests. · Release test(s): `T-RTK-001`
- `NR-RTK-002` — Every compression pass MUST record strategy, original and compressed token counts, compression ratio, tokens saved, and duration, and MUST preserve the protected nodes defined by `NR-CTX-002`.
  - Acceptance: Compression events appear in audit/ledger metadata; property tests prove requirements, decisions, contradictions, approvals, evidence handles, and active tool state survive dedup, prune, and auto strategies. · Release test(s): `T-RTK-001`

## Acceptance criteria

- [ ] `maturin build` in `rtk/` produces an importable `noerelay_compact` module.
- [ ] `is_native_available()` is true when built; the bridge returns None (fallback signal) when not.
- [ ] Compression contract tests pass with the native module installed and with it absent.
- [ ] Each compression pass emits strategy, token counts, ratio, tokens saved, and duration, and protected nodes survive.
