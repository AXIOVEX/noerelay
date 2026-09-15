# Plan: MCP-01 — Isolated MCP host, authorization, sessions, and reconciliation

## Approach

Translate MCP capabilities into tool proposals that still require Rust authorization. Never let advertised capability grant authority. Enforce session isolation and cleanup.

## Components

- `crates/noerelay-core/src/tools.rs (MCP capability translation)`
- `crates/noerelay-core/src/tool_execution.rs (MCP session execution)`

## Risks

- A malicious MCP schema or advertised capability escalates authority.
- A token is forwarded or a session is accessed cross-principal.
