# Spec: IAM-01 — Canonical tenancy and policy scope

> Work package `IAM-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `FND-02`

## Problem

Implement normalized organizations, projects, environments, principals, memberships, roles, permissions, quotas, and policy bindings, with scope derived from authenticated identity and forced RLS on every tenant-bearing table.

## Goals

- Normalize the tenancy and policy model in PostgreSQL and Rust.
- Derive scope from authenticated identity only.
- Force RLS on every tenant-bearing table.

## Non-goals

- No trust in caller-supplied scope headers.
- No cross-tenant read, inference, mutation, or enumeration.

## Requirements

- `NR-API-004` — Every request MUST carry or derive organization, project, environment, user, session, request, and trace identities.
  - Acceptance: Missing or conflicting scope fails closed; identifiers appear in authorized audit views. · Release test(s): `T-API-003`
- `NR-IAM-001` — Tenant, project, environment, principal, role, API key, quota, and policy scopes MUST be server-enforced.
  - Acceptance: Cross-tenant and cross-project negative matrices cannot read, infer, mutate, or enumerate foreign data. · Release test(s): `T-IAM-001`

## Acceptance criteria

- [ ] T-IAM-001 denies every unauthorized role x route x tenant x project combination.
- [ ] Direct-ID, list, pagination, search, timing, cache-key, stream-resume, export, and error-message enumeration attacks are denied or non-enumerating.
- [ ] RLS holds under distinct database roles and pooled-connection scope reset.
