# Spec: TOOL-02 — Bounded code/tool sandbox and egress broker

> Work package `TOOL-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-SEC` · Depends on: `TOOL-01`, `ART-01`

## Problem

Enforce a bounded sandbox for tool and code execution with CPU, memory, process, wall-clock, filesystem, network, DNS, output, artifact, and secret limits, and a default-deny egress broker.

## Goals

- Enforce resource, filesystem, network, DNS, output, and secret limits.
- Broker credentials with default-deny egress.
- Isolate tenants and runs and collect execution evidence.

## Non-goals

- No secret placed in prompts or environment dumps.
- No egress outside the allowlist.

## Requirements

- `NR-EXEC-005` — Tool and code execution MUST occur in a bounded sandbox with resource, filesystem, network, and output limits.
  - Acceptance: Escape, SSRF, fork bomb, secret access, and output-flood suites fail closed. · Release test(s): `T-EXEC-002`
- `NR-SEC-001` — TLS, secret management, deny-by-default egress, input/body/concurrency limits, least privilege, and secure headers MUST be enforced in the supported production profile.
  - Acceptance: Production configuration fails closed when any mandatory control is absent. · Release test(s): `T-SEC-001`

## Acceptance criteria

- [ ] Escape, SSRF, DNS rebinding, metadata-service, fork/process bomb, disk/memory exhaustion, output flood, symlink/path traversal, secret access, and cross-run contamination suites fail closed.
