# Plan: OPS-03 — Backup, PITR, restore, artifact reconciliation, DR exercises

## Approach

Restore into a clean environment and verify idempotent replay and receipts inside RPO/RTO. Run scheduled drills and record measured RPO/RTO.

## Components

- `crates/noerelay-store/src/lib.rs (ledger and receipt verification)`
- `deploy/ (container and orchestration manifests)`
- `docs/runbooks.md (backup/restore and incident procedures)`

## Risks

- A restore succeeds but ledger/receipt verification fails, masking corruption.
- RPO/RTO is claimed but never measured by a drill.
