# Plan: TOOL-01 — Versioned tool registry, schemas, grants, and approvals

## Approach

A model-visible description grants no authority. Rust validates the proposal and mints a narrowly scoped, expiring execution grant. Side-effecting tools require idempotency and risk-appropriate approval.

## Components

- `crates/noerelay-core/src/tools.rs (tool registry and grants)`
- `crates/noerelay-core/src/tool_execution.rs (governed execution)`
- `crates/noerelay-core/src/budget.rs (resource and cost grants)`

## Risks

- A tool proposal executes before deterministic authorization.
- A grant is over-scoped or does not expire.
