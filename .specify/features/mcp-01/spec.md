# Spec: MCP-01 — Isolated MCP host, authorization, sessions, and reconciliation

> Work package `MCP-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PROTO` · Depends on: `TOOL-01`, `TOOL-02`, `RUN-03`

## Problem

Implement one isolated stateful MCP client connection per server/principal scope with capability negotiation, server allowlisting, audience-bound authorization, token non-forwarding, schema pinning, bounded reads, cancellation, and reconciliation.

## Goals

- Isolate MCP sessions per server and principal.
- Authorize MCP capability use through Rust.
- Reconcile sessions and prevent token forwarding.

## Non-goals

- No advertised MCP capability granting authority.
- No token forwarding across sessions.

## Requirements

- `NR-EXEC-003` — Tool schemas, revisions, grants, credentials, egress, inputs, outputs, and side effects MUST be explicit.
  - Acceptance: A model-proposed tool call executes only after deterministic authorization. · Release test(s): `T-EXEC-002`
- `NR-EXEC-006` — MCP sessions MUST be isolated per server and principal; advertised capability MUST NOT grant authority.
  - Acceptance: Token forwarding and cross-session capability attacks fail. · Release test(s): `T-EXEC-002`
- `NR-EXEC-009` — Expose Docker MCP and bounded workspace agents through authenticated NoeRelay endpoints.
  - Acceptance: Tool discovery, real Docker execution, agent budgets, and operator authentication are verified. · Release test(s): `T-EXEC-009`

## Acceptance criteria

- [ ] T-EXEC-002 passes token confusion, advertised-capability escalation, cross-session access, malicious schemas/content, reconnect, and cancellation fixtures.
