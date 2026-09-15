# Spec: GOV-01 — Immutable V-model governance registry

> Work package `GOV-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-ARCH` · Depends on: `FND-02`, `FND-03`, `IAM-03`

## Problem

Persist immutable, bidirectionally linked revisions for architecture, requirements, threats, tests, policies, work orders, artifacts, evidence, and release baselines, with a queryable impact graph and revision pinning.

## Goals

- Persist immutable revisions for every governed object class.
- Maintain bidirectional links and an impact graph.
- Enforce revision pinning and stale-evidence invalidation.
- Keep the Rust release gate as the final automated authority.

## Non-goals

- No editing of a historical revision that governed an earlier run.
- No self-activation of a high-risk acceptance revision by its implementer.

## Requirements

- `NR-SPEC-001` — Every run MUST compile a versioned task contract containing outcome, constraints, acceptance criteria, risk, scope, budgets, allowed tools/agents, and required evidence.
  - Acceptance: Execution cannot start without a valid immutable contract. · Release test(s): `T-SPEC-001`
- `NR-SPEC-002` — The system MUST maintain bidirectional architecture -> requirement -> test -> evidence traceability.
  - Acceptance: Orphaned `MUST` requirements, tests, or accepted evidence fail the release gate. · Release test(s): `T-SPEC-001`
- `NR-SPEC-003` — High and critical risk work MUST reject missing acceptance criteria rather than invent them.
  - Acceptance: Adversarial vague requests stop in clarification/approval states. · Release test(s): `T-SPEC-001`
- `NR-SPEC-004` — Requirement and policy revisions MUST be immutable and runs MUST pin exact revisions.
  - Acceptance: Replaying a run never reads a moving `latest` revision. · Release test(s): `T-SPEC-001`
- `NR-SPEC-005` — The governance workflow MUST distinguish proposed, observed, inferred, contradicted, accepted, and rejected statements.
  - Acceptance: Tests prove an unobserved model claim cannot become verification evidence. · Release test(s): `T-SPEC-001`
- `NR-SPEC-006` — Release authority MUST require linked test evidence, not model self-attestation.
  - Acceptance: Self-reported “tests pass” text cannot satisfy a gate without an observed test event. · Release test(s): `T-SPEC-001`
- `NR-EXEC-008` — Architecture -> requirements -> implementation -> tests work MAY be delegated, but acceptance MUST remain with an independent verifier and the Rust release gate.
  - Acceptance: The implementing agent cannot satisfy its own high-risk acceptance requirement. · Release test(s): `T-A2A-001`

## Acceptance criteria

- [ ] T-SPEC-001 proves immutable revision pinning and historical replay.
- [ ] Orphan and cycle entries are rejected on write.
- [ ] Changing an active requirement marks dependent unexecuted evidence stale.
- [ ] Unauthorized activation or supersession is denied.
