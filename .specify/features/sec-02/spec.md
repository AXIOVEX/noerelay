# Spec: SEC-02 — SBOM, licenses, scans, provenance, and signing

> Work package `SEC-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-SEC`, `ROLE-SRE` · Depends on: `FND-03`, `immutable build pipeline`

## Problem

Pin dependencies and base images; scan source, secrets, dependencies, licenses, containers, and IaC; generate SPDX/CycloneDX SBOMs; produce SLSA/in-toto provenance; sign images, binaries, wheels, manifests, and release bundles; and verify signatures at deployment.

## Goals

- Generate SBOMs and provenance for every artifact.
- Sign and verify images, binaries, wheels, and release bundles.
- Scan source, secrets, dependencies, licenses, containers, and IaC.

## Non-goals

- No unsigned artifact deployed.
- No known disallowed risk passing CI.

## Requirements

- `NR-SEC-003` — Dependencies, licenses, source, containers, SBOMs, provenance, and releases MUST be scanned and signed.
  - Acceptance: CI produces attributable artifacts and blocks known disallowed risk. · Release test(s): `T-SEC-001`

## Acceptance criteria

- [ ] T-SEC-001 dependency audit, SBOM, provenance, and signature gates pass.
- [ ] CI produces attributable artifacts and blocks known disallowed risk.
