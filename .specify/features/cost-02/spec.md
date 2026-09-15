# Spec: COST-02 — Scoped rollups, invoices, tradeoffs, and route regret

> Work package `COST-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-WEB` · Depends on: `COST-01`, `EVAL-01`

## Problem

Compute complete scoped rollups, invoices, quality/cost/latency tradeoffs, and route regret only against candidates admissible at the historical decision using pinned registry/policy/features.

## Goals

- Compute complete scoped rollups and invoices.
- Compute quality/cost/latency tradeoffs and route regret.
- Keep feedback types distinct.

## Non-goals

- No regret computed against non-admissible historical candidates.
- No feedback type conflated (a thumbs-up is not proof of correctness).

## Requirements

- `NR-ROUTE-004` — Expected total cost MUST include inference, tools, verification, retries, fallback, infrastructure, and expected human review.
  - Acceptance: Cost-selection tests detect locally cheap but globally expensive plans. · Release test(s): `T-ROUTE-001`, `T-COST-001`
- `NR-COST-002` — Usage and cost MUST aggregate by organization, project, environment, user, API key, run, model, agent, and tool.
  - Acceptance: Roll-up totals equal source attempt records within declared rounding rules. · Release test(s): `T-COST-001`
- `NR-COST-004` — Reports MUST show quality/cost/latency tradeoffs and route regret, not only spend.
  - Acceptance: Cohort reports compare chosen and admissible alternatives with uncertainty. · Release test(s): `T-COST-001`, `T-ROUTE-002`

## Acceptance criteria

- [ ] T-COST-001 passes aggregation conservation, late billing, correction, refund, currency, retry/fallback, and invoice reconciliation fixtures.
- [ ] Cohort reports compare chosen and admissible alternatives with uncertainty.
