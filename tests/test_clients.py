import json
from pathlib import Path
import sys
import tomllib

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from noerelay import clients


@pytest.fixture
def config():
    return {'base_url': 'http://127.0.0.1:8080', 'api_key': 'secret-test-only', 'model': clients.MODEL}


def test_opencode_all_models_and_mcp_stay_on_gateway(config):
    data = clients.profile('opencode', config)
    assert data['model'] == data['small_model'] == 'noerelay/axiovex-agni-raw'
    assert data['enabled_providers'] == ['noerelay']
    assert data['provider']['noerelay']['options']['baseURL'].endswith(':8080/v1')
    assert config['api_key'] not in json.dumps(data)
    assert data['mcp']['noerelay']['command'][1:] == ['-m', 'noerelay.mcp_stdio']


def test_codex_valid_toml_stateless_local_defaults(config):
    text = clients.profile('codex', config)
    data = tomllib.loads(text)
    assert data['model_provider'] == 'noerelay'
    assert data['model_providers']['noerelay']['wire_api'] == 'responses'
    assert data['model_supports_reasoning_summaries'] is False
    assert data['web_search'] == 'disabled'
    assert data['mcp_servers']['noerelay']['required'] is True
    assert 'NOERELAY_API_KEY' in data['mcp_servers']['noerelay']['env_vars']
    assert data['model_context_window'] == 131072
    assert config['api_key'] not in text


def test_setup_idempotent_preserves_unrelated_settings(tmp_path, config):
    unrelated = tmp_path / 'config.json'
    unrelated.write_text('{"user":true}')
    for client in clients.CLIENTS:
        path = clients.setup(client, tmp_path, config)
        first = path.read_bytes()
        assert clients.setup(client, tmp_path, config).read_bytes() == first
    assert unrelated.read_text() == '{"user":true}'
    zoo = json.loads((tmp_path / 'zoo/settings.json').read_text())
    assert zoo['providerProfiles']['apiConfigs']['NoeRelay']['openAiModelInfo']['contextWindow'] == 131072
    assert zoo['globalSettings']['autoApprovalEnabled'] is False


@pytest.mark.parametrize('client', ['opencode', 'codex'])
def test_launch_uses_environment_and_preserves_argument_boundaries(tmp_path, config, monkeypatch, client):
    monkeypatch.setattr(clients, 'executable', lambda _: ['client.exe'])
    cmd, env = clients.launch(client, tmp_path, config, ['run', 'a prompt with spaces'])
    assert cmd == ['client.exe', 'run', 'a prompt with spaces']
    assert config['api_key'] not in ' '.join(cmd)
    assert env['NOERELAY_API_KEY'] == config['api_key']
    assert env['NOERELAY_BASE_URL'] == config['base_url']


def test_explicit_connection_never_inspects_local_docker(monkeypatch):
    monkeypatch.setenv('NOERELAY_API_KEY', 'explicit')
    monkeypatch.setenv('NOERELAY_BASE_URL', 'https://example.test/v1/')
    monkeypatch.setattr(clients.subprocess, 'check_output', lambda *a, **k: pytest.fail('unexpected docker access'))
    assert clients.connection()['base_url'] == 'https://example.test'
    assert clients.connection()['api_key'] == 'explicit'


def test_url_embedded_credentials_rejected(monkeypatch):
    monkeypatch.setenv('NOERELAY_BASE_URL', 'https://user:pass@example.test')
    with pytest.raises(ValueError):
        clients.connection()


def test_wsl_credential_capture_strips_crlf(monkeypatch):
    monkeypatch.setenv('NOERELAY_API_KEY', 'test-key\r\n')
    assert clients.connection()['api_key'] == 'test-key'


def test_zoo_launcher_scopes_settings_to_managed_workspace(tmp_path, config, monkeypatch):
    monkeypatch.setattr(clients.shutil, 'which', lambda _: 'code')
    workspace = tmp_path / 'project with spaces'
    workspace.mkdir()
    cmd, env = clients.launch('zoo', tmp_path / 'profiles', config, cwd=workspace)
    generated = json.loads(Path(cmd[1]).read_text())
    assert generated['folders'] == [{'path': str(workspace)}]
    assert generated['settings']['zoo-code.autoImportSettingsPath'].endswith('settings.json')
    assert not list(workspace.iterdir())
    assert config['api_key'] not in ' '.join(cmd)


def test_codex_smoke_guard_permits_only_exact_fixture_read():
    from noerelay.client_test_mcp import allowed
    command = 'cat /workspace/.noerelay/clients/tests/codex-123456789abc/nonce.txt'
    assert allowed({'name':'noerelay_workspace_execute', 'arguments':{'command':command}}, command)
    assert not allowed({'name':'noerelay_workspace_execute', 'arguments':{'command':command + '; touch other'}}, command)
    assert not allowed({'name':'different', 'arguments':{'command':command}}, command)
