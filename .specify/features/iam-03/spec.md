# Spec: IAM-03 — OIDC, service identities, and RBAC

> Work package `IAM-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SEC` · Depends on: `IAM-01`

## Problem

Define a versioned Rust identity-provider port that validates OIDC tokens and maps claims to the canonical scope model, with deny-by-default RBAC on every administrative route.

## Goals

- Define the versioned identity-provider port and OIDC validation.
- Map claims to the canonical principal and scope model.
- Enforce deny-by-default RBAC on every administrative route.

## Non-goals

- No unmapped administrative route reachable by a non-admin caller.
- No token confusion or replay across audiences.

## Requirements

- `NR-IAM-001` — Tenant, project, environment, principal, role, API key, quota, and policy scopes MUST be server-enforced.
  - Acceptance: Cross-tenant and cross-project negative matrices cannot read, infer, mutate, or enumerate foreign data. · Release test(s): `T-IAM-001`
- `NR-IAM-003` — Administrative routes MUST use deny-by-default RBAC and immutable audit events.
  - Acceptance: Every route maps to an explicit permission; unmapped routes deny non-admin callers. · Release test(s): `T-IAM-001`
- `NR-IAM-004` — External identity federation MUST be implementable behind a versioned identity port.
  - Acceptance: OIDC claims map to the same canonical principal and scope model without changing domain policy. · Release test(s): `T-IAM-001`

## Acceptance criteria

- [ ] OIDC/provider contract tests and token confusion/replay fixtures pass.
- [ ] Complete route-permission coverage: every admin route maps to a permission.
- [ ] Independent security review passes.
