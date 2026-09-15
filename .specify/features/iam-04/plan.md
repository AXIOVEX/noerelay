# Plan: IAM-04 — Tenant lifecycle, retention, deletion, legal hold, export

## Approach

Inventory every authoritative row, prompt, output, artifact, cache, trace, log, backup, receipt, recommendation feature, export, and provider copy. Apply versioned retention/residency policies; document what cannot be deleted immediately from immutable audit proofs or backups and why.

## Components

- `crates/noerelay-store/src/lifecycle.rs (retention, hold, deletion, export)`
- `crates/noerelay-store/src/artifacts.rs (artifact retention and deletion)`

## Risks

- A derived view (cache, index, recommendation feature) is missed by deletion.
- Legal hold is not enforced on a deletion job path.
