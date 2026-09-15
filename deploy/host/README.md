# Machine-side support

This directory owns the Windows host services used by the Docker project:

- `local-stack.ps1`: start, stop, restart, status for the complete installation.
- `start-local-router.ps1` and `local-models.ini`: llama.cpp model router.
- `local-model-plane.py`: native RTK, internal SDD/AEE, Docker MCP bridge.
- `client-env.py`: load client settings from the running gateway.
- `llama-watchdog*` and `register-llm-watchdog.ps1`: hidden scheduled recovery.

External machine dependencies remain outside the repository: Docker Desktop, WSL2, Python, native RTK/AEE packages, `C:\LLM\llama`, and `C:\Models`. The sanctioned `C:\LLM` start/stop wrappers remain the model lifecycle entry points. Host business logic uses the shared `src/noerelay` package; it is not duplicated here.

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 start
powershell -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 stop
powershell -ExecutionPolicy Bypass -File deploy/host/local-stack.ps1 status
```

See `docs/local-operations.md` and `docs/api-client-settings.md`.
