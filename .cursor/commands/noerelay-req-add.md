# /noerelay-req-add

Append a new requirement (and optionally a release test) to the NoeRelay coverage contract. The contract is **append-only**: never edit existing entries — add a new requirement ID instead.

## Instructions

1. Check what already exists so you pick fresh IDs:
```bash
set PYTHONPATH=src && python -m noerelay.cli req list
set PYTHONPATH=src && python -m noerelay.cli req tests
```

2. Propose the new requirement to the user and confirm before writing:
   - Requirement ID: `NR-<AREA>-NNN` (e.g. `NR-LLM-007`; area matches an existing work-package area)
   - Requirement text (what must be true)
   - Acceptance outcome (how it is observed)
   - Work packages (e.g. `LLM-01`) and release test IDs (e.g. `T-LLM-007`)
   - Section in `docs/requirements.md` (existing `###` heading, or a new one)
   - Gate: an existing gate ID (e.g. `G9`) to extend, or a new `G<n>` with `--gate-desc`

3. Append the requirement:
```bash
set PYTHONPATH=src && python -m noerelay.cli req add NR-LLM-007 "Requirement text here" "Acceptance outcome here" -p LLM-01 -t T-LLM-007 -s "Local LLM stack and operator tooling" -g G9
```
Creating a brand-new gate:
```bash
set PYTHONPATH=src && python -m noerelay.cli req add NR-LLM-008 "Requirement text" "Acceptance outcome" -p LLM-02 -t T-LLM-008 -s "New section name" -g G10 --gate-desc "Gate ten description"
```

4. Or append an extra release test to an existing requirement:
```bash
set PYTHONPATH=src && python -m noerelay.cli req test NR-LLM-001 T-LLM-099 -g G9
```

5. Verify the change landed and the contract still parses:
```bash
set PYTHONPATH=src && python -m noerelay.cli req show NR-LLM-007
set PYTHONPATH=src && python -m noerelay.cli req coverage
```

6. Regenerate the spec-kit feature packages so `.specify/features/` matches the manifest:
```bash
set PYTHONPATH=src && python -m noerelay.cli req regenerate
```

7. Report: the new requirement ID, which gate(s) were extended or created, and the post-change coverage counts.

Rules:
- Duplicate IDs and malformed IDs are rejected by the CLI — do not retry with edits to existing entries.
- The command validates the manifest JSON before writing; if it fails, nothing is changed.
