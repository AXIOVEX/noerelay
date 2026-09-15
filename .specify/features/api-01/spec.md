# Spec: API-01 — Frozen compatibility profiles and fixture matrix

> Work package `API-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PROTO` · Depends on: `FND-02`, `IAM-01`

## Problem

Freeze the supported OpenAI compatibility profile (text, structured output, tools, multimodal, usage, metadata, error, cancellation) and generate a positive/negative fixture matrix for every supported field.

## Goals

- Freeze the supported compatibility profile.
- Generate positive and negative fixtures per supported field.
- Reject unsupported fields with stable OpenAI-shaped errors.

## Non-goals

- No claim of every current and future OpenAI field.
- No unknown field passed through with altered meaning.

## Requirements

- `NR-API-001` — The service MUST implement `/v1/models`, `/v1/chat/completions`, and `/v1/responses`.
  - Acceptance: Official OpenAI-client-shaped fixtures pass for supported fields without client-specific adapters. · Release test(s): `T-API-001`
- `NR-API-003` — Unsupported fields MUST be rejected or explicitly documented; they MUST NOT be silently reinterpreted.
  - Acceptance: Negative compatibility fixtures produce stable OpenAI-shaped errors. · Release test(s): `T-API-001`

## Acceptance criteria

- [ ] T-API-001 passes all golden and negative fixtures.
- [ ] The support matrix is generated from tests and published.
- [ ] Official SDKs in at least three languages pass the suite.
