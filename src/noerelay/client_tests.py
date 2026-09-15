"""Real installed-client tests. Synthetic workspaces, no user project changes."""
from __future__ import annotations
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from .clients import launch, setup, executable


def _run(cmd, env, cwd, timeout=300):
    kwargs = {}
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        kwargs['startupinfo'] = startup
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=timeout, stdin=subprocess.DEVNULL, **kwargs)


def verify(selected, home, config):
    report = {'clients': {}, 'scope': 'Installed clients; synthetic file read and tool-result round trip'}
    for client in selected:
        started = time.monotonic()
        # Unique workspace prevents stale files/transcripts from satisfying a rerun.
        test_root = (Path(__file__).resolve().parents[2] / '.noerelay/clients/tests' if client == 'codex' else home / 'tests')
        work = test_root / (client + '-' + secrets.token_hex(6))
        work.mkdir(parents=True)
        nonce = 'NOERELAY_' + secrets.token_hex(12)
        (work / 'nonce.txt').write_text(nonce, encoding='utf-8')
        try:
            if client == 'zoo':
                entry, stdout, stderr = _zoo(home, config, work)
            else:
                prompt = 'Read nonce.txt in the current directory using a file or shell tool. Reply with its exact contents. Do not change files or use other directories.'
                if client == 'codex':
                    root = Path(__file__).resolve().parents[2]
                    relative = work.resolve().relative_to(root)
                    target = '/workspace/' + relative.as_posix() + '/nonce.txt'
                    prompt = ('Use the NoeRelay MCP noerelay_workspace_execute tool to run '
                        'cat ' + target + '. The file is in the Docker workspace, not the host shell. '
                        'Reply with its exact contents. Do not change files. If tools are still loading, discover the NoeRelay MCP tools first.')
                extra = (['run', '--format', 'json', prompt] if client == 'opencode' else
                    ['exec', '--skip-git-repo-check', '--ephemeral', '--json', prompt])
                cmd, env = launch(client, home, config, extra)
                if client == 'codex':
                    # Approve only a fixture-limited MCP shim in an isolated test profile.
                    fixture_home = work / 'profile'
                    settings = setup('codex', fixture_home, config)
                    settings.write_text(settings.read_text().replace('"noerelay.mcp_stdio"', '"noerelay.client_test_mcp"').replace('"PYTHONPATH"]', '"PYTHONPATH", "NOERELAY_TEST_READ_COMMAND"]') +
                        '\n[mcp_servers.noerelay.tools.noerelay_workspace_execute]\napproval_mode = "approve"\n', encoding='utf-8')
                    env['CODEX_HOME'] = str(settings.parent)
                    env['NOERELAY_TEST_READ_COMMAND'] = 'cat ' + target
                result = _run(cmd, env, work)
                stdout, stderr = result.stdout, result.stderr
                events = []
                for line in stdout.splitlines():
                    try: events.append(json.loads(line))
                    except ValueError: pass
                if client == 'opencode':
                    tool = any(e.get('type') == 'tool_use' and e.get('part', {}).get('state', {}).get('status') == 'completed' for e in events)
                    answer = '\n'.join(e.get('part', {}).get('text', '') for e in events if e.get('type') == 'text')
                else:
                    tool = any(e.get('type') == 'item.completed' and e.get('item', {}).get('type') in ('command_execution', 'mcp_tool_call') and e.get('item', {}).get('status') == 'completed' and not e.get('item', {}).get('error') and e.get('item', {}).get('server') == 'noerelay' for e in events)
                    answer = '\n'.join(e.get('item', {}).get('text', '') for e in events if e.get('type') == 'item.completed')
                version = _run(executable(client) + ['--version'], env, work, 30).stdout.strip()
                entry = {'passed': result.returncode == 0 and tool and nonce in answer,
                    'exit_code': result.returncode, 'tool_completed': tool,
                    'nonce_verified': nonce in answer, 'version': version}
            # Raw client logs are local only and redacted before persistence.
            for name, text in [('stdout.log', stdout), ('stderr.log', stderr)]:
                (work / name).write_text(text.replace(config['api_key'], '[REDACTED]'), encoding='utf-8')
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
            entry = {'passed': False, 'error': str(error).replace(config['api_key'], '[REDACTED]')}
        entry.update(seconds=round(time.monotonic() - started, 2), workspace=str(work))
        report['clients'][client] = entry
        print(f'{client}: {"PASS" if entry["passed"] else "FAIL"}', flush=True)
    (home / 'test-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def _zoo(home, config, work):
    if os.name != 'nt':
        raise RuntimeError('Zoo extension-host runner currently requires Windows VS Code; use protocol tests for WSL separately')
    code = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Microsoft VS Code/Code.exe'
    extensions = sorted((Path.home() / '.vscode/extensions').glob('zoocodeorganization.zoo-code-*'))
    if not code.is_file() or not extensions:
        raise RuntimeError('Install VS Code and Zoo Code before running its real extension-host test')
    settings = setup('zoo', home, config)
    user = work / 'vscode'
    storage = user / 'User/globalStorage/zoocodeorganization.zoo-code'
    (user / 'User').mkdir(parents=True)
    (user / 'User/settings.json').write_text(json.dumps({
        'security.workspace.trust.enabled': False, 'telemetry.telemetryLevel': 'off',
        'update.mode': 'none', 'extensions.autoUpdate': False,
        'zoo-code.autoImportSettingsPath': str(settings),
        'zoo-code.customStoragePath': str(storage),
    }), encoding='utf-8')
    output = work / 'result.json'
    env = {**os.environ, 'NOERELAY_ZOO_SETTINGS': str(settings),
        'NOERELAY_ZOO_RESULT': str(output), 'NOERELAY_ZOO_NONCE': str(work / 'nonce.txt'),
        'NOERELAY_ZOO_STORAGE': str(storage)}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    cmd = [str(code), '--user-data-dir', str(user), '--extensions-dir', str(work / 'extensions'),
        '--extensionDevelopmentPath=' + str(extensions[-1]),
        '--extensionTestsPath=' + str(Path(__file__).with_name('zoo_test.cjs')),
        '--disable-gpu', '--skip-welcome', '--skip-release-notes', str(work)]
    result = _run(cmd, env, work, 300)
    entry = json.loads(output.read_text()) if output.is_file() else {'passed': False, 'error': 'Extension test produced no result'}
    entry['exit_code'] = result.returncode
    entry['passed'] = entry['passed'] and result.returncode == 0
    return entry, result.stdout, result.stderr
