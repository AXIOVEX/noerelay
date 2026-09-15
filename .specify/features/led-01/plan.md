# Plan: LED-01 — Concurrent append/replay, artifact binding, signed exports, key rotation

## Approach

Canonicalize and hash-link every authority-changing event. Store signing keys in the approved KMS/HSM. Make scope/filter completeness testable without storing chain-of-thought or secrets. Bind accepted runs to signed receipts.

## Components

- `crates/noerelay-core/src/ledger.rs (hash-chained ledger)`
- `crates/noerelay-core/src/receipt.rs (signed receipts)`
- `crates/noerelay-store/src/lib.rs (insert_ledger_event, receipt, cost_rollups)`

## Risks

- A mutation, reorder, splice, or key substitution is not detected.
- An audit view leaks a foreign scope or a secret.
