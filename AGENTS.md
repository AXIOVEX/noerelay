# NoeRelay agent workflow

Read `docs/local-operations.md` and `docs/STATE.md` before changing the stack.

- Manage spec-kit and AEE internally. Maintain requirements, architecture, acceptance tests, and evidence without asking users to operate the methodology.
- Use `.specify/features/` for spec, plan, and tasks. Keep `spec/coverage-manifest.json`, `docs/requirements.md`, and `.noerelay/verification-matrix.md` consistent.
- Run the installed AEE extension after specification, planning, tasks, and implementation. Unsupported claims, assumptions, and contradictions remain visible. Run `python scripts/noerelay.py gaps` after recording evidence.
- Route all inference through NoeRelay: GPT-OSS Q5 for routine requests, Qwen3.6-35B-A3B for coding, Qwen3.8-27B for reasoning/escalation. Never silently substitute another model.
- Connect tools through NoeRelay's MCP/agent endpoints. Docker MCP owns the external tool profile; Open Terminal owns the Docker workspace execution environment.
- Never kill llama-server by raw PID. Use `deploy/host/local-stack.ps1` and the sanctioned C:\LLM wrappers. Manual stop must suppress the watchdog.
- Verify real completions, tool calls, and service health after deployment. Do not infer production readiness from container health, model output, or unit tests alone.
- Preserve existing uncommitted work and data volumes. Remove obsolete active wiring; retain conformance tests and historical evidence needed for audit.
