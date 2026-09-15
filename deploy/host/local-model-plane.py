"""Local RTK transport. Model selection remains in NoeRelay/LiteLLM/llama.cpp routers."""
import json
import hmac
import os
import sys
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from noerelay.sdd import prepare, audit, assess_feature, AGENT_INSTRUCTIONS
from noerelay.mcp_agent import DockerMCP, available_tools, agent_run, WORKSPACE_TOOLS, workspace_call, SDD_TOOL
from reference.gateway.compression import CompressionConfig, compress_messages
from reference.gateway.rtk_bridge import is_native_available

UPSTREAM = 'http://127.0.0.1:8081'
LOCK = threading.Lock()
CONFIG = CompressionConfig(enabled=True, strategy='dedup', min_tokens=512)
_env_file = ROOT / '.env.docker'
TOKEN = os.environ.get('LITELLM_MASTER_KEY') or next((line.partition('=')[2].strip().strip('"').strip("'")
              for line in (_env_file.read_text().splitlines() if _env_file.exists() else [])
              if line.startswith('LITELLM_MASTER_KEY=')), '')
GATEWAY_KEY = os.environ.get('NOERELAY_API_KEY') or next((line.partition('=')[2].strip().strip('"').strip("'")
              for line in (_env_file.read_text().splitlines() if _env_file.exists() else [])
              if line.startswith('NOERELAY_API_KEY=')), '')
TERMINAL_KEY = os.environ.get('OPEN_TERMINAL_API_KEY', '')


def compact_request(body):
    """Preserve structured tool exchanges; compact only ordinary text history."""
    messages = body.get('messages')
    if not isinstance(messages, list):
        return body, {'skipped': True, 'reason': 'no_chat_messages'}
    if any(not isinstance(m.get('content'), str) or m.get('tool_calls') or
           m.get('role') == 'tool' for m in messages):
        return body, {'skipped': True, 'reason': 'structured_or_tool_history'}
    with LOCK:
        result = compress_messages(messages, CONFIG)
    body = dict(body, messages=result.compressed_messages)
    metrics = asdict(result)
    metrics.pop('original_messages')
    metrics.pop('compressed_messages')
    return body, metrics


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def reply(self, code, value):
        data = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self.reply(200, {'status': 'ok', 'rtk_native': is_native_available()})
        return self.proxy()

    def do_POST(self):
        if self.path == '/shutdown' and self.client_address[0] == '127.0.0.1':
            self.reply(200, {'stopped': True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        return self.proxy()

    def proxy(self):
        if not TOKEN or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + TOKEN):
            return self.reply(401, {'error': 'unauthorized'})
        if self.path not in ('/v1/chat/completions', '/v1/responses', '/v1/models', '/mcp', '/agent', '/sdd/onboard', '/sdd/audit'):
            return self.reply(404, {'error': 'unsupported endpoint'})
        try:
            data = None
            if self.command == 'POST':
                length = int(self.headers.get('Content-Length', '0'))
                if length <= 0 or length > 16 * 1024 * 1024:
                    return self.reply(413, {'error': 'invalid request size'})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError('request must be an object')
                if self.path.startswith('/sdd/'):
                    project = str(body.get('project_id', 'default'))
                    if self.path == '/sdd/audit':
                        return self.reply(200, audit(ROOT, project))
                    with LOCK:
                        state = prepare(ROOT, project, [{'role': 'user', 'content': body.get('description') or body.get('project_name') or project}])
                    return self.reply(200, dict(state, initialized=True))
                if self.path == '/agent':
                    return self.reply(200, agent_run(body, TOKEN, GATEWAY_KEY, terminal_token=TERMINAL_KEY, root=ROOT))
                if self.path == '/mcp':
                    return self.mcp(body)
                body, metrics = compact_request(body)
                if body.get('model') == 'qwen3.6-35b-a3b':
                    body.setdefault('chat_template_kwargs', {'enable_thinking': False})
                    body.setdefault('temperature', 0.7)
                    body.setdefault('top_p', 0.8)
                sdd = body.pop('noerelay_sdd', None)
                if sdd:
                    messages = body.get('messages')
                    if not isinstance(messages, list):
                        value = body.get('input', '')
                        messages = ([{'role': 'user', 'content': value}] if isinstance(value, str)
                                    else [item for item in value if isinstance(item, dict) and item.get('role')])
                    with LOCK:
                        lifecycle = prepare(ROOT, str(sdd['project']), messages)
                    instruction = (AGENT_INSTRUCTIONS + '\nFeature: ' + lifecycle['feature']
                                   if body.get('tools') else
                                   'NoeRelay tracks this request internally. Answer the user directly; '
                                   'do not discuss internal requirements bookkeeping or pretend to have executed tools.')
                    if isinstance(body.get('messages'), list):
                        body['messages'].insert(0, {'role': 'system', 'content': instruction})
                    else:
                        body['instructions'] = instruction + '\n' + (body.get('instructions') or '')
                    print(json.dumps({'sdd': lifecycle}), flush=True)
                print(json.dumps({'model': body.get('model'), 'compression': metrics}), flush=True)
                data = json.dumps(body).encode()
            req = urllib.request.Request(UPSTREAM + self.path, data=data,
                                         headers={'Content-Type': 'application/json'})
            try:
                response = urllib.request.urlopen(req, timeout=600)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                self.send_response(response.status)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.close_connection = True
                while chunk := response.read1(8192):
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except (ValueError, TypeError, KeyError):
            self.reply(400, {'error': 'invalid JSON request'})
        except urllib.error.URLError:
            self.reply(502, {'error': 'model router unavailable'})
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            self.reply(503, {'error': 'SDD lifecycle unavailable', 'detail': str(exc)})

    def mcp(self, body):
        method, request_id = body.get('method'), body.get('id')
        if method == 'initialize':
            result = {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}},
                      'serverInfo': {'name': 'noerelay-docker-mcp', 'version': '0.2.0'}}
        elif method == 'notifications/initialized':
            return self.reply(202, {})
        elif method == 'ping':
            result = {}
        else:
            client = DockerMCP(TOKEN)
            tools = available_tools(client)
            if method == 'tools/list':
                result = {'tools': tools + WORKSPACE_TOOLS + [SDD_TOOL, {
                    'name': 'noerelay_requirements', 'description': 'Read NoeRelay requirement coverage and evidence gaps',
                    'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}}]}
            elif method == 'tools/call':
                params = body.get('params', {})
                if params.get('name') == 'noerelay_sdd_assess':
                    arguments = params.get('arguments', {})
                    output = assess_feature(ROOT, arguments['feature'], arguments.get('phase', 'after_implement'))
                    result = {'content': [{'type': 'text', 'text': json.dumps(output)}]}
                elif params.get('name') == 'noerelay_requirements':
                    from noerelay.reqtest import coverage_report
                    result = {'content': [{'type': 'text', 'text': json.dumps(coverage_report(ROOT))}]}
                elif params.get('name') in {tool['name'] for tool in WORKSPACE_TOOLS}:
                    output = workspace_call(params['name'], params.get('arguments', {}), TERMINAL_KEY, ROOT)
                    result = {'content': [{'type': 'text', 'text': json.dumps(output)}]}
                elif params.get('name') in {tool['name'] for tool in tools}:
                    result = client.call(method, params)
                else:
                    return self.reply(200, {'jsonrpc': '2.0', 'id': request_id,
                                           'error': {'code': -32602, 'message': 'Tool outside configured allowlist'}})
            else:
                return self.reply(200, {'jsonrpc': '2.0', 'id': request_id,
                                       'error': {'code': -32601, 'message': 'Method not found'}})
        return self.reply(200, {'jsonrpc': '2.0', 'id': request_id, 'result': result})


if __name__ == '__main__':
    if not is_native_available():
        raise SystemExit('Native RTK is required: install the rtk wheel first')
    env = dict(os.environ, MCP_GATEWAY_AUTH_TOKEN=TOKEN)
    log = (ROOT / '.noerelay/runtime/docker-mcp.log').open('a', encoding='utf-8')
    # Reuse an authenticated gateway surviving an earlier adapter shutdown.
    mcp = None
    try:
        DockerMCP(TOKEN)
    except (urllib.error.URLError, RuntimeError):
        mcp = subprocess.Popen(['docker', 'mcp', 'gateway', 'run', '--profile', 'ai_coding',
                            '--transport', 'streaming', '--host', '127.0.0.1', '--port', '8811'],
                           env=env, stdout=log, stderr=log,
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    try:
        for attempt in range(30):
            try:
                DockerMCP(TOKEN)
                break
            except (urllib.error.URLError, RuntimeError):
                if (mcp is not None and mcp.poll() is not None) or attempt == 29:
                    raise RuntimeError('Docker MCP did not become ready')
                time.sleep(1)
        ThreadingHTTPServer(('0.0.0.0', 8082), Handler).serve_forever()
    finally:
        if mcp is not None:
            mcp.terminate()
            mcp.wait(timeout=15)
        log.close()
