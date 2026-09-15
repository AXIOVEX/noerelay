# Plan: IAM-03 — OIDC, service identities, and RBAC

## Approach

Validate issuer, audience, signature, time claims, and nonce where applicable, with an explicit claim-to-scope mapping. Keep workload identities separate from humans. Map every administrative route and mutation to an explicit permission; unmapped routes deny. Bind step-up approvals to approver identity, scope, action hash, expiry, and separation of duties.

## Components

- `crates/noerelay-core/src/iam.rs (identity port, claim mapping)`
- `crates/noerelay-gateway/src/iam.rs (route-permission enforcement)`
- `crates/noerelay-gateway/src/admin.rs (administrative routes)`

## Risks

- A missing route-permission mapping defaults to allow instead of deny.
- Token replay or audience confusion grants cross-tenant admin.
