# Plan: OPS-02 — Scoped kill switches and safe rollback

## Approach

Define handling of in-flight work for each switch. Roll back by activating a previous signed revision rather than editing history. Record audit evidence for every switch action.

## Components

- `crates/noerelay-core/src/governance.rs (signed revision activation)`
- `crates/noerelay-store/src/lifecycle.rs (scope state)`

## Risks

- A kill switch does not stop cached work, so it keeps executing.
- A rollback edits history instead of activating a previous revision.
