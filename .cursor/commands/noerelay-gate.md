# /noerelay-gate

Check a release gate and record evidence envelopes for its release tests. Mirrors `xtask evidence gate` / `xtask evidence record`.

## Instructions

1. Check the gate (replace the gate ID):
```bash
set PYTHONPATH=src && python -m noerelay.cli req gate G9
```
Add `--strict` to exit non-zero when the gate fails (useful for CI).

2. Read the gate output:
   - Every requirement and release test must be COVERED by an `observed_pass` or `accepted` evidence envelope under `evidence/<work-package>/<test-id>.json`
   - Each "NOT covered" line names a release test that still needs evidence

3. For each uncovered release test, run the actual test command and record an envelope (replace the values):
```bash
set PYTHONPATH=src && python -m noerelay.cli req record -w LLM-01 -t T-LLM-001 -c "python -m pytest tests/test_compression.py -q" -q NR-LLM-001 --profile single-region-org-v1-local-test --runner ROLE-PYTHON
```
   - `-c` is executed from the repo root; exit 0 → `observed_pass`, non-zero → `observed_fail`
   - `-q` lists the requirement IDs this evidence covers (comma-separated)
   - Add `--verifier <identity>` when an independent verifier ran the check

4. Re-check the gate after recording:
```bash
set PYTHONPATH=src && python -m noerelay.cli req gate G9
```

5. Report:
   - Gate verdict (PASS/FAIL) and the remaining uncovered tests
   - Which envelopes were written (path + status + source revision)
   - Overall coverage summary: `set PYTHONPATH=src && python -m noerelay.cli req coverage`

Rules:
- Never record `observed_pass` for a command that was not actually run; `record` executes the command itself.
- Envelopes are written to `evidence/<work-package-id>/<test-id>.json` and are picked up by both the Python coverage report and `cargo run -p xtask -- evidence validate/coverage/gate`.
