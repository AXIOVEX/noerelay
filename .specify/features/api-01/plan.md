# Plan: API-01 — Frozen compatibility profiles and fixture matrix

## Approach

Use the official OpenAI Chat Completions and Responses references as inputs but freeze a supported NoeRelay profile. Generate positive and negative fixtures for each supported field and explicitly reject every unsupported field with stable OpenAI-shaped errors. Run official SDKs in at least Python, TypeScript, and one more language against the suite.

## Components

- `crates/noerelay-core/src/wire.rs (canonical wire request/response IR)`
- `tests/compat/test_fixtures.rs (compatibility fixtures)`

## Risks

- An unsupported field is silently reinterpreted instead of rejected.
- The support matrix is hand-maintained and drifts from the tests.
