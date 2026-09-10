#!/usr/bin/env python3
"""
NoeRelay Unified Installer
==========================

A polished, interactive installer that sets up the **complete** local AI
stack on Windows in one place:

* The **NoeRelay CLI** (bundled, stdlib-only — no pip/venv needed)
* A dual-GPU **llama.cpp** inference server (pinned CUDA build)
* A **GGUF model** (sensible default + catalog of alternatives)
* Startup / stop / scheduled-task scripts
* NoeRelay configuration wired to the local server

Everything is installed into a single directory (default ``C:\\LLM``) so the
whole stack is self-contained and easy to move or remove.

Layout produced
---------------
    <install_dir>\\
    ├── llama\\                  # llama.cpp binaries + CUDA runtime DLLs
    ├── noerelay\\               # bundled NoeRelay CLI package
    ├── noerelay.cmd            # CLI launcher
    ├── start-llama-server.ps1
    ├── stop-llama-server.ps1
    ├── create-scheduled-task.ps1
    ├── create-scheduled-task.cmd
    ├── config.json             # machine-readable install config
    └── README.md
    <models_dir>\\              # GGUF model files (default C:\\Models)

Usage
-----
    python installer/installer.py                 # interactive
    python installer/installer.py --yes           # non-interactive (defaults)
    python installer/installer.py --model mistral-24b
    python installer/installer.py --install-dir D:\\LLM --no-scheduled-task

Requires: Python 3.9+, ``rich``, ``requests``, ``huggingface_hub``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Force UTF-8 output on Windows (cp1252 cannot render check/cross marks).
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )
    from rich.prompt import Confirm, IntPrompt, Prompt
except ImportError:  # pragma: no cover
    print("This installer requires the 'rich' package. Install it with:")
    print("    pip install rich requests huggingface_hub")
    sys.exit(1)

console = Console()

# ---------------------------------------------------------------------------
# Pinned llama.cpp build
# ---------------------------------------------------------------------------

LLAMA_BUILD_TAG = "b10894"
LLAMA_BUILD_CUDA = "13.3"  # required for Blackwell (RTX 5060 Ti, sm_120)
LLAMA_BUILD_ARCH = "x64"

LLAMA_BASE_URL = (
    f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_BUILD_TAG}"
)
LLAMA_STD_ZIP = (
    f"llama-{LLAMA_BUILD_TAG}-bin-win-cuda-{LLAMA_BUILD_CUDA}-{LLAMA_BUILD_ARCH}.zip"
)
LLAMA_CUDART_ZIP = (
    f"cudart-llama-bin-win-cuda-{LLAMA_BUILD_CUDA}-{LLAMA_BUILD_ARCH}.zip"
)

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------


@dataclass
class ModelEntry:
    key: str
    name: str
    repo_id: str
    quant: str
    size_gb: float
    vram_gb: float
    notes: str
    default: bool = False


MODEL_CATALOG: list[ModelEntry] = [
    ModelEntry(
        key="qwen3.8-27b",
        name="Qwen3.8 27B (Q4_K_M)",
        repo_id="unsloth/Qwen3.8-27B-GGUF",
        quant="Q4_K_M",
        size_gb=15.3,
        vram_gb=18,
        notes="Default. Strong all-rounder, fits dual-GPU 28 GB.",
        default=True,
    ),
    ModelEntry(
        key="qwen3-32b",
        name="Qwen3 32B (Q4_K_M)",
        repo_id="unsloth/Qwen3-32B-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        vram_gb=24,
        notes="Larger, higher quality. Needs most of the 28 GB.",
    ),
    ModelEntry(
        key="qwen2.5-32b",
        name="Qwen2.5 32B Instruct (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-32B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        vram_gb=24,
        notes="Solid instruct model, good tool-use.",
    ),
    ModelEntry(
        key="mistral-24b",
        name="Mistral Small 24B (Q4_K_M)",
        repo_id="unsloth/Mistral-Small-3.1-24B-Instruct-2507-GGUF",
        quant="Q4_K_M",
        size_gb=14.5,
        vram_gb=17,
        notes="Fast, efficient, strong for its size.",
    ),
    ModelEntry(
        key="deepseek-r1-32b",
        name="DeepSeek-R1 Distill Qwen 32B (Q4_K_M)",
        repo_id="bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        vram_gb=24,
        notes="Reasoning-focused (chain-of-thought).",
    ),
    ModelEntry(
        key="llama-3.3-70b",
        name="Llama 3.3 70B (Q4_K_M)",
        repo_id="unsloth/Llama-3.3-70B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=42.0,
        vram_gb=48,
        notes="LARGE. Exceeds 28 GB VRAM; will offload to CPU/RAM.",
    ),
]

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class GPU:
    index: int
    name: str
    total_mib: int
    free_mib: int
    display_active: bool
    pci_bus_id: str = ""


@dataclass
class InstallPlan:
    install_dir: Path = Path(r"C:\LLM")
    models_dir: Path = Path(r"C:\Models")
    host: str = "127.0.0.1"
    port: int = 8080
    ctx_size: int = 16384
    parallel: int = 1
    tensor_split: str = "10,15"
    model: ModelEntry = field(default_factory=lambda: MODEL_CATALOG[0])
    custom_repo: Optional[str] = None
    custom_quant: Optional[str] = None
    register_scheduled_task: bool = True
    bundle_noerelay: bool = True
    noerelay_src: Optional[Path] = None  # override for the noerelay package source
    gpus: list[GPU] = field(default_factory=list)

    @property
    def llama_dir(self) -> Path:
        return self.install_dir / "llama"

    @property
    def llama_server(self) -> Path:
        return self.llama_dir / "llama-server.exe"

    @property
    def noerelay_pkg_dir(self) -> Path:
        return self.install_dir / "noerelay"

    @property
    def model_file(self) -> Path:
        return self.models_dir / f"{self.model.key}.gguf"

    @property
    def api_base(self) -> str:
        return f"http://{self.host}:{self.port}"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def run_cmd(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def http_get(url: str, dest: Path, progress: Progress, task_id: int) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "noerelay-installer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as fh:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        if total:
            progress.update(task_id, total=total)
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            fh.write(chunk)
            progress.update(task_id, advance=len(chunk))


# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------


def detect_gpus() -> list[GPU]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    res = run_cmd(
        [
            exe,
            "--query-gpu=index,name,memory.total,memory.free,display_active,pci.bus_id",
            "--format=csv,noheader,nounits",
        ]
    )
    if res.returncode != 0:
        return []
    gpus: list[GPU] = []
    for line in res.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            gpus.append(
                GPU(
                    index=int(parts[0]),
                    name=parts[1],
                    total_mib=int(parts[2]),
                    free_mib=int(parts[3]),
                    display_active=parts[4].lower() == "enabled",
                    pci_bus_id=parts[5] if len(parts) > 5 else "",
                )
            )
        except ValueError:
            continue
    return gpus


def recommend_split(gpus: list[GPU]) -> str:
    """
    Recommend a relative tensor-split.

    Weights are proportional to VRAM, but the display-driving GPU is reduced
    by 20% to leave headroom for the desktop compositor. Weights are
    normalized to integers summing to ~25 (matches the 10,15 style).
    """
    if not gpus:
        return "10,15"
    raw = []
    for g in gpus:
        factor = 0.8 if g.display_active else 1.0
        raw.append(g.total_mib * factor)
    total = sum(raw)
    if total == 0:
        return "10,15"
    scaled = [max(1, round(r / total * 25)) for r in raw]
    return ",".join(str(s) for s in scaled)


# ---------------------------------------------------------------------------
# llama.cpp build
# ---------------------------------------------------------------------------


def ensure_llama_build(plan: InstallPlan) -> None:
    if plan.llama_server.exists():
        console.print(f"[green]✓[/green] llama.cpp already present at {plan.llama_server}")
        return

    plan.llama_dir.mkdir(parents=True, exist_ok=True)
    tmp = plan.install_dir / "_dl"
    tmp.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel.fit(
            f"[bold]llama.cpp build[/bold]  {LLAMA_BUILD_TAG} (CUDA {LLAMA_BUILD_CUDA} {LLAMA_BUILD_ARCH})\n"
            f"Self-contained (bundles CUDA runtime). Target: [cyan]{plan.llama_dir}[/cyan]",
            border_style="blue",
        )
    )

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        for label, fname in [
            ("Standard build (executables)", LLAMA_STD_ZIP),
            ("CUDA runtime bundle (DLLs)", LLAMA_CUDART_ZIP),
        ]:
            dest = tmp / fname
            if dest.exists() and dest.stat().st_size > 1_000_000:
                console.print(f"[dim]  cached: {fname}[/dim]")
                continue
            task = progress.add_task(label, total=None)
            console.print(f"  [cyan]↓[/cyan] {label}")
            http_get(f"{LLAMA_BASE_URL}/{fname}", dest, progress, task)

    console.print("  [cyan]•[/cyan] Extracting standard build…")
    with zipfile.ZipFile(tmp / LLAMA_STD_ZIP) as zf:
        zf.extractall(plan.llama_dir)

    console.print("  [cyan]•[/cyan] Extracting CUDA runtime DLLs…")
    with zipfile.ZipFile(tmp / LLAMA_CUDART_ZIP) as zf:
        for member in zf.namelist():
            if member.lower().endswith(".dll"):
                zf.extract(member, plan.llama_dir)

    shutil.rmtree(tmp, ignore_errors=True)

    if not plan.llama_server.exists():
        console.print("[red]✗[/red] llama-server.exe not found after extraction.")
        sys.exit(1)
    console.print(f"[green]✓[/green] llama.cpp installed to {plan.llama_dir}")


# ---------------------------------------------------------------------------
# Model download
# ---------------------------------------------------------------------------


def resolve_gguf_file(repo_id: str, quant: str) -> Optional[str]:
    """Find the best single-file GGUF matching the quant in a HF repo."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        console.print("[yellow]! huggingface_hub not installed; using filename guess.[/yellow]")
        return None
    api = HfApi()
    try:
        files = api.list_repo_files(repo_id)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]! Could not list repo {repo_id}: {exc}[/yellow]")
        return None

    candidates = [
        f for f in files if f.lower().endswith(".gguf") and quant.lower() in f.lower()
    ]
    single = [f for f in candidates if re.search(r"of-\d+", f) is None]
    pool = single or candidates
    if not pool:
        return None

    def size_key(f: str) -> int:
        m = re.search(r"(\d+)[._-]gguf$", f, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    pool_sorted = sorted(pool, key=lambda f: (size_key(f), len(f)), reverse=True)
    return pool_sorted[0]


def _adopt_existing_model(plan: InstallPlan) -> bool:
    """
    If the models dir already contains a single .gguf (e.g. from a previous
    manual setup), adopt it as the canonical model file instead of
    re-downloading. Returns True if a model was adopted.
    """
    if plan.model_file.exists():
        console.print(f"[green]✓[/green] Model already present: {plan.model_file}")
        return True
    existing = sorted(plan.models_dir.glob("*.gguf"))
    if len(existing) == 1:
        src = existing[0]
        shutil.move(str(src), str(plan.model_file))
        size_gb = plan.model_file.stat().st_size / (1024**3)
        console.print(
            f"[green]✓[/green] Adopted existing model: {src.name} → {plan.model_file.name} ({size_gb:.2f} GB)"
        )
        return True
    return False


def download_model(plan: InstallPlan) -> None:
    plan.models_dir.mkdir(parents=True, exist_ok=True)
    if _adopt_existing_model(plan):
        return

    repo = plan.custom_repo or plan.model.repo_id
    quant = plan.custom_quant or plan.model.quant

    console.print(
        Panel.fit(
            f"[bold]Model[/bold]  {plan.model.name}\n"
            f"Repo: [cyan]{repo}[/cyan]   Quant: [cyan]{quant}[/cyan]\n"
            f"Target: [cyan]{plan.model_file}[/cyan]",
            border_style="green",
        )
    )

    filename = resolve_gguf_file(repo, quant)
    if filename is None:
        filename = f"{plan.model.key.replace('.', '')}-{quant}.gguf"
        console.print(f"[yellow]! Using guessed filename: {filename}[/yellow]")

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        console.print("[red]✗ huggingface_hub is required to download models.[/red]")
        console.print("  Install with:  pip install huggingface_hub")
        sys.exit(1)

    console.print(f"  [cyan]↓[/cyan] Downloading [bold]{filename}[/bold] from {repo} …")
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        progress.add_task("Downloading model", total=None)
        hf_hub_download(
            repo_id=repo,
            filename=filename,
            local_dir=str(plan.models_dir),
            local_dir_use_subfolders=False,
            tqdm_class=None,
            force_download=False,
        )

    src = plan.models_dir / filename
    if src.exists() and src != plan.model_file:
        shutil.move(str(src), str(plan.model_file))
    elif not plan.model_file.exists():
        console.print(f"[red]✗ Model file not found at {plan.model_file}[/red]")
        sys.exit(1)

    size_gb = plan.model_file.stat().st_size / (1024**3)
    console.print(f"[green]✓[/green] Model ready: {plan.model_file} ({size_gb:.2f} GB)")


# ---------------------------------------------------------------------------
# NoeRelay bundling
# ---------------------------------------------------------------------------


def find_noerelay_src(plan: InstallPlan) -> Optional[Path]:
    """Locate the noerelay package source to bundle."""
    if plan.noerelay_src and (plan.noerelay_src / "cli.py").exists():
        return plan.noerelay_src
    # Default: <repo>/src/noerelay relative to this installer file.
    here = Path(__file__).resolve().parent
    for cand in (
        here.parent / "src" / "noerelay",
        here / "noerelay",
        Path.cwd() / "src" / "noerelay",
    ):
        if (cand / "cli.py").exists():
            return cand
    return None


def bundle_noerelay(plan: InstallPlan) -> None:
    """Copy the noerelay package into the install dir + create a launcher."""
    src = find_noerelay_src(plan)
    if src is None:
        console.print(
            "[yellow]! NoeRelay package source not found — skipping bundle. "
            "Use --noerelay-src to point at the package.[/yellow]"
        )
        return

    plan.noerelay_pkg_dir.mkdir(parents=True, exist_ok=True)
    # Copy package files
    for f in src.iterdir():
        if f.is_file() and f.suffix == ".py":
            shutil.copy2(f, plan.noerelay_pkg_dir / f.name)
    console.print(f"[green]✓[/green] NoeRelay CLI bundled to {plan.noerelay_pkg_dir}")

    # Launcher
    launcher = plan.install_dir / "noerelay.cmd"
    launcher.write_text(
        NOERELAY_LAUNCHER.format(install_dir=str(plan.install_dir)), encoding="utf-8"
    )
    console.print(f"[green]✓[/green] CLI launcher: {launcher}")


# ---------------------------------------------------------------------------
# Script + config generation
# ---------------------------------------------------------------------------

NOERELAY_LAUNCHER = """@echo off
rem NoeRelay CLI launcher (bundled with the local LLM stack)
set "NOERELAY_HOME={install_dir}"
set "PYTHONPATH=%NOERELAY_HOME%;%PYTHONPATH%"
python -m noerelay.cli %*
"""

START_SCRIPT = """#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the local llama.cpp multi-GPU inference server.
.DESCRIPTION
    Generated by the NoeRelay Unified Installer.
    Model: {model_name}
    GPU split: {split} (layer mode)
    Context: {ctx}
.NOTES
    llama.cpp build: {build}
#>
$ErrorActionPreference = "Stop"

$LlamaServer = "{llama_server}"
$Model = "{model}"

if (-not (Test-Path $LlamaServer)) {{ throw "llama-server.exe not found at $LlamaServer" }}
if (-not (Test-Path $Model)) {{ throw "Model not found at $Model" }}

Write-Host "Starting llama.cpp inference server…"
Write-Host "  Model:   $Model"
Write-Host "  Host:    {host}:{port}"
Write-Host "  Split:   {split} (layer)"
Write-Host "  Context: {ctx}"
Write-Host ""

& $LlamaServer `
    -m $Model `
    --host {host} `
    --port {port} `
    --n-gpu-layers 999 `
    --split-mode layer `
    --tensor-split {split} `
    --ctx-size {ctx} `
    --parallel {parallel} `
    --metrics
"""

STOP_SCRIPT = """#Requires -Version 5.1
<#
.SYNOPSIS
    Stops the llama.cpp server.
#>
$ErrorActionPreference = "Stop"
Write-Host "Stopping llama-server…"
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
if (Get-Process llama-server -ErrorAction SilentlyContinue) {
    Write-Warning "llama-server may still be running"
} else {
    Write-Host "llama-server stopped"
}
"""

SCHEDULED_TASK_PS1 = """#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoProfile -ExecutionPolicy Bypass -File "{start_script}"'
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
Register-ScheduledTask -TaskName "Local LLM Server" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Starts the local llama.cpp multi-GPU inference server" -Force
Write-Host "Scheduled task 'Local LLM Server' created."
Get-ScheduledTask -TaskName "Local LLM Server" | Select-Object TaskName, State | Format-Table
"""

SCHEDULED_TASK_CMD = """@echo off
:: Run as Administrator to create the "Local LLM Server" scheduled task.
echo Creating "Local LLM Server" scheduled task...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "{task_ps1}"
echo.
pause
"""



def generate_scripts(plan: InstallPlan) -> None:
    plan.install_dir.mkdir(parents=True, exist_ok=True)

    start = plan.install_dir / "start-llama-server.ps1"
    start.write_text(
        START_SCRIPT.format(
            model_name=plan.model.name,
            split=plan.tensor_split,
            ctx=plan.ctx_size,
            build=LLAMA_BUILD_TAG,
            llama_server=str(plan.llama_server),
            model=str(plan.model_file),
            host=plan.host,
            port=plan.port,
            parallel=plan.parallel,
        ),
        encoding="utf-8",
    )

    (plan.install_dir / "stop-llama-server.ps1").write_text(STOP_SCRIPT, encoding="utf-8")

    task_ps1 = plan.install_dir / "create-scheduled-task.ps1"
    task_ps1.write_text(
        SCHEDULED_TASK_PS1.format(start_script=str(start)), encoding="utf-8"
    )
    (plan.install_dir / "create-scheduled-task.cmd").write_text(
        SCHEDULED_TASK_CMD.format(task_ps1=str(task_ps1)), encoding="utf-8"
    )

    # Machine-readable config
    config = {
        "install_dir": str(plan.install_dir),
        "models_dir": str(plan.models_dir),
        "llama_server": str(plan.llama_server),
        "noerelay_cli": str(plan.install_dir / "noerelay.cmd"),
        "model": str(plan.model_file),
        "model_name": plan.model.name,
        "model_repo": plan.custom_repo or plan.model.repo_id,
        "host": plan.host,
        "port": plan.port,
        "api_base": f"{plan.api_base}/v1",
        "tensor_split": plan.tensor_split,
        "ctx_size": plan.ctx_size,
        "parallel": plan.parallel,
        "build": LLAMA_BUILD_TAG,
        "gpus": [
            {
                "index": g.index,
                "name": g.name,
                "total_mib": g.total_mib,
                "display_active": g.display_active,
            }
            for g in plan.gpus
        ],
    }
    (plan.install_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    # README (from the bundled template, with safe token replacement)
    readme_template = Path(__file__).resolve().parent / "README_TEMPLATE.md"
    if readme_template.exists():
        readme = readme_template.read_text(encoding="utf-8")
        for token, value in {
            "__DATE__": time.strftime("%Y-%m-%d %H:%M"),
            "__BUILD__": LLAMA_BUILD_TAG,
            "__MODEL__": str(plan.model_file),
            "__MODEL_NAME__": plan.model.name,
            "__API_BASE__": plan.api_base,
            "__SPLIT__": plan.tensor_split,
            "__CTX__": str(plan.ctx_size),
            "__PARALLEL__": str(plan.parallel),
            "<install_dir>": str(plan.install_dir),
            "<models_dir>": str(plan.models_dir),
        }.items():
            readme = readme.replace(token, value)
        (plan.install_dir / "README.md").write_text(readme, encoding="utf-8")
    else:
        console.print("[yellow]! README_TEMPLATE.md not found; skipping README.[/yellow]")

    console.print(f"[green]✓[/green] Scripts + config + README written to {plan.install_dir}")


def configure_noerelay(plan: InstallPlan) -> None:
    """Write ~/.noerelay/config.json pointing at the local server."""
    config_path = Path.home() / ".noerelay" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    existing.update(
        {
            "base_url": plan.api_base,
            "api_key": existing.get("api_key", "noerelay-local"),
            "model": plan.model.key,
            "model_raw": plan.model.key,
            "project_id": existing.get("project_id", "default"),
        }
    )
    config_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] NoeRelay configured → {config_path}")


# ---------------------------------------------------------------------------
# Scheduled task
# ---------------------------------------------------------------------------


def register_scheduled_task(plan: InstallPlan) -> None:
    task_ps1 = plan.install_dir / "create-scheduled-task.ps1"
    if not is_windows():
        console.print("[yellow]! Scheduled tasks are Windows-only; skipping.[/yellow]")
        return
    if not is_admin():
        console.print(
            "[yellow]! Not running as administrator — Scheduled Task NOT registered.[/yellow]"
        )
        console.print(f"  To register later, run as admin:  [cyan]{task_ps1}[/cyan]")
        return
    res = run_cmd(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(task_ps1)],
        capture=False,
    )
    if res.returncode == 0:
        console.print("[green]✓[/green] Scheduled task 'Local LLM Server' registered.")
    else:
        console.print("[yellow]! Scheduled task registration returned an error.[/yellow]")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify(plan: InstallPlan) -> None:
    console.print(Panel.fit("[bold]Verification[/bold]", border_style="magenta"))

    cli = plan.llama_dir / "llama-cli.exe"
    if cli.exists():
        res = run_cmd([str(cli), "--list-devices"])
        console.print("[dim]" + res.stdout.strip() + "[/dim]")
    else:
        console.print("[yellow]! llama-cli.exe not found; skipping device check.[/yellow]")

    server = plan.llama_server
    if not server.exists() or not plan.model_file.exists():
        console.print("[yellow]! Server or model missing; skipping API check.[/yellow]")
        return

    console.print(f"  [cyan]•[/cyan] Starting a short-lived server on {plan.host}:{plan.port} …")
    proc = subprocess.Popen(
        [
            str(server),
            "-m", str(plan.model_file),
            "--host", plan.host,
            "--port", str(plan.port),
            "--n-gpu-layers", "999",
            "--split-mode", "layer",
            "--tensor-split", plan.tensor_split,
            "--ctx-size", str(min(plan.ctx_size, 4096)),
            "--parallel", "1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        ok = False
        for _ in range(90):
            time.sleep(1)
            try:
                with urllib.request.urlopen(
                    f"{plan.api_base}/v1/models", timeout=3
                ) as resp:
                    if resp.status == 200:
                        ok = True
                        break
            except Exception:
                continue
        if ok:
            console.print("[green]✓[/green] API is responding at /v1/models")
        else:
            console.print("[yellow]! API did not respond in time (model may still be loading).[/yellow]")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        console.print("  [dim]Smoke-test server stopped.[/dim]")


# ---------------------------------------------------------------------------
# Interactive flow
# ---------------------------------------------------------------------------


def print_banner() -> None:
    console.print(
        Panel(
            "[bold cyan]NoeRelay · Unified Installer[/bold cyan]\n"
            "[dim]NoeRelay CLI + dual-GPU llama.cpp + model, in one place[/dim]",
            border_style="cyan",
            expand=False,
        )
    )


def preflight(plan: InstallPlan) -> None:
    console.print(Panel.fit("[bold]Preflight checks[/bold]", border_style="blue"))
    checks = Table(show_header=False, box=None, pad_edge=False)
    checks.add_column("Check", style="bold")
    checks.add_column("Result")

    checks.add_row("OS", "Windows" if is_windows() else f"{platform.system()} (non-Windows)")
    if not is_windows():
        console.print("[yellow]! This installer targets Windows. Continuing anyway.[/yellow]")

    py_ok = sys.version_info >= (3, 9)
    checks.add_row("Python", f"{platform.python_version()} {'✓' if py_ok else '✗ (need 3.9+)'}")
    checks.add_row("nvidia-smi", "found" if shutil.which("nvidia-smi") else "[red]NOT FOUND[/red]")

    try:
        free_gb = shutil.disk_usage(
            str(plan.install_dir if plan.install_dir.exists() else Path("C:\\"))
        ).free / (1024**3)
        need = plan.model.size_gb + 5
        checks.add_row(
            "Disk free",
            f"{free_gb:.0f} GB {'✓' if free_gb > need else '[yellow]low[/yellow]'} (need ~{need:.0f} GB)",
        )
    except Exception:
        pass

    checks.add_row("Admin", "yes" if is_admin() else "no (needed only for Scheduled Task)")
    checks.add_row("NoeRelay src", "found" if find_noerelay_src(plan) else "[yellow]not found[/yellow]")
    console.print(checks)


def choose_gpus(plan: InstallPlan, yes: bool) -> None:
    plan.gpus = detect_gpus()
    if not plan.gpus:
        console.print(
            "[yellow]! No NVIDIA GPUs detected via nvidia-smi. Using default split 10,15.[/yellow]"
        )
        return

    t = Table(title="Detected GPUs")
    t.add_column("#", style="cyan")
    t.add_column("GPU")
    t.add_column("VRAM", justify="right")
    t.add_column("Free", justify="right")
    t.add_column("Display")
    for g in plan.gpus:
        t.add_row(
            str(g.index),
            g.name,
            f"{g.total_mib/1024:.1f} GB",
            f"{g.free_mib/1024:.1f} GB",
            "[green]yes[/green]" if g.display_active else "no",
        )
    console.print(t)

    rec = recommend_split(plan.gpus)
    if yes:
        plan.tensor_split = rec
        console.print(f"[dim]Recommended tensor-split: {rec}[/dim]")
        return

    chosen = Prompt.ask(
        "Tensor-split (weights per GPU, in CUDA order)", default=rec, console=console
    ).strip()
    plan.tensor_split = chosen or rec
    console.print(f"[dim]Using tensor-split: {plan.tensor_split}[/dim]")


def choose_model(plan: InstallPlan, yes: bool) -> None:
    default = next((m for m in MODEL_CATALOG if m.default), MODEL_CATALOG[0])
    if yes:
        plan.model = default
        console.print(f"[dim]Model: {default.name}[/dim]")
        return

    t = Table(title="Model catalog")
    t.add_column("#", style="cyan")
    t.add_column("Model")
    t.add_column("Size", justify="right")
    t.add_column("VRAM", justify="right")
    t.add_column("Notes", max_width=48)
    for i, m in enumerate(MODEL_CATALOG, start=1):
        marker = " [bold green]★ default[/bold green]" if m.default else ""
        t.add_row(str(i), m.name + marker, f"{m.size_gb:.1f} GB", f"~{m.vram_gb} GB", m.notes)
    t.add_row("[dim]c[/dim]", "[dim]Custom HuggingFace repo…[/dim]", "", "", "")
    console.print(t)

    choice = Prompt.ask(
        "Select a model (number, or 'c' for custom)",
        default=str(next(i for i, m in enumerate(MODEL_CATALOG, start=1) if m.default)),
        console=console,
    ).strip().lower()

    if choice == "c":
        repo = Prompt.ask("HuggingFace repo id (e.g. unsloth/Qwen3-32B-GGUF)", console=console).strip()
        quant = Prompt.ask("Quantization (e.g. Q4_K_M)", default="Q4_K_M", console=console).strip()
        plan.custom_repo = repo
        plan.custom_quant = quant
        plan.model = ModelEntry(
            key="custom",
            name=f"Custom ({repo.split('/')[-1]})",
            repo_id=repo,
            quant=quant,
            size_gb=0,
            vram_gb=0,
            notes="Custom selection",
        )
        return

    try:
        idx = int(choice) - 1
        plan.model = MODEL_CATALOG[idx]
    except (ValueError, IndexError):
        plan.model = default
    console.print(f"[dim]Selected: {plan.model.name}[/dim]")


def choose_settings(plan: InstallPlan, yes: bool) -> None:
    if yes:
        return
    plan.install_dir = Path(
        Prompt.ask("Install directory", default=str(plan.install_dir), console=console).strip()
    )
    plan.models_dir = Path(
        Prompt.ask("Model directory", default=str(plan.models_dir), console=console).strip()
    )
    plan.port = IntPrompt.ask("Port", default=plan.port, console=console)
    plan.ctx_size = IntPrompt.ask("Context size", default=plan.ctx_size, console=console)
    if not Confirm.ask(
        "Register a logon Scheduled Task?", default=plan.register_scheduled_task, console=console
    ):
        plan.register_scheduled_task = False


def print_summary(plan: InstallPlan) -> None:
    t = Table(title="Install summary", show_header=False)
    t.add_column("Item", style="bold cyan")
    t.add_column("Value")
    t.add_row("llama.cpp", f"{LLAMA_BUILD_TAG} (CUDA {LLAMA_BUILD_CUDA})")
    t.add_row("NoeRelay CLI", "bundled" if plan.bundle_noerelay else "skipped")
    t.add_row("Install dir", str(plan.install_dir))
    t.add_row("Model", f"{plan.model.name}  →  {plan.model_file}")
    t.add_row("API base", f"{plan.api_base}/v1")
    t.add_row("Tensor-split", plan.tensor_split)
    t.add_row("Context", str(plan.ctx_size))
    t.add_row("Parallel", str(plan.parallel))
    t.add_row("Scheduled task", "yes" if plan.register_scheduled_task else "no")
    console.print(t)
    console.print(
        "\n[bold]Point your apps at:[/bold]  [cyan]{api}/v1[/cyan]  "
        "(API key: any non-empty string)".format(api=plan.api_base)
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NoeRelay Unified Installer")
    p.add_argument("--yes", "-y", action="store_true", help="Non-interactive; accept defaults")
    p.add_argument("--model", help="Model key from the catalog (e.g. mistral-24b)")
    p.add_argument("--install-dir", help="Install directory (default C:\\LLM)")
    p.add_argument("--models-dir", help="Model directory (default C:\\Models)")
    p.add_argument("--port", type=int, help="Server port (default 8080)")
    p.add_argument("--ctx", type=int, help="Context size (default 16384)")
    p.add_argument("--split", help="Tensor-split (default: auto-recommended)")
    p.add_argument("--no-scheduled-task", action="store_true", help="Skip Scheduled Task")
    p.add_argument("--no-noerelay", action="store_true", help="Skip bundling the NoeRelay CLI")
    p.add_argument("--noerelay-src", help="Path to the noerelay package source")
    p.add_argument("--skip-download", action="store_true", help="Skip llama.cpp + model downloads")
    p.add_argument("--skip-verify", action="store_true", help="Skip verification")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    yes = args.yes

    plan = InstallPlan()
    if args.install_dir:
        plan.install_dir = Path(args.install_dir)
    if args.models_dir:
        plan.models_dir = Path(args.models_dir)
    if args.port:
        plan.port = args.port
    if args.ctx:
        plan.ctx_size = args.ctx
    if args.split:
        plan.tensor_split = args.split
    if args.no_scheduled_task:
        plan.register_scheduled_task = False
    if args.no_noerelay:
        plan.bundle_noerelay = False
    if args.noerelay_src:
        plan.noerelay_src = Path(args.noerelay_src)
    if args.model:
        match = next((m for m in MODEL_CATALOG if m.key == args.model), None)
        if match:
            plan.model = match
        else:
            console.print(f"[red]Unknown model key '{args.model}'.[/red]")
            console.print("Available: " + ", ".join(m.key for m in MODEL_CATALOG))
            return 2

    print_banner()
    preflight(plan)

    if not yes:
        console.print()
        if not Confirm.ask("Proceed with installation?", default=True, console=console):
            console.print("[dim]Aborted.[/dim]")
            return 1

    console.print()
    choose_gpus(plan, yes)
    if not args.model:
        choose_model(plan, yes)
    if not yes:
        choose_settings(plan, yes)

    console.print()
    print_summary(plan)

    if not args.skip_download:
        console.print()
        ensure_llama_build(plan)
        console.print()
        download_model(plan)

    console.print()
    if plan.bundle_noerelay:
        bundle_noerelay(plan)
        console.print()
    generate_scripts(plan)
    configure_noerelay(plan)

    if plan.register_scheduled_task:
        console.print()
        register_scheduled_task(plan)

    if not args.skip_verify:
        console.print()
        verify(plan)

    console.print()
    console.print(
        Panel(
            "[bold green]Installation complete.[/bold green]\n"
            f"Start the server:  [cyan]{plan.install_dir / 'start-llama-server.ps1'}[/cyan]\n"
            f"NoeRelay CLI:      [cyan]{plan.install_dir / 'noerelay.cmd'}[/cyan]\n"
            f"API base:          [cyan]{plan.api_base}/v1[/cyan]",
            border_style="green",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
