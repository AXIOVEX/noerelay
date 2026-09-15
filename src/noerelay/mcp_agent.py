"""NoeRelay's Docker MCP bridge and bounded tool-using agent loop."""
import json
import urllib.request
import urllib.parse
import hashlib
import time
from pathlib import Path


class DockerMCP:
    def __init__(self, token, url='http://127.0.0.1:8811/mcp'):
        self.token, self.url, self.session = token, url, None
        self.call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                'clientInfo': {'name': 'noerelay', 'version': '0.2.0'}})
        self.call('notifications/initialized', {}, notification=True)

    def call(self, method, params=None, notification=False):
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notification:
            payload['id'] = 1
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-03-26'}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        request = urllib.request.Request(self.url, json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(request, timeout=90) as response:
            self.session = response.headers.get('Mcp-Session-Id', self.session)
            if notification or response.status == 202:
                return {}
            if 'text/event-stream' in response.headers.get('Content-Type', ''):
                for line in response:
                    if line.startswith(b'data: '):
                        value = json.loads(line[6:])
                        if value.get('id') == 1:
                            break
                else:
                    raise RuntimeError('Docker MCP stream ended without a result')
            else:
                value = json.load(response)
        if 'error' in value:
            raise RuntimeError(str(value['error']))
        return value.get('result', {})


def available_tools(client):
    # Do not expose Docker's dynamic catalog-management tools to the model.
    allowed = {'resolve-library-id', 'query-docs', 'sequentialthinking'}
    return [tool for tool in client.call('tools/list').get('tools', []) if tool['name'] in allowed]


WORKSPACE_TOOLS = [
    {'name': 'noerelay_workspace_execute', 'description': 'Execute a bounded Linux command in the Docker workspace /workspace. Use to inspect/edit project files and run tests. Returns a process ID and observed output. Never use for actions outside the user task.',
     'inputSchema': {'type': 'object', 'properties': {'command': {'type': 'string'}}, 'required': ['command'], 'additionalProperties': False}},
    {'name': 'noerelay_workspace_status', 'description': 'Read completion status and output of a Docker workspace command.',
     'inputSchema': {'type': 'object', 'properties': {'process_id': {'type': 'string'}}, 'required': ['process_id'], 'additionalProperties': False}},
]
SDD_TOOL = {'name': 'noerelay_sdd_assess', 'description': 'Run the internal AEE assessment on an agent-managed spec-kit feature; unsupported claims remain open.',
            'inputSchema': {'type': 'object', 'properties': {'feature': {'type': 'string'},
                'phase': {'type': 'string', 'enum': ['after_specify', 'after_plan', 'after_tasks', 'after_implement']}},
                'required': ['feature'], 'additionalProperties': False}}


def workspace_call(name, arguments, token, root):
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    if name == 'noerelay_workspace_execute':
        command = arguments.get('command')
        if not isinstance(command, str) or not 1 <= len(command) <= 16000:
            raise ValueError('command must contain 1 to 16000 characters')
        request = urllib.request.Request('http://127.0.0.1:8002/execute?wait=30&tail=100',
                                         json.dumps({'command': command, 'cwd': '/workspace'}).encode(), headers)
    else:
        process = urllib.parse.quote(str(arguments['process_id']), safe='')
        request = urllib.request.Request(f'http://127.0.0.1:8002/execute/{process}/status?wait=30&tail=100', headers=headers)
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.load(response)
    evidence = root / '.noerelay/runtime/tool-evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    artifact = evidence / f'{time.time_ns()}.json'
    record = json.dumps({'tool': name, 'arguments': arguments, 'observed_result': result}, indent=2)
    artifact.write_text(record, encoding='utf-8')
    return {'result': result, 'evidence_path': artifact.relative_to(root).as_posix(),
            'sha256': hashlib.sha256(record.encode()).hexdigest()}


def agent_run(body, token, gateway_key, gateway='http://127.0.0.1:8080', terminal_token='', root=None):
    prompt = body.get('prompt')
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('prompt must be nonempty text')
    steps = body.get('max_steps', 4)
    if not isinstance(steps, int) or not 1 <= steps <= 8:
        raise ValueError('max_steps must be between 1 and 8')
    client = DockerMCP(token)
    tools = available_tools(client) + (WORKSPACE_TOOLS if terminal_token else []) + [SDD_TOOL]
    names = {tool['name'] for tool in tools}
    messages = [{'role': 'user', 'content': prompt}]
    trace = []
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + gateway_key,
               'x-noerelay-project': str(body.get('project', 'noerelay-agent'))}
    if body.get('escalate') is True:
        headers['x-noerelay-capability'] = 'reasoning'
    for step in range(steps):
        payload = {'model': 'axiovex-agni-raw', 'messages': messages, 'max_tokens': 2048,
                   'tools': [{'type': 'function', 'function': {'name': tool['name'],
                              'description': tool.get('description', ''),
                              'parameters': tool.get('inputSchema', {})}} for tool in tools]}
        req = urllib.request.Request(gateway + '/v1/chat/completions', json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.load(response)
            receipt = response.headers.get('x-noerelay-run-id')
        # Provider response metadata is not a valid OpenAI request message field.
        message = {key: value for key, value in result['choices'][0]['message'].items()
                   if key in ('role', 'content', 'tool_calls', 'name', 'tool_call_id')}
        trace.append({'step': step + 1, 'run_id': receipt})
        messages.append(message)
        calls = message.get('tool_calls', [])
        if not calls:
            from .sdd import audit, assess_feature
            state = audit(root, str(body.get('project', 'noerelay-agent')))
            assessment = assess_feature(root, state['feature']) if 'feature' in state else {'verification_status': 'requires_evidence'}
            return {'status': 'responded', 'content': message.get('content', ''), 'steps': trace, 'sdd': assessment}
        if len(calls) > 8:
            return {'status': 'tool_limit', 'content': 'Tool call limit exceeded; task incomplete.', 'steps': trace}
        for call in calls:
            name = call['function']['name']
            if name not in names:
                output = {'error': 'Tool is outside the configured Docker MCP allowlist'}
            else:
                arguments = json.loads(call['function']['arguments'])
                if name == 'noerelay_sdd_assess':
                    from .sdd import assess_feature
                    output = assess_feature(root, arguments['feature'], arguments.get('phase', 'after_implement'))
                elif name.startswith('noerelay_workspace_'):
                    output = workspace_call(name, arguments, terminal_token, root)
                else:
                    output = client.call('tools/call', {'name': name, 'arguments': arguments})
                observed = output.get('result', output) if isinstance(output, dict) else {}
                if (isinstance(observed, dict) and observed.get('exit_code') not in (None, 0)) or (
                        isinstance(output, dict) and output.get('isError') is True):
                    headers['x-noerelay-capability'] = 'reasoning'
                    trace[-1]['escalation'] = 'observed_tool_failure'
            messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': json.dumps(output)})
            trace[-1].setdefault('tools', []).append(name)
    return {'status': 'step_limit', 'content': 'Agent step budget exhausted; task remains incomplete.', 'steps': trace}
