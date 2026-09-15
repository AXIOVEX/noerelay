"""Automatic, local spec-kit/AEE lifecycle for agent work.

Artifacts record requests and observations, never infer test success from prose.
The agent edits the generated plan/tasks and attaches actual test evidence.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import re
import sys
from pathlib import Path


def prepare(root: Path, project: str, messages: list[dict]) -> dict:
    root = root.resolve()
    runner = root / '.specify/extensions/aee/scripts/python/run_aee.py'
    if not runner.is_file():
        raise RuntimeError('Spec-kit AEE extension is required for the internal SDD lifecycle')
    key = hashlib.sha256(project.encode()).hexdigest()[:16]
    feature = root / '.specify/features' / ('runtime-' + key)
    if not feature.resolve().is_relative_to(root):
        raise RuntimeError('Spec-kit feature escapes the project root')
    feature.mkdir(parents=True, exist_ok=True)
    user = next((m.get('content', '') for m in reversed(messages) if m.get('role') == 'user'), '')
    text = user if isinstance(user, str) else json.dumps(user, ensure_ascii=False)
    request_id = hashlib.sha256(text.encode()).hexdigest()[:16]
    claim_id = 'REQ-' + request_id.upper()
    spec = feature / 'spec.md'
    if not spec.exists():
        spec.write_text('# Agent-managed specification\n\nRequests are unverified requirements until tested.\n', encoding='utf-8')
    content = spec.read_text(encoding='utf-8')
    if claim_id not in content:
        with spec.open('a', encoding='utf-8') as out:
            out.write(f'\n## {claim_id}\n\n{text}\n\n- Status: requested; acceptance criteria and falsification tests require agent refinement.\n')
    defaults = {
        'plan.md': '# Architecture and plan\n\nThe agent must inspect the existing architecture, document boundaries, dependencies, alternatives, and the chosen implementation before editing.\n',
        'tasks.md': '# Agent-managed tasks\n\n- [ ] Refine atomic requirements and acceptance tests in spec.md.\n- [ ] Record architecture decisions in plan.md.\n- [ ] Implement the requested change.\n- [ ] Run relevant tests; record exact commands, exit codes, revision, and artifact hashes.\n- [ ] Run AEE and resolve or disclose unsupported claims before reporting completion.\n',
    }
    for name, value in defaults.items():
        path = feature / name
        if not path.exists():
            path.write_text(value, encoding='utf-8')
    claims = feature / ('claims-' + request_id + '.json')
    if not claims.exists():
        claims.write_text(json.dumps({'schema_version': '1.0', 'claims': [{
            'id': claim_id, 'text': text or 'No explicit user request supplied',
            'kind': 'requirement', 'status': 'unsupported',
            'boundary': ['Current local project and requested task'],
            'depends_on': [], 'conflicts_with': [], 'falsification_tests': [],
            'source_ref': str(spec.relative_to(root)), 'uncertainty': 'high', 'evidence': [],
        }]}, indent=2), encoding='utf-8')
    result = subprocess.run([sys.executable, str(runner), '--project-root', str(root),
                             'assess', '--input', str(claims.relative_to(root)),
                             '--phase', 'after_specify'], capture_output=True, text=True, timeout=60)
    # The adapter returns assessment/gate outcomes, including unsupported claims.
    if result.returncode not in (0, 1):
        raise RuntimeError('AEE assessment failed: ' + result.stderr[-1000:] + result.stdout[-1000:])
    state = {'project': project, 'feature': feature.relative_to(root).as_posix(),
            'claim_id': claim_id, 'aee_exit_code': result.returncode,
            'assessment': result.stdout.strip(), 'status': 'requires_agent_verification'}
    (feature / 'state.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    return state


def audit(root: Path, project: str):
    key = hashlib.sha256(project.encode()).hexdigest()[:16]
    state = root / '.specify/features' / ('runtime-' + key) / 'state.json'
    return json.loads(state.read_text(encoding='utf-8')) if state.is_file() else {
        'project': project, 'status': 'no_prior_work', 'initialized': False}


def assess_feature(root: Path, feature: str, phase='after_implement'):
    target = (root / feature).resolve()
    if not target.is_relative_to((root / '.specify/features').resolve()):
        raise ValueError('Feature must be within .specify/features')
    if phase not in ('after_specify', 'after_plan', 'after_tasks', 'after_implement'):
        raise ValueError('Unsupported SDD phase')
    runner = root / '.specify/extensions/aee/scripts/python/run_aee.py'
    assessments = []
    for claims in sorted(target.glob('claims-*.json')):
        result = subprocess.run([sys.executable, str(runner), '--project-root', str(root),
                                 'assess', '--input', str(claims.relative_to(root)), '--phase', phase],
                                capture_output=True, text=True, timeout=60)
        if result.returncode not in (0, 1):
            raise RuntimeError('AEE failed: ' + result.stderr[-1000:])
        assessments.append({'exit_code': result.returncode, 'artifacts': result.stdout})
    return {'phase': phase, 'assessments': assessments,
            'verification_status': 'supported' if assessments and all(a['exit_code'] == 0 for a in assessments) else 'requires_evidence'}


def generate_gaps(root: Path, close: str | None = None):
    """Adapt NoeRelay EvidenceEnvelope and Markdown IDs to the AEE gap engine."""
    from aee.gaps import GapEngine
    from .reqtest import load_envelopes, is_release_ready

    class EnvelopeGapEngine(GapEngine):
        _MATRIX_ROW_RE = re.compile(r'\|\s*`?(T-[A-Z0-9]+-\d+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|')

        def _collect_passing_tests(self, evidence_dir):
            envelopes, problems = load_envelopes(evidence_dir)
            if problems:
                raise RuntimeError('Invalid evidence: ' + '; '.join(problems))
            return {test for envelope in envelopes if is_release_ready(envelope)
                    for test in envelope.get('test_ids', [])}

    engine = EnvelopeGapEngine()
    output = root / '.noerelay/GAPS.md'
    register = engine.generate(root / '.noerelay/verification-matrix.md', root / 'evidence')
    if close:
        register = engine.close_gap(register, close)
    output.write_text(register.to_markdown(), encoding='utf-8')
    return register


AGENT_INSTRUCTIONS = '''Manage epistemically driven spec-driven development internally.
Use the attached spec-kit feature: refine atomic requirements and acceptance tests in spec.md;
maintain architecture decisions in plan.md and execution/test tasks in tasks.md.
Refine the claims-*.json files with atomic claims, falsification tests, and observed evidence
references. Use noerelay_sdd_assess to evaluate the feature after each phase.
Use available workspace tools to inspect and edit these artifacts. Run relevant tests and record
commands, exit codes, revision, and evidence hashes. Run the installed spec-kit AEE assessment
after specification, planning, and implementation; inspect unsupported claims and contradictions.
Do not ask the user to manage spec-kit, AEE, requirement IDs, or test bookkeeping.
Never label generated prose, scaffolding, or an AEE score as proof of implementation correctness.
If workspace tools are unavailable, explain the execution limitation and leave tasks pending.
Routine inference uses gpt-oss-20b-Q5_K_M, coding uses qwen3.6-35b-a3b,
and escalation uses qwen3.8-27b through the router.
'''
