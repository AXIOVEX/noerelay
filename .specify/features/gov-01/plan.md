# Plan: GOV-01 — Immutable V-model governance registry

## Approach

Store immutable revisions with the lifecycle draft->proposed->reviewed->approved->active->superseded (plus rejected). Runs pin exact revisions and never read a moving latest pointer. Changing an active requirement creates a new revision and marks dependent unexecuted evidence stale; it never edits history. The implementing identity cannot activate its own high-risk acceptance revision.

## Components

- `crates/noerelay-store/src/governance.rs (governance repository)`
- `crates/noerelay-core/src/governance.rs (governance domain model)`
- `crates/noerelay-core/src/traceability.rs (impact graph, orphan/cycle detection)`
- `crates/noerelay-gateway/src/lib.rs (governance_release_gate route)`

## Risks

- A moving latest pointer lets a run read a revision it was not governed by.
- An orphan or cycle in the impact graph silently breaks traceability.
