# Plan: API-04 — Governed incremental streaming, resume, and cancellation

## Approach

Parse provider SSE into canonical events (never treated as authority). Low risk may stream verified-safe increments; medium/high/critical output is buffered or provisional until checks pass. A terminal accepted event is impossible before durable verification and receipt commit; rejected output is not leaked through earlier chunks.

## Components

- `crates/noerelay-gateway/src/lib.rs (format_sse, stream handling, release_response)`
- `crates/noerelay-store/src/execution.rs (acquire_stream, renew_stream, release_stream)`

## Risks

- A rejected high-risk output leaks through an earlier chunk.
- A slow client or disconnect leaves an orphaned stream.
