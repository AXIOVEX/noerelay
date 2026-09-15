# Plan: SEC-02 — SBOM, licenses, scans, provenance, and signing

## Approach

Separate untrusted pull-request workflows from protected credentials. Publish multi-architecture artifacts. Block known disallowed risk in CI.

## Components

- `xtask/ (build automation and evidence)`
- `.github/ (CI workflows)`
- `deploy/docker/Dockerfile (image build)`
- `deploy/ (IaC and orchestration)`

## Risks

- An unsigned or unprovenanced artifact is deployed.
- A pull-request workflow accesses protected credentials.
