# Spec: COST-01 — Attempt-level measured/estimated/provider/billed cost ledger

> Work package `COST-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `RUN-01`, `RUN-02`, `RUN-03`, `REG-01`, `PROV-01`

## Problem

Record immutable attempt-level token, request, tool, verifier, artifact, infrastructure, and human-review quantities, preserving expected, estimated, provider-reported, and billed sources separately with currency, pricing revision, rounding rule, and reconciliation status.

## Goals

- Record immutable attempt-level cost quantities.
- Preserve the four cost sources separately.
- Reserve before and reconcile after each attempt.

## Non-goals

- No overspend of a shared cap under concurrency.
- No blending of estimated and billed values.

## Requirements

- `NR-ROUTE-003` — Among admissible plans, routing MUST minimize expected total cost, then latency, then maximize calibrated acceptance likelihood.
  - Acceptance: Deterministic fixtures return the same plan and complete rejection reasons. · Release test(s): `T-ROUTE-001`
- `NR-ROUTE-004` — Expected total cost MUST include inference, tools, verification, retries, fallback, infrastructure, and expected human review.
  - Acceptance: Cost-selection tests detect locally cheap but globally expensive plans. · Release test(s): `T-ROUTE-001`, `T-COST-001`
- `NR-COST-001` — Token, request, tool, verification, artifact, and human-review cost MUST be measured or explicitly estimated per attempt.
  - Acceptance: Reconciliation separates estimated, provider-reported, and billed values. · Release test(s): `T-COST-001`
- `NR-COST-003` — Hard budgets MUST be reserved before execution and reconciled after execution.
  - Acceptance: Concurrent requests cannot overspend a shared cap. · Release test(s): `T-COST-001`

## Acceptance criteria

- [ ] T-COST-001 passes concurrency, overflow, rounding, and reservation fixtures.
- [ ] Reconciliation separates estimated, provider-reported, and billed values.
