# Host provisioning

The implementation lives in `src/noerelay/installer.py` and the canonical CLI. The previous standalone installer duplicated model catalogs and lifecycle behavior; its launcher now delegates to the shared implementation.

From the repository root, inspect supported provisioning options:

```powershell
python scripts/noerelay.py provision --help
```

For this already-installed three-model Docker stack, use `deploy/host/local-stack.ps1`; do not reprovision over its router configuration. `README_TEMPLATE.md` is the template used by generic provisioning.
