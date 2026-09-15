# Spec: VER-03 — Human approval and signed external-attestation APIs

> Work package `VER-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-WEB` · Depends on: `VER-01`, `IAM-03`, `API-05`

## Problem

Provide human approval and signed external-attestation APIs that are scoped, expiring, replay-protected, and bound to the exact action/artifact hash.

## Goals

- Implement signed, scoped, expiring, replay-protected attestations.
- Bind attestations to exact action and artifact hashes.
- Enforce separation of duties for high-risk approval.

## Non-goals

- No self-approval of high-risk work by the implementing identity.
- No replayed or out-of-scope attestation accepted.

## Requirements

- `NR-SPEC-006` — Release authority MUST require linked test evidence, not model self-attestation.
  - Acceptance: Self-reported “tests pass” text cannot satisfy a gate without an observed test event. · Release test(s): `T-SPEC-001`
- `NR-VER-002` — High/critical work MUST use verifier independence appropriate to the risk.
  - Acceptance: Same-family-only review cannot satisfy an independent-family gate. · Release test(s): `T-VER-001`
- `NR-VER-003` — Verification failure MUST trigger bounded repair, fallback, clarification, rejection, or escalation.
  - Acceptance: No failure path silently marks a run accepted. · Release test(s): `T-VER-001`

## Acceptance criteria

- [ ] T-VER-001 proves critical human approval and replay protection.
- [ ] Attestations bind to exact action/artifact hashes and expire correctly.
