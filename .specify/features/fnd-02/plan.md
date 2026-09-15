# Plan: FND-02 — One versioned cross-language schema lineage

## Approach

Own object definitions in Rust; generate JSON Schema and OpenAPI from the Rust types via xtask; gate every change with a breaking-change diff and golden round-trip vectors. Handwritten competing definitions are prohibited.

## Components

- `crates/noerelay-core/src/wire.rs (canonical wire types)`
- `crates/noerelay-core/src/types.rs (domain types)`
- `xtask/src/schema.rs (generate_json, generate_openapi, diff)`
- `xtask/src/golden.rs (golden vector round-trip)`
- `spec/schemas/ (committed generated schemas)`

## Risks

- A hand-edited generated file drifts from the Rust source of truth.
- Breaking changes ship without a recorded diff and invalidate dependent evidence.
