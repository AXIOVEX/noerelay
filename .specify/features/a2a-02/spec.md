# Spec: A2A-02 — A2A depth/fan-out/cycle/replay/cancel/reconnect/budget gates

> Work package `A2A-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PROTO`, `ROLE-SEC` · Depends on: `A2A-01`, `VER-01`

## Problem

Enforce depth, fan-out, total descendants, TTL, lineage cycle detection, per-branch budgets, data-class limits, cancellation, replay protection, and independent verification for agent delegation.

## Goals

- Enforce depth, fan-out, descendant, TTL, and cycle limits.
- Enforce per-branch budgets and data-class limits.
- Protect against replay, and verify independently.

## Non-goals

- No delegation loop, flood, or replay accepted.
- No implementing agent satisfying its own high-risk acceptance.

## Requirements

- `NR-EXEC-007` — Agent delegation MUST be authenticated, allowlisted, contract-bound, depth/fan-out/cycle limited, budgeted, and independently verified.
  - Acceptance: A2A loop, flood, replay, cancellation, and foreign-tenant tests pass. · Release test(s): `T-A2A-001`
- `NR-EXEC-008` — Architecture -> requirements -> implementation -> tests work MAY be delegated, but acceptance MUST remain with an independent verifier and the Rust release gate.
  - Acceptance: The implementing agent cannot satisfy its own high-risk acceptance requirement. · Release test(s): `T-A2A-001`

## Acceptance criteria

- [ ] T-A2A-001 and the governed delegation end-to-end scenario pass.
- [ ] Loop, flood, replay, cancellation, reconnect, and foreign-tenant suites pass.
