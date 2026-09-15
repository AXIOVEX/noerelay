# Plan: REL-01 — Quantitative load/soak/fault/chaos/SLO evidence

## Approach

Run the load/soak/fault/chaos suites in a protected environment. Publish measured methodology, environment, raw results, summaries, regressions, and artifact hashes. Targets are not evidence; measured results are.

## Components

- `xtask/ (evidence recording for release metrics)`
- `benchmarks/ (load and soak harnesses)`

## Risks

- A target is reported as met without a measured result.
- A network-dependent suite runs without a spend ceiling.
