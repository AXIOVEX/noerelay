# Plan: COMP-02 — Data inventory and tested retention/residency/deletion/hold/export

## Approach

Simulate and test lifecycle policies per tenant/project. Document what cannot be deleted immediately and why. Complete privacy/legal review and vendor inventory.

## Components

- `crates/noerelay-store/src/lifecycle.rs (retention, hold, deletion, export)`
- `crates/noerelay-store/src/artifacts.rs (artifact retention)`

## Risks

- A residency or deletion policy is not enforced for a derived store.
- A vendor/subprocessor is missing from the inventory.
