# Plan: SEC-01 — Threat-model-driven application/API/tenant/sandbox hardening

## Approach

Cover public APIs, OpenRouter, PostgreSQL, object store, queue, OIDC, KMS, tools/sandbox, MCP, A2A, Python workers, console, CI/CD, telemetry, and operators. GA permits no open critical/high finding.

## Components

- `docs/threat-model.md (trust boundaries and data flows)`
- `crates/noerelay-gateway/src/lib.rs (authorized, constant_time_equal, auth boundary)`
- `crates/noerelay-store/src/ (tenant and ledger boundaries)`

## Risks

- A tenant-crossover or SSRF vector is missed by the suite set.
- A finding is closed without retest evidence.
