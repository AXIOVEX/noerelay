# Plan: COST-02 — Scoped rollups, invoices, tradeoffs, and route regret

## Approach

Roll up by organization, project, environment, user, API key, run, model, provider, agent, tool, cohort, and time. Compute regret against historically admissible alternatives. Keep feedback types distinct.

## Components

- `crates/noerelay-core/src/analytics.rs (rollups and regret)`
- `crates/noerelay-core/src/usage.rs (source quantities)`
- `crates/noerelay-gateway/src/lib.rs (cost_report)`

## Risks

- A rollup total does not equal the source attempt records within rounding rules.
- Route regret uses a candidate that was not admissible at the decision time.
