# Spec: EVAL-01 — Versioned cohort/benchmark/harness registry and signed results

> Work package `EVAL-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PY-EVAL`, `ROLE-RUST` · Depends on: `VER-01`, `MEM-01`, `COST-01`

## Problem

Build the evaluation plane (primarily Python) through immutable manifests and Rust-controlled promotion APIs, versioning dataset/cohort, task, metric, harness, prompt, model, provider, tool, verifier, environment, seed, and code revision, with signed result artifacts and uncertainty/calibration metrics.

## Goals

- Version every evaluation dimension (cohort, harness, model, seed, code).
- Store signed result artifacts with uncertainty and calibration.
- Resist gaming with hidden/mutation/adversarial suites.

## Non-goals

- No transferable result without its tested harness.
- No promotion outside the Rust-controlled API.

## Requirements

- `NR-ROUTE-006` — Recommendations MUST learn only from versioned, scoped observations and MUST remain advisory until signed promotion.
  - Acceptance: Online statistics cannot mutate an active policy or acceptance threshold. · Release test(s): `T-ROUTE-002`
- `NR-COST-004` — Reports MUST show quality/cost/latency tradeoffs and route regret, not only spend.
  - Acceptance: Cohort reports compare chosen and admissible alternatives with uncertainty. · Release test(s): `T-COST-001`, `T-ROUTE-002`
- `NR-COST-005` — Feedback MUST distinguish preference, deterministic outcome, environment outcome, verifier judgment, and human authorization.
  - Acceptance: A thumbs-up cannot be treated as proof of correctness. · Release test(s): `T-COST-001`, `T-ROUTE-002`

## Acceptance criteria

- [ ] Every launch cohort has a signed benchmark manifest and results.
- [ ] Calibration and hidden anti-gaming tests are included.
- [ ] Promotion occurs only through the Rust-controlled API.
