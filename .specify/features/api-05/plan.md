# Plan: API-05 — Stable admin/run/evidence/cost interfaces and generated SDK

## Approach

Expose stable, versioned administration interfaces. Keep the outward response simple while governance metadata is available through extensions, headers, and run/receipt endpoints. Generate the TypeScript client from OpenAPI; the console never owns authority and never receives secrets after creation.

## Components

- `crates/noerelay-gateway/src/admin.rs (administration endpoints)`
- `crates/noerelay-gateway/src/lib.rs (cost_report, receipt, governance_release_gate)`

## Risks

- An admin endpoint leaks a foreign tenant's run or receipt.
- The SDK is hand-written and drifts from the OpenAPI contract.
