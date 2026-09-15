# Plan: RUN-02 — Transactional outbox, leases, retries, and circuit breakers

## Approach

Emit outbox events atomically with the state change. Workers claim jobs with bounded leases and fencing tokens. Classify failures as transport, rate/quota, capability, semantic, epistemic, policy, specification, cancellation, or permanent; retry policy is operation-specific and budget-aware. Circuit breakers are scoped by provider/model/agent/tool and emit audit events.

## Components

- `crates/noerelay-store/src/execution.rs (enqueue_outbox_event, claim_work_item, record_circuit_success/failure, expire_leases)`

## Risks

- A duplicate or reordered outbox delivery double-applies an effect.
- An expired lease is re-claimed while the original worker is still running.
