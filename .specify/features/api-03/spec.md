# Spec: API-03 — Complete supported Responses behavior

> Work package `API-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `API-01`, `RUN-01`

## Problem

Implement the complete supported Responses behavior, normalizing into the same internal Rust request IR and projecting terminal results back into the Responses profile.

## Goals

- Normalize Responses into the shared canonical IR.
- Project terminal results back into the Responses profile.
- Keep Chat and Responses behavior consistent through the shared IR.

## Non-goals

- No dependence on one provider's beta semantics in the canonical IR.
- No field outside the frozen profile.

## Requirements

- `NR-API-001` — The service MUST implement `/v1/models`, `/v1/chat/completions`, and `/v1/responses`.
  - Acceptance: Official OpenAI-client-shaped fixtures pass for supported fields without client-specific adapters. · Release test(s): `T-API-001`
- `NR-API-003` — Unsupported fields MUST be rejected or explicitly documented; they MUST NOT be silently reinterpreted.
  - Acceptance: Negative compatibility fixtures produce stable OpenAI-shaped errors. · Release test(s): `T-API-001`

## Acceptance criteria

- [ ] T-API-001 passes Responses golden and negative fixtures.
- [ ] Chat and Responses produce consistent governance through the shared IR.
- [ ] Usage and error shapes match the frozen profile.
