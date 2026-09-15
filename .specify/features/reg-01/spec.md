# Spec: REG-01 — Versioned model/provider/agent/tool registry and quarantine

> Work package `REG-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `FND-02`, `IAM-01`

## Problem

Persist immutable model/provider/agent/tool revisions with provenance, times, explicit OpenRouter IDs, modalities, capabilities, limits, price snapshots, data policies, health, benchmark versions, and allowed roles; quarantine incomplete or stale entries.

## Goals

- Persist immutable registry revisions with full capability metadata.
- Quarantine incomplete, stale, contradictory, or unevaluated entries.
- Activate only signed revisions.

## Non-goals

- No unversioned or incomplete candidate routed.
- No editing of registry history.

## Requirements

- `NR-ROUTE-001` — The registry MUST store explicit OpenRouter model IDs, capabilities, context limits, price snapshots, data policy, regions, health, benchmark versions, and allowed roles.
  - Acceptance: Unversioned or incomplete candidates are quarantined. · Release test(s): `T-ROUTE-001`
- `NR-ROUTE-002` — Routing MUST filter every hard constraint before optimization.
  - Acceptance: Property tests prove an inadmissible candidate never wins regardless of price. · Release test(s): `T-ROUTE-001`
- `NR-ROUTE-003` — Among admissible plans, routing MUST minimize expected total cost, then latency, then maximize calibrated acceptance likelihood.
  - Acceptance: Deterministic fixtures return the same plan and complete rejection reasons. · Release test(s): `T-ROUTE-001`

## Acceptance criteria

- [ ] Unversioned or incomplete candidates are quarantined.
- [ ] Activation points to a signed revision and never edits history.
- [ ] T-ROUTE-001 reads only admissible, complete registry entries.
