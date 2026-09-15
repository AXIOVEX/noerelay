"""Requirement and release-test management for the NoeRelay coverage contract.

The machine contract is two files:

* ``docs/requirements.md`` — human-authored ``| ID | Requirement | Acceptance
  outcome |`` tables; the single source of truth for requirement wording.
* ``spec/coverage-manifest.json`` — the append-only registry mapping
  requirement -> work package -> release test, plus the ``G0..`` evidence
  gates parsed by ``xtask evidence validate/coverage/gate``.

This module implements the operator loop in stdlib-only Python so it works on
any machine with the repo checked out:

* ``req list``       — requirement table with coverage status
* ``req show ID``    — one requirement with wording, packages, tests, evidence
* ``req tests``      — release-test registry with evidence status
* ``req add ID``     — append a new requirement to both files (append-only)
* ``req test ID T``  — append a release test to an existing requirement
* ``req coverage``   — mirrors ``xtask evidence coverage``
* ``req gate Gx``    — mirrors ``xtask evidence gate Gx``
* ``req record``     — run a command and write an evidence envelope
* ``req regenerate`` — re-run ``scripts/generate_specify_features.py``

Append-only policy: existing manifest entries and the ``G0``-``G8`` gate keys
are never rewritten or renamed (they are the machine contract for ``xtask``);
new requirements, tests, and gates are appended.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional

REQ_ID_RE = re.compile(r"^NR-[A-Z]+-\d{3}$")
TEST_ID_RE = re.compile(r"^T-[A-Z]+-\d{3}$")
GATE_ID_RE = re.compile(r"^G\d+$")

# EnvelopeStatus values that satisfy a release gate (mirrors
# noerelay_core::evidence::EvidenceEnvelope::is_release_ready).
RELEASE_READY = {"observed_pass", "accepted"}

DEFAULT_PROFILE = "single-region-org-v1-local-test"
DEFAULT_RUNNER = "ROLE-RUST"

MANIFEST_RELPATH = Path("spec") / "coverage-manifest.json"
REQUIREMENTS_RELPATH = Path("docs") / "requirements.md"
GENERATOR_RELPATH = Path("scripts") / "generate_specify_features.py"


# --------------------------------------------------------------------------- #
# Repo location and source parsing
# --------------------------------------------------------------------------- #
def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from *start* (default: cwd) to the NoeRelay repo root.

    The root is the first ancestor containing both
    ``spec/coverage-manifest.json`` and ``docs/requirements.md``. Falls back to
    the tree this module lives in (``src/noerelay/reqtest.py`` -> root).
    """
    cur = (start or Path.cwd()).resolve()
    for cand in [cur, *cur.parents]:
        if (cand / MANIFEST_RELPATH).is_file() and (cand / REQUIREMENTS_RELPATH).is_file():
            return cand
    here = Path(__file__).resolve()
    for cand in here.parents:
        if (cand / MANIFEST_RELPATH).is_file() and (cand / REQUIREMENTS_RELPATH).is_file():
            return cand
    raise FileNotFoundError(
        "could not locate the NoeRelay repo root "
        f"(no ancestor of {cur} contains spec/coverage-manifest.json)"
    )


def load_manifest(root: Path) -> dict:
    with open(root / MANIFEST_RELPATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_requirements_md(path: Path) -> "OrderedDict[str, dict]":
    """Parse ``| ID | Requirement | Acceptance outcome |`` tables."""
    reqs: "OrderedDict[str, dict]" = OrderedDict()
    in_table = False
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            s = line.strip()
            if s.startswith("| ID | Requirement"):
                in_table = True
                continue
            if not in_table:
                continue
            if not s.startswith("|"):
                in_table = False
                continue
            if set(s.replace("|", "").strip()) <= set("-: "):
                continue  # separator row
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 3:
                rid = cells[0].strip("`").strip()
                if REQ_ID_RE.match(rid):
                    reqs[rid] = {"text": cells[1], "acceptance": cells[2]}
    return reqs


# --------------------------------------------------------------------------- #
# Evidence loading (mirrors xtask/src/coverage.rs)
# --------------------------------------------------------------------------- #
def load_envelopes(evidence_dir: Path):
    """Load all evidence envelopes under *evidence_dir* (recursive).

    Returns ``(envelopes, problems)``; malformed files are reported in
    ``problems`` and skipped, matching how the gate must keep working as
    evidence accumulates.
    """
    envelopes: List[dict] = []
    problems: List[str] = []
    if not evidence_dir.is_dir():
        return envelopes, problems
    for path in sorted(evidence_dir.rglob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{path}: {exc}")
            continue
        if not isinstance(data, dict) or not isinstance(data.get("evidence_version"), str):
            continue  # benchmark/portfolio artifacts are not evidence envelopes
        if "evidence_id" not in data:
            problems.append(f"{path}: not an evidence envelope (missing evidence_id)")
            continue
        envelopes.append(data)
    return envelopes, problems


def is_release_ready(env: dict) -> bool:
    """Mirror of ``EvidenceEnvelope::is_release_ready`` (observed_pass|accepted)."""
    return env.get("status") in RELEASE_READY


def coverage_report(root: Path) -> dict:
    """Requirement coverage report mirroring ``xtask evidence coverage``."""
    manifest = load_manifest(root)
    envelopes, problems = load_envelopes(root / "evidence")
    by_req: "dict[str, list]" = {}
    for env in envelopes:
        for rid in env.get("requirement_ids", []):
            by_req.setdefault(rid, []).append(env)

    entries: "OrderedDict[str, dict]" = OrderedDict()
    covered = partial = missing = 0
    for req in manifest.get("requirements", []):
        rid = req["requirement_id"]
        evs = by_req.get(rid, [])
        ready = [e for e in evs if is_release_ready(e)]
        if ready:
            status, covered = "COVERED", covered + 1
        elif evs:
            status, partial = "PARTIAL", partial + 1
        else:
            status, missing = "MISSING", missing + 1
        shown = ready if ready else evs
        entries[rid] = {
            "work_packages": req.get("primary_work_packages", []),
            "tests": req.get("primary_release_tests", []),
            "status": status,
            "evidence": [e.get("evidence_id", "?") for e in shown],
        }
    total = len(entries)
    return {
        "total": total,
        "covered": covered,
        "partial": partial,
        "missing": missing,
        "passed": missing == 0,
        "entries": entries,
        "problems": problems,
    }


def gate_report(root: Path, gate_id: str) -> dict:
    """Gate check mirroring ``xtask evidence gate`` (``check_gate``)."""
    manifest = load_manifest(root)
    gates = manifest.get("release_gates", {})
    if gate_id not in gates:
        raise KeyError(f"unknown release gate: {gate_id}")
    envelopes, _ = load_envelopes(root / "evidence")
    covered = set()
    for env in envelopes:
        if is_release_ready(env):
            covered.update(env.get("requirement_ids", []))
    reqs = gates[gate_id].get("requirements", [])
    missing = [r for r in reqs if r not in covered]
    return {
        "gate_id": gate_id,
        "description": gates[gate_id].get("description", ""),
        "requirements": reqs,
        "tests": gates[gate_id].get("tests", []),
        "missing": missing,
        "passed": not missing,
    }


# --------------------------------------------------------------------------- #
# Append-only manifest editing (style-preserving, line-oriented)
# --------------------------------------------------------------------------- #
def _trailing_newline(text: str) -> str:
    return "\n" if text.endswith("\n") else ""


def _append_requirement_entry(text: str, entry: dict) -> str:
    """Insert one requirement entry line before the requirements array closes."""
    line = "    " + json.dumps(entry, ensure_ascii=False)
    lines = text.splitlines()
    in_reqs = False
    insert_at = None
    for i, l in enumerate(lines):
        if not in_reqs:
            if '"requirements"' in l:
                in_reqs = True
            continue
        if l.strip() == "],":
            insert_at = i
            break
    if insert_at is None:
        raise ValueError("requirements array not found in manifest")
    # The previous last entry may lack a trailing comma (the array's final
    # element is valid JSON without one); add it before inserting.
    prev = insert_at - 1
    while prev >= 0 and not lines[prev].strip():
        prev -= 1
    if (
        prev >= 0
        and lines[prev].strip().startswith("{")
        and not lines[prev].rstrip().endswith(",")
    ):
        lines[prev] = lines[prev].rstrip() + ","
    lines.insert(insert_at, line)
    return "\n".join(lines) + _trailing_newline(text)


def _upsert_gate(text: str, gate_id: str, description: str,
                 requirements: List[str], tests: List[str]):
    """Append a gate or extend an existing one. Returns ``(text, created)``."""
    if not GATE_ID_RE.match(gate_id):
        raise ValueError(f"invalid gate id {gate_id!r} (expected G<n>)")
    lines = text.splitlines()
    gate_key = f'"{gate_id}":'
    for i, line in enumerate(lines):
        if gate_key in line:
            # Gate lines are key-value members of the release_gates object
            # ("G9": {...}), not standalone objects: wrap for parsing and
            # re-emit as a key-value member, preserving comma state.
            stripped = line.strip()
            had_comma = stripped.endswith(",")
            obj = json.loads("{" + stripped.rstrip(",") + "}")
            gate = obj[gate_id]
            for r in requirements:
                if r not in gate.get("requirements", []):
                    gate.setdefault("requirements", []).append(r)
            for t in tests:
                if t not in gate.get("tests", []):
                    gate.setdefault("tests", []).append(t)
            suffix = "," if had_comma else ""
            lines[i] = f'    "{gate_id}": ' + json.dumps(gate, ensure_ascii=False) + suffix
            return "\n".join(lines) + _trailing_newline(text), False

    entry = {
        "description": description,
        "requirements": list(requirements),
        "tests": list(tests),
    }
    gate_line = f'    "{gate_id}": ' + json.dumps(entry, ensure_ascii=False)
    start = None
    for i, line in enumerate(lines):
        if '"release_gates"' in line:
            start = i
            break
    if start is None:
        raise ValueError("release_gates block not found in manifest")
    last = None
    for i in range(start + 1, len(lines)):
        if re.match(r'^\s*"G\d+":', lines[i]):
            last = i
        elif lines[i].strip() in ("}", "},"):
            break
    if last is not None and not lines[last].rstrip().endswith(","):
        lines[last] = lines[last].rstrip() + ","
    insert_at = (last + 1) if last is not None else start + 1
    lines.insert(insert_at, gate_line)
    return "\n".join(lines) + _trailing_newline(text), True


# --------------------------------------------------------------------------- #
# Append-only requirements.md editing
# --------------------------------------------------------------------------- #
def _append_requirement_row(md_text: str, section: str, row: str) -> str:
    """Append *row* to the table under ``### <section>``, creating it if needed."""
    lines = md_text.splitlines()
    idx = None
    for i, line in enumerate(lines):
        if line.strip() == f"### {section}":
            idx = i
            break
    if idx is None:
        # New section: insert before "## Supported v1 deployment profile".
        anchor = None
        for i, line in enumerate(lines):
            if line.strip().startswith("## Supported v1 deployment profile"):
                anchor = i
                break
        block = [
            f"### {section}",
            "",
            "| ID | Requirement | Acceptance outcome |",
            "|---|---|---|",
            row,
            "",
        ]
        if anchor is None:
            lines.extend(block)
        else:
            lines[anchor:anchor] = block
        return "\n".join(lines) + _trailing_newline(md_text)

    j = idx + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines) or not lines[j].strip().startswith("| ID |"):
        # Section exists but has no table yet: create one right after the heading.
        block = ["", "| ID | Requirement | Acceptance outcome |", "|---|---|---|", row]
        lines[j:j] = block
        return "\n".join(lines) + _trailing_newline(md_text)

    k = j
    while k < len(lines) and lines[k].strip().startswith("|"):
        k += 1
    lines[k:k] = [row]
    return "\n".join(lines) + _trailing_newline(md_text)


# --------------------------------------------------------------------------- #
# Public mutation API
# --------------------------------------------------------------------------- #
def append_requirement(
    root: Path,
    requirement_id: str,
    text: str,
    acceptance: str,
    work_packages: List[str],
    test_ids: List[str],
    section: str,
    gate: Optional[str] = None,
    gate_desc: Optional[str] = None,
) -> dict:
    """Append a new requirement to both contract files (append-only)."""
    if not REQ_ID_RE.match(requirement_id):
        raise ValueError(
            f"invalid requirement id {requirement_id!r} (expected NR-<AREA>-NNN)"
        )
    if not text or not acceptance:
        raise ValueError("requirement text and acceptance outcome are required")
    if not work_packages:
        raise ValueError("at least one work package is required")
    if not test_ids:
        raise ValueError("at least one release test is required")
    for t in test_ids:
        if not TEST_ID_RE.match(t):
            raise ValueError(f"invalid release test id {t!r} (expected T-<AREA>-NNN)")

    manifest_path = root / MANIFEST_RELPATH
    md_path = root / REQUIREMENTS_RELPATH
    manifest_text = manifest_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    if f'"{requirement_id}"' in manifest_text:
        raise ValueError(
            f"{requirement_id} already exists in the manifest "
            "(append-only: add a new requirement id instead of editing)"
        )
    if requirement_id in parse_requirements_md(md_path):
        raise ValueError(f"{requirement_id} already exists in docs/requirements.md")

    entry = {
        "requirement_id": requirement_id,
        "primary_work_packages": list(work_packages),
        "primary_release_tests": list(test_ids),
        "must": True,
    }
    new_manifest_text = _append_requirement_entry(manifest_text, entry)

    gates_touched = []
    if gate:
        new_manifest_text, created = _upsert_gate(
            new_manifest_text,
            gate,
            description=gate_desc or f"Gate {gate}",
            requirements=[requirement_id],
            tests=list(test_ids),
        )
        gates_touched.append(f"{gate} ({'created' if created else 'extended'})")

    row = f"| `{requirement_id}` | {text} | {acceptance} |"
    new_md_text = _append_requirement_row(md_text, section, row)

    json.loads(new_manifest_text)  # must stay valid JSON
    manifest_path.write_text(new_manifest_text, encoding="utf-8")
    md_path.write_text(new_md_text, encoding="utf-8")
    return {
        "requirement_id": requirement_id,
        "work_packages": ", ".join(work_packages),
        "release_tests": ", ".join(test_ids),
        "section": section,
        "gates": ", ".join(gates_touched) if gates_touched else "(none)",
    }


def append_release_test(
    root: Path,
    requirement_id: str,
    test_id: str,
    gate: Optional[str] = None,
) -> dict:
    """Append a release test to an existing requirement (append-only)."""
    if not REQ_ID_RE.match(requirement_id):
        raise ValueError(
            f"invalid requirement id {requirement_id!r} (expected NR-<AREA>-NNN)"
        )
    if not TEST_ID_RE.match(test_id):
        raise ValueError(f"invalid release test id {test_id!r} (expected T-<AREA>-NNN)")

    manifest_path = root / MANIFEST_RELPATH
    text = manifest_path.read_text(encoding="utf-8")
    req_key = f'"requirement_id": "{requirement_id}"'
    lines = text.splitlines()
    found = False
    for i, line in enumerate(lines):
        if req_key in line:
            # Entry lines are array members and may carry a trailing comma
            # (only the final element omits it): strip it for parsing and
            # preserve it on write-back.
            stripped = line.strip()
            had_comma = stripped.endswith(",")
            entry = json.loads(stripped.rstrip(","))
            if test_id not in entry["primary_release_tests"]:
                entry["primary_release_tests"].append(test_id)
                suffix = "," if had_comma else ""
                lines[i] = "    " + json.dumps(entry, ensure_ascii=False) + suffix
            found = True
            break
    if not found:
        raise ValueError(f"{requirement_id} not found in the manifest")
    new_text = "\n".join(lines) + _trailing_newline(text)
    if gate:
        new_text, _ = _upsert_gate(
            new_text, gate,
            description=f"Gate {gate}",
            requirements=[requirement_id],
            tests=[test_id],
        )
    json.loads(new_text)
    manifest_path.write_text(new_text, encoding="utf-8")
    return {"requirement_id": requirement_id, "test_id": test_id, "gate": gate or "(none)"}


# --------------------------------------------------------------------------- #
# Evidence recording (pure-Python mirror of `xtask evidence record`)
# --------------------------------------------------------------------------- #
def _rfc3339_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_revision(cwd: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=15,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


ENVELOPE_STATUSES = (
    "observed_pass", "observed_fail", "accepted",
    "claimed", "inferred", "contradicted", "rejected",
)


def write_envelope(
    root: Path,
    work_package_id: str,
    test_id: str,
    command: str,
    requirement_ids: List[str],
    status: str,
    result_artifact_sha256: str,
    logs_artifact_sha256: str,
    started_at: str,
    finished_at: str,
    profile: str = DEFAULT_PROFILE,
    runner: str = DEFAULT_RUNNER,
    verifier: Optional[str] = None,
    evidence_dir: str = "evidence",
    artifact_digests: Optional[dict] = None,
    exceptions: Optional[List[str]] = None,
    notes: str = "",
) -> Path:
    """Write an evidence envelope for an already-executed command.

    Pure writer: the caller is responsible for having run the command and for
    computing the artifact/log digests. Uses the exact
    ``noerelay_core::evidence::EvidenceEnvelope`` schema (snake_case fields,
    ``observed_pass``/``observed_fail`` status) so ``xtask evidence
    validate/coverage/gate`` and the Python coverage report both accept it.
    Written to ``<root>/<evidence_dir>/<work_package_id>/<test_id>.json``.
    """
    if not TEST_ID_RE.match(test_id):
        raise ValueError(f"invalid release test id {test_id!r} (expected T-<AREA>-NNN)")
    if status not in ENVELOPE_STATUSES:
        raise ValueError(f"invalid envelope status {status!r} (expected one of {ENVELOPE_STATUSES})")
    envelope = {
        "evidence_version": "1.0.0",
        "evidence_id": str(uuid.uuid4()),
        "work_package_id": work_package_id,
        "requirement_ids": list(requirement_ids),
        "test_ids": [test_id],
        "status": status,
        "source_revision": _git_revision(root),
        "artifact_digests": dict(artifact_digests or {}),
        "environment_profile": profile,
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "runner_identity": runner,
        "result_artifact_sha256": result_artifact_sha256,
        "logs_artifact_sha256": logs_artifact_sha256,
        "exceptions": list(exceptions or []),
        "notes": notes,
    }
    if verifier:
        envelope["independent_verifier_identity"] = verifier
    out_dir = root / evidence_dir / work_package_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{test_id}.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(envelope, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return out_path


def record_evidence(
    root: Path,
    work_package_id: str,
    test_id: str,
    command: str,
    requirement_ids: List[str],
    profile: str = DEFAULT_PROFILE,
    runner: str = DEFAULT_RUNNER,
    verifier: Optional[str] = None,
    evidence_dir: str = "evidence",
) -> Path:
    """Run *command* and write an evidence envelope for *test_id*.

    The command's combined stdout+stderr is hashed as both the result and the
    logs digest (stand-in for a separate result artifact). Harnesses that
    produce real artifacts should use :func:`write_envelope` directly.
    """
    started = _rfc3339_now()
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=root)
    finished = _rfc3339_now()
    combined = f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
    logs_hash = _sha256_text(combined)
    success = proc.returncode == 0
    return write_envelope(
        root,
        work_package_id=work_package_id,
        test_id=test_id,
        command=command,
        requirement_ids=requirement_ids,
        status="observed_pass" if success else "observed_fail",
        result_artifact_sha256=logs_hash,
        logs_artifact_sha256=logs_hash,
        started_at=started,
        finished_at=finished,
        profile=profile,
        runner=runner,
        verifier=verifier,
        evidence_dir=evidence_dir,
        exceptions=[] if success else [f"command exited with code {proc.returncode}"],
    )


def regenerate_features(root: Path) -> int:
    """Re-run the spec-kit feature generator from the manifest."""
    script = root / GENERATOR_RELPATH
    if not script.is_file():
        print(f"ERROR: generator not found at {script}", file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(script)], cwd=root)


# --------------------------------------------------------------------------- #
# CLI command handlers (invoked from noerelay.cli `req ...`)
# --------------------------------------------------------------------------- #
def _root_from_args(args) -> Path:
    root_arg = getattr(args, "root", None)
    return find_repo_root(Path(root_arg) if root_arg else None)


def _print_problems(problems: List[str], verbose: bool = False) -> None:
    """Print evidence-scan problems: one summary line by default, per-file detail with verbose."""
    if not problems:
        return
    if not verbose:
        print(
            f"  note: {len(problems)} non-envelope JSON file(s) under evidence/ skipped "
            "(use --verbose to list)",
            file=sys.stderr,
        )
        return
    for p in problems:
        print(f"  warning: {p}", file=sys.stderr)


def cmd_req_list(args) -> int:
    root = _root_from_args(args)
    report = coverage_report(root)
    manifest = load_manifest(root)
    print(f"=== Requirements ({report['total']}) ===")
    for rid, e in report["entries"].items():
        print(
            f"  [{e['status']:<8}] {rid}  "
            f"WPs: {', '.join(e['work_packages'])}  Tests: {', '.join(e['tests'])}"
        )
    print(
        f"Covered: {report['covered']}  Partial: {report['partial']}  "
        f"Missing: {report['missing']}  Result: {'PASS' if report['passed'] else 'FAIL'}"
    )
    gates = sorted(manifest.get("release_gates", {}).keys())
    print(f"Gates: {', '.join(gates)}")
    _print_problems(report["problems"], getattr(args, "verbose", False))
    return 0


def cmd_req_show(args) -> int:
    root = _root_from_args(args)
    rid = args.requirement_id
    md = parse_requirements_md(root / REQUIREMENTS_RELPATH)
    manifest = load_manifest(root)
    entry = next(
        (r for r in manifest.get("requirements", []) if r["requirement_id"] == rid), None
    )
    if entry is None and rid not in md:
        print(f"ERROR: unknown requirement {rid}", file=sys.stderr)
        return 1
    print(f"### {rid}")
    if rid in md:
        print(f"Requirement:  {md[rid]['text']}")
        print(f"Acceptance:   {md[rid]['acceptance']}")
    if entry is not None:
        print(f"Work packages:  {', '.join(entry.get('primary_work_packages', []))}")
        print(f"Release tests:  {', '.join(entry.get('primary_release_tests', []))}")
        print(f"MUST:           {entry.get('must', True)}")
        for gid, gate in sorted(manifest.get("release_gates", {}).items()):
            if rid in gate.get("requirements", []):
                print(f"Gate:           {gid} — {gate.get('description', '')}")
    envelopes, _ = load_envelopes(root / "evidence")
    evs = [e for e in envelopes if rid in e.get("requirement_ids", [])]
    if evs:
        print("Evidence:")
        for e in evs:
            mark = "ready" if is_release_ready(e) else "not-ready"
            print(
                f"  - {e.get('evidence_id', '?')} [{e.get('status', '?')}/{mark}] "
                f"WP={e.get('work_package_id', '?')} tests={', '.join(e.get('test_ids', []))}"
            )
    else:
        print("Evidence:       (none recorded)")
    return 0


def cmd_req_tests(args) -> int:
    root = _root_from_args(args)
    manifest = load_manifest(root)
    envelopes, _ = load_envelopes(root / "evidence")
    test_reqs: "OrderedDict[str, list]" = OrderedDict()
    for req in manifest.get("requirements", []):
        for t in req.get("primary_release_tests", []):
            test_reqs.setdefault(t, []).append(req["requirement_id"])
    ready_tests = set()
    for env in envelopes:
        if is_release_ready(env):
            ready_tests.update(env.get("test_ids", []))
    print(f"=== Release tests ({len(test_reqs)}) ===")
    for t, reqs in test_reqs.items():
        mark = "EVIDENCE   " if t in ready_tests else "no-evidence"
        print(f"  [{mark}] {t}  <- {', '.join(reqs)}")
    return 0


def cmd_req_add(args) -> int:
    root = _root_from_args(args)
    packages = [p.strip() for p in (args.packages or "").split(",") if p.strip()]
    tests = [t.strip() for t in (args.tests or "").split(",") if t.strip()]
    try:
        summary = append_requirement(
            root,
            requirement_id=args.requirement_id,
            text=args.text,
            acceptance=args.acceptance,
            work_packages=packages,
            test_ids=tests,
            section=args.section or "Phase 2 additions",
            gate=args.gate,
            gate_desc=args.gate_desc,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Appended requirement:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("Next: run `noerelay req regenerate` to refresh .specify/features/.")
    return 0


def cmd_req_test(args) -> int:
    root = _root_from_args(args)
    try:
        summary = append_release_test(
            root, args.requirement_id, args.test_id, gate=args.gate
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Appended release test:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return 0


def cmd_req_coverage(args) -> int:
    root = _root_from_args(args)
    report = coverage_report(root)
    print("=== Requirement Coverage Report ===")
    print(f"Total requirements: {report['total']}")
    print(f"  Covered:  {report['covered']}")
    print(f"  Partial:  {report['partial']}")
    print(f"  Missing:  {report['missing']}")
    print(f"Result: {'PASS' if report['passed'] else 'FAIL'}")
    _print_problems(report["problems"], getattr(args, "verbose", False))
    if getattr(args, "verbose", False):
        print()
        for rid, e in report["entries"].items():
            print(
                f"  [{e['status']}] {rid} -> WPs: {e['work_packages']} | "
                f"Tests: {e['tests']} | Evidence: {e['evidence']}"
            )
    return 1 if (report["passed"] is False and getattr(args, "strict", False)) else 0


def cmd_req_gate(args) -> int:
    root = _root_from_args(args)
    try:
        report = gate_report(root, args.gate_id)
    except KeyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    verdict = "PASS" if report["passed"] else "FAIL"
    print(f"Gate {report['gate_id']} ({report['description']}) : {verdict}")
    if report["missing"]:
        for rid in report["missing"]:
            print(f"  Gate {report['gate_id']}: requirement {rid} NOT covered")
    return 1 if (not report["passed"] and getattr(args, "strict", False)) else 0


def cmd_req_record(args) -> int:
    root = _root_from_args(args)
    reqs = [r.strip() for r in (args.requirements or "").split(",") if r.strip()]
    if not reqs:
        print("ERROR: --requirements is required", file=sys.stderr)
        return 1
    try:
        path = record_evidence(
            root,
            work_package_id=args.work_package_id,
            test_id=args.test_id,
            command=getattr(args, "record_command", None) or args.command,
            requirement_ids=reqs,
            profile=args.profile,
            runner=args.runner,
            verifier=args.verifier,
            evidence_dir=args.evidence_dir,
        )
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    with open(path, "r", encoding="utf-8") as f:
        env = json.load(f)
    print(f"Evidence recorded to {path}")
    print(f"  status:   {env['status']}")
    print(f"  revision: {env['source_revision'] or '(no git revision)'}")
    return 0


def cmd_req_regenerate(args) -> int:
    root = _root_from_args(args)
    return regenerate_features(root)
