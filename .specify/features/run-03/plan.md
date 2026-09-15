# Plan: RUN-03 — Scoped idempotency, cancellation, and side effects

## Approach

Store response/terminal references durably. Propagate cancellation through runs, provider streams, tools, MCP, A2A, and reservations. Use stable effect IDs, downstream idempotency where supported, reconciliation where not, and explicit unknown_effect_state escalation.

## Components

- `crates/noerelay-store/src/execution.rs (claim_idempotency_key, request_cancellation, record_effect_request/result, reconcile_effect)`

## Risks

- Same key with changed input is replayed instead of conflicting.
- A cancelled run leaves a reserved budget unreconciled.
