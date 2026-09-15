# Plan: MEDIA-02 — Explicit image generation/editing routes

## Approach

Generate/edit through governed tool and provider paths with declared parameters. Bind transformation/generation parameters, provider/model revision, hashes, and retention. Apply safety and verification steps before acceptance.

## Components

- `crates/noerelay-core/src/tools.rs (image tool definitions)`
- `crates/noerelay-core/src/tool_execution.rs (governed tool execution)`
- `crates/noerelay-core/src/artifacts.rs (generated media binding)`

## Risks

- A generated image bypasses safety/verification and is accepted.
- Generation parameters are not bound, breaking provenance.
