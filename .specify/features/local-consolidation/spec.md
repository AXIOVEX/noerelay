# Local consolidation

- NR-LLM-007: automatically route GPT-OSS Q5 routine, Qwen3.6 coding, Qwen3.8 reasoning. T-LLM-007 verifies actual model selection and records cold/warm timings. Preserve quantization quality; optimize residency and avoid CPU offload.
- NR-OPS-005: internal spec-kit/AEE lifecycle, preserving agent edits and unsupported claims. T-OPS-005 verifies fail-closed and artifact behavior.
- NR-EXEC-009: authenticated Docker MCP and bounded agents. T-EXEC-009 verifies actual tool execution, allowlist, and step limits.

Performance observations are not general coding-quality calibration. Production approvals remain separate.

- NR-API-007: Windows and Ubuntu WSL2 use the same authenticated API. T-API-004 verifies model listing, a real completion, and rejection without a key from both clients.

AEE claim decomposition retains each separately testable behavior under its parent requirement. AEE acceptance is scoped to these local observations, not all repository release requirements.

- NR-API-008: validated reasoning_effort on Zoo multipart chat. T-API-005 verifies WSL requests.
- NR-LLM-008: 131072 total allocated context per routed model. T-LLM-008 verifies model metadata plus a beyond-16K retrieval prompt; full-window quality is not implied.
- NR-OPS-006: deploy/host owns machine support; deploy/docker owns container definitions. T-OPS-006 verifies layout imports and deployment contracts.
