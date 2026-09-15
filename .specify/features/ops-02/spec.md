# Spec: OPS-02 — Scoped kill switches and safe rollback

> Work package `OPS-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SRE` · Depends on: `IAM-03`, `REG-01`, `RUN-02`

## Problem

Implement audited kill switches globally and by tenant, project, provider, model, agent, tool, policy, and capability, stopping new and cached work and propagating to workers, with rollback by activating a previous signed revision.

## Goals

- Implement audited kill switches at every scope.
- Stop new and cached work and propagate to workers.
- Roll back by activating a previous signed revision.

## Non-goals

- No rollback by editing history.
- No kill switch without audit evidence.

## Requirements

- `NR-OPS-002` — Administrative kill switches MUST exist globally and by tenant, project, provider, model, agent, and tool.
  - Acceptance: Kill-switch tests stop new/cached work and produce audit evidence. · Release test(s): `T-OPS-001`

## Acceptance criteria

- [ ] T-OPS-001 kill-switch tests stop new/cached work and produce audit evidence.
- [ ] Rollback activates a previous signed revision without editing history.
