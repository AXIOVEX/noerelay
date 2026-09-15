# Spec: OPS-01 — Liveness/readiness/metrics/traces/logs/events and SLO dashboards

> Work package `OPS-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-SRE`, `ROLE-RUST` · Depends on: `RUN-04`, `API-04`

## Problem

Expose separate liveness and dependency-aware readiness, Prometheus-compatible metrics, OpenTelemetry traces, structured redacted logs, sanitized audit/security events, correlation, and SLO/error-budget dashboards.

## Goals

- Expose separate liveness and dependency-aware readiness.
- Emit metrics, traces, redacted logs, and correlated events.
- Provide SLO/error-budget dashboards.

## Non-goals

- No prompt/output captured by default.
- No dependency failure causing a false liveness failure.

## Requirements

- `NR-OPS-001` — The service MUST expose separate liveness, readiness, metrics, trace, structured-log, and sanitized event interfaces.
  - Acceptance: Dependency failure removes readiness without causing false liveness failure. · Release test(s): `T-OPS-001`
- `NR-SEC-001` — TLS, secret management, deny-by-default egress, input/body/concurrency limits, least privilege, and secure headers MUST be enforced in the supported production profile.
  - Acceptance: Production configuration fails closed when any mandatory control is absent. · Release test(s): `T-SEC-001`

## Acceptance criteria

- [ ] T-OPS-001 passes probes and telemetry correlation/redaction.
- [ ] Dependency failure removes readiness without a false liveness failure.
