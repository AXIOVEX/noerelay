# Spec: RUN-01 — Persistent run/step/attempt/work-item state machines

> Work package `RUN-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `FND-02`, `IAM-01`

## Problem

Represent execution as normalized, append-friendly, durable entities (run, step, attempt, work item, dependency, reservation, approval, tool effect, provider call, verification check, artifact, terminal outcome) with legal transitions defined in Rust and enforced by database constraints.

## Goals

- Model the normalized durable execution entities.
- Define legal transitions in Rust and as database constraints.
- Make invariants transactional and versioned.

## Non-goals

- No regeneration of completed work from prose on restart.
- No whole-project snapshot as the sole authority.

## Requirements

- `NR-SPEC-001` — Every run MUST compile a versioned task contract containing outcome, constraints, acceptance criteria, risk, scope, budgets, allowed tools/agents, and required evidence.
  - Acceptance: Execution cannot start without a valid immutable contract. · Release test(s): `T-SPEC-001`
- `NR-EXEC-001` — Runs and steps MUST be durable, cancelable, resumable, leased, and idempotent.
  - Acceptance: Worker-death and duplicate-delivery tests converge to one terminal result and one side effect. · Release test(s): `T-EXEC-001`
- `NR-LED-001` — All authority-changing events MUST be canonicalized and hash-linked.
  - Acceptance: Tamper, deletion, reorder, and cross-run splice tests invalidate the chain. · Release test(s): `T-LED-001`

## Acceptance criteria

- [ ] Restart at every transition boundary reconstructs the same admissible next actions.
- [ ] Completed work is never regenerated from prose.
- [ ] Illegal transitions are rejected by both Rust and the database constraints.
