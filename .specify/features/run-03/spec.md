# Spec: RUN-03 — Scoped idempotency, cancellation, and side effects

> Work package `RUN-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `RUN-01`, `RUN-02`

## Problem

Bind external idempotency keys to principal scope, endpoint profile, normalized request hash, and policy revision; propagate cancellation through the run DAG; and use an effect-intent/effect-result protocol with stable effect IDs.

## Goals

- Bind idempotency keys to scope, profile, request hash, and policy revision.
- Propagate cancellation across the full run DAG.
- Guarantee exactly-once visible effects via the effect protocol.

## Non-goals

- No duplicate externally visible side effect under retry.
- No silent unknown effect state without escalation.

## Requirements

- `NR-API-002` — Chat and Responses MUST support streaming and non-streaming operation.
  - Acceptance: SSE framing, terminal events, disconnect cancellation, and error behavior pass contract tests. · Release test(s): `T-API-002`
- `NR-API-004` — Every request MUST carry or derive organization, project, environment, user, session, request, and trace identities.
  - Acceptance: Missing or conflicting scope fails closed; identifiers appear in authorized audit views. · Release test(s): `T-API-003`
- `NR-API-005` — Idempotency keys MUST bind to caller scope and normalized request hash.
  - Acceptance: Same key/same input replays one result; same key/different input returns conflict. · Release test(s): `T-API-003`
- `NR-EXEC-001` — Runs and steps MUST be durable, cancelable, resumable, leased, and idempotent.
  - Acceptance: Worker-death and duplicate-delivery tests converge to one terminal result and one side effect. · Release test(s): `T-EXEC-001`
- `NR-EXEC-004` — Side-effecting tools MUST require idempotency and risk-appropriate approval.
  - Acceptance: Replay and retry cannot duplicate the side effect. · Release test(s): `T-EXEC-001`
- `NR-COST-003` — Hard budgets MUST be reserved before execution and reconciled after execution.
  - Acceptance: Concurrent requests cannot overspend a shared cap. · Release test(s): `T-COST-001`

## Acceptance criteria

- [ ] T-API-003 and T-EXEC-001 prove same-key replay and conflict on changed input.
- [ ] No duplicate visible effect under retry.
- [ ] Budget is released and reconciled after cancellation.
