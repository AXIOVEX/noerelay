# Project State

Updated 2026-09-15. Local three-model consolidation is operational and verified.

## Current architecture

Rust NoeRelay on 8080 routes GPT-OSS Q5 routine, Qwen3.6 coding, and Qwen3.8 reasoning through LiteLLM, the native RTK/SDD adapter on 8082, and llama.cpp on 8081. One model uses both GPUs on demand; Qwen CPU offload was removed after measurements. Docker MCP and bounded workspace agents connect through NoeRelay. Spec-kit/AEE tracking is internal and preserves unsupported claims.

See [local operations](local-operations.md) for start, stop, restart, endpoints, and tuning. The STOPPED flag suppresses automatic restart. Retired active Ollama/remote-tunnel services were removed; data volumes and historical evidence remain.

## Evidence

Live three-model completions, CORS, MCP discovery, and Docker workspace execution passed. Timing artifacts are in evidence/local-recovery. Full Python baseline: 1,254 passed, 5 skipped; focused changes are retested separately. Rust workspace tests passed; ignored database integration tests are not claimed as executed.

New requirements NR-LLM-007, NR-OPS-005, NR-EXEC-009, NR-API-007 are tracked by G10 and .specify/features/local-consolidation. G10 passes in Python and Rust. The deployed agent completed a two-step Docker execution, the manual stop survived a watchdog check, and start restored all services. Responses, SSE, and stdio MCP also passed live checks. Overall requirement coverage is 15/77; the gap register has 20 open and 14 closed test entries. Local-feature AEE verification passes all four phases for 20 atomic claims. Evidence hashes match, and the 60-entry ledger verifies. The prior blockers were two composite claims, now decomposed; the source-independence note was advisory. Windows and Ubuntu WSL2 both pass authenticated completions at http://127.0.0.1:8080/v1. See api-client-settings.md.

## Remaining release work

Local operation is not production readiness. Run `python scripts/noerelay.py req coverage` and `python scripts/noerelay.py gaps` for actual coverage. Production DEC-01 approvals and broad calibration/load/security evidence remain required. No benchmark acknowledgment is needed to resume the user-authorized local optimization. Earlier phase handoffs are superseded by this state and local-operations.md.

## Zoo compatibility, context, and cleanup

Zoo Code multipart requests with reasoning_effort pass from WSL2. The wire profile is versioned 2026-09-15. All three local models allocate 131072 tokens. A 113764-token coding retrieval request passed (39 seconds with 40704 cached tokens); this is not a cold full-window quality benchmark. Use 24K–32K input / 4096 output normally, or up to 114688 input / 8192 output with overhead reserved.

Host support is in deploy/host; Docker definitions are in deploy/docker. The root Compose include preserves commands. Targeted Python tests: 81 passed. Core/gateway Rust suites passed after compatibility fixtures were updated. G10 and four-phase AEE pass; unrelated production gates remain separate.
