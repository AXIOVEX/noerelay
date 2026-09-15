# Spec: MEM-01 — Durable typed project/user/session epistemic graph

> Work package `MEM-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `RUN-01`, `ART-01`, `IAM-04`

## Problem

Persist typed facts, requirements, decisions, assumptions, observations, predictions, preferences, artifacts, and evidence/support/refutation edges with source handles, uncertainty, retention, and revisions, preserving four-valued epistemic states.

## Goals

- Persist the typed epistemic graph with evidence and support/refutation edges.
- Preserve four-valued epistemic states.
- Apply retention and residency to nodes, embeddings, indexes, and caches.

## Non-goals

- No candidate claim accepted on extraction.
- No contradiction averaged away.

## Requirements

- `NR-SPEC-005` — The governance workflow MUST distinguish proposed, observed, inferred, contradicted, accepted, and rejected statements.
  - Acceptance: Tests prove an unobserved model claim cannot become verification evidence. · Release test(s): `T-SPEC-001`
- `NR-CTX-001` — Context MUST be compiled from durable project/user/session state rather than forwarded as an unbounded transcript.
  - Acceptance: Token use stays within the selected model limit with an auditable inclusion manifest. · Release test(s): `T-CTX-001`
- `NR-CTX-003` — Summaries MUST carry provenance and an uncertainty class.
  - Acceptance: Summaries cannot overwrite source evidence and can be expanded back to source handles. · Release test(s): `T-CTX-001`
- `NR-CTX-004` — Claims MUST use four-valued epistemic state: supported, refuted, both, or neither.
  - Acceptance: Truth-table and merge tests preserve contradictions instead of averaging them away. · Release test(s): `T-CTX-001`
- `NR-CTX-005` — The system MUST distinguish facts, requirements, decisions, assumptions, observations, predictions, preferences, and artifacts.
  - Acceptance: Each type has valid transitions, evidence rules, retention, and rendering behavior. · Release test(s): `T-CTX-001`

## Acceptance criteria

- [ ] T-CTX-001 truth-table and merge tests preserve contradictions.
- [ ] Each claim type has valid transitions, evidence rules, retention, and rendering.
