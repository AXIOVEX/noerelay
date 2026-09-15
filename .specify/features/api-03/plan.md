# Plan: API-03 — Complete supported Responses behavior

## Approach

Share the canonical IR with Chat Completions so the two profiles do not diverge. Project terminal results into the Responses shape, preserving usage, errors, and tool behavior within the frozen profile.

## Components

- `crates/noerelay-gateway/src/lib.rs (responses, proxy_openai_request)`
- `crates/noerelay-core/src/wire.rs (shared canonical IR)`

## Risks

- The Responses profile diverges from Chat through a separate code path.
- A provider beta semantic leaks into the canonical IR.
