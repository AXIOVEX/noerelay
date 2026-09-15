"""
OS-appropriate launcher scripts for the NoeRelay local LLM stack.

Generates small, self-contained scripts next to the install so the user can:

* **activate the venv** and get the ``noerelay`` CLI on PATH,
* **start / stop** the llama.cpp server,
* **register autostart** (Windows Scheduled Task / macOS LaunchAgent).

NR-LLM-004: all lifecycle scripts are **thin wrappers** — they resolve the
provisioned venv interpreter and invoke the Python entry points
(``python -m noerelay.cli llm start|stop|schedule``).  No PowerShell
lifecycle scripts are generated; Windows gets ``.bat``, macOS/Linux get
``.sh``.  The server arguments themselves come from the master YAML config
written by the installer (NR-LLM-005).
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
    py = str(venv_python_path(plan))
    return f"""@echo off
REM NoeRelay: start the llama.cpp server (Python lifecycle entry point).
"{py}" -m noerelay.cli llm start --dir "{plan.install_dir}"
"""


def _win_stop(plan: ProvisionPlan) -> str:
    py = str(venv_python_path(plan))
    return f"""@echo off
REM NoeRelay: stop the llama.cpp server (Python lifecycle entry point).
"{py}" -m noerelay.cli llm stop --dir "{plan.install_dir}"
"""


def _win_autostart(plan: ProvisionPlan) -> str:
    py = str(venv_python_path(plan))
    return f"""@echo off
REM NoeRelay: register a logon Scheduled Task (Python entry point;
REM native schtasks under the hood - no PowerShell lifecycle scripts).
"{py}" -m noerelay.cli llm schedule --dir "{plan.install_dir}"
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
    py = str(venv_python_path(plan))
    return f"""#!/usr/bin/env bash
# NoeRelay: start the llama.cpp server (Python lifecycle entry point).
exec "{py}" -m noerelay.cli llm start --dir "{plan.install_dir}"
"""


def _sh_stop(plan: ProvisionPlan) -> str:
    py = str(venv_python_path(plan))
    return f"""#!/usr/bin/env bash
# NoeRelay: stop the llama.cpp server (Python lifecycle entry point).
exec "{py}" -m noerelay.cli llm stop --dir "{plan.install_dir}"
"""


def _mac_autostart(plan: ProvisionPlan) -> str:
    py = str(venv_python_path(plan))
    return f"""#!/usr/bin/env bash
# NoeRelay: register a macOS LaunchAgent (Python entry point).
exec "{py}" -m noerelay.cli llm schedule --dir "{plan.install_dir}"
"""


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
