#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
venv="$repo/.noerelay/cli-venv-linux"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install -e "$repo"
printf 'Activate: source "%s/bin/activate"\n' "$venv"
printf 'Then: noerelay client setup all; noerelay client run opencode\n'
