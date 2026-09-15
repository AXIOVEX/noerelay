# Spec: A2A-01 — Agent registry, outbound dispatcher, trust roots, durable mapping

> Work package `A2A-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `REG-01`, `RUN-01`, `RUN-02`, `RUN-03`, `IAM-03`

## Problem

Retain the narrow Go inbound adapter while placing outbound delegation selection, trust policy, data envelope, contract binding, budgets, lineage, and acceptance in Rust, with an immutable agent registry and durable local/remote task mapping.

## Goals

- Implement the immutable agent registry with trust roots.
- Implement the outbound Rust dispatcher with contract binding and budgets.
- Persist durable local/remote task mapping before sending.

## Non-goals

- No A2A message treated as durable authority.
- No outbound delegation outside trust and budget policy.

## Requirements

- `NR-EXEC-007` — Agent delegation MUST be authenticated, allowlisted, contract-bound, depth/fan-out/cycle limited, budgeted, and independently verified.
  - Acceptance: A2A loop, flood, replay, cancellation, and foreign-tenant tests pass. · Release test(s): `T-A2A-001`

## Acceptance criteria

- [ ] T-A2A-001 passes trust, scope, and durable-mapping tests.
- [ ] Outbound delegation is contract-bound, budgeted, and lineage-tracked.
