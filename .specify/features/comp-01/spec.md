# Spec: COMP-01 — Versioned compliance framework mappings

> Work package `COMP-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-COMP` · Depends on: `FND-03`, `LED-01`

## Problem

Create versioned, profile-specific control mappings listing framework/control version, applicability, implementation, observed evidence, gaps, owner, reviewer, and next review date, as evidence aids rather than legal-certification claims.

## Goals

- Create versioned, profile-specific control mappings.
- Tie each control to observed evidence, gaps, owner, and review date.
- Keep mappings as evidence aids, not certification claims.

## Non-goals

- No certified or compliant claim from an automated check alone.
- No framework mapping included without authorized reviewer selection.

## Requirements

- `NR-COMP-001` — Compliance mappings MUST be versioned evidence aids, not legal-certification claims.
  - Acceptance: Reports identify framework version, applicable controls, evidence, gaps, owner, and review date. · Release test(s): `T-COMP-001`

## Acceptance criteria

- [ ] T-COMP-001 versioned framework mapping and gap disclosure fixtures pass.
- [ ] Reports identify framework version, controls, evidence, gaps, owner, and review date.
