# Spec: MEDIA-01 — Vision and image-processing routes

> Work package `MEDIA-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `REG-01`, `PROV-01`, `ART-01`

## Problem

Treat vision understanding and deterministic image processing as distinct capabilities with separate artifacts, policies, provenance, costs, and verification steps.

## Goals

- Route vision understanding and image processing as distinct capabilities.
- Bind media provenance, cost, and verification per capability.
- Keep binary media out of JSON/database rows.

## Non-goals

- No media capability sharing an artifact or policy with text.
- No binary media stored in JSON/database rows.

## Requirements

Supporting capability package: `MEDIA-01` is not a primary owner of any MUST requirement in `spec/coverage-manifest.json`. It contributes to the routed capabilities and is exercised through the release tests of the packages that own the requirements it supports.

## Acceptance criteria

- [ ] Supported modality fixtures pass size/type/decompression-bomb, unsupported-media, corrupt-artifact, provenance, cost, and release tests.
