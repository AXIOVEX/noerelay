# Spec: API-02 — Complete supported Chat Completions behavior

> Work package `API-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `API-01`, `RUN-01`

## Problem

Implement the complete supported Chat Completions behavior, normalizing the public API into the internal Rust request IR and projecting terminal results back into the requested profile.

## Goals

- Normalize Chat Completions into the canonical IR.
- Project terminal results back into the Chat profile.
- Preserve tool-call, usage, and error behavior in profile.

## Non-goals

- No field outside the frozen profile.
- No authority decision made outside Rust.

## Requirements

- `NR-API-001` — The service MUST implement `/v1/models`, `/v1/chat/completions`, and `/v1/responses`.
  - Acceptance: Official OpenAI-client-shaped fixtures pass for supported fields without client-specific adapters. · Release test(s): `T-API-001`
- `NR-API-003` — Unsupported fields MUST be rejected or explicitly documented; they MUST NOT be silently reinterpreted.
  - Acceptance: Negative compatibility fixtures produce stable OpenAI-shaped errors. · Release test(s): `T-API-001`

## Acceptance criteria

- [ ] T-API-001 passes Chat golden and negative fixtures.
- [ ] Legacy tool envelopes are promoted only for allowed tools.
- [ ] Usage and error shapes match the frozen profile.
