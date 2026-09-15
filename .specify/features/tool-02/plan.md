# Plan: TOOL-02 — Bounded code/tool sandbox and egress broker

## Approach

Mount only declared inputs; default-deny egress; broker credentials without placing them in prompts or environment dumps; isolate tenants and runs; collect deterministic execution evidence.

## Components

- `crates/noerelay-core/src/tool_execution.rs (sandboxed execution and egress broker)`
- `crates/noerelay-core/src/budget.rs (resource limits)`

## Risks

- A sandbox escape, SSRF, or DNS rebinding reaches the host or metadata service.
- A fork/process bomb or output flood exhausts resources.
