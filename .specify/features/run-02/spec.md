# Spec: RUN-02 — Transactional outbox, leases, retries, and circuit breakers

> Work package `RUN-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `RUN-01`

## Problem

Write authority state and an outbox event in one PostgreSQL transaction; run workers with bounded leases, heartbeats, fencing tokens, attempt limits, and poison-message quarantine; classify failures and scope circuit breakers.

## Goals

- Emit outbox events atomically with authority state.
- Run leased, fenced, bounded workers with poison-message quarantine.
- Classify failures and scope circuit breakers with audit events.

## Non-goals

- No policy failure retried as a transport failure.
- No unbounded retry or unscoped circuit breaker.

## Requirements

- `NR-EXEC-001` — Runs and steps MUST be durable, cancelable, resumable, leased, and idempotent.
  - Acceptance: Worker-death and duplicate-delivery tests converge to one terminal result and one side effect. · Release test(s): `T-EXEC-001`
- `NR-EXEC-002` — Timeouts, retries, and circuit breakers MUST be classified by operation and failure class.
  - Acceptance: Fault injection proves policy failures are not retried as transport failures. · Release test(s): `T-EXEC-001`

## Acceptance criteria

- [ ] Killing workers before, during, and after provider/tool calls converges to one valid terminal state.
- [ ] Duplicate and reordered deliveries are handled without duplicate effects.
- [ ] Lease expiry and database failure are handled without split-brain.
