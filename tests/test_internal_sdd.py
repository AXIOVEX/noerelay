import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.sdd import prepare


def test_missing_aee_fails_instead_of_claiming_initialization(tmp_path):
    with pytest.raises(RuntimeError, match='AEE extension is required'):
        prepare(tmp_path, 'test', [{'role': 'user', 'content': 'Build a thing'}])


def test_sdd_records_unsupported_claims_and_preserves_agent_edits(tmp_path, monkeypatch):
    runner = tmp_path / '.specify/extensions/aee/scripts/python/run_aee.py'
    runner.parent.mkdir(parents=True)
    runner.write_text('')
    calls = []
    def assess(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, '{"outcome":"gather_evidence"}', '')
    monkeypatch.setattr(subprocess, 'run', assess)
    request = [{'role': 'user', 'content': 'Add local inference'}]
    first = prepare(tmp_path, '../../outside', request)
    feature = tmp_path / first['feature']
    (feature / 'plan.md').write_text('Agent architecture decision')
    second = prepare(tmp_path, '../../outside', request)
    assert first == second
    assert (feature / 'plan.md').read_text() == 'Agent architecture decision'
    assert (feature / 'spec.md').read_text().count('## REQ-') == 1
    claim = json.loads(next(feature.glob('claims-*.json')).read_text())['claims'][0]
    assert claim['status'] == 'unsupported' and claim['evidence'] == []
    assert len(calls) == 2
    assert feature.resolve().is_relative_to(tmp_path.resolve())


def test_rtk_transport_preserves_tool_protocol_and_native_protected_nodes():
    spec = importlib.util.spec_from_file_location('local_plane_test', ROOT / 'deploy/host/local-model-plane.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tools = {'messages': [{'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call1'}]},
                          {'role': 'tool', 'tool_call_id': 'call1', 'content': 'result'}]}
    same, meta = module.compact_request(tools)
    assert same == tools and meta['skipped']
    body = {'messages': [{'role': 'system', 'content': 'REQUIREMENT: preserve this decision'},
                         {'role': 'assistant', 'content': 'log output ' * 700},
                         {'role': 'assistant', 'content': 'log output ' * 700},
                         {'role': 'user', 'content': 'Active requirement: keep this'}]}
    compacted, meta = module.compact_request(body)
    assert compacted['messages'][0] == body['messages'][0]
    assert compacted['messages'][-1] == body['messages'][-1]
    assert meta['tokens_saved'] > 0
