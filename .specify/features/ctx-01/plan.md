# Plan: CTX-01 — Retrieval, provenance summaries, compaction, and tokenizer accounting

## Approach

Drive retrieval by active requirements and unresolved claims. Preserve protected nodes verbatim or addressable. Summaries carry provenance and uncertainty and never overwrite sources. Fail closed (clarify/abstain) under insufficient evidence.

## Components

- `crates/noerelay-core/src/context.rs (retrieval, compaction, tokenizer accounting)`
- `crates/noerelay-core/src/epistemic.rs (protected nodes)`
- `crates/noerelay-gateway/src/lib.rs (compile_wire_context)`

## Risks

- Compaction drops a protected requirement, decision, or evidence handle.
- Token accounting overruns the selected model limit.
