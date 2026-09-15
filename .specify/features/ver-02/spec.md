# Spec: VER-02 — Bounded repair/fallback/clarification/rejection/escalation state machines

> Work package `VER-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `VER-01`, `PROV-02`

## Problem

Implement bounded repair cycles with unchanged acceptance criteria and explicit value/cost limits, plus clarification, abstention, rejection, and escalation states.

## Goals

- Implement bounded repair with unchanged acceptance criteria.
- Implement clarification, abstention, rejection, and escalation states.
- Bound repair by value and cost.

## Non-goals

- No acceptance-criteria weakening during repair.
- No unbounded repair loop.

## Requirements

- `NR-SPEC-003` — High and critical risk work MUST reject missing acceptance criteria rather than invent them.
  - Acceptance: Adversarial vague requests stop in clarification/approval states. · Release test(s): `T-SPEC-001`
- `NR-ROUTE-008` — Provider fallback, capability fallback, semantic fallback, epistemic escalation, and specification clarification MUST be distinct and bounded.
  - Acceptance: Each class has separate budgets, events, metrics, and terminal behavior. · Release test(s): `T-ROUTE-001`
- `NR-CTX-006` — When evidence is insufficient, the system MUST clarify, gather information, abstain, or escalate.
  - Acceptance: No-route and low-confidence fixtures never fabricate an accepted answer. · Release test(s): `T-CTX-001`
- `NR-VER-003` — Verification failure MUST trigger bounded repair, fallback, clarification, rejection, or escalation.
  - Acceptance: No failure path silently marks a run accepted. · Release test(s): `T-VER-001`

## Acceptance criteria

- [ ] T-VER-001 proves bounded repair and that no failure path marks a run accepted.
- [ ] Clarification/abstention/rejection/escalation states are reachable and correct.
