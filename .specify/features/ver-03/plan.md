# Plan: VER-03 — Human approval and signed external-attestation APIs

## Approach

Bind each attestation to the approver identity, scope, action hash, artifact hash, and expiry. Enforce separation of duties so the implementing identity cannot approve its own high-risk work.

## Components

- `crates/noerelay-core/src/verification.rs (approval state)`
- `crates/noerelay-core/src/receipt.rs (signed attestation binding)`
- `crates/noerelay-gateway/src/admin.rs (approval endpoints)`

## Risks

- An attestation is replayed against a different action or artifact.
- An approver approves their own high-risk implementation.
