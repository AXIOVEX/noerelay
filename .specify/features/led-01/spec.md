# Spec: LED-01 — Concurrent append/replay, artifact binding, signed exports, key rotation

> Work package `LED-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-DATA` · Depends on: `RUN-01`, `ART-01`, `IAM-03`

## Problem

Extend the ledger for concurrent scoped append, canonicalization versioning, artifact hashes, key rotation, public-key history, offline verification, replay, signed exports, and redacted audit views.

## Goals

- Support concurrent scoped append and canonicalization versioning.
- Bind artifacts and produce signed, offline-verifiable receipts.
- Support key rotation, replay, signed exports, and redacted audit views.

## Non-goals

- No chain-of-thought or secrets stored in the ledger.
- No scope or secret leaked through an audit view.

## Requirements

- `NR-API-006` — The outward response MUST remain simple while governance metadata is available through response extensions, headers, and run/receipt endpoints.
  - Acceptance: Standard clients work unchanged; authorized clients can retrieve the complete evidence chain. · Release test(s): `T-API-001`
- `NR-LED-001` — All authority-changing events MUST be canonicalized and hash-linked.
  - Acceptance: Tamper, deletion, reorder, and cross-run splice tests invalidate the chain. · Release test(s): `T-LED-001`
- `NR-LED-002` — Accepted runs MUST produce signed/verifiable receipts binding scope, input, contract, route, artifacts, checks, costs, claims, and ledger head.
  - Acceptance: Offline verification detects any altered bound field. · Release test(s): `T-LED-001`
- `NR-LED-003` — Audit views MUST support organization, project, user, model, agent, tool, policy, and time filters without exposing hidden reasoning or secrets.
  - Acceptance: Authorization and export fixtures prove scoped completeness and redaction. · Release test(s): `T-LED-001`

## Acceptance criteria

- [ ] T-LED-001 detects mutation, deletion, reorder, duplicate, splice, artifact tamper, receipt tamper, key substitution, and scope leakage, including after restore.
