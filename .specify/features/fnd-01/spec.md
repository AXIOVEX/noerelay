# Spec: FND-01 — Freeze profile, scope, baseline, and risks

> Work package `FND-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-ORCH` · Depends on: —

## Problem

Capture the immutable baseline: the named v1 deployment profile, the frozen requirement set, the requirement-to-work-package traceability, and the initial risk register. Everything downstream is validated against this baseline.

## Goals

- Freeze the named deployment profile and its non-goals.
- Freeze the authoritative MUST requirement set and its IDs.
- Produce and validate the requirement-to-work-package coverage manifest.
- Establish the initial risk register and the local/test-only evidence profile.

## Non-goals

- No production deployment or external customer commitment.
- No requirement additions or scope changes after freeze (those are new revisions).

## Requirements

- `NR-REL-003` — “100% ready” MUST refer to this frozen requirement set and a named deployment profile, never to universal fitness or automatic legal compliance.
  - Acceptance: Release record identifies remaining external/customer responsibilities and non-goals. · Release test(s): `T-REL-001`

## Acceptance criteria

- [ ] Every MUST requirement has at least one primary work package and one release test.
- [ ] No orphaned requirements, no duplicate IDs, no TBD placeholders in the manifest.
- [ ] Named profile ID and DEC-01 local/test-only status are recorded and approved.
