# Plan: OPS-01 — Liveness/readiness/metrics/traces/logs/events and SLO dashboards

## Approach

Keep liveness separate from dependency-aware readiness so a dependency failure removes readiness without a false liveness failure. Disable prompt/output capture by default; capture only through explicit redacted tenant policy.

## Components

- `crates/noerelay-gateway/src/lib.rs (ready, health handlers)`
- `crates/noerelay-gateway/src/main.rs (server bootstrap and probes)`

## Risks

- A dependency failure is reported as a liveness failure, triggering a needless restart.
- Prompt/output content is captured without an explicit redacted policy.
