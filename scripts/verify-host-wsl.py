"""Verify identical API settings from Windows and Ubuntu WSL2."""
import json
import subprocess
import sys
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
settings = runpy.run_path(str(ROOT / 'deploy/host/client-env.py'))['settings']()
probe = ROOT / 'scripts/verify-client-access.py'
wsl_path = '/mnt/' + probe.drive[0].lower() + probe.as_posix()[2:]
results = []
for name, command in [('windows', [sys.executable, str(probe)]),
                      ('wsl2-ubuntu', ['wsl', '-d', 'Ubuntu-24.04', '--', 'python3', wsl_path])]:
    result = subprocess.run(command, input=json.dumps(settings), text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(name + ': ' + result.stderr)
    observation = json.loads(result.stdout)
    observation['client'] = name
    results.append(observation)
path = ROOT / 'evidence/local-recovery/host-wsl-access.json'
path.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results))
