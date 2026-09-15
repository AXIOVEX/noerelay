# Spec: PROV-02 — Bounded transport/capability/semantic/epistemic/specification fallbacks

> Work package `PROV-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `PROV-01`, `VER-01`

## Problem

Implement separate bounded fallback paths for endpoint transport, provider, capability, semantic repair, epistemic escalation, specification clarification, rejection, and human escalation, each with its own budget, evidence, and terminal code.

## Goals

- Implement distinct, bounded fallback paths per failure class.
- Cost every attempt across fallback paths.
- Emit distinct failure events per class.

## Non-goals

- No fallback weakening data policy, verifier independence, or acceptance.
- No unbounded fallback loop.

## Requirements

- `NR-ROUTE-008` — Provider fallback, capability fallback, semantic fallback, epistemic escalation, and specification clarification MUST be distinct and bounded.
  - Acceptance: Each class has separate budgets, events, metrics, and terminal behavior. · Release test(s): `T-ROUTE-001`
- `NR-EXEC-002` — Timeouts, retries, and circuit breakers MUST be classified by operation and failure class.
  - Acceptance: Fault injection proves policy failures are not retried as transport failures. · Release test(s): `T-EXEC-001`

## Acceptance criteria

- [ ] The provider failure end-to-end scenario proves complete attempt costing and distinct failure events.
- [ ] Each fallback class has separate budgets, events, metrics, and terminal behavior.
