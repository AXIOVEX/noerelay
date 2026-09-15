# Spec: MEDIA-02 — Explicit image generation/editing routes

> Work package `MEDIA-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `MEDIA-01`, `TOOL-01`

## Problem

Treat image generation and editing as explicit capabilities with separate artifacts, policies, provenance, costs, and safety/verification steps.

## Goals

- Route image generation and editing as explicit governed capabilities.
- Bind generation parameters, provenance, and cost.
- Apply safety and verification before acceptance.

## Non-goals

- No implicit image generation outside a governed tool path.
- No unverified generated media accepted.

## Requirements

Supporting capability package: `MEDIA-02` is not a primary owner of any MUST requirement in `spec/coverage-manifest.json`. It contributes to the routed capabilities and is exercised through the release tests of the packages that own the requirements it supports.

## Acceptance criteria

- [ ] Image generation/editing fixtures pass provenance, cost, safety, and release tests.
- [ ] Generated media is bound with parameters, revision, and hashes.
