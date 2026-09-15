# Spec: ART-01 — S3-compatible content-addressed artifact plane

> Work package `ART-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-DATA` · Depends on: `FND-02`, `IAM-01`

## Problem

Store large inputs, outputs, media, and test logs in a content-addressed object store with scope metadata, encryption, retention, integrity hashes, and receipt binding, while the database remains the authority for artifact identity and authorization.

## Goals

- Store large payloads in a content-addressed object store.
- Bind scope, integrity, retention, and receipt in the database.
- Keep the database authoritative for identity and authorization.

## Non-goals

- No binary media stored in JSON/database rows.
- No artifact accepted without an integrity hash and scope binding.

## Requirements

- `NR-LED-002` — Accepted runs MUST produce signed/verifiable receipts binding scope, input, contract, route, artifacts, checks, costs, claims, and ledger head.
  - Acceptance: Offline verification detects any altered bound field. · Release test(s): `T-LED-001`

## Acceptance criteria

- [ ] Corrupt-object and object-store-outage suites fail closed.
- [ ] Every accepted artifact verifies its integrity hash and scope binding.
- [ ] Artifacts are bound to receipts and respect retention.
