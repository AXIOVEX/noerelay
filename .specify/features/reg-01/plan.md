# Plan: REG-01 — Versioned model/provider/agent/tool registry and quarantine

## Approach

Store immutable revisions with fetched-at/valid-at times and provenance. Quarantine incomplete, stale, contradictory, or unevaluated entries. Activation points to a signed revision and never edits history.

## Components

- `crates/noerelay-store/src/registry.rs (registry repository)`
- `crates/noerelay-core/src/registry.rs (registry domain model)`
- `crates/noerelay-core/src/route_target.rs (route target model)`

## Risks

- An incomplete candidate is routed because a field defaulted instead of quarantining.
- Activation edits history instead of pointing to a new signed revision.
