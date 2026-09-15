"""Verify a real bounded agent executes a harmless Docker workspace command."""
import json
import sys
import urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.mcp_stdio import local_config
config = local_config()
body = {'prompt': 'Use noerelay_workspace_execute to run python -c "print(731 + 269)" in the Docker workspace. Report its actual output. This is a tool smoke test; do not edit project files or claim release verification.',
        'project': 'noerelay-agent-smoke', 'max_steps': 4}
request = urllib.request.Request(config['base_url'] + '/v1/noerelay/agent', json.dumps(body).encode(),
    {'Authorization': 'Bearer ' + config['api_key'], 'Content-Type': 'application/json'})
with urllib.request.urlopen(request, timeout=600) as response:
    result = json.load(response)
(ROOT / 'evidence/local-recovery/agent.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
assert any('noerelay_workspace_execute' in step.get('tools', []) for step in result['steps'])
assert result['status'] == 'responded' and '1000' in result['content']
assert result['sdd']['verification_status'] == 'requires_evidence'
