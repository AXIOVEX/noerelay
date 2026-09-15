# Plan: VER-02 — Bounded repair/fallback/clarification/rejection/escalation state machines

## Approach

On verification failure, trigger bounded repair, fallback, clarification, rejection, or escalation. Repair cycles keep acceptance criteria unchanged and are bounded by value and cost. No failure path marks a run accepted.

## Components

- `crates/noerelay-core/src/verification.rs (repair/escalation state machines)`
- `crates/noerelay-core/src/routing.rs (fallback integration)`

## Risks

- A repair cycle weakens the acceptance criteria to force a pass.
- A repair loop exceeds its value/cost bound.
