# Spec: API-04 — Governed incremental streaming, resume, and cancellation

> Work package `API-04` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST` · Depends on: `API-02`, `API-03`, `RUN-03`

## Problem

Implement a durable stream event model with monotonic sequence IDs, bounded buffers, backpressure, heartbeats, resume cursors, disconnect cancellation, and risk-class-aware output gating.

## Goals

- Implement the durable stream event model with monotonic sequence IDs.
- Gate output by risk class without leaking rejected content.
- Support resume cursors and disconnect cancellation.

## Non-goals

- No terminal accepted event before durable verification and receipt commit.
- No provider SSE treated as authority.

## Requirements

- `NR-API-002` — Chat and Responses MUST support streaming and non-streaming operation.
  - Acceptance: SSE framing, terminal events, disconnect cancellation, and error behavior pass contract tests. · Release test(s): `T-API-002`

## Acceptance criteria

- [ ] T-API-002 passes event ordering, slow clients, disconnects, resumption, provider truncation, duplicate chunks, malformed frames, and cancellation.
- [ ] High-risk non-leakage holds: no rejected content in earlier chunks.
