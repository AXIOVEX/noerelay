# NoeRelay

Local AI routing and agent execution with a Rust governance gateway, native RTK context compression, Docker MCP tools, and agent-managed spec-kit/AEE development.

## Start, stop, and use

Run from this repository in PowerShell with Docker Desktop running:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 start
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 status
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 stop
```

Open [the Web UI](http://localhost:3001). The authenticated OpenAI-compatible API is `http://localhost:8080/v1`; MCP is `http://localhost:8080/mcp`. CORS supports browser frontends with bearer-token authentication.

**[Complete operating instructions](docs/local-operations.md)** include restart, configuration, troubleshooting, verification, and agent/MCP setup.

## Model routing

| Task | Model |
|---|---|
| Routine requests | GPT-OSS-20B Q5_K_M |
| Coding and tool-using agents | Qwen3.6-35B-A3B |
| Complex reasoning and escalation | Qwen3.8-27B |

Clients use the public aliases `axiovex-agni` or `axiovex-agni-raw`. NoeRelay chooses an admissible model using task type, capabilities, and governance constraints. Actual model placement and offloading are configured in [local-models.ini](deploy/host/local-models.ini); measured results are recorded under `evidence/local-recovery/`.

```text
Frontend / IDE / API client
          |
    NoeRelay Rust gateway (8080)
          |                 |
    LiteLLM adapter     MCP / bounded agent
          |                 |
    Native RTK + spec-kit/AEE adapter (8082)
          |                 |
    llama.cpp router    Docker MCP + Open Terminal
       (8081)           documentation + workspace tools
          |
    GPT-OSS / Qwen3.6 / Qwen3.8
```

PostgreSQL retains governance state and receipts. Open WebUI supplies the frontend, Docling supplies document processing, and the A2A adapter supplies agent interoperability. The recovery alias uses the same local model plane but bypasses Rust governance for maintenance; it does not provide governed receipts.

## Agent-managed development

```powershell
python scripts/noerelay.py agent "Inspect the project and propose a verified improvement" --project noerelay
python scripts/noerelay.py mcp
```

The second command is the stdio entry point for MCP clients. Cursor's project configuration already points to it.

NoeRelay automatically creates spec-kit artifacts and runs AEE. The agent maintains requirements, architecture, acceptance tests, and evidence; users describe the desired result. Untested claims remain unsupported. Review [AGENTS.md](AGENTS.md), [requirements](docs/requirements.md), the [verification matrix](.noerelay/verification-matrix.md), and [current state](docs/STATE.md).

## Primary CLI and coding clients

Use `noerelay` as the primary CLI. The repository entry point `python scripts/noerelay.py` exposes exactly the same commands.

### Windows

```powershell
# Create the isolated CLI environment (one time)
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/host/setup-cli.ps1
& .noerelay/cli-venv/Scripts/Activate.ps1

# Save isolated managed profiles; existing client configuration is preserved
noerelay client setup all
noerelay client status all

# Launch from the project you want to work on
noerelay client run opencode
noerelay client run codex
noerelay client run zoo
```

OpenCode is the recommended terminal client for this deployment. Install it first with `noerelay install opencode` if absent; Codex uses `noerelay install codex`. Zoo Code requires VS Code with the `ZooCodeOrganization.zoo-code` extension. Zoo launch opens a generated `.code-workspace` that automatically imports its NoeRelay profile and loads its managed MCP settings. The normal launch does not enable blanket tool approval.

For noninteractive use:

```powershell
noerelay client run opencode -- run "Inspect this project and explain its entry point"
noerelay client run codex -- exec "Inspect this project and explain its entry point"
```

The older `noerelay run opencode` and `noerelay run codex` commands use the same managed launch implementation.

### WSL2 / Linux

```bash
bash deploy/host/setup-cli.sh
source .noerelay/cli-venv-linux/bin/activate
noerelay client setup opencode
noerelay client run opencode
```

Use a **native Linux** OpenCode installation inside WSL, not a Windows npm shim inherited through `/mnt/c`. The CLI automatically finds this machine’s verified OpenCode 1.14.28 binary. To run that binary directly:

```bash
export PATH="$PWD/.noerelay/tools/opencode-linux/package/bin:$PATH"
```

Windows and mirrored-network WSL2 use `http://127.0.0.1:8080/v1`. Managed profiles select `axiovex-agni-raw`, keeping model selection in NoeRelay. OpenCode uses Chat Completions; Codex uses Responses and an explicit local-model catalog. Codex's managed profile disables hosted web search and multi-agent fan-out; NoeRelay MCP tools remain available. Local backends do not emit encrypted reasoning or hosted-tool results.

### Credentials, profiles, and tools

Profiles default to `~/.noerelay/clients`. Override with `NOERELAY_CLIENT_HOME`, or `--directory PATH` for setup/status/test. Launch profiles are separate from existing OpenCode/Codex settings. Explicit `NOERELAY_BASE_URL` and `NOERELAY_API_KEY` override local discovery; otherwise the CLI obtains the running Docker gateway key when available and falls back to the existing NoeRelay configuration.

OpenCode and Codex receive credentials in their child environment, never command arguments. Zoo's import/MCP files contain the credential and remain private local configuration; do not commit or share them. `noerelay client env --shell powershell|bash|json` emits credentials for capture by your shell, not for pasting into logs.

All three clients connect MCP through `noerelay mcp`. Docker MCP and Open Terminal remain behind NoeRelay. Interactive Codex MCP calls may ask for approval. Noninteractive `codex exec` cannot answer approval prompts; the provided smoke test uses its narrowly guarded fixture instead. Native client file/shell tools operate in the client workspace; the NoeRelay workspace tools execute inside Docker. Inference automatically invokes RTK/spec-kit/AEE; unsupported claims remain visible. Read [client settings](docs/api-client-settings.md) and [local operations](docs/local-operations.md).

Use 131,072 total context tokens, typically 24K–32K input and 4,096 output; reserve overhead for tools and reasoning. OpenCode's managed output limit is 4,096. Codex auto-compaction starts at 98,304 tokens. These settings bound context, not guaranteed coding quality.

### Real integration tests

```powershell
noerelay client test all
noerelay client test opencode
noerelay client test zoo
noerelay client test codex
python -m pytest tests/test_clients.py
```

Tests launch the installed clients in fresh workspaces, create an unpredictable `nonce.txt`, require an observed file/shell tool call, and verify the model returns the file contents. Zoo runs in a separate VS Code extension-test host, imports the generated profile, and verifies persisted tool history. Codex verifies its Docker MCP tool against an exact-command, read-only fixture guard; the noninteractive test approves only that guarded tool. Its fixture lives under the repository’s `.noerelay/clients/tests` so Docker can see it. Other results and redacted logs remain under the managed client directory; failures return a nonzero exit status. The Zoo extension-host test currently requires Windows VS Code. These are real client smoke tests, not a comprehensive coding-quality benchmark.

Recorded local results: OpenCode 1.14.28, Zoo Code 3.82.1, and Codex 0.153.4 passed; native WSL OpenCode also passed. The focused Python suite passed 25 tests, Rust core/gateway suites passed, and G11 plus all four client-feature AEE phases pass. See [client evidence](evidence/local-recovery/client-integrations.json).

## Router implementation

The production routing authority is Rust `noerelay-core::StagedRouter`. Python handles client setup, RTK/SDD adapters, and bounded agents; the Python reference router is not used by the live gateway. Capability and governance constraints apply before deterministic selection and admissible fallback. Whole-word task matching avoids false reasoning escalation for phrases such as “improve this function.”

See [router decision](docs/adr/0003-local-client-router.md) for the comparison with RouteLLM, LiteLLM routing, and vLLM Semantic Router. No learned router is claimed to be calibrated for these three local models.

## Verification

```powershell
python scripts/verify-local-stack.py
python -m pytest tests -q
cargo test --workspace --locked
python scripts/noerelay.py req coverage
python scripts/noerelay.py gaps
```

The supported deployment is local/test. Passing local checks does not grant production approval or close missing release evidence. Python conformance code and historical evidence remain available for verification; the active model deployment no longer uses Ollama or a remote GPU tunnel.

## Deployment layout

- `deploy/host/`: machine-side model router, RTK/SDD adapter, lifecycle, installer support, client settings.
- `deploy/docker/`: Compose definition, Dockerfiles, LiteLLM configuration, WebUI assets.
- `docker-compose.yml`: small root compatibility entry point.

Zoo Code and WSL2 settings, including the 128K total context budget: [API client settings](docs/api-client-settings.md).
