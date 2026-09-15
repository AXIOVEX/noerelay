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
