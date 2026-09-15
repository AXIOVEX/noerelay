# Plan: IAM-02 — API keys

## Approach

Store keys with Argon2id (or an approved keyed hash). Verify in constant time. Never log or return the secret after creation. Enforce per-key rate and concurrency limits and record immutable audit events for the key lifecycle.

## Components

- `crates/noerelay-store/src/api_keys.rs (issue/verify/revoke/rotate, rate + concurrency)`

## Risks

- A timing side-channel in verification leaks secret material.
- A non-atomic rotation window lets a revoked key keep working.
