"""Emit client environment settings; output contains a credential, so capture it."""
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def settings():
    container = subprocess.check_output(['docker', 'compose', '--project-directory', str(ROOT),
        '--env-file', str(ROOT / '.env.docker'), 'ps', '-q', 'noerelay'], text=True).strip()
    if not container:
        raise RuntimeError('Start NoeRelay before loading client settings')
    info = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]
    environment = dict(item.split('=', 1) for item in info['Config']['Env'] if '=' in item)
    return {'OPENAI_BASE_URL': 'http://127.0.0.1:8080/v1',
            'OPENAI_API_KEY': environment['NOERELAY_API_KEY'], 'OPENAI_MODEL': 'axiovex-agni-raw'}


if __name__ == '__main__':
    # Windows Python is also invoked from WSL; emit shell-compatible LF endings.
    sys.stdout.reconfigure(newline='\n')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell', choices=['bash', 'powershell', 'json'], default='json')
    args = parser.parse_args()
    values = settings()
    if args.shell == 'json':
        print(json.dumps(values))
    else:
        for key, value in values.items():
            if args.shell == 'bash':
                print('export ' + key + '=' + shlex.quote(value))
            else:
                print("$env:" + key + " = '" + value.replace("'", "''") + "'")
