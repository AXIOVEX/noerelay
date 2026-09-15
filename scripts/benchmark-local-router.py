"""Measured cold/warm routed latency; outputs are observations, not quality scores."""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.mcp_stdio import local_config

config = local_config()
results = []
for capability, prompt in [
    ('code', 'Implement a Python merge_intervals(intervals) function for unsorted integer pairs. Include a docstring, type hints, input validation, and five assert tests covering empty input, overlaps, touching endpoints, nested intervals, and disjoint intervals. Return only Python code.'),
    ('reasoning', 'Use complex reasoning to explain when a database transaction can lose an update and how optimistic concurrency control prevents this. Give a concrete two-writer timeline and pseudocode for retrying on a version conflict. Keep it under 250 words.')]:
    for attempt in range(2):
        request = urllib.request.Request(config['base_url'] + '/v1/chat/completions',
            json.dumps({'model': 'axiovex-agni-raw', 'messages': [{'role': 'user', 'content': prompt}],
                        'max_tokens': 1536}).encode(),
            {'Authorization': 'Bearer ' + config['api_key'], 'Content-Type': 'application/json',
             'x-noerelay-project': 'noerelay-speed-verification', 'x-noerelay-capability': capability})
        started = time.monotonic()
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.load(response)
        observation = {'capability': capability, 'attempt': attempt + 1,
                       'elapsed_seconds': round(time.monotonic() - started, 3),
                       'timings': result.get('timings'), 'usage': result.get('usage'),
                       'message': result['choices'][0]['message'],
                       'finish_reason': result['choices'][0].get('finish_reason')}
        results.append(observation)
        (ROOT / 'evidence/local-recovery/performance.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in observation.items() if k != 'message'}), flush=True)
