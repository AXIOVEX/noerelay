# Spec: TOOL-01 — Versioned tool registry, schemas, grants, and approvals

> Work package `TOOL-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SEC` · Depends on: `REG-01`, `IAM-03`, `RUN-03`

## Problem

Create immutable tool revisions with input/output JSON Schema, risk class, side-effect class, required permissions, credential grants, egress allowlist, resource profile, timeout, idempotency semantics, approval policy, and verifier requirements.

## Goals

- Model immutable tool revisions with full authority metadata.
- Mint narrowly scoped, expiring execution grants.
- Require idempotency and approval for side-effecting tools.

## Non-goals

- No model-visible description granting authority.
- No side-effecting tool without idempotency and approval.

## Requirements

- `NR-EXEC-003` — Tool schemas, revisions, grants, credentials, egress, inputs, outputs, and side effects MUST be explicit.
  - Acceptance: A model-proposed tool call executes only after deterministic authorization. · Release test(s): `T-EXEC-002`
- `NR-EXEC-004` — Side-effecting tools MUST require idempotency and risk-appropriate approval.
  - Acceptance: Replay and retry cannot duplicate the side effect. · Release test(s): `T-EXEC-001`

## Acceptance criteria

- [ ] A model-proposed tool call executes only after deterministic authorization.
- [ ] Replay and retry cannot duplicate a side effect.
- [ ] T-EXEC-002 passes tool schema/grant fixtures.
