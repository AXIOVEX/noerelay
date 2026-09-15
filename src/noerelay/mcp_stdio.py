"""Stdio MCP adapter: every request goes through NoeRelay's authenticated /mcp."""
import json
import sys
import urllib.request


def local_config():
    from .clients import connection
    return connection()


def main():
    config = local_config()
    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line)
            req = urllib.request.Request(config['base_url'] + '/mcp', json.dumps(request).encode(),
                                         {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config['api_key']})
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.load(response)
            if 'id' in request:
                print(json.dumps(result), flush=True)
        except Exception as exc:
            if isinstance(request, dict) and 'id' in request:
                print(json.dumps({'jsonrpc': '2.0', 'id': request['id'],
                                  'error': {'code': -32603, 'message': str(exc)}}), flush=True)
            else:
                print(str(exc), file=sys.stderr)


if __name__ == '__main__':
    main()
