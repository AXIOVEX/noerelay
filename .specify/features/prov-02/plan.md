# Plan: PROV-02 — Bounded transport/capability/semantic/epistemic/specification fallbacks

## Approach

Keep each fallback class distinct with its own attempt count, cost reservation, latency budget, evidence requirements, and terminal code. No fallback may weaken data policy, verifier independence, or acceptance criteria.

## Components

- `crates/noerelay-core/src/routing.rs (fallback policy)`
- `crates/noerelay-core/src/route_target.rs (route target and fallback targets)`
- `crates/noerelay-core/src/verification.rs (epistemic escalation)`

## Risks

- A semantic failure is retried as a transport failure, hiding the real cause.
- A fallback loop exceeds budget because the class is not bounded.
