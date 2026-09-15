# Plan: EVAL-01 — Versioned cohort/benchmark/harness registry and signed results

## Approach

Use hidden/mutation/adversarial suites to resist gaming. A model name without its tested harness is not a transferable result. Promotion is controlled by Rust.

## Components

- `crates/noerelay-core/src/evaluator_ingestion.rs (SpecKitHook outcome ingestion)`
- `crates/noerelay-core/src/evaluator_result.rs (signed results)`
- `crates/noerelay-core/src/analytics.rs (cohort statistics)`
- `bindings/python (evaluation plane)`

## Risks

- A result is attributed to a model without its harness, overclaiming transferability.
- An evaluation is gamed because only visible suites are used.
