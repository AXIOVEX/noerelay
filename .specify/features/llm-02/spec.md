# Spec: LLM-02 — Python-native server lifecycle and master YAML config

> Work package `LLM-02` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-PY-EVAL`, `ROLE-SRE` · Depends on: `LLM-01`

## Problem

Replace the hand-written `C:\LLM` PowerShell lifecycle scripts with noerelay Python entry points, and drive the llama-server invocation from a single master YAML that carries the full reference argument set (NR-LLM-004, NR-LLM-005).

## Goals

- Implement server start/stop/schedule in the Python package with CLI verbs.
- Make generated installer scripts thin venv-resolving wrappers (no `.ps1`).
- Define and validate a master YAML schema for llama-server settings.
- Generate the full server argument list from the YAML.

## Non-goals

- No PowerShell lifecycle scripts are generated or required.
- No change to the OpenRouter cloud plane; this is local provisioner behavior.

## Requirements

- `NR-LLM-004` — Local LLM server lifecycle (start, stop, scheduled-task creation) MUST be implemented in the noerelay Python package; generated installer scripts MUST be thin wrappers that invoke the Python entry points in the provisioned virtual environment. No PowerShell lifecycle scripts are generated or required.
  - Acceptance: `python -m noerelay.cli` (or `noerelay`) performs start/stop/schedule on Windows and POSIX; the installer emits only `.bat`/`.sh` wrappers that resolve the venv interpreter; no `.ps1` lifecycle files are produced. · Release test(s): `T-LLM-004`
- `NR-LLM-005` — A single master YAML configuration MUST carry all llama-server settings (model, host/port, context, parallelism, batch/ubatch, flash attention, cache types, tensor split, GPU layers, flags) matching the reference `start-llama-server` argument set, and the provisioner MUST generate server arguments from it.
  - Acceptance: The provisioned server process is launched with the full argument set from the YAML; changing a YAML value changes the generated invocation; schema validation rejects unknown keys. · Release test(s): `T-LLM-005`

## Acceptance criteria

- [ ] `noerelay` start/stop/schedule work on Windows and POSIX using the venv Python.
- [ ] The installer emits only `.bat`/`.sh` wrappers that resolve the venv interpreter; no `.ps1` lifecycle files.
- [ ] The provisioned server launches with the full reference argument set generated from the YAML.
- [ ] Changing a YAML value changes the generated invocation; unknown keys are rejected.
