# Spec: REC-02 — Shadow/canary/promotion/drift/rollback controls

> Work package `REC-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PY-EVAL` · Depends on: `REC-01`, `OPS-02`

## Problem

Implement shadow decisions, deterministic canary allocation, spending/risk envelopes, signed promotion, rollback, and automatic disable triggers.

## Goals

- Implement shadow and deterministic canary allocation.
- Implement signed promotion and rollback.
- Implement automatic disable triggers.

## Non-goals

- No promotion without signed evaluation.
- No rollback by editing history.

## Requirements

- `NR-ROUTE-006` — Recommendations MUST learn only from versioned, scoped observations and MUST remain advisory until signed promotion.
  - Acceptance: Online statistics cannot mutate an active policy or acceptance threshold. · Release test(s): `T-ROUTE-002`
- `NR-OPS-002` — Administrative kill switches MUST exist globally and by tenant, project, provider, model, agent, and tool.
  - Acceptance: Kill-switch tests stop new/cached work and produce audit evidence. · Release test(s): `T-OPS-001`

## Acceptance criteria

- [ ] T-ROUTE-002 proves promotion independence, canary bounds, and rollback.
- [ ] Automatic disable triggers fire on the defined violation classes.
