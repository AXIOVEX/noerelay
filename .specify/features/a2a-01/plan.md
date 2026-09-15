# Plan: A2A-01 — Agent registry, outbound dispatcher, trust roots, durable mapping

## Approach

Pin/signed Agent Card metadata where available and configured trust roots where signing is absent. Persist the local/remote task mapping before sending. Do not treat A2A messages as durable authority.

## Components

- `crates/noerelay-core/src/agent_dispatch.rs (outbound dispatcher, trust, mapping)`
- `crates/noerelay-core/src/registry.rs (agent registry)`
- `services/a2a-adapter (narrow Go inbound adapter)`

## Risks

- A foreign-tenant or malicious agent card is trusted.
- A task is sent before the durable mapping is persisted, losing lineage.
