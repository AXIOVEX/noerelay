# Spec: PROV-01 — Production OpenRouter adapter and explicit provider controls

> Work package `PROV-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `REG-01`, `RUN-02`, `API-02`, `API-03`

## Problem

Implement live OpenRouter adapters with explicit selected model/provider policy, restricted base URL, DNS/IP/redirect protections, TLS validation, timeouts, body/stream limits, rate-limit handling, sanitized errors, and usage capture.

## Goals

- Implement the live OpenRouter adapter with explicit provider controls.
- Enforce restricted egress, TLS, timeouts, and body/stream limits.
- Capture usage and sanitize errors.

## Non-goals

- No OpenRouter automatic model selection replacing route authority.
- No implicit paid tests.

## Requirements

- `NR-ROUTE-002` — Routing MUST filter every hard constraint before optimization.
  - Acceptance: Property tests prove an inadmissible candidate never wins regardless of price. · Release test(s): `T-ROUTE-001`
- `NR-ROUTE-005` — OpenRouter automatic model selection MUST NOT replace NoeRelay route authority.
  - Acceptance: Upstream requests always contain the explicit selected model and bounded provider policy. · Release test(s): `T-ROUTE-001`

## Acceptance criteria

- [ ] Upstream requests always contain the explicit selected model and bounded policy.
- [ ] DNS/IP/redirect protections, TLS validation, and timeouts hold.
- [ ] Usage capture and sanitized errors are verified.
