# Plan: FND-03 — Executable observed-evidence pipeline

## Approach

Implement the evidence envelope and the record/validate/coverage/gate commands in xtask; ingest evaluator outcomes (pass/warn/iterate/clarify/gather_evidence/block) as observed events; enforce that a test ID is not evidence until a runner records the full envelope.

## Components

- `xtask/src/evidence.rs (TestRunRecorder, envelope)`
- `xtask/src/validate.rs (BundleValidator)`
- `xtask/src/coverage.rs (coverage report, gate check)`
- `crates/noerelay-core/src/evidence.rs (evidence model)`
- `crates/noerelay-core/src/evaluator_ingestion.rs (SpecKitHook outcome mapping)`
- `evidence/ (recorded bundles and baselines)`

## Risks

- Evidence recorded against the wrong revision is silently stale.
- A test ID treated as passing without a recorded envelope defeats the gate.
