# Plan: IAM-01 — Canonical tenancy and policy scope

## Approach

Scope is derived from authenticated identity and server-side bindings, never trusted from caller headers. Apply and force RLS to every tenant-bearing table including caches, streams, outbox rows, artifacts, reports, and recommendation data. Build the full role x route x tenant x project allow/deny matrix.

## Components

- `crates/noerelay-store/src/iam.rs (tenancy repository)`
- `crates/noerelay-core/src/iam.rs (tenancy domain model)`
- `crates/noerelay-gateway/src/iam.rs (scope derivation at the boundary)`

## Risks

- A pooled connection that does not reset scope leaks a prior tenant's RLS context.
- A cache or stream key that omits scope enables cross-tenant disclosure.
