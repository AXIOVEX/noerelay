# Spec: IAM-02 — API keys

> Work package `IAM-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SEC` · Depends on: `IAM-01`

## Problem

Implement one-time API-key issuance with versioned prefix plus high-entropy secret, keyed-hash storage, constant-time verification, scoping, expiry, revocation, atomic rotation, and per-key rate and concurrency limits.

## Goals

- Issue, verify, rotate, and revoke keys with keyed-hash storage.
- Enforce per-key rate and concurrency limits.
- Record immutable audit events for every key lifecycle action.

## Non-goals

- No secret returned or logged after creation.
- No non-constant-time secret comparison.

## Requirements

- `NR-IAM-002` — API keys MUST be hashed at rest, scoped, revocable, rotatable, rate-limited, and never returned after creation.
  - Acceptance: Rotation is atomic and old-key use immediately fails. · Release test(s): `T-IAM-002`

## Acceptance criteria

- [ ] T-IAM-002 passes creation, hash-at-rest, rotation, revocation, expiry, and concurrent use.
- [ ] Old-key use fails immediately after an atomic rotation.
- [ ] Brute-force attempts are throttled; compromised-key exercise revokes cleanly.
