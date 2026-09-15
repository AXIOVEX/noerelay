# Tasks: RTK-01 — RTK native compression engine and PyO3 bridge

- [ ] 1. Align `rtk/` pyo3 version and build it standalone with maturin.
- [ ] 2. Verify `rtk_bridge.py` maps the crate's dict contract and returns None when native is missing.
- [ ] 3. Wire the gateway pipeline to prefer native compression after route selection.
- [ ] 4. Add/extend tests proving native and fallback parity and metric emission.
- [ ] 5. Record T-RTK-001 evidence for NR-RTK-001/NR-RTK-002.
