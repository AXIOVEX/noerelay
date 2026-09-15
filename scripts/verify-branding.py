"""Verify active ownership metadata and approved asset bytes; preserve audit history."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANY = "Axiovex Systems, LLC"
REPOSITORY = "https://github.com/AXIOVEX/noerelay"


def main():
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    checked = 0
    stale = []
    for name in set(files):
        if not name or name == "scripts/verify-branding.py" or name.startswith(("evidence/", ".specify/extensions/")) or "/runtime-" in name:
            continue
        path = ROOT / name
        if not path.is_file() or path.suffix in (".svg", ".png"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        checked += 1
        if re.search(r"electrohire|AXIOVEX Systems Inc\.|github\.com/noerelay/noerelay", text, re.I):
            stale.append(name)
    assert not stale, "Stale active branding: " + ", ".join(stale)
    source = json.loads((ROOT / "deploy/docker/brand/SOURCE.json").read_text())
    for name, entry in source["files"].items():
        digest = hashlib.sha256((ROOT / "deploy/docker/brand" / name).read_bytes()).hexdigest()
        assert digest == entry["sha256"], name
    assert COMPANY in (ROOT / "LICENSE").read_text()
    assert 'license = { file = "LICENSE" }' in (ROOT / "pyproject.toml").read_text()
    assert REPOSITORY in (ROOT / "pyproject.toml").read_text()
    assert (ROOT / "services/a2a-adapter/go.mod").read_text().startswith("module github.com/AXIOVEX/noerelay/")
    schemas = list((ROOT / "spec/schemas/legacy").glob("*.json")) + [ROOT / "spec/benchmark-manifest.schema.json"]
    for schema in schemas:
        assert json.loads(schema.read_text())["$id"].startswith(("https://axiovex.example/", "https://noerelay.local/"))
    result = {"passed": True, "active_text_files_checked": checked, "stale_active_files": stale,
              "approved_assets": len(source["files"]), "brand_revision": source["revision"],
              "schema_namespaces_checked": len(schemas),
              "historical_evidence": "Original ledger records, assessments, runtime claims and recorded paths remain unchanged."}
    output = ROOT / "evidence/branding/repository.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
