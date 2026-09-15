# Plan: RUN-04 — Multi-replica conflict recovery and failover

## Approach

Use compare-and-swap on work items with optimistic reload/retry. Claim work leader-free where possible. Drain gracefully on shutdown. Define and test database failover behavior and multi-replica stream ownership without split-brain acceptance.

## Components

- `crates/noerelay-store/src/execution.rs (acquire_lease, update_work_item_cas, claim_orphaned_work, acquire_stream, handle_failover, register/heartbeat/drain worker)`

## Risks

- Two replicas accept the same work item during a failover.
- A stale lease holder is not fenced after failover.
