# Plan: LLM-02 — Python-native server lifecycle and master YAML config

## Approach

Move start/stop/scheduled-task logic into `src/noerelay/` (server lifecycle module + CLI verbs) so `python -m noerelay.cli` performs the operations on Windows and POSIX; have the installer generate only thin `.bat`/`.sh` wrappers that resolve the provisioned venv interpreter and call the Python entry points; introduce a master YAML schema for all llama-server settings (model, host/port, ctx, parallel, batch/ubatch, flash-attn, cache types, tensor split, gpu layers, flags) and generate `ProvisionPlan.server_args()` from it, matching the reference `start-llama-server` arguments.

## Components

- `src/noerelay/cli.py (start/stop/schedule verbs)`
- `src/noerelay/provision.py (ProvisionPlan.server_args from YAML)`
- `src/noerelay/installer.py (write_config, generate_scripts)`
- `src/noerelay/scripts.py (thin .bat/.sh wrappers)`
- `deploy/host/installer/README_TEMPLATE.md (operator docs)`

## Risks

- Generated wrappers invoke the wrong interpreter when the venv path is not resolved.
- YAML schema accepts unknown keys and silently drops a required flag.
- Scheduled-task creation differs between Windows and POSIX and is untested.
