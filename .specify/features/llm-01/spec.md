# Spec: LLM-01 — Two-model local plane, GPU priority, and quant benchmark

> Work package `LLM-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PY-EVAL` · Depends on: `FND-01`

## Problem

Make the local profile a two-model plane (fast `gpt-oss-20b`, hard `qwen3.8-27b`) with the operator's primary GPU (RTX 4070 SUPER) as the preferred tensor owner, a recorded quant benchmark for `gpt-oss-20b`, and a machine-readable supported-model list (NR-LLM-001, NR-LLM-002, NR-LLM-003).

## Goals

- Add `gpt-oss-20b` (Q4_K_M/Q5_K_M/Q6_K) to the catalog with tier and VRAM metadata.
- Make the primary/display GPU the preferred tensor owner in the generated split.
- Record a per-quant benchmark artifact and derive the default quant from it.
- Expose a machine-readable supported-model list.

## Non-goals

- No cloud routing changes; this is the local llama-server plane only.
- No automatic model self-upgrade; selection stays explicit and auditable.

## Requirements

- `NR-LLM-001` — The local provisioner MUST treat the operator-designated primary GPU (default: the display GPU, e.g. an RTX 4070 SUPER) as the preferred tensor owner, and MUST expose a machine-readable supported-model list derived from the model catalog.
  - Acceptance: On the reference two-GPU host the generated tensor split assigns the primary GPU the larger share; `noerelay models` (or the catalog source) lists every supported local model with quant and VRAM guidance. · Release test(s): `T-LLM-001`
- `NR-LLM-002` — The local profile MUST support a two-model plane: a fast model (`gpt-oss-20b`) for routine work and a hard model (`qwen3.8-27b`) for difficult work, with routing metadata that keeps the selection explicit and auditable.
  - Acceptance: Both models appear in the catalog with distinct tier metadata; a routing fixture selects the fast tier by default and the hard tier only under the declared escalation condition. · Release test(s): `T-LLM-002`
- `NR-LLM-003` — Quantization selection for `gpt-oss-20b` (Q4_K_M / Q5_K_M / Q6_K) MUST be backed by a recorded benchmark (tokens/s, TTFT, VRAM, quality proxy) rather than an unrecorded preference.
  - Acceptance: A benchmark artifact under `evidence/` records per-quant results and the chosen quant; the choice is reproducible from the artifact. · Release test(s): `T-LLM-003`

## Acceptance criteria

- [ ] On the reference two-GPU host the generated tensor split assigns the 4070 SUPER the larger share.
- [ ] Both `gpt-oss-20b` and `qwen3.8-27b` appear in the catalog with distinct tier metadata.
- [ ] A routing fixture picks the fast tier by default and the hard tier only under the declared escalation.
- [ ] A benchmark artifact under `evidence/` records per-quant results and the chosen quant.
