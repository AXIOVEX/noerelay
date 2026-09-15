# Plan: RUN-01 — Persistent run/step/attempt/work-item state machines

## Approach

Replace whole-project snapshots as the only execution representation. Keep snapshot/replay projections only if useful, but make invariants transactional and explicitly versioned. Restarting at any transition boundary must reconstruct the same admissible next actions and never regenerate completed work from prose.

## Components

- `crates/noerelay-store/src/execution.rs (create_run/step/attempt/work_item, status updates)`
- `crates/noerelay-core/src/execution.rs (execution domain model)`

## Risks

- An illegal transition accepted at the boundary corrupts the run.
- A restart regenerates completed work, double-executing side effects.
