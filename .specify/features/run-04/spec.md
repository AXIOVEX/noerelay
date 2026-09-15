# Spec: RUN-04 — Multi-replica conflict recovery and failover

> Work package `RUN-04` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SRE` · Depends on: `RUN-01`, `RUN-02`, `RUN-03`

## Problem

Add optimistic-conflict reload/retry, leader-free work claiming where possible, graceful drain, database failover behavior, and multi-replica stream ownership.

## Goals

- Recover from optimistic conflicts via reload/retry.
- Support graceful drain and database failover.
- Own streams across multiple replicas without split-brain.

## Non-goals

- No split-brain acceptance under contention or failover.
- No lost or duplicated work across replicas.

## Requirements

- `NR-EXEC-001` — Runs and steps MUST be durable, cancelable, resumable, leased, and idempotent.
  - Acceptance: Worker-death and duplicate-delivery tests converge to one terminal result and one side effect. · Release test(s): `T-EXEC-001`
- `NR-OPS-001` — The service MUST expose separate liveness, readiness, metrics, trace, structured-log, and sanitized event interfaces.
  - Acceptance: Dependency failure removes readiness without causing false liveness failure. · Release test(s): `T-OPS-001`

## Acceptance criteria

- [ ] Multi-replica contention, object-store outage, corrupt object, database failover, and rolling-deployment suites pass without split-brain acceptance.
- [ ] Orphaned work is reclaimed exactly once.
