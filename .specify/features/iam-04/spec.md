# Spec: IAM-04 — Tenant lifecycle, retention, deletion, legal hold, export

> Work package `IAM-04` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-DATA`, `ROLE-COMP` · Depends on: `IAM-01`, `ART-01`

## Problem

Implement tenant data lifecycle: a complete data inventory, versioned lifecycle policies, legal hold, deletion jobs, cryptographic deletion where appropriate, export, tombstones, and reconciliation.

## Goals

- Build the authoritative data inventory.
- Implement versioned retention, legal hold, deletion, and export.
- Reconcile lifecycle behavior across every store and derived view.

## Non-goals

- No scoped record remains after deletion except configured tombstones/audit proofs.
- No legal-hold bypass.

## Requirements

- `NR-IAM-005` — Tenant deletion and retention operations MUST cover authoritative rows, artifacts, caches, credentials, and derived views.
  - Acceptance: Deletion tests prove no scoped record remains except legally configured tombstones/audit proofs. · Release test(s): `T-IAM-001`, `T-COMP-001`
- `NR-COMP-002` — Retention, residency, privacy, legal hold, deletion, and export policies MUST be explicit per tenant/project.
  - Acceptance: Policy simulation and lifecycle tests prove configured behavior. · Release test(s): `T-COMP-001`

## Acceptance criteria

- [ ] Seeded canary records are removed or retained exactly per policy across every store and view.
- [ ] Backup expiry and legal-hold behavior are independently verified.
- [ ] Deletion tests prove no scoped record remains except configured tombstones/audit proofs.
