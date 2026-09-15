# Plan: REC-01 — Advisory recommendations with uncertainty/freshness/coverage/reasons

## Approach

Learn only from versioned, scoped observations and remain advisory until signed promotion. Sparse or stale data produces abstention or qualified advice, never false certainty.

## Components

- `crates/noerelay-core/src/recommendation.rs (advisory recommendations)`
- `crates/noerelay-core/src/ranking.rs (advisory ranking)`

## Risks

- A recommendation mutates an active policy before signed promotion.
- Sparse data produces overconfident advice.
