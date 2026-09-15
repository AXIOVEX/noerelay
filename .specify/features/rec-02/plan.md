# Plan: REC-02 — Shadow/canary/promotion/drift/rollback controls

## Approach

Promote only via signed evaluation. Trigger automatic disable on policy violations, unsafe accepts, tenant leaks, duplicate effects, calibration breaches, unexplained cost spikes, or evidence failures. Roll back by activating a previous signed revision.

## Components

- `crates/noerelay-core/src/recommendation.rs (canary and promotion)`
- `crates/noerelay-core/src/ranking.rs (shadow decisions)`
- `crates/noerelay-core/src/governance.rs (signed revision activation)`

## Risks

- A canary exceeds its spending or risk envelope.
- A promotion is not reversible because history was edited.
