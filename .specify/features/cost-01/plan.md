# Plan: COST-01 — Attempt-level measured/estimated/provider/billed cost ledger

## Approach

Reserve worst-case admissible cost before each attempt and reconcile atomically after. Keep the four cost sources distinct so reconciliation is exact.

## Components

- `crates/noerelay-core/src/usage.rs (usage and cost quantities)`
- `crates/noerelay-core/src/budget.rs (reservation and reconciliation)`
- `crates/noerelay-store/src/lib.rs (cost_rollups)`

## Risks

- Concurrent requests overspend a shared cap because reservation is not atomic.
- A late billing event is not reconciled, skewing totals.
