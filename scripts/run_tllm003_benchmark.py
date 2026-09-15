#!/usr/bin/env python3
"""T-LLM-003 benchmark orchestrator (NR-LLM-003).

The gpt-oss-20b quants need exclusive GPU access, but the session llama-server
(qwen3.8-27b on 127.0.0.1:8080) holds ~20 GB of VRAM and serves this agent
session. This orchestrator:

  1. Sets a self-expiring maintenance flag (C:\\LLM\\MAINTENANCE) so the OS-level
     LLM Watchdog stays quiet while we own the GPUs.
  2. Stops the session server via the sanctioned ``C:\\LLM\\stop-llama-server.ps1``
     (never a raw PID kill).
  3. Waits for VRAM to be released.
  4. Runs ``scripts/benchmark_local_models.py`` with exclusive access.
  5. ALWAYS restarts the session server via ``C:\\LLM\\start-llama-server.ps1``
     (detached, so it survives this process), then clears the maintenance flag
     and waits for ``http://127.0.0.1:8080/health`` to return 200.

Safety layers (the agent session is never left without its backend):
  * The restart is in a ``finally`` block, so it runs on success OR exception.
  * The maintenance flag is cleared as soon as the restart is launched, so the
    LLM Watchdog (a 1-minute scheduled task) can revive the server if the
    launched process fails.
  * If this orchestrator is hard-killed mid-benchmark, the flag expires after
    90 minutes and the watchdog revives the server.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STOP = r"C:\LLM\stop-llama-server.ps1"
START = r"C:\LLM\start-llama-server.ps1"
HEALTH = "http://127.0.0.1:8080/health"
VRAM_FREE_THRESHOLD_MIB = 2048
MAINTENANCE_FLAG = Path(r"C:\LLM\MAINTENANCE")


def log(msg: str) -> None:
    print(f"[orchestrator] {msg}", flush=True)


def vram_total_mib() -> int:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=30, check=True,
    )
    total = 0
    for line in out.stdout.splitlines():
        t = line.strip()
        if t.isdigit():
            total += int(t)
    if not any(line.strip().isdigit() for line in out.stdout.splitlines()):
        raise RuntimeError("nvidia-smi returned no VRAM readings")
    return total


def wait_vram_free(timeout: float = 120.0) -> None:
    deadline = time.time() + timeout
    total = vram_total_mib()
    while time.time() < deadline and total >= VRAM_FREE_THRESHOLD_MIB:
        time.sleep(3)
        total = vram_total_mib()
    log(f"VRAM used total: {total} MiB")
    if total >= VRAM_FREE_THRESHOLD_MIB:
        raise TimeoutError("GPUs did not become free; refusing shared benchmark")


def health_ok() -> bool:
    try:
        with urllib.request.urlopen(HEALTH, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def wait_healthy(timeout: float = 300.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if health_ok():
            return True
        time.sleep(3)
    return False


def set_maintenance() -> None:
    try:
        MAINTENANCE_FLAG.write_text(str(int(time.time())), encoding="utf-8")
        log(f"maintenance flag set: {MAINTENANCE_FLAG}")
    except OSError as e:
        raise RuntimeError(f"could not set maintenance flag: {e}") from e


def clear_maintenance() -> None:
    try:
        if MAINTENANCE_FLAG.exists():
            MAINTENANCE_FLAG.unlink()
            log("maintenance flag cleared")
    except OSError as e:
        log(f"WARNING: could not clear maintenance flag: {e}")


def main() -> int:
    log("=== T-LLM-003 benchmark orchestrator ===")
    set_maintenance()

    bench_rc = 1
    try:
        log(f"[1/4] Stopping session llama-server via {STOP}")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", STOP],
            check=True, timeout=120,
        )

        log("[2/4] Waiting for VRAM release")
        wait_vram_free()

        log("[3/4] Running benchmark (exclusive GPU access)")
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(REPO / "src"), str(REPO / "reference")])
        bench_rc = subprocess.call(
            [sys.executable, str(REPO / "scripts" / "benchmark_local_models.py"),
             "--root", str(REPO)],
            cwd=str(REPO), env=env,
        )
    finally:
        log(f"[4/4] Restarting session llama-server via {START}")
        try:
            restart_log = REPO / "evidence" / "LLM-01" / "T-LLM-003-server-restart.log"
            restart_log.parent.mkdir(parents=True, exist_ok=True)
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | \
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            with open(restart_log, "ab") as logf:
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", START],
                    creationflags=flags, stdout=logf, stderr=subprocess.STDOUT,
                )
        finally:
            clear_maintenance()  # Let the watchdog recover even if launch fails.
        log("Waiting for session server to become healthy on :8080 ...")
        if wait_healthy():
            log("session server healthy on :8080")
        else:
            bench_rc = 1
            log("WARNING: session server NOT healthy after 300s - the LLM Watchdog "
                "will retry; check C:\\LLM if it does not come up")

    log(f"=== benchmark exit code: {bench_rc} ===")
    return bench_rc


if __name__ == "__main__":
    sys.exit(main())
