# Spec: FND-03 — Executable observed-evidence pipeline

> Work package `FND-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-ORCH` · Depends on: `FND-01`, `FND-02`

## Problem

Make evidence collection executable: every test ID records command, revision, environment, result, and artifact hash into an evidence bundle that the release gate can validate.

## Goals

- Record a complete evidence envelope per test run.
- Validate bundles against the coverage manifest.
- Report requirement coverage and gate readiness.

## Non-goals

- No acceptance from model self-attestation without an observed test event.
- No reuse of evidence from a different revision or artifact digest.

## Requirements

- `NR-SPEC-002` — The system MUST maintain bidirectional architecture -> requirement -> test -> evidence traceability.
  - Acceptance: Orphaned `MUST` requirements, tests, or accepted evidence fail the release gate. · Release test(s): `T-SPEC-001`
- `NR-SPEC-006` — Release authority MUST require linked test evidence, not model self-attestation.
  - Acceptance: Self-reported “tests pass” text cannot satisfy a gate without an observed test event. · Release test(s): `T-SPEC-001`

## Acceptance criteria

- [ ] xtask evidence validate passes only for complete, manifest-consistent bundles.
- [ ] xtask evidence coverage reports per-requirement coverage with no orphans.
- [ ] xtask evidence gate reports pass/fail per G0-G8 gate.
