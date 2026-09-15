"""Run an explicit local check and retain its logs and evidence envelope."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.reqtest import write_envelope

package, test, requirement, *command = sys.argv[1:]
started = datetime.now(timezone.utc).isoformat()
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
finished = datetime.now(timezone.utc).isoformat()
path = ROOT / 'evidence/local-recovery' / (test + '.log')
path.write_text(result.stdout + '\nSTDERR:\n' + result.stderr, encoding='utf-8')
digest = hashlib.sha256(path.read_bytes()).hexdigest()
sources = ['deploy/host/local-models.ini', 'deploy/host/local-model-plane.py', 'src/noerelay/sdd.py',
           'src/noerelay/mcp_agent.py', 'crates/noerelay-gateway/src/lib.rs', 'crates/noerelay-core/src/wire.rs', 'deploy/docker/compose.yml', 'docker-compose.yml']
digests = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
envelope = write_envelope(ROOT, package, test, subprocess.list2cmdline(command), [requirement],
    'observed_pass' if result.returncode == 0 else 'observed_fail', digest, digest, started, finished,
    artifact_digests=digests, exceptions=[] if result.returncode == 0 else [f'exit {result.returncode}'],
    notes=f'Local working-tree observation. Retained log: {path.relative_to(ROOT).as_posix()}. Source digests identify uncommitted code; no independent verification or production certification claimed.')
print(result.stdout)
print(result.stderr)
print(envelope)
sys.exit(result.returncode)
