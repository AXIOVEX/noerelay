# Plan: MEM-01 — Durable typed project/user/session epistemic graph

## Approach

Extract candidate claims without accepting them; corroboration and contradiction remain evidence operations. Preserve supported, refuted, both, and neither. Apply deletion and residency policies to graph nodes, embeddings, indexes, and caches.

## Components

- `crates/noerelay-core/src/epistemic.rs (epistemic graph and four-valued state)`
- `crates/noerelay-core/src/context.rs (graph-driven context)`

## Risks

- A contradiction is merged into a single averaged claim.
- A deleted node leaves residue in an embedding index or cache.
