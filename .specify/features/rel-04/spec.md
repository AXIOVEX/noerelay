# Spec: REL-04 — Immutable GA bundle, approvals, deployment, and rollback

> Work package `REL-04` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-ORCH`, `ROLE-HUMAN` · Depends on: `REL-03`

## Problem

Produce the immutable GA evidence bundle with exact artifact/source approvals, deployment, and a tested rollback package, recorded as a signed release record.

## Goals

- Assemble the immutable GA evidence bundle with exact digests.
- Record the signed release record with all approvals.
- Prepare and test the rollback package.

## Non-goals

- No GA bundle with a missing or stale artifact digest.
- No release record without exact source and artifact approvals.

## Requirements

- `NR-REL-002` — A release MUST have product, engineering, security, evaluation, and operations sign-off evidence.
  - Acceptance: Missing approval leaves the release candidate non-GA. · Release test(s): `T-REL-001`
- `NR-REL-003` — “100% ready” MUST refer to this frozen requirement set and a named deployment profile, never to universal fitness or automatic legal compliance.
  - Acceptance: Release record identifies remaining external/customer responsibilities and non-goals. · Release test(s): `T-REL-001`

## Acceptance criteria

- [ ] T-REL-001 complete evidence bundle, approvals, non-goals, and external-responsibility disclosure pass.
- [ ] The release record identifies remaining external/customer responsibilities and non-goals.
