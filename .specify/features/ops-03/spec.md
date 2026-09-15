# Spec: OPS-03 — Backup, PITR, restore, artifact reconciliation, DR exercises

> Work package `OPS-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-SRE`, `ROLE-DATA` · Depends on: `ART-01`, `LED-01`, `RUN-04`

## Problem

Automate encrypted backups, point-in-time recovery, object-store versioning/replication, restore into a clean environment, reconciliation, ledger/receipt verification, queue/outbox recovery, and key-availability procedures, with scheduled drills recording measured RPO/RTO.

## Goals

- Automate encrypted backups and PITR.
- Restore into a clean environment and verify receipts.
- Run scheduled DR drills recording measured RPO/RTO.

## Non-goals

- No restore that fails ledger/receipt verification.
- No unmeasured RPO/RTO claim.

## Requirements

- `NR-OPS-003` — Backups, point-in-time recovery, ledger verification, and disaster recovery MUST be exercised.
  - Acceptance: A documented restore drill meets declared RPO/RTO and validates receipts afterward. · Release test(s): `T-OPS-001`

## Acceptance criteria

- [ ] T-OPS-001 backup, restore, replay, and post-restore ledger verification pass.
- [ ] A documented restore drill meets declared RPO/RTO and validates receipts afterward.
