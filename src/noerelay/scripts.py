"""
OS-appropriate launcher scripts for the NoeRelay local LLM stack.

Generates small, self-contained scripts next to the install so the user can:

* **activate the venv** and get the ``noerelay`` CLI on PATH,
* **start / stop** the llama.cpp server with the exact args the provisioner
  chose,
* (Windows) **register autostart** via a Scheduled Task,
* (macOS) **register autostart** via a LaunchAgent.

Windows gets ``.bat``/``.ps1``; macOS/Linux get ``.sh``. All scripts are
generated from the :class:`ProvisionPlan` so they always match the detected
hardware (split, offload, model, port).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from .provision import ProvisionPlan


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def venv_python_path(plan: ProvisionPlan) -> Path:
    if plan.os == "windows":
        return plan.venv_dir / "Scripts" / "python.exe"
    return plan.venv_dir / "bin" / "python"


def venv_noerelay_path(plan: ProvisionPlan) -> Path:
    if plan.os == "windows":
        return plan.venv_dir / "Scripts" / "noerelay.exe"
    return plan.venv_dir / "bin" / "noerelay"


def _server_exe(plan: ProvisionPlan) -> str:
    return "llama-server.exe" if plan.os == "windows" else "llama-server"


def _server_path(plan: ProvisionPlan) -> str:
    return str(plan.llama_dir / _server_exe(plan))


# ---------------------------------------------------------------------------
# Windows scripts
# ---------------------------------------------------------------------------


def _win_activate(plan: ProvisionPlan) -> str:
    return f"""@echo off
REM NoeRelay: activate the virtualenv and put 'noerelay' on PATH.
call "{plan.venv_dir}\\Scripts\\activate.bat"
echo NoeRelay venv active. Use: noerelay <command>
"""


def _win_start(plan: ProvisionPlan) -> str:
    args = " ".join(_quote(a) for a in plan.server_args())
    return f"""@echo off
REM NoeRelay: start the llama.cpp server (backend={plan.backend}).
cd /d "{plan.llama_dir}"
echo Starting llama.cpp server on {plan.host}:{plan.port} ...
"{_server_path(plan)}" {args}
"""


def _win_stop(plan: ProvisionPlan) -> str:
    return f"""@echo off
REM NoeRelay: stop the llama.cpp server.
taskkill /F /IM llama-server.exe >nul 2>&1
if %errorlevel%==0 (echo Stopped llama-server.exe) else (echo llama-server.exe not running)
"""


def _win_autostart(plan: ProvisionPlan) -> str:
    start = str(plan.bin_dir / "start-server.bat")
    return f"""@echo off
REM NoeRelay: register a logon Scheduled Task that starts the server.
REM Run this from an ELEVATED (Administrator) prompt.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute '{start}';" ^
  "$t = New-ScheduledTaskTrigger -AtLogOn;" ^
  "Register-ScheduledTask -TaskName 'NoeRelayLLM' -Action $a -Trigger $t -Description 'NoeRelay local LLM server'"
echo Done. The server now starts at logon.
"""


# ---------------------------------------------------------------------------
# macOS / Linux scripts
# ---------------------------------------------------------------------------


def _sh_activate(plan: ProvisionPlan) -> str:
    return f"""#!/usr/bin/env bash
# NoeRelay: activate the virtualenv and put 'noerelay' on PATH.
source "{plan.venv_dir}/bin/activate"
echo "NoeRelay venv active. Use: noerelay <command>"
"""


def _sh_start(plan: ProvisionPlan) -> str:
    args = " ".join(_sh_quote(a) for a in plan.server_args())
    log = str(plan.install_dir / "server.log")
    return f"""#!/usr/bin/env bash
# NoeRelay: start the llama.cpp server (backend={plan.backend}).
cd "{plan.llama_dir}"
echo "Starting llama.cpp server on {plan.host}:{plan.port} ..."
exec "{_server_path(plan)}" {args}
"""


def _sh_stop(plan: ProvisionPlan) -> str:
    return """#!/usr/bin/env bash
# NoeRelay: stop the llama.cpp server.
pkill -f llama-server && echo "Stopped llama-server" || echo "llama-server not running"
"""


def _mac_autostart(plan: ProvisionPlan) -> str:
    start = str(plan.bin_dir / "start-server.sh")
    plist = str(plan.install_dir / "com.noerelay.llm.plist")
    return f"""#!/usr/bin/env bash
# NoeRelay: register a macOS LaunchAgent that starts the server at login.
PLIST="{plist}"
cat > "$PLIST" <<'EOF'
{{{{
  "Label": "com.noerelay.llm",
  "ProgramArguments": ["{start}"],
  "RunAtLoad": true,
  "KeepAlive": false
}}}}
EOF
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST" "$HOME/Library/LaunchAgents/"
launchctl load "$HOME/Library/LaunchAgents/com.noerelay.llm.plist"
echo "Done. The server now starts at login."
"""


# ---------------------------------------------------------------------------
# Quoting helpers
# ---------------------------------------------------------------------------


def _quote(s: str) -> str:
    return f'"{s}"' if " " in s else s


def _sh_quote(s: str) -> str:
    if any(c in s for c in " \t\"'"):
        return "'" + s.replace("'", "'\\''") + "'"
    return s


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_scripts(plan: ProvisionPlan) -> None:
    plan.bin_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if plan.os == "windows":
        specs = {
            "activate.bat": _win_activate(plan),
            "start-server.bat": _win_start(plan),
            "stop-server.bat": _win_stop(plan),
            "autostart.bat": _win_autostart(plan),
        }
    else:
        specs = {
            "activate.sh": _sh_activate(plan),
            "start-server.sh": _sh_start(plan),
            "stop-server.sh": _sh_stop(plan),
        }
        if plan.os == "darwin":
            specs["autostart.sh"] = _mac_autostart(plan)

    for name, content in specs.items():
        p = plan.bin_dir / name
        p.write_text(content, encoding="utf-8")
        if plan.os != "windows":
            p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        written.append(p)

    # A convenience `noerelay` wrapper that activates the venv and runs the CLI.
    if plan.os == "windows":
        (plan.bin_dir / "noerelay.bat").write_text(
            f'@echo off\r\ncall "{plan.venv_dir}\\Scripts\\activate.bat" >nul\r\n'
            f'"{venv_noerelay_path(plan)}" %*\r\n',
            encoding="utf-8",
        )
    else:
        wrapper = plan.bin_dir / "noerelay"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nexec \"{venv_noerelay_path(plan)}\" \"$@\"\n",
            encoding="utf-8",
        )
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        written.append(wrapper)

    for p in written:
        print(f"  + {p}")
