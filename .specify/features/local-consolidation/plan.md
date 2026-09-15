# Architecture

Rust NoeRelay owns governance and routing. LiteLLM maps three models to the host RTK/SDD adapter. llama.cpp loads one selected model across both GPUs, preserving Q5 GPT and Q4 Qwen weights. Qwen3.6 uses nonthinking coding by default; Qwen3.8 provides bounded reasoning. Native RTK preserves protected text and bypasses structured tool exchanges. The adapter owns Docker MCP; workspace execution occurs in Open Terminal. Agent-managed spec-kit features and real AEE assessments precede inference. A final answer never implies verified implementation.

Rejected: strict single-GPU Qwen placement requires CPU offload and measured only 26/10 tokens per second. Shared GPUs measured approximately 97/24 on longer requests. Model switches remain costly; keep coding tasks on the coding route.

## Windows and WSL2 access

Existing mirrored WSL networking exposes the Docker-published NoeRelay port at 127.0.0.1:8080 in both environments. Clients use /v1 and axiovex-agni-raw. A credential-loading helper reads the running gateway configuration without writing keys to documentation or evidence. No firewall or WSL restart is required.
