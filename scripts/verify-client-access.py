"""Authenticated client probe; reads credentials on stdin and never records them."""
import json
import platform
import sys
import urllib.error
import urllib.request

settings = json.load(sys.stdin)
base = settings['OPENAI_BASE_URL']
headers = {'Authorization': 'Bearer ' + settings['OPENAI_API_KEY'], 'Content-Type': 'application/json',
           'x-noerelay-project': 'wsl-access-verification'}
checks = []
for path, payload in [('/models', None), ('/chat/completions', {
    'model': settings['OPENAI_MODEL'], 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': 'Reply with READY.'},
        {'type': 'text', 'text': 'Zoo Code multipart compatibility check.'}]}],
    'reasoning_effort': 'low', 'max_tokens': 256})]:
    request = urllib.request.Request(base + path, None if payload is None else json.dumps(payload).encode(), headers)
    with urllib.request.urlopen(request, timeout=180) as response:
        value = json.load(response)
    passed = bool(value.get('data')) if payload is None else 'READY' in value['choices'][0]['message'].get('content', '')
    checks.append({'path': path, 'passed': passed})
try:
    urllib.request.urlopen(base + '/models', timeout=10)
    checks.append({'path': '/models_without_key', 'passed': False})
except urllib.error.HTTPError as error:
    checks.append({'path': '/models_without_key', 'passed': error.code in (401, 403)})
print(json.dumps({'platform': platform.platform(), 'base_url': base, 'model': settings['OPENAI_MODEL'], 'checks': checks}))
assert all(check['passed'] for check in checks)
