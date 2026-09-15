# Local NoeRelay operations

Run these commands from the NoeRelay checkout root in PowerShell. Docker Desktop must be running.

```powershell
# Start everything
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 start

# Check services and inference
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 status

# Stop everything; stays stopped even with the watchdog enabled
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 stop

# Apply local configuration changes
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 restart
```

`stop` preserves models, PostgreSQL, chat history, and Docker volumes. The `.noerelay/runtime/STOPPED` flag suppresses the watchdog until `start` clears it. Inference starts and stops through the sanctioned `C:\LLM\start-llama-server.ps1` and `C:\LLM\stop-llama-server.ps1` wrappers. Do not kill llama-server by PID.

## Interfaces

| Interface | Address |
|---|---|
| Web UI | http://localhost:3001 |
| OpenAI-compatible API | http://localhost:8080/v1 |
| NoeRelay MCP | http://localhost:8080/mcp |
| Bounded coding agent | POST http://localhost:8080/v1/noerelay/agent |
| Gateway readiness | http://localhost:8080/ready |
| Internal llama.cpp model router | http://127.0.0.1:8081 |
| Internal native RTK/SDD/tool adapter | http://127.0.0.1:8082 |
| Internal Docker MCP gateway | http://127.0.0.1:8811/mcp |
| Internal Docker workspace API | http://127.0.0.1:8002 |

Windows and mirrored-network Ubuntu WSL2 both use `http://127.0.0.1:8080/v1`. See [API client settings](api-client-settings.md) for tested credential-loading commands. Use the configured `NOERELAY_API_KEY` as a bearer token. The API supports CORS from any origin, including Authorization preflight; CORS does not disable authentication. Use explicit bearer tokens, not cross-site cookies. MCP and agent execution currently require the operator key.

## Three-model routing

Clients use `axiovex-agni` or `axiovex-agni-raw`; the router chooses the actual model.

| Job | Model | GPU configuration |
|---|---|---|
| Routine, short requests | GPT-OSS-20B Q5_K_M | Split across both GPUs |
| Coding, implementation, tool-using agent tasks | Qwen3.6-35B-A3B UD-Q4_K_M | Both GPUs, full GPU layer offload |
| Architecture, complex reasoning, root-cause analysis, coding-route failure | Qwen3.8-27B | Both GPUs, full GPU layer offload |

The task classifier is deterministic and uses task text and tool availability. Explicit `x-noerelay-capability: code` or `reasoning` can require a tier. The Rust router applies governance constraints first and retries admissible candidates on provider failures. This is an initial task policy, not a learned guarantee of best-model selection. High-risk governance still requires acceptance criteria and suitable evidence; selecting a reasoning model does not waive those checks.

Only one model is resident at a time (`--models-max 1`). Model switches incur loading time. Qwen3.6's 22 GB Q4 weights do not fit entirely in the 12 GB 4070 SUPER, despite having only 3B active parameters. Both Qwen models therefore use both GPUs, with a 9:14 layer split and no CPU expert offload. This supersedes the original strict GPU assignments at the user's request. See `evidence/local-recovery/verification.json` for measured local checks rather than assuming a “fast” label proves performance.

Qwen3.6 defaults to nonthinking mode for responsive coding; callers may explicitly enable thinking. Qwen3.8 has a default 1,024-token reasoning budget to leave room for a final answer. This is a latency/quality tradeoff, not a guarantee that every hard problem fits the budget. Increase the model preset budget for deeper investigations. Context is 131,072 total tokens with Q8 KV cache and one sequence at a time.

Final longer coding responses sustained 87–98 tokens/s and completed in 9–10 seconds while resident. Qwen3.8 sustained 22–24 tokens/s; the sampled reasoning answer took about 63 seconds warm, including internal reasoning. Cold switches add roughly 10–15 seconds. Two generated coding samples passed six independent basic checks each in isolated Docker containers. These observations do not establish broad coding quality or algorithmic efficiency. See `evidence/local-recovery/performance.json` and `coding-quality-smoke.json`.

Model settings: `deploy/host/local-models.ini`. Provider mappings: `deploy/docker/litellm-config.yaml`. Task classification: `crates/noerelay-gateway/src/lib.rs`. Candidate capabilities: `docker-compose.yml`.

## Agent and MCP use

```powershell
python scripts/noerelay.py agent "Inspect the project and propose a small verified improvement" --project noerelay --max-steps 4
python scripts/noerelay.py agent "Investigate the root cause of the failing test" --project noerelay --escalate
```

The agent calls NoeRelay for every completion, uses the Docker MCP `ai_coding` profile for documentation/reasoning tools, and uses Open Terminal for workspace commands. The workspace is `/workspace` inside Docker. Commands execute in the Docker container, not in the host shell. Its host bind mount points at this repository; edits are real. The two deployment credential files are masked inside the container.

An observed nonzero workspace exit code or Docker tool error escalates the next step to Qwen3.8 through the router. Successful steps stay on the coding tier. The agent has a maximum of eight inference steps and eight calls per step. Exhaustion reports an incomplete task. A final model answer is reported separately from AEE verification. Tool results are stored under `.noerelay/runtime/tool-evidence/` with hashes; a successful command does not automatically become release evidence.

Cursor is configured in `.cursor/mcp.json` to run `python scripts/noerelay.py mcp`. Other MCP clients can use the same stdio command (absolute script path) or the authenticated HTTP endpoint. Connect clients to NoeRelay rather than configuring separate direct model providers or Docker MCP gateways.

## Automatic spec-kit and AEE

NoeRelay creates `spec.md`, `plan.md`, `tasks.md`, structured claims, and state under `.specify/features/runtime-<project-hash>/`, then runs the installed AEE extension before inference. The agent refines requirements, architecture, acceptance tests, and evidence. Spec-kit lifecycle hooks are automatic, and `noerelay_sdd_assess` evaluates phase artifacts. The bounded agent runs an assessment before returning its final result. Unsupported claims stay open; users do not need to operate spec-kit manually.

This repository's durable requirements are in `docs/requirements.md`, the machine contract is `spec/coverage-manifest.json`, and release-test links are in `.noerelay/verification-matrix.md`. The AEE adapter understands NoeRelay evidence envelopes and regenerates the gap register:

```powershell
python scripts/noerelay.py req coverage
python scripts/noerelay.py gaps
python scripts/noerelay.py req gate G10
```

## Verification and troubleshooting

```powershell
python scripts/verify-local-stack.py
python -m pytest tests -q
cargo test --workspace --locked
docker compose --env-file .env.docker logs --tail 50 noerelay litellm open-webui-init
```

Host logs live in `.noerelay/runtime/`: `router.stderr.log`, `rtk.jsonl`, `rtk.stderr.log`, and `docker-mcp.log`. RTK compacts plain-text history and records counts, savings, strategy, and duration. Structured tool exchanges and multimodal messages bypass compaction to preserve their protocol.

After Rust changes, build before restarting: `docker compose --env-file .env.docker build noerelay`. After Python adapter changes, restart the stack. A stopped/failed native adapter is an error; it must not silently bypass SDD or RTK. Docker MCP uses existing Docker Desktop credentials; documentation tools may depend on external service availability.

The local stack being operational does not mean all production release gates pass. Consult the coverage report and gap register for remaining evidence and approval work.

## Completed local AEE verification

The local consolidation now passes all four AEE phases for 20 atomic claims. The evidence hashes and 60-entry ledger verify; `evidence/local-recovery/aee-completion.json` records the result. The prior failure findings required splitting two composite claims, which is complete. Independent-source diversity remains an advisory limitation of these local observations, not an outstanding AEE gate failure.

## Repository layout

Machine-side support is consolidated in `deploy/host/`. Container definitions, Dockerfiles, model-plane mappings, and WebUI assets are in `deploy/docker/`. The root `docker-compose.yml` is a compatibility include. Runtime secrets stay in ignored root environment files; models, data volumes, live state, source code, tests, and evidence are retained. Generated build/test caches and superseded probes were removed. See `evidence/local-recovery/cleanup.json`.


## Managed coding clients

Run `noerelay client setup all` after activating the CLI environment, then `noerelay client run opencode`, `noerelay client run zoo`, or `noerelay client run codex`. OpenCode is the default recommendation for this deployment. The generated profiles use NoeRelay for inference and MCP. See [README](../README.md#primary-cli-and-coding-clients) for Windows/WSL setup, token budgets, and actual installed-client tests.

`noerelay client test all` creates fresh disposable fixtures and checks tool results. The Codex fixture uses the repository's Docker bind mount and a read-only command guard. Zoo's extension test requires Windows VS Code. Profile setup is idempotent and separate from existing client configuration.
