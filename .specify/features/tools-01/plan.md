# Plan: TOOLS-01 — Local state locality and Hugging Face operator CLI

## Approach

Confirm and, where needed, pin the tooling defaults so databases, logs, run artifacts, gap/verification matrices, and exports are written under `.noerelay/` and `noerelay gaps` reads/writes there by default; add `noerelay hf search` and `noerelay hf download` (GGUF resolution, progress, resume) backed by huggingface_hub where available with a stdlib fallback; add completion data for catalog and HF repo identifiers so tab-completion works without a network round-trip for catalog entries.

## Components

- `src/noerelay/cli.py (hf search/download verbs, completion data)`
- `src/noerelay/config.py (state paths under .noerelay/)`
- `src/noerelay/models.py (catalog identifiers for completion)`
- `reference/gateway/config.py (gateway defaults to .noerelay/)`

## Risks

- A tool writes managed state outside `.noerelay/` and breaks the locality contract.
- Download resume loses partial progress on interruption.
- Completion data drifts from the catalog and suggests stale identifiers.
