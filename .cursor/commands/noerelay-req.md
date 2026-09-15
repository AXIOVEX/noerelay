# /noerelay-req

Inspect the NoeRelay requirement and release-test coverage contract (append-only machine contract in `spec/coverage-manifest.json` + `docs/requirements.md`).

## Instructions

1. List all requirements with coverage status:
```bash
set PYTHONPATH=src && python -m noerelay.cli req list
```

2. List release tests with evidence status:
```bash
set PYTHONPATH=src && python -m noerelay.cli req tests
```

3. Show one requirement in detail (replace the ID):
```bash
set PYTHONPATH=src && python -m noerelay.cli req show NR-LLM-001
```

4. Print the full coverage report (mirrors `xtask evidence coverage`):
```bash
set PYTHONPATH=src && python -m noerelay.cli req coverage
```
Add `--strict` to make the command exit non-zero while any requirement is uncovered.

5. Report:
   - Total requirement count and gate list (G0..Gn)
   - How many requirements are COVERED vs MISSING
   - The release verdict (PASS/FAIL) and which gates fail
   - Any evidence-scan notes (e.g. skipped non-envelope JSON files; re-run with `--verbose` for detail)

Do NOT modify the contract from this command. To change it, use `/noerelay-req-add` or `/noerelay-gate`.
