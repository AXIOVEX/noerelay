# Spec: API-05 — Stable admin/run/evidence/cost interfaces and generated SDK

> Work package `API-05` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-WEB` · Depends on: `FND-02`, `IAM-03`

## Problem

Create versioned Rust administration APIs for runs, evidence, receipts, costs, and governance, and generate the client SDK from OpenAPI.

## Goals

- Expose stable versioned admin/run/evidence/cost APIs.
- Keep governance metadata retrievable without changing the simple response.
- Generate the client SDK from OpenAPI.

## Non-goals

- No authority owned by the console or SDK.
- No secret returned after creation.

## Requirements

- `NR-API-006` — The outward response MUST remain simple while governance metadata is available through response extensions, headers, and run/receipt endpoints.
  - Acceptance: Standard clients work unchanged; authorized clients can retrieve the complete evidence chain. · Release test(s): `T-API-001`
- `NR-LED-003` — Audit views MUST support organization, project, user, model, agent, tool, policy, and time filters without exposing hidden reasoning or secrets.
  - Acceptance: Authorization and export fixtures prove scoped completeness and redaction. · Release test(s): `T-LED-001`
- `NR-COST-002` — Usage and cost MUST aggregate by organization, project, environment, user, API key, run, model, agent, and tool.
  - Acceptance: Roll-up totals equal source attempt records within declared rounding rules. · Release test(s): `T-COST-001`

## Acceptance criteria

- [ ] Role-scoped API tests pass for runs, evidence, receipts, and costs.
- [ ] The generated SDK matches the OpenAPI contract.
- [ ] Secret redaction and pagination/export tests pass.
