"""
Cross-platform system detection for NoeRelay provisioning.

This module inspects the host (OS + version, CPU architecture, CPU model,
logical/physical cores, RAM, GPUs, VRAM) and decides which llama.cpp *backend*
the machine should use:

* ``cuda``  — one or more NVIDIA GPUs (Windows / Linux)
* ``metal`` — Apple Silicon (M1/M2/M3/M4) with the unified-memory Metal backend
* ``cpu``   — no accelerator; CPU-only inference

Everything here is best-effort and defensive: a missing tool (``nvidia-smi``,
``sysctl``, ``wmic``) or a permission error must never raise out of
``detect_system()``. The result is a plain :class:`SystemInfo` that the
provisioning logic and the ``noerelay detect`` / ``noerelay doctor`` CLI
commands render.

No third-party dependencies — stdlib only, so it runs anywhere Python runs.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class GPU:
    """A single accelerator device."""

    index: int
    name: str
    total_mib: int = 0
    free_mib: int = 0
    display_active: bool = False
    pci_bus_id: str = ""
    vendor: str = "nvidia"  # nvidia | apple | other

    @property
    def total_gb(self) -> float:
        return round(self.total_mib / 1024.0, 2)

    @property
    def free_gb(self) -> float:
        return round(self.free_mib / 1024.0, 2)


@dataclass
class SystemInfo:
    """A snapshot of the host machine."""

    os: str = ""                 # windows | darwin | linux
    os_version: str = ""         # e.g. "11 (build 26200)", "14.5", "Ubuntu 24.04"
    arch: str = ""               # x86_64 | arm64 | ...
    cpu_model: str = ""
    cpu_count: int = 0           # logical cores / threads
    physical_cores: int = 0      # physical cores (0 if unknown)
    ram_gb: float = 0.0
    hostname: str = ""
    gpus: list[GPU] = field(default_factory=list)
    backend: str = "cpu"         # cuda | metal | cpu
    python_version: str = ""
    apple_silicon: bool = False

    # -- convenience -------------------------------------------------------

    @property
    def total_vram_gb(self) -> float:
        return round(sum(g.total_gb for g in self.gpus), 2)

    @property
    def gpu_count(self) -> int:
        return len(self.gpus)

    def _cpu_label(self) -> str:
        model = self.cpu_model or "unknown"
        if self.physical_cores and self.physical_cores != self.cpu_count:
            return f"{model}  ({self.cpu_count} threads / {self.physical_cores} cores)"
        return f"{model}  ({self.cpu_count} cores)"

    def summary_lines(self) -> list[str]:
        """Human-readable lines for the CLI."""
        os_line = self.os
        if self.os_version:
            os_line = f"{self.os} {self.os_version}"
        lines = [
            f"OS:          {os_line} ({self.arch})",
            f"CPU:         {self._cpu_label()}",
            f"RAM:         {self.ram_gb:.1f} GB",
            f"Backend:     {self.backend}",
            f"Python:      {self.python_version}",
        ]
        if self.hostname:
            lines.append(f"Host:        {self.hostname}")
        if self.gpus:
            for g in self.gpus:
                disp = " [display]" if g.display_active else ""
                lines.append(
                    f"GPU {g.index}:     {g.name}  {g.total_gb:.1f} GB VRAM{disp}"
                )
        else:
            lines.append("GPU:         none detected (CPU-only)")
        return lines


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 15) -> Optional[str]:
    """Run a command, return stdout, or None on any failure."""
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if res.returncode == 0:
            return res.stdout
    except Exception:
        return None
    return None


def _os_name() -> str:
    s = platform.system().lower()
    if s in ("windows", "darwin", "linux"):
        return s
    return s or "unknown"


def _arch_name() -> str:
    """Normalize the CPU architecture to a short token."""
    machine = (platform.machine() or "").lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return machine or "unknown"


def _os_version() -> str:
    """Best-effort, human-friendly OS version string. Never raises."""
    os_name = _os_name()
    try:
        if os_name == "windows":
            # platform.version() -> "10.0.26200" (build); platform.release() -> "10"
            build = platform.version()
            parts = build.split(".")
            build_num = parts[-1] if parts else ""
            try:
                major_build = int(build_num)
            except (ValueError, TypeError):
                major_build = 0
            # Windows 11 builds start at 22000.
            label = "11" if major_build >= 22000 else "10"
            if build_num:
                return f"{label} (build {build_num})"
            return label
        if os_name == "darwin":
            ver = platform.mac_ver()[0]
            return ver or platform.release()
        if os_name == "linux":
            try:
                with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if line.startswith("PRETTY_NAME="):
                            val = line.split("=", 1)[1].strip().strip('"')
                            if val:
                                return val
            except Exception:
                pass
            return platform.release() or platform.platform()
    except Exception:
        pass
    return platform.release() or ""


def _cpu_model() -> str:
    """Detect the CPU model name. Never raises.

    Windows: ``wmic`` is deprecated and removed on Windows 11, so we prefer
    PowerShell + WMI/CIM and fall back to ``wmic`` only if it still exists.
    """
    os_name = _os_name()
    if os_name == "windows":
        out = _run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name",
            ]
        )
        if out and out.strip():
            return out.strip()
        # Legacy fallback for older Windows where wmic is still present.
        out = _run(["wmic", "cpu", "get", "name"])
        if out:
            for line in out.splitlines():
                line = line.strip()
                if line and line.lower() != "name":
                    return line
        return ""
    if os_name == "darwin":
        out = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if out and out.strip():
            return out.strip()
    # linux + fallback
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or ""


def _cpu_count() -> int:
    try:
        import os

        return os.cpu_count() or 0
    except Exception:
        return 0


def _physical_cores() -> int:
    """Detect physical core count. Returns 0 if unknown. Never raises."""
    os_name = _os_name()
    try:
        if os_name == "windows":
            out = _run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor | "
                    "Measure-Object -Property NumberOfCores -Sum).Sum",
                ]
            )
            if out and out.strip():
                return int(out.strip())
        elif os_name == "darwin":
            out = _run(["sysctl", "-n", "hw.physicalcpu"])
            if out and out.strip():
                return int(out.strip())
        else:
            # linux: count unique "physical id" entries in /proc/cpuinfo.
            try:
                ids = set()
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if line.lower().startswith("physical id"):
                            ids.add(line.split(":", 1)[1].strip())
                if ids:
                    return len(ids)
            except Exception:
                pass
    except Exception:
        pass
    return 0


def _hostname() -> str:
    try:
        return platform.node() or ""
    except Exception:
        return ""


def _ram_gb() -> float:
    os_name = _os_name()
    try:
        if os_name == "darwin":
            out = _run(["sysctl", "-n", "hw.memsize"])
            if out:
                return int(out.strip()) / (1024 ** 3)
        elif os_name == "windows":
            out = _run(["powershell", "-NoProfile", "-Command",
                        "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"])
            if out:
                return float(out.strip())
        else:
            # Prefer /proc/meminfo (MemTotal in kB) — more reliable than `free`.
            try:
                with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if line.lower().startswith("memtotal:"):
                            kb = int(line.split(":", 1)[1].strip().split()[0])
                            return kb / (1024 ** 2)
            except Exception:
                pass
            out = _run(["free", "-g"])
            if out:
                for line in out.splitlines():
                    if line.lower().startswith("mem:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return float(parts[1])
    except Exception:
        pass
    return 0.0


def _is_apple_silicon() -> bool:
    if _os_name() != "darwin":
        return False
    if _arch_name() == "arm64":
        return True
    # Fallback: some Intel Macs report arm64 under Rosetta; check the brand.
    brand = _cpu_model().lower()
    return brand.startswith("apple m") or "apple silicon" in brand


# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------


def _detect_nvidia() -> list[GPU]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    out = _run(
        [
            exe,
            "--query-gpu=index,name,memory.total,memory.free,display_active,pci.bus_id",
            "--format=csv,noheader,nounits",
        ]
    )
    if not out:
        return []
    gpus: list[GPU] = []
    for line in out.strip().splitlines():
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
                    vendor="nvidia",
                )
            )
        except ValueError:
            continue
    return gpus


def _detect_apple() -> list[GPU]:
    """
    Apple Silicon exposes a single unified-memory accelerator. We model it as
    one 'GPU' whose VRAM is the unified memory (shared with the CPU).
    """
    if not _is_apple_silicon():
        return []
    ram = _ram_gb()
    # Unified memory is shared; a conservative fraction is usable for the
    # GPU. Report the full amount but let provisioning apply a headroom factor.
    return [
        GPU(
            index=0,
            name="Apple Silicon (unified memory)",
            total_mib=int(ram * 1024),
            free_mib=int(ram * 1024),
            display_active=True,
            vendor="apple",
        )
    ]


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def _select_backend(os_name: str, arch: str, gpus: list[GPU], apple: bool) -> str:
    if gpus and any(g.vendor == "nvidia" for g in gpus):
        return "cuda"
    if apple:
        return "metal"
    return "cpu"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect_system() -> SystemInfo:
    """Detect the host system. Never raises."""
    os_name = _os_name()
    arch = _arch_name()
    apple = _is_apple_silicon()

    gpus: list[GPU] = []
    if os_name in ("windows", "linux"):
        gpus = _detect_nvidia()
    if os_name == "darwin":
        gpus = _detect_apple()

    backend = _select_backend(os_name, arch, gpus, apple)

    return SystemInfo(
        os=os_name,
        os_version=_os_version(),
        arch=arch,
        cpu_model=_cpu_model(),
        cpu_count=_cpu_count(),
        physical_cores=_physical_cores(),
        ram_gb=round(_ram_gb(), 2),
        hostname=_hostname(),
        gpus=gpus,
        backend=backend,
        python_version=".".join(platform.python_version_tuple()[:2]),
        apple_silicon=apple,
    )
