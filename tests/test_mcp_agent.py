import io
import json
import pytest
from noerelay import mcp_agent as agent
from noerelay import sdd


class Reply(io.BytesIO):
    headers = {'x-noerelay-run-id': 'observed-run'}


def install(monkeypatch, messages):
    class Docker:
        def __init__(self, token):
            pass
        def call(self, method, params=None):
            assert method == 'tools/list'
            return {'tools': []}
    monkeypatch.setattr(agent, 'DockerMCP', Docker)
    iterator = iter(messages)
    def complete(request, **kwargs):
        payload = json.loads(request.data)
        assert all('provider_specific_fields' not in item for item in payload['messages'])
        return Reply(json.dumps({'choices': [{'message': next(iterator)}]}).encode())
    monkeypatch.setattr(agent.urllib.request, 'urlopen', complete)


def test_agent_runs_workspace_tool_and_keeps_verification_separate(monkeypatch, tmp_path):
    install(monkeypatch, [
        {'role': 'assistant', 'provider_specific_fields': {'refusal': None}, 'tool_calls': [{'id': 'one', 'function': {
            'name': 'noerelay_workspace_execute', 'arguments': '{"command":"python --version"}'}}]},
        {'role': 'assistant', 'content': 'Done'}])
    calls = []
    monkeypatch.setattr(agent, 'workspace_call', lambda *args: calls.append(args) or {'exit_code': 0})
    monkeypatch.setattr(sdd, 'audit', lambda *a: {'feature': '.specify/features/test'})
    monkeypatch.setattr(sdd, 'assess_feature', lambda *a: {'verification_status': 'requires_evidence'})
    result = agent.agent_run({'prompt': 'Inspect Python'}, 'mcp', 'gateway', terminal_token='terminal', root=tmp_path)
    assert calls[0][0] == 'noerelay_workspace_execute'
    assert result['status'] == 'responded'
    assert result['sdd']['verification_status'] == 'requires_evidence'
    assert result['steps'][0]['tools'] == ['noerelay_workspace_execute']


def test_unknown_tool_never_executes_and_step_budget_stops(monkeypatch, tmp_path):
    install(monkeypatch, [{'role': 'assistant', 'tool_calls': [{'id': 'one', 'function': {
        'name': 'unconfigured_tool', 'arguments': '{}'}}]}])
    result = agent.agent_run({'prompt': 'Do work', 'max_steps': 1}, 'mcp', 'gateway', root=tmp_path)
    assert result['status'] == 'step_limit'


def test_observed_workspace_failure_escalates_next_routed_call(monkeypatch, tmp_path):
    install(monkeypatch, [
        {'role': 'assistant', 'tool_calls': [{'id': 'one', 'function': {
            'name': 'noerelay_workspace_execute', 'arguments': '{"command":"pytest"}'}}]},
        {'role': 'assistant', 'content': 'Investigate the failure'}])
    original = agent.urllib.request.urlopen
    capabilities = []
    def complete(request, **kwargs):
        capabilities.append(dict(request.header_items()).get('X-noerelay-capability'))
        return original(request, **kwargs)
    monkeypatch.setattr(agent.urllib.request, 'urlopen', complete)
    monkeypatch.setattr(agent, 'workspace_call', lambda *args: {'result': {'exit_code': 1}})
    monkeypatch.setattr(sdd, 'audit', lambda *a: {})
    result = agent.agent_run({'prompt': 'Run tests'}, 'mcp', 'gateway', terminal_token='terminal', root=tmp_path)
    assert capabilities == [None, 'reasoning']
    assert result['steps'][0]['escalation'] == 'observed_tool_failure'


@pytest.mark.parametrize('steps', [0, 9, '4'])
def test_invalid_agent_budget_rejected(steps):
    with pytest.raises(ValueError, match='max_steps'):
        agent.agent_run({'prompt': 'Do work', 'max_steps': steps}, '', '')
