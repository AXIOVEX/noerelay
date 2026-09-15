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


## Managed client integration verification (2026-09-15)

The primary `noerelay client setup|status|run|test` CLI now manages OpenCode, Zoo Code, and Codex profiles. Windows profiles and WSL native OpenCode are installed/configured. Live tool round trips passed for OpenCode 1.14.28, Zoo Code 3.82.1, and Codex 0.153.4. Native WSL OpenCode also passed. Both environments authenticate to the running gateway without manually copying a key.

The final focused Python suite passed 25 tests; Rust core/gateway suites passed. G11 passes. All four client-feature AEE phases pass for ten atomic claims with zero failure modes; the 154-entry ledger verifies. The gap register retains 20 open and 16 closed entries. These are local feature observations, not a claim that unrelated release gates are complete. Evidence: `evidence/local-recovery/client-integrations.json`, `client-aee.json`, and `client-ledger-verification.json`.

Responses profile is now `2026-09-15.1`, including stateless Codex metadata, developer messages, function tool history, and namespace translation. Codex's live test used an exact-command read-only MCP guard. Native Windows shell execution was blocked by client policy; interactive MCP approvals remain enabled. Zoo's real extension-host test ran on Windows. The Rust router remains authoritative, with whole-word classification fixing the improve/prove false escalation. See ADR 0003 and the README for usage and limits.


## AXIOVEX ownership migration (2026-09-15)

The canonical repository is now `https://github.com/AXIOVEX/noerelay`, owned by Axiovex Systems, LLC. Public visibility and repository history were preserved. Current legal notices, package metadata, URLs, telemetry vendor labels, schema namespaces, and UI company copy use the new identity. The approved banner is pinned alongside the existing approved logos; live served bytes match upstream checksums. Historical evidence and AEE records retain their original paths and hashes.

G12 tracks NR-OPS-008 / T-OPS-008. See `docs/branding.md` and `evidence/branding/` for migration checks. Publication checks also corrected Rust formatting and Linux CI issues in the optional console fallback, platform-specific test fixtures, stale model assertion, and Conformance test dependencies.

Final migration validation: Windows 1270 passed / 5 skipped; clean Linux container 1201 passed / 74 skipped plus 920 subtests. Rust formatting and strict core/gateway clippy, Go tests, package build, live gateway/MCP and served branding checks pass. G12 and all four AEE phases pass for 12 atomic claims; the 164-entry ledger verifies. WSL full-suite attempts were interrupted; no WSL full-suite pass is claimed.
