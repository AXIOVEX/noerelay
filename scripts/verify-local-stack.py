"""Live local checks. Saves observed results, without credentials or production claims."""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.mcp_stdio import local_config


def main():
    config = local_config()
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config['api_key'],
               'x-noerelay-project': 'noerelay-local-verification'}
    results = []
    def call(path, body=None, method=None, extra=None):
        req = urllib.request.Request(config['base_url'] + path, None if body is None else json.dumps(body).encode(),
                                     dict(headers, **(extra or {})), method=method)
        with urllib.request.urlopen(req, timeout=600) as response:
            data = response.read()
            return response.status, dict(response.headers), json.loads(data) if data else None
    try:
        status, response_headers, _ = call('/v1/chat/completions', method='OPTIONS',
            extra={'Origin': 'https://example.test', 'Access-Control-Request-Headers': 'authorization,content-type'})
        assert status == 204 and response_headers.get('access-control-allow-origin') == '*'
        results.append({'check': 'cors_preflight', 'passed': True})
        _, _, mcp = call('/mcp', {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})
        names = [t['name'] for t in mcp['result']['tools']]
        assert 'noerelay_workspace_execute' in names and 'query-docs' in names
        results.append({'check': 'mcp_tools', 'tools': names, 'passed': True})
        _, _, workspace = call('/mcp', {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
            'params': {'name': 'noerelay_workspace_execute', 'arguments': {'command': 'python -c "print(731 + 269)"'}}})
        assert '1000' in json.dumps(workspace)
        results.append({'check': 'docker_workspace', 'passed': True, 'result': workspace})
        for expected, prompt in [
            ('gpt-oss-20b-Q5_K_M', 'Reply with exactly READY.'),
            ('qwen3.6-35b-a3b', 'Implement a Python function add(a, b). Return only the function.'),
            ('qwen3.8-27b', 'Use complex reasoning to calculate 17 times 19. Reply only with the answer.')]:
            start = time.monotonic()
            _, receipt_headers, completion = call('/v1/chat/completions', {
                'model': 'axiovex-agni-raw', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2048})
            models = json.load(urllib.request.urlopen('http://127.0.0.1:8081/v1/models'))
            loaded = [m['id'] for m in models['data'] if m.get('status', {}).get('value') == 'loaded']
            content = completion['choices'][0]['message'].get('content', '')
            passed = expected in loaded and bool(content)
            context = next(m.get('meta', {}).get('n_ctx') for m in models['data'] if m['id'] == expected)
            passed = passed and context == 131072
            result = {'check': 'model_route', 'expected': expected, 'loaded': loaded,
                      'allocated_context': context,
                      'elapsed_seconds': round(time.monotonic()-start, 3), 'content': content,
                      'timings': completion.get('timings'), 'usage': completion.get('usage'),
                      'run_id': receipt_headers.get('x-noerelay-run-id'), 'passed': passed}
            results.append(result)
            print(json.dumps(result), flush=True)
            assert passed, f'{expected} did not complete on its intended route'
    finally:
        path = ROOT / 'evidence/local-recovery/verification.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'checks': results}, indent=2), encoding='utf-8')
        print(str(path))


if __name__ == '__main__':
    main()
