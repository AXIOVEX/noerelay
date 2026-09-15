# Spec: TOOLS-01 — Local state locality and Hugging Face operator CLI

> Work package `TOOLS-01` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PY-EVAL`, `ROLE-SRE` · Depends on: `LLM-02`

## Problem

Keep all NoeRelay-managed local state inside the project-local `.noerelay/` directory, and give operators Hugging Face model search, download with progress and resume, and shell autocomplete in the CLI (NR-OPS-004, NR-LLM-006).

## Goals

- Default all managed local state to `.noerelay/` and keep tools reading from there.
- Add `noerelay hf search` and `noerelay hf download` with progress and resume.
- Provide autocomplete for model identifiers and quant names.

## Non-goals

- No secret storage or credential handling in the CLI.
- No replacement of the provisioner's model download; this is an operator-facing helper.

## Requirements

- `NR-OPS-004` — All NoeRelay-managed local state (databases, logs, run artifacts, gap/verification matrices, exports) MUST be written to the project-local `.noerelay/` directory, and tooling that consumes these artifacts MUST default to that location.
  - Acceptance: No tool writes managed state outside `.noerelay/` on the supported local profile; `noerelay gaps` and equivalent commands read and write there by default. · Release test(s): `T-OPS-004`
- `NR-LLM-006` — The noerelay CLI MUST support Hugging Face model operations: search, download (with progress and resume), and shell-style autocomplete for model identifiers and quant names.
  - Acceptance: `noerelay hf search/download` resolves and fetches GGUF artifacts; tab-completion suggests catalog and HF repo identifiers without a network round-trip for catalog entries. · Release test(s): `T-LLM-006`

## Acceptance criteria

- [ ] No tool writes managed state outside `.noerelay/` on the local profile; `noerelay gaps` uses it by default.
- [ ] `noerelay hf search/download` resolves and fetches GGUF artifacts with progress and resume.
- [ ] Tab-completion suggests catalog and HF repo identifiers; catalog entries need no network.
