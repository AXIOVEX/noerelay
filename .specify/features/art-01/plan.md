# Plan: ART-01 — S3-compatible content-addressed artifact plane

## Approach

Address artifacts by content hash. Bind scope, content type, size, retention, and integrity hash in the database. Keep binary media out of JSON/database rows. Apply malware/content checks where applicable and bind artifacts to receipts.

## Components

- `crates/noerelay-store/src/artifacts.rs (artifact repository)`
- `crates/noerelay-core/src/artifacts.rs (artifact domain model)`

## Risks

- A corrupt or swapped object is accepted without integrity verification.
- An artifact is readable across scope because the binding is missing.
