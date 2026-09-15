"""
Python-native llama.cpp server lifecycle (NR-LLM-004).

Start, stop, status, and scheduled-task creation are implemented here in the
noerelay package — no PowerShell lifecycle scripts are generated or required.
Generated installer scripts are thin wrappers that invoke these entry points
in the provisioned virtual environment.

Windows scheduled tasks use the native ``schtasks`` executable (not
PowerShell); macOS uses a LaunchAgent plist; Linux uses a systemd user unit
(best effort).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llama_config import (
    LlamaConfigError,
    load_llama_config,
    server_args_from_config,
)

IS_WINDOWS = os.name == "nt"

#: Default install dir resolution: $NOERELAY_LLM_HOME, else ~/noerelay-llm.
DEFAULT_INSTALL_DIR = Path(
    os.environ.get("NOERELAY_LLM_HOME") or (Path.home() / "noerelay-llm")
)

PID_FILE_NAME = "server.pid"
LOG_FILE_NAME = "server.log"

#: Reference scheduled-task name (matches the operator's C:\LLM task).
DEFAULT_TASK_NAME = "NoeRelay LLM Server"


class LifecycleError(RuntimeError):
    """Raised when a lifecycle operation fails."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def install_dir_from(arg: Optional[str] = None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    return Path(DEFAULT_INSTALL_DIR).resolve()


def llama_config_path(install_dir: Path) -> Path:
    return install_dir / "llama.yaml"


def server_exe_path(install_dir: Path) -> Path:
    name = "llama-server.exe" if IS_WINDOWS else "llama-server"
    return install_dir / "llama" / name


def pid_file(install_dir: Path) -> Path:
    return install_dir / PID_FILE_NAME


def log_file(install_dir: Path) -> Path:
    return install_dir / LOG_FILE_NAME


def base_url_from(install_dir: Path) -> str:
    try:
        cfg = load_llama_config(llama_config_path(install_dir).read_text(encoding="utf-8"))
        s = cfg["server"]
        return f"http://{s['host']}:{int(s['port'])}"
    except (OSError, LlamaConfigError):
        return "http://127.0.0.1:8080"


# ---------------------------------------------------------------------------
# Start / stop / status
# ---------------------------------------------------------------------------


def start_server(
    install_dir_arg: Optional[str] = None,
    wait: bool = False,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Start llama-server from the master YAML config; return a status dict.

    The server is launched detached (survives the calling shell) with output
    appended to ``<install_dir>/server.log`` and its PID recorded in
    ``<install_dir>/server.pid``.
    """
    install_dir = install_dir_from(install_dir_arg)
    cfg_path = llama_config_path(install_dir)
    if not cfg_path.is_file():
        raise LifecycleError(
            f"master config not found: {cfg_path} (run `noerelay provision` first)"
        )
    cfg = load_llama_config(cfg_path.read_text(encoding="utf-8"))
    server = cfg["server"]

    exe = server_exe_path(install_dir)
    if not exe.is_file():
        raise LifecycleError(f"llama-server not found: {exe}")

    model = server.get("model") or ""
    if not model:
        raise LifecycleError("server.model is empty in llama.yaml")
    if not Path(model).is_file():
        raise LifecycleError(f"model file not found: {model}")

    args = [str(exe)] + server_args_from_config(cfg)
    install_dir.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_file(install_dir), "ab")

    if IS_WINDOWS:
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            args,
            cwd=str(install_dir / "llama"),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            close_fds=True,
        )
    else:
        proc = subprocess.Popen(
            args,
            cwd=str(install_dir / "llama"),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    log_fh.close()
    pid_file(install_dir).write_text(str(proc.pid), encoding="utf-8")

    result: Dict[str, Any] = {
        "started": True,
        "pid": proc.pid,
        "base_url": base_url_from(install_dir),
        "log": str(log_file(install_dir)),
        "command": " ".join(args),
    }
    if wait:
        ready = wait_for_ready(base_url_from(install_dir), timeout=timeout)
        result["ready"] = ready
        if not ready:
            raise LifecycleError(f"server did not become ready within {timeout}s")
    return result


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WINDOWS:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        return str(pid) in (out.stdout or "")
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def read_pid(install_dir: Path) -> Optional[int]:
    p = pid_file(install_dir)
    if not p.is_file():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def stop_server(install_dir_arg: Optional[str] = None, timeout: float = 20.0) -> Dict[str, Any]:
    """Stop the llama-server started by :func:`start_server`."""
    install_dir = install_dir_from(install_dir_arg)
    pid = read_pid(install_dir)
    if pid is None or not _pid_alive(pid):
        # clean stale pid file
        try:
            pid_file(install_dir).unlink()
        except OSError:
            pass
        return {"stopped": False, "reason": "not running"}

    if IS_WINDOWS:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, text=True, timeout=timeout,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.time() + timeout
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.2)
        if _pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    try:
        pid_file(install_dir).unlink()
    except OSError:
        pass
    return {"stopped": True, "pid": pid}


def server_status(install_dir_arg: Optional[str] = None) -> Dict[str, Any]:
    """Report whether the server process is alive and the API is reachable."""
    install_dir = install_dir_from(install_dir_arg)
    pid = read_pid(install_dir)
    alive = pid is not None and _pid_alive(pid)
    base = base_url_from(install_dir)
    reachable = False
    try:
        req = urllib.request.Request(f"{base}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            reachable = resp.status == 200
    except Exception:  # noqa: BLE001
        reachable = False
    return {
        "install_dir": str(install_dir),
        "pid": pid,
        "process_alive": alive,
        "base_url": base,
        "api_reachable": reachable,
    }


def wait_for_ready(base_url: str, timeout: float = 180.0, poll: float = 2.0) -> bool:
    """Poll ``/health`` until the server answers (model loaded)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{base_url}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(poll)
    return False


# ---------------------------------------------------------------------------
# Scheduled task creation (native, no PowerShell)
# ---------------------------------------------------------------------------


def schedule_task(
    install_dir_arg: Optional[str] = None,
    task_name: str = DEFAULT_TASK_NAME,
) -> Dict[str, Any]:
    """Register a logon scheduled task that starts the server.

    * Windows: native ``schtasks /Create`` (ONLOGON trigger).
    * macOS: LaunchAgent plist + ``launchctl load``.
    * Linux: systemd user unit + ``systemctl --user enable`` (best effort).
    """
    install_dir = install_dir_from(install_dir_arg)
    if IS_WINDOWS:
        return _schedule_windows(install_dir, task_name)
    if sys.platform == "darwin":
        return _schedule_macos(install_dir, task_name)
    return _schedule_linux(install_dir, task_name)


def _wrapper_path(install_dir: Path) -> Path:
    return install_dir / "bin" / ("start-server.bat" if IS_WINDOWS else "start-server.sh")


def _schedule_windows(install_dir: Path, task_name: str) -> Dict[str, Any]:
    wrapper = _wrapper_path(install_dir)
    if not wrapper.is_file():
        raise LifecycleError(f"start wrapper not found: {wrapper}")
    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", task_name,
        "/TR", f'"{wrapper}"',
        "/SC", "ONLOGON",
        "/RL", "LIMITED",
        "/IT",  # interactive (session) — matches the reference task
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise LifecycleError(
            f"schtasks failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return {
        "scheduled": True,
        "platform": "windows",
        "task_name": task_name,
        "trigger": "ONLOGON",
        "command": " ".join(cmd),
    }


def _schedule_macos(install_dir: Path, task_name: str) -> Dict[str, Any]:
    wrapper = _wrapper_path(install_dir)
    if not wrapper.is_file():
        raise LifecycleError(f"start wrapper not found: {wrapper}")
    label = "com.noerelay.llm"
    plist = install_dir / f"{label}.plist"
    plist.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        f'  <key>Label</key><string>{label}</string>\n'
        f'  <key>ProgramArguments</key><array><string>{wrapper}</string></array>\n'
        '  <key>RunAtLoad</key><true/>\n'
        '  <key>KeepAlive</key><false/>\n'
        '</dict></plist>\n',
        encoding="utf-8",
    )
    agents = Path.home() / "Library" / "LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    target = agents / f"{label}.plist"
    target.write_text(plist.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["launchctl", "load", str(target)], capture_output=True, timeout=30)
    return {
        "scheduled": True,
        "platform": "macos",
        "task_name": task_name,
        "trigger": "RunAtLoad (LaunchAgent)",
        "plist": str(target),
    }


def _schedule_linux(install_dir: Path, task_name: str) -> Dict[str, Any]:
    wrapper = _wrapper_path(install_dir)
    if not wrapper.is_file():
        raise LifecycleError(f"start wrapper not found: {wrapper}")
    unit = "noerelay-llm.service"
    units_dir = Path.home() / ".config" / "systemd" / "user"
    units_dir.mkdir(parents=True, exist_ok=True)
    (units_dir / unit).write_text(
        f"[Unit]\nDescription=NoeRelay local LLM server\n\n"
        "[Service]\nType=forking\nExecStart={wrapper}\n\n"
        "[Install]\nWantedBy=default.target\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["systemctl", "--user", "enable", unit],
        capture_output=True, text=True, timeout=30,
    )
    return {
        "scheduled": proc.returncode == 0,
        "platform": "linux",
        "task_name": task_name,
        "trigger": "systemd user unit (default.target)",
        "detail": proc.stderr.strip() or proc.stdout.strip(),
    }


def unschedule_task(install_dir_arg: Optional[str] = None, task_name: str = DEFAULT_TASK_NAME) -> Dict[str, Any]:
    """Remove the logon scheduled task created by :func:`schedule_task`."""
    install_dir = install_dir_from(install_dir_arg)
    if IS_WINDOWS:
        proc = subprocess.run(
            ["schtasks", "/Delete", "/F", "/TN", task_name],
            capture_output=True, text=True, timeout=30,
        )
        return {"unscheduled": proc.returncode == 0, "platform": "windows",
                "detail": proc.stderr.strip() or proc.stdout.strip()}
    if sys.platform == "darwin":
        target = Path.home() / "Library" / "LaunchAgents" / "com.noerelay.llm.plist"
        if target.is_file():
            subprocess.run(["launchctl", "unload", str(target)], capture_output=True, timeout=30)
            target.unlink()
        return {"unscheduled": True, "platform": "macos", "plist": str(target)}
    proc = subprocess.run(
        ["systemctl", "--user", "disable", "noerelay-llm.service"],
        capture_output=True, text=True, timeout=30,
    )
    return {"unscheduled": proc.returncode == 0, "platform": "linux",
            "detail": proc.stderr.strip() or proc.stdout.strip()}
