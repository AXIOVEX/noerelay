# Plan: A2A-02 — A2A depth/fan-out/cycle/replay/cancel/reconnect/budget gates

## Approach

Run the official A2A conformance kit plus malicious-card, loop, flood, foreign-tenant, reconnect, lost-message, poisoned-artifact, and verifier-collusion suites. Keep acceptance with an independent verifier and the Rust release gate.

## Components

- `crates/noerelay-core/src/agent_dispatch.rs (depth/fan-out/cycle/budget gates)`
- `services/a2a-adapter (conformance and adversarial harness entry)`

## Risks

- A delegation cycle or flood is not detected and exhausts budget.
- A replayed A2A message re-triggers a side effect.
