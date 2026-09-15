# Local LLM Stack — Model Recommendations by Platform

## Windows (Current Machine)

**Final recommendation:**

| Role | Model | Notes |
|------|-------|-------|
| **Main agentic coding** | `Qwen3.8-27B` Q4_K_M | Large enough to run properly; no need to compromise to 14B |
| **Fast tool-calling / general reasoning** | `gpt-oss-20B` | Alternative for latency-sensitive or lighter tasks |

- Runtime: llama.cpp (CUDA, multi-GPU tensor-split)
- Context: 16K
- This machine has sufficient VRAM for the 27B model at Q4_K_M; do not downsize unless latency becomes the priority over capability.

---

## Apple Silicon (MacBook) — Testing Plan

## Default Recommendation (Apple Silicon)

| Setting | Value |
|---------|-------|
| **Model** | `gpt-oss-20b` |
| **Quantization** | Native MXFP4 or the runtime's recommended Apple Silicon build |
| **Context** | 8K initially |
| **Reasoning** | `medium` for normal work, `high` for difficult planning or debugging |
| **Runtime** | **MLX** (preferred); Ollama as fallback |

> **Push for MLX.** It's the native Apple Silicon inference runtime with the best
> performance-to-memory ratio. Ollama is the fallback only if MLX is unavailable
> or a model isn't available in MLX format.

## Models to Test

### Default (must work)
- [ ] `gpt-oss-20B` — set as the default model

### Experiments (benchmark & compare)
- [ ] `Qwen3.8-27B` Q3 quantization
- [ ] `Gemma 4 26B`
- [ ] `Qwen3-Coder 30B`

## Setup Steps

### 1. Install MLX runtime

```bash
# Option A: pip (preferred)
pip install mlx-lm

# Option B: Homebrew
brew install mlx

# Verify
python -c "import mlx.core as mx; print(mx.default_device())"
# Expected: mlx.core.Device(type='gpu')
```

### 2. Pull the default model

```bash
# gpt-oss-20B via MLX
python -m mlx_lm.generate --model mlx-community/gpt-oss-20b-4bit --prompt "Hello" --max-tokens 32

# Or via Ollama (fallback)
ollama pull gpt-oss-20b
```

### 3. Configure NoeRelay for Apple Silicon

```bash
# Set the gateway to use MLX backend
noerelay config set backend mlx
noerelay config set model gpt-oss-20b
noerelay config set ctx-size 8192
noerelay config set reasoning medium
```

### 4. Benchmark each model

For each model, record:
- [ ] Tokens/sec (generation speed)
- [ ] Peak memory usage
- [ ] Time-to-first-token (TTFT)
- [ ] Quality on a standard prompt set (coding, planning, summarization)
- [ ] Whether it fits in unified memory at the target context size

| Model | Quant | Tokens/s | Peak RAM | TTFT | Quality Notes |
|-------|-------|----------|----------|------|---------------|
| gpt-oss-20B | MXFP4 | | | | |
| Qwen3.8-27B | Q3 | | | | |
| Gemma 4 26B | native | | | | |
| Qwen3-Coder 30B | native | | | | |

### 5. Reasoning mode comparison

Test `medium` vs `high` reasoning on:
- [ ] A complex multi-step planning task
- [ ] A debugging session with a non-trivial bug
- [ ] A simple code generation task (should be fine at medium)

Record: quality difference, latency cost, token overhead.

### 6. MLX vs Ollama comparison (if both available)

| Metric | MLX | Ollama |
|--------|-----|--------|
| Tokens/s | | |
| Memory | | |
| Model availability | | |
| Setup complexity | | |

## Deliverables

- [ ] Update `src/noerelay/provision.py` with Apple Silicon defaults (MLX-first, gpt-oss-20B)
- [ ] Update `deploy/host/installer/installer.py` to detect Apple Silicon and prefer MLX
- [ ] Update `deploy/host/installer/README_TEMPLATE.md` with Apple Silicon section
- [ ] Update `README.md` local LLM stack section with Apple Silicon guidance
- [ ] Commit benchmark results to `evidence/`
