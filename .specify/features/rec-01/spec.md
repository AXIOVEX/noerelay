# Spec: REC-01 — Advisory recommendations with uncertainty/freshness/coverage/reasons

> Work package `REC-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PY-EVAL` · Depends on: `EVAL-01`, `COST-02`

## Problem

Compute advisory recommendations in Rust from scoped versioned observations, reporting cohort coverage, sample size, lower confidence bound, uncertainty, freshness, drift, cost, latency, and reasons for abstention, keeping hard constraints first.

## Goals

- Compute advisory recommendations from scoped versioned observations.
- Report uncertainty, coverage, freshness, and abstention reasons.
- Keep hard constraints first and remain advisory until promotion.

## Non-goals

- No online statistic mutating an active policy or acceptance threshold.
- No false certainty from sparse or stale data.

## Requirements

- `NR-ROUTE-003` — Among admissible plans, routing MUST minimize expected total cost, then latency, then maximize calibrated acceptance likelihood.
  - Acceptance: Deterministic fixtures return the same plan and complete rejection reasons. · Release test(s): `T-ROUTE-001`
- `NR-ROUTE-006` — Recommendations MUST learn only from versioned, scoped observations and MUST remain advisory until signed promotion.
  - Acceptance: Online statistics cannot mutate an active policy or acceptance threshold. · Release test(s): `T-ROUTE-002`
- `NR-ROUTE-007` — Recommendations MUST report uncertainty, cohort coverage, freshness, and reasons.
  - Acceptance: Sparse or stale data produces abstention or qualified advice, never false certainty. · Release test(s): `T-ROUTE-002`
- `NR-COST-004` — Reports MUST show quality/cost/latency tradeoffs and route regret, not only spend.
  - Acceptance: Cohort reports compare chosen and admissible alternatives with uncertainty. · Release test(s): `T-COST-001`, `T-ROUTE-002`
- `NR-COST-005` — Feedback MUST distinguish preference, deterministic outcome, environment outcome, verifier judgment, and human authorization.
  - Acceptance: A thumbs-up cannot be treated as proof of correctness. · Release test(s): `T-COST-001`, `T-ROUTE-002`

## Acceptance criteria

- [ ] T-ROUTE-002 proves cohort isolation, sparse/stale abstention, and advisory-only behavior.
- [ ] Recommendations report uncertainty, coverage, freshness, and reasons.
