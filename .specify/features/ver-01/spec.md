# Spec: VER-01 — Persistent risk-scaled verification DAG and verifier independence

> Work package `VER-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `RUN-01`, `ART-01`, `REG-01`

## Problem

Persist verification DAG definitions, check revisions, inputs, outputs, evidence, verifier identity/family, independence constraints, attempts, and terminal state, running deterministic checks before probabilistic review.

## Goals

- Persist the verification DAG with check revisions and evidence.
- Run deterministic checks before probabilistic review.
- Enforce risk-appropriate verifier independence.

## Non-goals

- No failure path silently marking a run accepted.
- No same-family-only review satisfying an independent gate.

## Requirements

- `NR-SPEC-005` — The governance workflow MUST distinguish proposed, observed, inferred, contradicted, accepted, and rejected statements.
  - Acceptance: Tests prove an unobserved model claim cannot become verification evidence. · Release test(s): `T-SPEC-001`
- `NR-EXEC-008` — Architecture -> requirements -> implementation -> tests work MAY be delegated, but acceptance MUST remain with an independent verifier and the Rust release gate.
  - Acceptance: The implementing agent cannot satisfy its own high-risk acceptance requirement. · Release test(s): `T-A2A-001`
- `NR-VER-001` — A risk-scaled verification DAG MUST run deterministic checks before probabilistic review.
  - Acceptance: Check ordering and dependency tests are deterministic and replayable. · Release test(s): `T-VER-001`
- `NR-VER-002` — High/critical work MUST use verifier independence appropriate to the risk.
  - Acceptance: Same-family-only review cannot satisfy an independent-family gate. · Release test(s): `T-VER-001`

## Acceptance criteria

- [ ] T-VER-001 proves deterministic ordering, verifier independence, and every fail-closed terminal path.
- [ ] Check ordering and dependency tests are deterministic and replayable.
