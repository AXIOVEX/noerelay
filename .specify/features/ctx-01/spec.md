# Spec: CTX-01 — Retrieval, provenance summaries, compaction, and tokenizer accounting

> Work package `CTX-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-RUST`, `ROLE-PY-EVAL` · Depends on: `MEM-01`, `REG-01`

## Problem

Compile context from durable graph state and the active contract using model-specific tokenizer accounting, requirement-driven retrieval, provenance-carrying summaries, protected nodes, and an auditable inclusion/omission manifest.

## Goals

- Compile bounded context from durable graph state.
- Preserve protected nodes under compaction.
- Produce provenance-carrying summaries with an inclusion/omission manifest.

## Non-goals

- No summary overwriting source evidence.
- No accepted answer fabricated under insufficient evidence.

## Requirements

- `NR-CTX-001` — Context MUST be compiled from durable project/user/session state rather than forwarded as an unbounded transcript.
  - Acceptance: Token use stays within the selected model limit with an auditable inclusion manifest. · Release test(s): `T-CTX-001`
- `NR-CTX-002` — Deduplication, pruning, summarization, and retrieval MUST preserve protected nodes.
  - Acceptance: Property tests preserve requirements, decisions, contradictions, approvals, evidence handles, and active tool state. · Release test(s): `T-CTX-001`
- `NR-CTX-003` — Summaries MUST carry provenance and an uncertainty class.
  - Acceptance: Summaries cannot overwrite source evidence and can be expanded back to source handles. · Release test(s): `T-CTX-001`
- `NR-CTX-006` — When evidence is insufficient, the system MUST clarify, gather information, abstain, or escalate.
  - Acceptance: No-route and low-confidence fixtures never fabricate an accepted answer. · Release test(s): `T-CTX-001`

## Acceptance criteria

- [ ] T-CTX-001 property/differential tests prove token bounds, protected-node recovery, contradiction preservation, provenance expansion, deletion, and abstention.
