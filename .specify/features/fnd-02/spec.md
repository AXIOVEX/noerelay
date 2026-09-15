# Spec: FND-02 — One versioned cross-language schema lineage

> Work package `FND-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-ARCH` · Depends on: `FND-01`

## Problem

Establish a single versioned schema lineage that defines all wire and domain objects across Rust, Python, Go, and TypeScript, so no language hand-writes a competing definition.

## Goals

- Generate JSON Schema and OpenAPI from the Rust canonical types.
- Gate schema changes with a breaking-change diff.
- Prove round-trip stability with golden vectors.

## Non-goals

- No language-specific divergent object models.
- No hand-edited generated files.

## Requirements

- `NR-SPEC-004` — Requirement and policy revisions MUST be immutable and runs MUST pin exact revisions.
  - Acceptance: Replaying a run never reads a moving `latest` revision. · Release test(s): `T-SPEC-001`

## Acceptance criteria

- [ ] JSON Schema and OpenAPI regenerate cleanly with an empty diff on a no-op run.
- [ ] Golden vectors round-trip without loss for every supported wire object.
- [ ] A breaking change is detected by the diff gate before merge.
