"""
Cross-platform installer for the NoeRelay local LLM stack.

Consumes a :class:`noerelay.provision.ProvisionPlan` and materializes the whole
stack on disk:

* downloads the correct **llama.cpp** build for the detected backend/OS/arch,
* creates a **virtualenv** and installs the **noerelay** CLI into it,
* downloads the **GGUF model** (or adopts an existing one),
* writes a machine-readable **config.json**,
* generates OS-appropriate **scripts** (see :mod:`noerelay.scripts`).

Everything is stdlib-only (``urllib``, ``venv``, ``zipfile``, ``tarfile``) so
the installer itself has no hard dependencies. ``rich`` and ``huggingface_hub``
are used opportunistically when available but are not required.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import venv
import zipfile
from pathlib import Path
from typing import Optional

from .provision import ProvisionPlan
from .system_info import detect_system

# Force UTF-8 output on Windows (cp1252 cannot render check/cross marks).
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Console (rich if available, plain otherwise)
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )

    _console = Console()
    _HAS_RICH = True
except ImportError:  # pragma: no cover
    _HAS_RICH = False

    class _PlainConsole:
        def print(self, *a, **k):
            print(*a)

        def rule(self, *a, **k):
            print("-" * 60)

        class _Panel:
            @staticmethod
            def fit(text, **k):
                return text

        Panel = _Panel

    _console = _PlainConsole()


def _progress():
    if _HAS_RICH:
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=_console,
        )
    return _NoProgress()


class _NoProgress:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def add_task(self, desc, total=None):
        print(f"  {desc}")
        return 0

    def update(self, task_id, **k):
        pass


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _http_get(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "noerelay-installer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as fh:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        with _progress() as progress:
            task = progress.add_task(url.rsplit("/", 1)[-1], total=total)
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                fh.write(chunk)
                progress.update(task, advance=len(chunk))


def _extract(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif archive.suffix in (".gz", ".tgz") or archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(dest)
    else:
        raise ValueError(f"Unsupported archive: {archive.name}")


# ---------------------------------------------------------------------------
# llama.cpp build
# ---------------------------------------------------------------------------


def ensure_llama_build(plan: ProvisionPlan, skip_download: bool = False) -> None:
    server = plan.llama_dir / ("llama-server.exe" if plan.os == "windows" else "llama-server")
    if server.exists():
        _console.print(f"[green]✓[/green] llama.cpp already present at {server}")
        return
    if skip_download:
        _console.print(f"[yellow]! --skip-download: assuming llama.cpp at {server}[/yellow]")
        return

    plan.llama_dir.mkdir(parents=True, exist_ok=True)
    tmp = plan.install_dir / "_dl"
    tmp.mkdir(parents=True, exist_ok=True)

    _console.print(
        f"[bold]llama.cpp build[/bold]  {plan.build_tag}  ({plan.backend}, {plan.os}/{plan.arch})\n"
        f"Target: [cyan]{plan.llama_dir}[/cyan]"
    )

    for fname in plan.build_assets:
        dest = tmp / fname
        if dest.exists() and dest.stat().st_size > 1_000_000:
            _console.print(f"  [dim]cached: {fname}[/dim]")
            continue
        _console.print(f"  [cyan]↓[/cyan] {fname}")
        _http_get(f"{plan.base_url}/{fname}", dest)
        _extract(dest, plan.llama_dir)
        dest.unlink(missing_ok=True)

    shutil.rmtree(tmp, ignore_errors=True)

    if not server.exists():
        _console.print(f"[red]✗[/red] llama-server not found after extraction in {plan.llama_dir}")
        sys.exit(1)
    _console.print(f"[green]✓[/green] llama.cpp installed to {plan.llama_dir}")


# ---------------------------------------------------------------------------
# venv + noerelay CLI
# ---------------------------------------------------------------------------


def ensure_venv(plan: ProvisionPlan) -> Path:
    """Create the virtualenv and return its python executable path."""
    venv_dir = plan.venv_dir
    if not venv_dir.exists():
        _console.print(f"[bold]Creating virtualenv[/bold] at {venv_dir}")
        venv.create(venv_dir, with_pip=True, clear=False)
    if plan.os == "windows":
        py = venv_dir / "Scripts" / "python.exe"
    else:
        py = venv_dir / "bin" / "python"
    if not py.exists():
        _console.print(f"[red]✗[/red] venv python not found at {py}")
        sys.exit(1)
    return py


def install_noerelay(plan: ProvisionPlan, venv_py: Path, src: Optional[Path] = None) -> None:
    """Install the noerelay CLI into the venv (local source preferred, else pip)."""
    _console.print("[bold]Installing noerelay CLI into venv[/bold]")
    # Prefer a local source checkout so we always install the current code.
    if src is None:
        # Walk up from this file to find a pyproject.toml (repo root).
        here = Path(__file__).resolve()
        for parent in [here.parent, *here.parents]:
            if (parent / "pyproject.toml").exists():
                src = parent
                break
    if src is not None and (src / "pyproject.toml").exists():
        res = _run([str(venv_py), "-m", "pip", "install", "-q", str(src)])
        if res.returncode != 0:
            _console.print(f"[yellow]! pip install from source failed: {res.stderr.strip()}[/yellow]")
    else:
        res = _run([str(venv_py), "-m", "pip", "install", "-q", "noerelay"])
        if res.returncode != 0:
            _console.print(f"[yellow]! pip install noerelay failed: {res.stderr.strip()}[/yellow]")
    _console.print("[green]✓[/green] noerelay CLI installed")


# ---------------------------------------------------------------------------
# Model download
# ---------------------------------------------------------------------------


def _resolve_gguf_file(repo_id: str, quant: str) -> Optional[str]:
    """Find the best single-file GGUF matching the quant in a HF repo."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        _console.print("[yellow]! huggingface_hub not installed; using filename guess.[/yellow]")
        return None
    api = HfApi()
    try:
        files = api.list_repo_files(repo_id)
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[yellow]! Could not list repo {repo_id}: {exc}[/yellow]")
        return None
    candidates = [f for f in files if f.lower().endswith(".gguf") and quant.lower() in f.lower()]
    single = [f for f in candidates if re.search(r"of-\d+", f) is None]
    pool = single or candidates
    if not pool:
        return None

    def size_key(f: str) -> int:
        m = re.search(r"(\d+)[._-]gguf$", f, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    return sorted(pool, key=lambda f: (size_key(f), len(f)), reverse=True)[0]


def ensure_model(plan: ProvisionPlan, skip_download: bool = False) -> None:
    plan.model_file.parent.mkdir(parents=True, exist_ok=True)
    if plan.model_file.exists():
        _console.print(f"[green]✓[/green] model already present: {plan.model_file}")
        return
    if skip_download:
        _console.print(f"[yellow]! --skip-download: expecting model at {plan.model_file}[/yellow]")
        return

    _console.print(f"[bold]Downloading model[/bold]  {plan.model.name}")
    fname = _resolve_gguf_file(plan.model.repo_id, plan.model.quant)
    if fname:
        url = f"https://huggingface.co/{plan.model.repo_id}/resolve/main/{fname}"
    else:
        url = (
            f"https://huggingface.co/{plan.model.repo_id}/resolve/main/"
            f"{plan.model.key}_{plan.model.quant}.gguf"
        )
    _console.print(f"  [cyan]↓[/cyan] {url}")
    _http_get(url, plan.model_file)
    _console.print(f"[green]✓[/green] model saved to {plan.model_file}")


# ---------------------------------------------------------------------------
# Config + scripts
# ---------------------------------------------------------------------------


def write_config(plan: ProvisionPlan) -> None:
    from .scripts import venv_python_path, venv_noerelay_path

    config = {
        "install_dir": str(plan.install_dir),
        "models_dir": str(plan.model_file.parent),
        "llama_dir": str(plan.llama_dir),
        "venv_dir": str(plan.venv_dir),
        "backend": plan.backend,
        "os": plan.os,
        "arch": plan.arch,
        "build": plan.build_tag,
        "model": str(plan.model_file),
        "model_name": plan.model.name,
        "model_repo": plan.model.repo_id,
        "host": plan.host,
        "port": plan.port,
        "api_base": f"{plan.api_base}/v1",
        "n_gpu_layers": plan.n_gpu_layers,
        "split_mode": plan.split_mode,
        "tensor_split": plan.tensor_split,
        "ctx_size": plan.ctx_size,
        "parallel": plan.parallel,
        "noerelay_cli": str(venv_noerelay_path(plan)),
        "gpus": [
            {
                "index": g.index,
                "name": g.name,
                "total_mib": g.total_mib,
                "display_active": g.display_active,
                "vendor": g.vendor,
            }
            for g in plan.system.gpus
        ],
        "server_args": plan.server_args(),
    }
    (plan.install_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )
    _console.print(f"[green]✓[/green] config.json written")


def write_readme(plan: ProvisionPlan) -> None:
    """Render the bundled README template with the detected values."""
    template = Path(__file__).resolve().parent.parent.parent / "installer" / "README_TEMPLATE.md"
    if not template.exists():
        # Fall back to a copy shipped next to the package, if present.
        template = Path(__file__).resolve().parent / "README_TEMPLATE.md"
    if not template.exists():
        _console.print("[yellow]! README_TEMPLATE.md not found; skipping README.[/yellow]")
        return
    readme = template.read_text(encoding="utf-8")
    for token, value in {
        "__DATE__": time.strftime("%Y-%m-%d %H:%M"),
        "__OS__": plan.os,
        "__BACKEND__": plan.backend,
        "__BUILD__": plan.build_tag,
        "__MODEL__": str(plan.model_file),
        "__MODEL_NAME__": plan.model.name,
        "__API_BASE__": plan.api_base,
        "__SPLIT__": plan.tensor_split or "n/a",
        "__CTX__": str(plan.ctx_size),
        "__PARALLEL__": str(plan.parallel),
        "__NGUPLAYER__": str(plan.n_gpu_layers),
        "<install_dir>": str(plan.install_dir),
        "<models_dir>": str(plan.model_file.parent),
    }.items():
        readme = readme.replace(token, value)
    (plan.install_dir / "README.md").write_text(readme, encoding="utf-8")
    _console.print("[green]✓[/green] README.md written")


def configure_noerelay(plan: ProvisionPlan) -> None:
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
    _console.print(f"[green]✓[/green] NoeRelay configured → {config_path}")


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------


def provision(
    install_dir: Optional[Path] = None,
    models_dir: Optional[Path] = None,
    model_key: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8080,
    ctx_size: Optional[int] = None,
    parallel: int = 1,
    skip_download: bool = False,
    skip_venv: bool = False,
    noerelay_src: Optional[Path] = None,
) -> ProvisionPlan:
    """Detect the system, build a plan, and install the stack. Returns the plan."""
    from .provision import make_plan
    from .scripts import generate_scripts

    system = detect_system()
    plan = make_plan(
        system,
        install_dir=install_dir,
        models_dir=models_dir,
        model_key=model_key,
        host=host,
        port=port,
        ctx_size=ctx_size,
        parallel=parallel,
    )

    _console.print(Panel.fit("\n".join(plan.summary_lines()), border_style="blue"))
    plan.install_dir.mkdir(parents=True, exist_ok=True)

    ensure_llama_build(plan, skip_download=skip_download)
    if not skip_venv:
        venv_py = ensure_venv(plan)
        install_noerelay(plan, venv_py, src=noerelay_src)
    ensure_model(plan, skip_download=skip_download)
    write_config(plan)
    generate_scripts(plan)
    write_readme(plan)
    configure_noerelay(plan)

    _console.print(Panel.fit(
        "[bold green]Provisioning complete[/bold green]\n"
        f"Start the server:  [cyan]{plan.bin_dir / ('start-server.bat' if plan.os == 'windows' else 'start-server.sh')}[/cyan]\n"
        f"API:               [cyan]{plan.api_base}/v1[/cyan]",
        border_style="green",
    ))
    return plan
