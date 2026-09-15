"""Exercise a prompt beyond the old 16K limit through the public coding router."""
import json
import sys
import time
import urllib.request
import argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.mcp_stdio import local_config

config = local_config()
parser = argparse.ArgumentParser()
parser.add_argument('--rows', type=int, default=3000)
args = parser.parse_args()
rows = ''.join(f'row {index}: alpha beta gamma delta epsilon.\n' for index in range(args.rows))
rows = rows.replace('row 1500: alpha beta gamma delta epsilon.', 'row 1500: MARKER=742913.')
body = {'model': 'axiovex-agni-raw', 'messages': [{'role': 'user', 'content':
    'Coding context retrieval test. Read the data below. Return only the six-digit MARKER on row 1500.\n' + rows}],
    'max_tokens': 128}
request = urllib.request.Request(config['base_url'] + '/v1/chat/completions', json.dumps(body).encode(),
    {'Authorization': 'Bearer ' + config['api_key'], 'Content-Type': 'application/json',
     'x-noerelay-capability': 'code', 'x-noerelay-project': 'long-context-verification'})
start = time.monotonic()
with urllib.request.urlopen(request, timeout=600) as response:
    result = json.load(response)
content = result['choices'][0]['message'].get('content', '')
passed = '742913' in content and result['usage']['prompt_tokens'] > 16384
report = {'passed': passed, 'content': content, 'usage': result['usage'],
          'elapsed_seconds': round(time.monotonic()-start, 3), 'timings': result.get('timings'),
          'scope': 'Beyond-16K retrieval smoke test; not a full-window accuracy benchmark.'}
(ROOT / 'evidence/local-recovery/long-context.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
assert passed
