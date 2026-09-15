# Plan: API-02 — Complete supported Chat Completions behavior

## Approach

Normalize Chat Completions into the canonical IR, apply governance, route, execute, verify, and project the result back. Preserve tool-call normalization, streaming, usage, and error behavior within the frozen profile.

## Components

- `crates/noerelay-gateway/src/lib.rs (chat_completions, proxy_openai_request, normalize_legacy_tool_calls)`
- `crates/noerelay-core/src/wire.rs (canonical IR)`

## Risks

- A legacy tool-call envelope is promoted to a native call without an allowed tool.
- A rejected output leaks through an earlier stream chunk.
