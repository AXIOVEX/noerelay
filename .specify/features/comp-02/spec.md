# Spec: COMP-02 — Data inventory and tested retention/residency/deletion/hold/export

> Work package `COMP-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-COMP`, `ROLE-DATA` · Depends on: `IAM-04`, `ART-01`, `OPS-03`

## Problem

Complete the data inventory and privacy/legal review, vendor/subprocessor inventory, data processing terms, retention/residency/deletion decisions, incident commitments, and customer-responsibility disclosures, with tested lifecycle behavior.

## Goals

- Complete the data inventory and vendor/subprocessor inventory.
- Test retention, residency, deletion, legal hold, and export per tenant/project.
- Complete privacy/legal review and disclosures.

## Non-goals

- No lifecycle behavior claimed without a test.
- No unreviewed vendor or subprocessor.

## Requirements

- `NR-IAM-005` — Tenant deletion and retention operations MUST cover authoritative rows, artifacts, caches, credentials, and derived views.
  - Acceptance: Deletion tests prove no scoped record remains except legally configured tombstones/audit proofs. · Release test(s): `T-IAM-001`, `T-COMP-001`
- `NR-COMP-002` — Retention, residency, privacy, legal hold, deletion, and export policies MUST be explicit per tenant/project.
  - Acceptance: Policy simulation and lifecycle tests prove configured behavior. · Release test(s): `T-COMP-001`

## Acceptance criteria

- [ ] T-COMP-001 retention, residency, deletion, legal-hold, and export fixtures pass.
- [ ] Policy simulation and lifecycle tests prove configured behavior.
