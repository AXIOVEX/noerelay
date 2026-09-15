# Spec: SEC-01 — Threat-model-driven application/API/tenant/sandbox hardening

> Work package `SEC-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-SEC` · Depends on: `IAM-01..04`, `RUN-01..04`, `TOOL-01..02`, `MCP-01`, `A2A-01..02`

## Problem

Maintain a data-flow and trust-boundary threat model and run adversarial auth/authz, parser, injection, SSRF, egress, tenant crossover, quota, ledger, artifact, sandbox, agent, stream, and secret-redaction suites, tracking every finding to closure.

## Goals

- Maintain the data-flow and trust-boundary threat model.
- Run the full adversarial suite set.
- Track every finding with severity, owner, remediation, and acceptance.

## Non-goals

- No open critical/high finding at release.
- No finding closed without retest.

## Requirements

- `NR-IAM-001` — Tenant, project, environment, principal, role, API key, quota, and policy scopes MUST be server-enforced.
  - Acceptance: Cross-tenant and cross-project negative matrices cannot read, infer, mutate, or enumerate foreign data. · Release test(s): `T-IAM-001`
- `NR-SEC-001` — TLS, secret management, deny-by-default egress, input/body/concurrency limits, least privilege, and secure headers MUST be enforced in the supported production profile.
  - Acceptance: Production configuration fails closed when any mandatory control is absent. · Release test(s): `T-SEC-001`
- `NR-SEC-002` — Authentication, authorization, SSRF, injection, tenant crossover, ledger tampering, quota abuse, and secret redaction MUST have adversarial suites.
  - Acceptance: No critical/high finding remains open at release. · Release test(s): `T-SEC-001`

## Acceptance criteria

- [ ] T-SEC-001 auth bypass, parser abuse, injection, SSRF, tenant crossover, and quota abuse suites pass.
- [ ] No critical/high finding remains open at release.
