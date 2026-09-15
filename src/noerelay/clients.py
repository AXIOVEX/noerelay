"""Managed coding-client profiles. Credentials stay in child environments.

Profiles live outside the project by default. No client receives a direct model
backend URL: inference and MCP both terminate at NoeRelay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

CLIENTS = ('opencode', 'zoo', 'codex')
MODEL = 'axiovex-agni-raw'


def connection():
    from .cli import load_config
    config = load_config()
    root = Path(__file__).resolve().parents[2]
    # Explicit environment configuration wins, including for remote deployments.
    if not os.environ.get('NOERELAY_API_KEY') and not os.environ.get('NOERELAY_BASE_URL'):
        try:
            container = subprocess.check_output([
                'docker', 'compose', '--project-directory', str(root),
                '--env-file', str(root / '.env.docker'), 'ps', '-q', 'noerelay'],
                text=True, stderr=subprocess.DEVNULL, timeout=15).strip()
            if container:
                info = json.loads(subprocess.check_output(['docker', 'inspect', container],
                    text=True, stderr=subprocess.DEVNULL, timeout=15))[0]
                env = dict(x.split('=', 1) for x in info['Config']['Env'] if '=' in x)
                config['api_key'] = env['NOERELAY_API_KEY']
        except (OSError, subprocess.SubprocessError, KeyError, ValueError):
            pass
    base = config['base_url'].rstrip('/')
    if base.endswith('/v1'):
        base = base[:-3]
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('NOERELAY_BASE_URL must be an HTTP(S) URL without credentials')
    return {'base_url': base, 'api_key': config['api_key'].strip(), 'model': MODEL}


def directory(value=None):
    return Path(value or os.environ.get('NOERELAY_CLIENT_HOME', Path.home() / '.noerelay/clients')).resolve()


def _write(path, content, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if private and path.exists():
        path.chmod(0o600)
    # Managed profiles are separate from user files; atomic replacement is safe.
    temp = path.with_suffix(path.suffix + '.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
        out.write(content)
    temp.replace(path)
    if private:
        path.chmod(0o600)


def executable(client):
    """Resolve Windows npm installations without executing shell-built commands."""
    if os.name != 'nt' and client == 'opencode':
        native = Path(__file__).resolve().parents[2] / '.noerelay/tools/opencode-linux/package/bin/opencode'
        if native.is_file():
            return [str(native)]
    if os.name == 'nt':
        npm = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules'
        if client == 'opencode':
            for variant in ('opencode-windows-x64', 'opencode-windows-x64-baseline'):
                path = npm / 'opencode-ai/node_modules' / variant / 'bin/opencode.exe'
                if path.is_file():
                    return [str(path)]
        if client == 'codex':
            script = npm / '@openai/codex/bin/codex.js'
            node = shutil.which('node') or 'C:/Program Files/nodejs/node.exe'
            if script.is_file() and Path(node).is_file():
                return [node, str(script)]
    found = shutil.which(client)
    if found:
        return [found]
    raise RuntimeError(f'{client} is not installed; run noerelay install {client}')


def profile(client, config):
    base, model = config['base_url'], config.get('model', MODEL)
    mcp = [sys.executable, '-m', 'noerelay.mcp_stdio']
    if client == 'opencode':
        return {'$schema': 'https://opencode.ai/config.json',
            'model': f'noerelay/{model}', 'small_model': f'noerelay/{model}',
            'enabled_providers': ['noerelay'], 'share': 'disabled', 'autoupdate': False,
            'provider': {'noerelay': {'npm': '@ai-sdk/openai-compatible', 'name': 'NoeRelay',
                'options': {'baseURL': base + '/v1', 'apiKey': '{env:NOERELAY_API_KEY}', 'timeout': 600000},
                'models': {model: {'name': 'NoeRelay automatic coding router',
                    'limit': {'context': 131072, 'output': 4096}}}}},
            'mcp': {'noerelay': {'type': 'local', 'command': mcp, 'enabled': True, 'timeout': 180000}},
            'permission': {'external_directory': 'ask'},
        }
    if client == 'codex':
        q = json.dumps
        return '\n'.join([
            f'model = {q(model)}', 'model_provider = "noerelay"',
            'model_context_window = 131072', 'model_auto_compact_token_limit = 98304',
            'model_supports_reasoning_summaries = false', 'web_search = "disabled"',
            'sandbox_mode = "workspace-write"', 'approval_policy = "on-request"',
            '[features]', 'multi_agent = false', 'plugins = false',
            '[model_providers.noerelay]', 'name = "NoeRelay"',
            f'base_url = {q(base + "/v1")}', 'env_key = "NOERELAY_API_KEY"',
            'wire_api = "responses"', 'supports_websockets = false',
            'stream_idle_timeout_ms = 600000',
            '[mcp_servers.noerelay]', f'command = {q(mcp[0])}',
            'args = ["-m", "noerelay.mcp_stdio"]',
            'env_vars = ["NOERELAY_BASE_URL", "NOERELAY_API_KEY", "PYTHONPATH"]',
            'required = true', 'startup_timeout_sec = 180', 'tool_timeout_sec = 180', '',
        ])
    if client == 'zoo':
        return {'providerProfiles': {'currentApiConfigName': 'NoeRelay',
            'apiConfigs': {'NoeRelay': {'apiProvider': 'openai',
                'openAiBaseUrl': base + '/v1', 'openAiApiKey': config['api_key'],
                'openAiModelId': model, 'openAiUseStreaming': True,
                'openAiModelInfo': {'maxTokens': 4096, 'contextWindow': 131072,
                    'supportsImages': False, 'supportsPromptCache': False,
                    'inputPrice': 0, 'outputPrice': 0}}}},
            'globalSettings': {'autoApprovalEnabled': False}}
    raise ValueError('Unknown client: ' + client)


def setup(client, home, config):
    folder = home / client
    data = profile(client, config)
    if client == 'codex':
        catalog = folder / 'models.json'
        _write(catalog, json.dumps({'models': [{
            'slug': config.get('model', MODEL), 'display_name': 'NoeRelay',
            'description': 'Local three-model router', 'default_reasoning_level': None,
            'supported_reasoning_levels': [], 'shell_type': 'unified_exec',
            'visibility': 'list', 'supported_in_api': True, 'priority': 1,
            'base_instructions': 'You are a coding assistant. Use tools to inspect files and verify changes. All inference is routed by NoeRelay. Use available NoeRelay MCP tools when appropriate.',
            'supports_reasoning_summaries': False, 'support_verbosity': False,
            'context_window': 131072, 'max_context_window': 131072,
            'effective_context_window_percent': 95, 'input_modalities': ['text'],
            'experimental_supported_tools': [], 'default_verbosity': None,
            'truncation_policy': {'mode': 'tokens', 'limit': 10000},
        }]}, indent=2))
        data = 'model_catalog_json = ' + json.dumps(str(catalog)) + '\n' + data
    name = {'opencode': 'opencode.json', 'codex': 'config.toml', 'zoo': 'settings.json'}[client]
    path = folder / name
    _write(path, data if isinstance(data, str) else json.dumps(data, indent=2) + '\n', private=client == 'zoo')
    if client == 'zoo':
        mcp_data = {'mcpServers': {'noerelay': {
            'command': sys.executable, 'args': ['-m', 'noerelay.mcp_stdio'],
            'env': {'NOERELAY_BASE_URL': config['base_url'], 'NOERELAY_API_KEY': config['api_key'],
                    'PYTHONPATH': str(Path(__file__).resolve().parents[1])},
            'alwaysAllow': [], 'disabled': False}}}
        _write(folder / 'mcp.json', json.dumps(mcp_data, indent=2), private=True)
        _write(folder / 'storage/settings/mcp_settings.json', json.dumps(mcp_data, indent=2), private=True)
    return path


def launch(client, home, config, extra=(), cwd=None):
    path = setup(client, home, config)
    env = {**os.environ, 'NOERELAY_API_KEY': config['api_key'],
           'NOERELAY_BASE_URL': config['base_url']}
    # Editable source checkout remains importable from any client workspace.
    source = Path(__file__).resolve().parents[1]
    env['PYTHONPATH'] = str(source) + os.pathsep + env.get('PYTHONPATH', '')
    if client == 'opencode':
        env['OPENCODE_CONFIG_CONTENT'] = path.read_text(encoding='utf-8')
        env['OPENCODE_DISABLE_AUTOUPDATE'] = 'true'
        cmd = executable(client)
    elif client == 'codex':
        env['CODEX_HOME'] = str(path.parent)
        cmd = executable(client)
    else:
        workspace = Path(cwd or Path.cwd()).resolve()
        name = hashlib.sha256(str(workspace).encode()).hexdigest()[:12]
        project = path.parent / (name + '.code-workspace')
        _write(project, json.dumps({'folders': [{'path': str(workspace)}], 'settings': {
            'zoo-code.autoImportSettingsPath': str(path),
            'zoo-code.customStoragePath': str(path.parent / 'storage'),
            'zoo-code.apiRequestTimeout': 600}}, indent=2))
        code = shutil.which('code')
        if os.name == 'nt':
            binary = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Microsoft VS Code/Code.exe'
            if binary.is_file(): code = str(binary)
        if not code:
            raise RuntimeError('VS Code is not installed; import the generated Zoo settings manually')
        cmd = [code, str(project)]
    return cmd + list(extra), env


def register(parser):
    sub = parser.add_subparsers(dest='client_action', required=True)
    env = sub.add_parser('env', help='Emit credentials for capture by the current shell')
    env.add_argument('--shell', choices=('bash', 'powershell', 'json'), default='json')
    for action in ('setup', 'status', 'run', 'test'):
        item = sub.add_parser(action)
        item.add_argument('client', choices=(*CLIENTS, 'all') if action != 'run' else CLIENTS)
        item.add_argument('--directory', help='Managed client settings directory')
        if action == 'run':
            item.add_argument('extra', nargs=argparse.REMAINDER)


def main(args):
    config = connection()
    if args.client_action == 'env':
        # Bash capture from Windows must not inject CR into exported credentials.
        if args.shell == 'bash' and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(newline='\n')
        values = {'NOERELAY_BASE_URL': config['base_url'], 'NOERELAY_API_KEY': config['api_key'],
                  'OPENAI_BASE_URL': config['base_url'] + '/v1', 'OPENAI_API_KEY': config['api_key'],
                  'OPENAI_MODEL': config['model']}
        if args.shell == 'json':
            print(json.dumps(values))
        else:
            for key, value in values.items():
                print('export ' + key + '=' + shlex.quote(value) if args.shell == 'bash' else
                      "$env:" + key + " = '" + value.replace("'", "''") + "'")
        return 0
    home = directory(args.directory)
    selected = CLIENTS if args.client == 'all' else (args.client,)
    if args.client_action == 'run':
        extra = args.extra[1:] if args.extra[:1] == ['--'] else args.extra
        cmd, env = launch(args.client, home, config, extra)
        return subprocess.run(cmd, env=env).returncode
    if args.client_action == 'test':
        from .client_tests import verify
        report = verify(selected, home, config)
        print(json.dumps(report, indent=2))
        return 0 if all(x['passed'] for x in report['clients'].values()) else 1
    failed = False
    for client in selected:
        if args.client_action == 'setup':
            path = setup(client, home, config)
            print(f'{client}: {path}')
            if client == 'zoo':
                print('Run: noerelay client run zoo (opens a managed workspace with automatic import and MCP).')
        else:
            try:
                if client == 'zoo':
                    extension_root = Path.home() / ('.vscode/extensions' if os.name == 'nt' else '.vscode-server/extensions')
                    installed = sorted(extension_root.glob('zoocodeorganization.zoo-code-*'))
                    if not installed:
                        raise RuntimeError('Zoo Code extension is not installed in this environment')
                    command = [str(installed[-1])]
                else:
                    command = executable(client)
                print(f'{client}: ' + ' '.join(command))
            except (RuntimeError, OSError) as error:
                failed = True
                print(str(error))
    return 1 if failed else 0
