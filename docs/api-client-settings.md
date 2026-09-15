# Windows and WSL2 API settings

Verified on Windows 11 and Ubuntu-24.04 under WSL2 on 2026-09-15. This machine uses mirrored WSL networking. Both clients completed authenticated requests at the same address; no firewall change or WSL restart was needed.

| Setting | Windows host | Ubuntu WSL2 |
|---|---|---|
| Provider/API type | OpenAI-compatible | OpenAI-compatible |
| Base URL | `http://127.0.0.1:8080/v1` | `http://127.0.0.1:8080/v1` |
| Model for coding/agents | `axiovex-agni-raw` | `axiovex-agni-raw` |
| Model for branded chat | `axiovex-agni` | `axiovex-agni` |
| Authentication | Bearer API key | Same bearer API key |
| Context window | 131,072 tokens total | 131,072 tokens total |
| Initial output limit | 4,096 tokens | 4,096 tokens |
| Request timeout | 600 seconds for large prompts | 600 seconds for large prompts |
| Streaming | Supported | Supported |
| Temperature | Leave unset for model defaults | Leave unset for model defaults |

Use the public alias so NoeRelay selects GPT-OSS Q5, Qwen3.6 coding, or Qwen3.8 reasoning internally. Do not configure clients against the internal ports 8081/8082. Optional `x-noerelay-capability: reasoning` requests the reasoning tier. Agent tool failures also trigger escalation through the router.

Chat URL: `http://127.0.0.1:8080/v1/chat/completions`. Responses URL: `http://127.0.0.1:8080/v1/responses`. MCP URL: `http://127.0.0.1:8080/mcp`. The API accepts CORS from any origin while retaining bearer authentication.

## Load the correct API key

Start the stack first. The helper reads the running gateway's key, avoiding stale values from older configuration files. Capture its output as shown; it contains the credential. It sets `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL` in the current shell only.

### Windows PowerShell

From `C:\Users\trist\Development\ElectroHire\noerelay`:

```powershell
Invoke-Expression ((& python deploy/host/client-env.py --shell powershell) -join "`n")

Invoke-RestMethod "$env:OPENAI_BASE_URL/models" -Headers @{
    Authorization = "Bearer $env:OPENAI_API_KEY"
}
```

### Ubuntu WSL2 Bash

This invokes the installed Windows Python helper to read the same running gateway credential. It does not require installing NoeRelay or AEE inside WSL.

```bash
eval "$(/mnt/c/Users/trist/scoop/apps/python312/current/python.exe \
  C:/Users/trist/Development/ElectroHire/noerelay/deploy/host/client-env.py \
  --shell bash </dev/null)"

curl --fail "$OPENAI_BASE_URL/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

For a frontend settings dialog, enter the base URL and public model alias from the table, then supply the same configured gateway key. Model selection stays automatic.

## Verification

`python scripts/verify-host-wsl.py` checks authenticated model listing, a real completion, and rejection without a key from both Windows and Ubuntu WSL2. Its report is `evidence/local-recovery/host-wsl-access.json`; it contains no API key.

The local consolidation's AEE claims were split into atomic, requirement-linked statements. The final assessment passes with no failure findings. Evidence hashes and the epistemic ledger were verified. This covers the local feature; unrelated production release requirements retain their own gates.

## Zoo Code and token budgets

Zoo Code's `reasoning_effort` field is now explicitly accepted and validated by the gateway. Its previous 400 response was a wire-profile rejection, not a WSL network error. Use OpenAI-compatible provider, `http://127.0.0.1:8080/v1`, and `axiovex-agni-raw`. `low` reasoning effort was tested from WSL2 with multipart content. The branded `axiovex-agni` alias was also tested successfully.

- Everyday coding: keep input around 24K–32K tokens; allow 4,096 output tokens.
- Large changes: allow 8,192 output tokens and keep input at or below 114,688 tokens. Reserve another 8,192 for system prompts, tool schemas, and template overhead.
- The 131,072 window is input plus output, including reasoning tokens. It is not 128K input plus a separate output allowance.
- All three models allocate 131,072 tokens with Q8 KV caches and both GPUs. The host's 64 GB RAM helps the OS, Docker, and model file cache; it does not replace VRAM bandwidth. One model remains resident at a time.
- Use a 600-second client timeout for unusually large prompts. Larger input increases prompt-processing latency; keep ordinary requests smaller even though the larger window is available.

Current context observations are in `evidence/local-recovery/verification.json` and `long-context.json`. A retrieval smoke test does not prove general reasoning accuracy at every context length.


## Managed OpenCode, Zoo Code, and Codex

Create the CLI environment with `deploy/host/setup-cli.ps1` on Windows or `deploy/host/setup-cli.sh` in WSL. Activate it, then run `noerelay client setup all`. Launch the selected client with `noerelay client run opencode`, `noerelay client run zoo`, or `noerelay client run codex`. See the README for installation and real-client test commands.

OpenCode uses Chat Completions; Codex uses stateless Responses with a managed local-model catalog. Wire profile `2026-09-15.1` accepts developer messages, function-call history, text tool results, validated stateless metadata, and function namespaces. Namespace names are translated for local providers and restored in Responses/SSE output. Stored responses, hosted tools, and non-text tool-result parts are unsupported. An optional encrypted-reasoning include is accepted but does not manufacture encrypted content.

Codex forwards connection variables explicitly to NoeRelay MCP and requires successful MCP startup. Interactive MCP calls retain approval prompts. Noninteractive exec cannot answer those prompts. The real Codex test approves only an exact nonce-file read through a guarded NoeRelay MCP process; it does not grant general shell access. Native Windows Codex shell execution was blocked by its execution policy in this test environment, so successful verification covers the Docker MCP workspace path.

NoeRelay's Docker workspace is this repository at `/workspace`. A client opened in another host project can use native file tools there, but Docker tools still target the configured repository mount. Change the workspace mount deliberately before using Docker tools for a different project.
