# Plan: REL-04 — Immutable GA bundle, approvals, deployment, and rollback

## Approach

Assemble the complete evidence bundle with exact source and artifact digests. Record the signed release record. Prepare and test the rollback package. Identify remaining external/customer responsibilities and non-goals.

## Components

- `xtask/ (evidence bundle validation)`
- `evidence/ (GA evidence bundle)`
- `deploy/ (deployment and rollback manifests)`

## Risks

- A stale or reused evidence artifact is included in the GA bundle.
- The rollback package is not tested before GA.
