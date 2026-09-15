"""Read-only forwarding guard for the installed Codex smoke test only."""
import json
import os
import re
import sys
import urllib.request
from .clients import connection


def allowed(params, command):
    return (params.get('name') == 'noerelay_workspace_execute' and
            params.get('arguments') == {'command': command})


def main():
    command = os.environ['NOERELAY_TEST_READ_COMMAND']
    if not re.fullmatch(r'cat /workspace/\.noerelay/clients/tests/codex-[0-9a-f]{12}/nonce\.txt', command):
        raise ValueError('Only the generated test fixture may be read')
    config = connection()
    for line in sys.stdin:
        req = json.loads(line)
        try:
            if req.get('method') == 'tools/call' and not allowed(req.get('params', {}), command):
                raise ValueError('Test guard permits only the exact nonce read command')
            request = urllib.request.Request(config['base_url'] + '/mcp', json.dumps(req).encode(),
                {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config['api_key']})
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.load(response)
            if req.get('method') == 'tools/list':
                result['result']['tools'] = [t for t in result['result']['tools']
                    if t['name'] == 'noerelay_workspace_execute']
            if 'id' in req:
                print(json.dumps(result), flush=True)
        except Exception as exc:
            if 'id' in req:
                print(json.dumps({'jsonrpc':'2.0', 'id':req['id'],
                    'error':{'code':-32602, 'message':str(exc)}}), flush=True)


if __name__ == '__main__':
    main()
