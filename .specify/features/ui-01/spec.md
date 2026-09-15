# Spec: UI-01 — Operator console for onboarding, runs, evidence, cost, approvals, policy

> Work package `UI-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-WEB` · Depends on: `API-05`, `VER-03`, `COST-02`

## Problem

Build a TypeScript operator console for tenant/project onboarding, key metadata and rotation, policies/quotas, registry status, runs/steps/attempts, evidence/receipts, costs, route reasons/regret, approvals, recommendations, audit exports, kill switches, deletion/export requests, and operational status.

## Goals

- Build the operator console over the generated SDK.
- Keep the console non-authoritative and secret-free after creation.
- Pass accessibility, redaction, and usability tests.

## Non-goals

- No authority owned by the console.
- No secret displayed after creation.

## Requirements

- `NR-API-006` — The outward response MUST remain simple while governance metadata is available through response extensions, headers, and run/receipt endpoints.
  - Acceptance: Standard clients work unchanged; authorized clients can retrieve the complete evidence chain. · Release test(s): `T-API-001`
- `NR-LED-003` — Audit views MUST support organization, project, user, model, agent, tool, policy, and time filters without exposing hidden reasoning or secrets.
  - Acceptance: Authorization and export fixtures prove scoped completeness and redaction. · Release test(s): `T-LED-001`
- `NR-COST-002` — Usage and cost MUST aggregate by organization, project, environment, user, API key, run, model, agent, and tool.
  - Acceptance: Roll-up totals equal source attempt records within declared rounding rules. · Release test(s): `T-COST-001`

## Acceptance criteria

- [ ] Role-scoped browser/API end-to-end tests pass.
- [ ] Accessibility, secret-redaction, and pagination/export tests pass.
- [ ] Pilot usability tasks pass.
