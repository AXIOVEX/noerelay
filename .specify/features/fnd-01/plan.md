# Plan: FND-01 — Freeze profile, scope, baseline, and risks

## Approach

Record the DEC-01 local/test-only decision, the named profile ID, non-goals, and risk register in docs/fnd-01-scope-baseline.md; freeze the requirement set and the machine-readable coverage manifest; validate traceability (no orphans, unique IDs, no placeholders) before any implementation wave starts.

## Components

- `docs/fnd-01-scope-baseline.md (DEC-01 record, profile, risk register, traceability validation)`
- `spec/coverage-manifest.json (machine-readable req -> package -> test + gates)`
- `xtask/src/main.rs (evidence record/validate/coverage/gate entry points)`

## Risks

- Scope creep after freeze invalidates earlier evidence; must be gated as a new revision.
- Placeholder or orphaned requirement IDs silently weaken the release gate.
