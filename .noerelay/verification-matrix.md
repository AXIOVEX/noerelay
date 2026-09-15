# NoeRelay v1 verification matrix

**Status:** Required release evidence catalog  
**Rule:** a test identifier is not evidence until a runner records its command, revision, environment, result, and artifact hash.

Current implementation evidence and unresolved release blockers are tracked in [implementation-status.md](../docs/implementation-status.md). This matrix is the target gate catalog, not a claim that every row currently passes.

## Automated suites

| Test ID | Requirement coverage | Layer | Gate |
|---|---|---|---|
| `T-API-005` | `NR-API-008` | Compatibility | Zoo-style multipart requests with validated reasoning effort complete from WSL2. |
| `T-LLM-008` | `NR-LLM-008` | Local inference | Three models allocate 131072 context; beyond-16K retrieval succeeds. |
| `T-OPS-008` | `NR-OPS-008` | Integration | AXIOVEX ownership, approved brand assets, affected tests, and live WebUI identity verify. |
| `T-OPS-007` | `NR-OPS-007` | Integration | Installed OpenCode, Zoo Code and Codex read fresh fixture data through NoeRelay; managed profiles preserve user settings. |
| `T-ROUTE-003` | `NR-ROUTE-009` | Regression | Rust routing and Responses namespace/tool history regressions pass. |
| `T-OPS-006` | `NR-OPS-006` | Deployment | Host and Docker assets are separated; imports, Compose and lifecycle remain functional. |
| `T-API-004` | `NR-API-007` | Local integration | Windows and WSL2 complete authenticated requests at the documented API endpoint; missing keys are rejected. |
| `T-LLM-007` | `NR-LLM-007` | Local integration | All three routes complete; shared-GPU cold/warm timing artifacts recorded. |
| `T-OPS-005` | `NR-OPS-005` | Integration | Internal spec-kit/AEE preserves edits, records unsupported claims, and fails closed if missing. |
| `T-EXEC-009` | `NR-EXEC-009` | Local integration | Authenticated Docker MCP discovery/execution and bounded agent tool calls pass. |
| `T-API-001` | `NR-API-001..003`, `NR-API-006` | Contract | OpenAI-compatible chat, Responses, models, errors, and unknown-field fixtures pass. |
| `T-API-002` | `NR-API-002`, `NR-EXEC-001` | Integration | SSE ordering, terminal event, resume policy, disconnect cancellation, and slow-client bounds pass. |
| `T-API-003` | `NR-API-004..005` | Security | Scope derivation and idempotency collision/replay matrices pass. |
| `T-IAM-001` | `NR-IAM-001..005` | Security | Full role x route x tenant/project matrix denies every unauthorized combination. |
| `T-IAM-002` | `NR-IAM-002` | Integration | Key creation, hashing, rotation, revocation, expiry, and concurrent-use tests pass. |
| `T-SPEC-001` | `NR-SPEC-001..006` | Domain | Contract compilation, missing acceptance, revision pinning, orphan detection, and observed-evidence rules pass. |
| `T-ROUTE-001` | `NR-ROUTE-001..005`, `NR-ROUTE-008` | Property | Generated portfolios prove constraint-first deterministic selection and complete rejection reasons. |
| `T-ROUTE-002` | `NR-ROUTE-006..007`, `NR-COST-004..005` | Evaluation | Recommendation uncertainty, freshness, cohort isolation, advisory-only, and anti-feedback-gaming tests pass. |
| `T-CTX-001` | `NR-CTX-001..006` | Property | Protected-node preservation, four-valued merge, provenance, bounded context, and abstention tests pass. |
| `T-EXEC-001` | `NR-EXEC-001..004` | Fault | Timeout, cancellation, worker death, duplicate delivery, lease loss, retry class, and side-effect idempotency pass. |
| `T-EXEC-002` | `NR-EXEC-003..006` | Security | Tool schema/grant, sandbox escape, resource limits, SSRF, egress, output flood, MCP session, and token tests pass. |
| `T-A2A-001` | `NR-EXEC-007..008` | Contract/security | A2A conformance plus trust, scope, depth, fan-out, loop, replay, cancel, reconnect, budget, and independent-verifier tests pass. |
| `T-VER-001` | `NR-VER-001..003` | Domain | DAG ordering, verifier independence, repair bounds, and every fail-closed terminal path pass. |
| `T-LED-001` | `NR-LED-001..003` | Property/security | Canonicalization vectors, concurrent append, tamper/delete/reorder/splice detection, receipt signing, offline verification, scope, and redaction pass. |
| `T-COMP-001` | `NR-COMP-001..002` | Contract | Versioned framework mapping, gap disclosure, retention, residency, deletion, legal-hold, and export fixtures pass. |
| `T-COST-001` | `NR-COST-001..005` | Domain/integration | Metering, rounding, aggregation, reservation concurrency, reconciliation, route regret, and feedback labels pass. |
| `T-OPS-001` | `NR-OPS-001..003` | Integration/fault | Probes, telemetry correlation/redaction, kill switches, backup, restore, replay, and post-restore ledger verification pass. |
| `T-SEC-001` | `NR-SEC-001..003` | Security/supply chain | Production fail-closed config, auth bypass, parser abuse, injection, secret scanning, dependency audit, SBOM, provenance, and signature gates pass. |
| `T-REL-001` | `NR-REL-001..003` | Release | Load/soak/fault objectives, named profile, complete evidence bundle, approvals, non-goals, and external-responsibility disclosure pass. |

## Phase 2 suites (G9)

| Test ID | Requirement coverage | Layer | Gate |
|---|---|---|---|
| `T-RTK-001` | `NR-RTK-001..002` | Property | The native PyO3 bridge returns compression results when built and a null signal that triggers the documented Python fallback otherwise; both paths pass the same contract tests, and every pass records strategy, token counts, ratio, tokens saved, and duration while protected nodes survive dedup, prune, and auto. |
| `T-OPS-004` | `NR-OPS-004` | Integration | No tool writes managed state outside `.noerelay/` on the supported local profile, and `noerelay gaps` reads the matrix and writes the gap register there by default. |
| `T-LLM-001` | `NR-LLM-001` | Integration | On the reference two-GPU host the generated tensor split assigns the operator-designated primary GPU the larger share, and the catalog lists every supported local model with quant and VRAM guidance. |
| `T-LLM-002` | `NR-LLM-002` | Domain | Both tier models appear in the catalog with distinct tier metadata, and a routing fixture selects the fast tier by default and the hard tier only under the declared escalation condition. |
| `T-LLM-003` | `NR-LLM-003` | Evaluation | A benchmark artifact under `evidence/` records per-quant tokens/s, TTFT, VRAM, and quality proxy for `gpt-oss-20b` Q4_K_M/Q5_K_M/Q6_K, and the chosen quant is reproducible from the artifact. |
| `T-LLM-004` | `NR-LLM-004` | Integration | `python -m noerelay.cli` performs start/stop/schedule of the local LLM server on Windows and POSIX, and the installer emits only thin `.bat`/`.sh` wrappers that resolve the provisioned venv interpreter. |
| `T-LLM-005` | `NR-LLM-005` | Contract | The provisioned server is launched with the full argument set from the master YAML, changing a YAML value changes the generated invocation, and schema validation rejects unknown keys. |
| `T-LLM-006` | `NR-LLM-006` | Integration | `noerelay hf search/download` resolves and fetches GGUF artifacts with progress and resume, and tab completion suggests catalog and HF repository identifiers without a network round-trip for catalog entries. |

## Required end-to-end scenarios

| Scenario | Proof required |
|---|---|
| Cheapest admissible coding route | A user sends an ordinary chat request; the contract, context manifest, model choice, verification, response, usage, cost, and receipt are inspectable without changing client code. |
| Architecture -> requirements -> tests | A vague build request becomes explicit architecture and requirements, receives linked tests, is implemented by a bounded worker/agent, and is accepted only from observed independent evidence. |
| Ambiguous high-risk request | The gateway asks a targeted clarification or requests approval; no model/tool execution occurs before the contract is sufficient. |
| Tool side effect | A model proposes an action; policy checks grant/scope/budget/approval, retries share one idempotency key, and the ledger shows exactly one effect. |
| Context pressure | A long project session is compacted under a fixed token budget while protected requirements, contradictions, evidence handles, and active tool state remain verbatim or addressable. |
| Provider failure | OpenRouter transport failure uses only an allowed endpoint/provider fallback; semantic failure follows its separate bounded path and all attempts are costed. |
| Recommendation learning | Versioned outcomes update a cohort recommendation with uncertainty but do not modify active policy until signed evaluation and promotion. |
| Cross-tenant attack | A caller attempts direct identifiers, cache collisions, stream resume, export, webhook, and timing enumeration across tenants; every path denies or is non-enumerating. |
| Ledger tampering | One stored event and one artifact are altered offline; chain and receipt verification identify the first invalid boundary. |
| Disaster recovery | Authoritative state and artifacts are restored into a clean environment; idempotent replay and receipt verification still succeed inside RPO/RTO. |

## Manual and organizational gates

| Gate | Owner evidence |
|---|---|
| Threat-model review | Independent reviewer identity, scope, findings, closure links, date, and signed approval. |
| Privacy/legal review | Applicable jurisdictions/framework versions, data map, DPAs/terms, retention and deletion decisions, gaps, and counsel approval. |
| Pilot | Seven consecutive days for the named customer-like cohort with spend ceiling and no unresolved launch blocker. |
| Operations | On-call ownership, alerts, runbooks, backup/restore and incident exercise evidence. |
| Evaluation | Signed benchmark manifest/results for every launch cohort, including calibration and hidden anti-gaming tests. |
| Release record | Product, engineering, security, evaluation, and operations approvals tied to the exact source and artifact digests. |

## Initial quantitative objectives

These are release targets for the first supported profile and must be replaced by measured results, not treated as evidence themselves.

- Availability SLO: 99.9% monthly excluding documented upstream-provider outage attribution.
- Gateway-added latency: p95 <= 25 ms and p99 <= 75 ms for non-stream setup at 100 concurrent requests, excluding provider time.
- Admission decisions: p99 <= 10 ms for a 1,000-candidate in-memory registry snapshot.
- Durability: RPO <= 5 minutes and RTO <= 60 minutes in the documented single-region profile.
- Tenant isolation: zero known cross-scope disclosures or writes.
- Ledger verification: 100% of accepted-run receipts verify in release sampling.
- Cost accounting: provider-reported token totals reconcile within exact integer equality; billed currency reconciles within the provider’s declared rounding unit.
- Security: zero open critical or high findings; medium findings require named owner and release acceptance.
