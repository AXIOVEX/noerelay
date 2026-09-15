# Plan: VER-01 — Persistent risk-scaled verification DAG and verifier independence

## Approach

Order checks deterministically with dependencies. Enforce verifier independence appropriate to risk (same-family-only cannot satisfy an independent-family gate). Keep every failure path non-accepted.

## Components

- `crates/noerelay-core/src/verification.rs (verification DAG and independence)`
- `crates/noerelay-core/src/evaluator_result.rs (check results)`

## Risks

- A probabilistic review runs before deterministic checks, ordering the DAG wrongly.
- A same-family verifier satisfies an independence gate.
