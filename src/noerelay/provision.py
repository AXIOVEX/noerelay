"""
Auto-provisioning: turn a detected :class:`SystemInfo` into a concrete
:class:`ProvisionPlan`.

This is the "most optimized install for the setup" engine. Given the host's
backend (cuda / metal / cpu), GPU count, VRAM and RAM it decides:

* which **llama.cpp build** to download (backend + arch asset names),
* whether to **split across GPUs** (multi-GPU layer split) or not,
* how many **layers to offload** to the accelerator (``n-gpu-layers``),
* which **model** actually fits the machine's usable memory,
* a sensible **context size**.

The plan is pure data — nothing here downloads or writes files. The installer
(:mod:`noerelay.installer`) consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models import MODEL_CATALOG, ModelEntry, default_model
from .system_info import SystemInfo

# ---------------------------------------------------------------------------
# Pinned llama.cpp build
# ---------------------------------------------------------------------------

LLAMA_BUILD_TAG = "b10894"
LLAMA_BUILD_CUDA = "13.3"  # required for Blackwell (RTX 5060 Ti, sm_120)

LLAMA_BASE_URL = (
    f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_BUILD_TAG}"
)


def _build_assets(backend: str, os_name: str, arch: str) -> list[str]:
    """
    Return the llama.cpp release asset filename(s) for a backend/OS/arch.

    llama.cpp publishes one asset per platform; the CUDA Windows build needs a
    second asset (the CUDA runtime DLLs). Names follow the current release
    convention and can be overridden via ``--build-tag`` / manual download.
    """
    if backend == "cuda":
        if os_name == "windows":
            a = "x64" if arch in ("x86_64", "amd64") else arch
            return [
                f"llama-{LLAMA_BUILD_TAG}-bin-win-cuda-{LLAMA_BUILD_CUDA}-{a}.zip",
                f"cudart-llama-bin-win-cuda-{LLAMA_BUILD_CUDA}-{a}.zip",
            ]
        # linux (and other unix)
        a = "x64" if arch in ("x86_64", "amd64") else "arm64"
        return [f"llama-{LLAMA_BUILD_TAG}-bin-ubuntu-cuda-{LLAMA_BUILD_CUDA}-{a}.tar.gz"]
    if backend == "metal":
        a = "arm64" if arch == "arm64" else "x64"
        return [f"llama-{LLAMA_BUILD_TAG}-bin-macos-{a}.zip"]
    # cpu
    if os_name == "windows":
        a = "x64" if arch in ("x86_64", "amd64") else arch
        return [f"llama-{LLAMA_BUILD_TAG}-bin-win-{a}.zip"]
    if os_name == "darwin":
        a = "arm64" if arch == "arm64" else "x64"
        return [f"llama-{LLAMA_BUILD_TAG}-bin-macos-{a}.zip"]
    a = "x64" if arch in ("x86_64", "amd64") else "arm64"
    return [f"llama-{LLAMA_BUILD_TAG}-bin-ubuntu-{a}.tar.gz"]


# ---------------------------------------------------------------------------
# Memory heuristics
# ---------------------------------------------------------------------------

# Fraction of total memory we consider safely usable for the model.
_VRAM_HEADROOM = {
    "cuda": 0.90,   # leave room for KV cache + OS
    "metal": 0.70,  # unified memory is shared with the CPU
    "cpu": 0.0,
}
_RAM_HEADROOM = 0.60  # leave room for OS + KV cache when offloading


# Approximate memory bandwidth (GB/s) for known NVIDIA GPUs, keyed by a
# substring of the device name. LLM token generation is memory-bandwidth-bound,
# so this — not raw VRAM — is the better proxy for per-layer speed. Unknown
# GPUs return ``None`` and fall back to a VRAM-based weight.
_GPU_BANDWIDTH_GBS: list[tuple[str, float]] = [
    # Most-specific first so substrings resolve correctly
    # (e.g. "4070 SUPER" before "4070", "5060 TI" before "5060").
    ("4070 SUPER", 504.0),
    ("4070 TI", 672.0),
    ("4070", 504.0),
    ("4060 TI", 288.0),
    ("4060", 272.0),
    ("4080 SUPER", 736.0),
    ("4080", 717.0),
    ("4090", 1008.0),
    ("5060 TI", 448.0),
    ("5060", 448.0),
    ("5070", 672.0),
    ("5080", 960.0),
    ("5090", 1792.0),
    ("3090", 936.0),
    ("3080", 912.0),
    ("3070", 448.0),
    ("3060", 360.0),
]


def _gpu_bandwidth_gbs(name: str) -> Optional[float]:
    """Best-effort memory bandwidth (GB/s) for a GPU name, or ``None``."""
    upper = name.upper()
    for key, bw in _GPU_BANDWIDTH_GBS:
        if key in upper:
            return bw
    return None


def _recommend_split(system: SystemInfo) -> str:
    """
    Relative tensor-split across NVIDIA GPUs.

    Weights are proportional to **memory bandwidth** when it is known (LLM
    token generation is memory-bandwidth-bound, so the faster GPU should hold
    more layers), falling back to VRAM for unknown GPUs. The display-driving
    GPU is reduced by 20% to leave desktop headroom. Weights are normalized to
    integers summing to ~25 (the ``9,16`` style).
    """
    gpus = [g for g in system.gpus if g.vendor == "nvidia"]
    if len(gpus) < 2:
        return ""
    raw: list[float] = []
    for g in gpus:
        bw = _gpu_bandwidth_gbs(g.name)
        base = bw if bw is not None else max(1, g.total_mib)
        raw.append(base * (0.8 if g.display_active else 1.0))
    total = sum(raw)
    if total == 0:
        return ",".join("1" for _ in gpus)
    scaled = [max(1, round(r / total * 25)) for r in raw]
    return ",".join(str(s) for s in scaled)


def _pick_model(system: SystemInfo) -> ModelEntry:
    """
    Pick the **best agentic-AI candidate that fits** the machine's usable
    memory.

    Selection is by ``agentic_score`` (tool-use / instruction-following /
    structured-output suitability), *not* by raw size — so a strong agentic
    model (e.g. Qwen3.8 27B) is preferred over a bigger-but-weaker one. Size
    is only a tiebreaker.
    """
    usable_vram = system.total_vram_gb * _VRAM_HEADROOM.get(system.backend, 0.0)
    usable_ram = system.ram_gb * _RAM_HEADROOM

    # Rank key: best agentic score first, then larger model as a tiebreaker.
    def _rank(m: ModelEntry):
        return (m.agentic_score, m.min_vram_gb)

    # 1) Fully on GPU: best agentic model whose VRAM requirement fits.
    fits_vram = [
        m for m in MODEL_CATALOG
        if system.backend in ("cuda", "metal") and m.min_vram_gb <= usable_vram
    ]
    if fits_vram:
        return max(fits_vram, key=_rank)

    # 2) Offloaded / CPU: best agentic model whose RAM requirement fits.
    fits_ram = [m for m in MODEL_CATALOG if m.min_ram_gb <= usable_ram]
    if fits_ram:
        # Prefer CPU-friendly models when there is no accelerator.
        if system.backend == "cpu":
            cpu_ok = [m for m in fits_ram if m.cpu_friendly]
            if cpu_ok:
                return max(cpu_ok, key=_rank)
        return max(fits_ram, key=_rank)

    # 3) Nothing fits — smallest CPU-friendly model.
    cpu_friendly = [m for m in MODEL_CATALOG if m.cpu_friendly]
    return min(cpu_friendly or MODEL_CATALOG, key=lambda m: m.min_ram_gb)


def _pick_ctx(system: SystemInfo, model: ModelEntry) -> int:
    """Scale context size with available memory.

    The master YAML config (NR-LLM-005) is the authoritative source at
    runtime; this heuristic only seeds the initial plan.  The reference
    operator host runs 131072 with dual-GPU + quantized KV cache.
    """
    if system.backend == "cpu":
        return 4096
    if system.total_vram_gb >= 24 or system.ram_gb >= 32:
        return 16384
    if system.total_vram_gb >= 12 or system.ram_gb >= 16:
        return 131072
    return 8192


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


@dataclass
class ProvisionPlan:
    system: SystemInfo
    backend: str = "cpu"
    os: str = ""
    arch: str = ""
    build_tag: str = LLAMA_BUILD_TAG
    build_assets: list[str] = field(default_factory=list)
    base_url: str = LLAMA_BASE_URL
    split_mode: str = "none"      # layer | none
    tensor_split: str = ""        # e.g. "9,16" (empty = no split)
    n_gpu_layers: int = 0         # 999 = all, 0 = none
    model: ModelEntry = field(default_factory=default_model)
    ctx_size: int = 131072
    parallel: int = 1
    host: str = "127.0.0.1"
    port: int = 8080
    batch_size: int = 512
    ubatch_size: int = 256
    flash_attn: str = "auto"
    cache_type_k: str = "q4_0"
    cache_type_v: str = "q4_0"
    no_mtp: bool = False
    no_reasoning_preserve: bool = True
    metrics: bool = True
    install_dir: Path = field(default_factory=lambda: Path.home() / "noerelay-llm")
    models_dir: Optional[Path] = None
    notes: list[str] = field(default_factory=list)
    #: Master YAML config (NR-LLM-005).  When set, :meth:`server_args`
    #: generates the invocation from it.
    llama_config: Optional[dict] = None

    # -- derived -----------------------------------------------------------

    @property
    def llama_dir(self) -> Path:
        return self.install_dir / "llama"

    @property
    def venv_dir(self) -> Path:
        return self.install_dir / "venv"

    @property
    def bin_dir(self) -> Path:
        return self.install_dir / "bin"

    @property
    def model_file(self) -> Path:
        d = self.models_dir or (self.install_dir / "models")
        # Use the catalog's exact filename when provided so the plan matches
        # operator model dirs (e.g. C:\Models\gpt-oss-20b-Q4_K_M.gguf).
        return d / (self.model.filename or f"{self.model.key}.gguf")

    @property
    def api_base(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def is_multi_gpu(self) -> bool:
        return self.split_mode == "layer" and "," in self.tensor_split

    def server_args(self) -> list[str]:
        """The llama-server command-line arguments for this plan.

        Generated from the master YAML config when present (NR-LLM-005);
        otherwise from the plan fields (same reference argument set).
        """
        if self.llama_config is not None:
            from .llama_config import server_args_from_config
            return server_args_from_config(self.llama_config, model_path=str(self.model_file))
        args = [
            "-m", str(self.model_file),
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(self.ctx_size),
            "--parallel", str(self.parallel),
        ]
        if self.backend == "cpu":
            args += ["--n-gpu-layers", "0"]
        else:
            args += ["--n-gpu-layers", str(self.n_gpu_layers)]
        if self.is_multi_gpu:
            args += ["--split-mode", "layer", "--tensor-split", self.tensor_split]
        args += [
            "--batch-size", str(self.batch_size),
            "--ubatch-size", str(self.ubatch_size),
            "--flash-attn", self.flash_attn,
            "--cache-type-k", self.cache_type_k,
            "--cache-type-v", self.cache_type_v,
        ]
        if self.no_mtp:
            args.append("--no-mtp")
        if self.no_reasoning_preserve:
            args.append("--no-reasoning-preserve")
        if self.metrics:
            args.append("--metrics")
        return args

    def summary_lines(self) -> list[str]:
        lines = [
            f"Backend:      {self.backend}",
            f"Build:        {self.build_tag}  ({', '.join(self.build_assets)})",
            f"Model:        {self.model.name}",
            f"  file:       {self.model_file}",
            f"  min VRAM:   {self.model.min_vram_gb} GB   min RAM: {self.model.min_ram_gb} GB",
            f"GPU layers:   {self.n_gpu_layers if self.backend != 'cpu' else '0 (CPU)'}",
            f"Split:        {self.tensor_split or 'none'}" + (
                f"  (layer mode)" if self.is_multi_gpu else ""
            ),
            f"Context:      {self.ctx_size}",
            f"API:          {self.api_base}/v1",
            f"Install dir:  {self.install_dir}",
        ]
        if self.notes:
            lines.append("Notes:")
            lines += [f"  - {n}" for n in self.notes]
        return lines


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def make_plan(
    system: SystemInfo,
    install_dir: Optional[Path] = None,
    models_dir: Optional[Path] = None,
    model_key: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8080,
    ctx_size: Optional[int] = None,
    parallel: int = 1,
) -> ProvisionPlan:
    """Build a :class:`ProvisionPlan` from a detected system."""
    backend = system.backend
    os_name = system.os
    arch = system.arch

    plan = ProvisionPlan(
        system=system,
        backend=backend,
        os=os_name,
        arch=arch,
        build_assets=_build_assets(backend, os_name, arch),
        host=host,
        port=port,
        parallel=parallel,
        install_dir=install_dir or (Path.home() / "noerelay-llm"),
        models_dir=models_dir,
    )

    # -- GPU split / offload ---------------------------------------------
    nvidia = [g for g in system.gpus if g.vendor == "nvidia"]
    if backend == "cuda":
        plan.n_gpu_layers = 999
        if len(nvidia) >= 2:
            plan.split_mode = "layer"
            plan.tensor_split = _recommend_split(system)
            plan.notes.append(
                f"Multi-GPU layer split across {len(nvidia)} GPUs "
                f"(weights {plan.tensor_split})."
            )
        else:
            plan.split_mode = "none"
            plan.tensor_split = ""
            plan.notes.append("Single GPU — all layers offloaded, no split.")
    elif backend == "metal":
        plan.n_gpu_layers = 999
        plan.split_mode = "none"
        plan.tensor_split = ""
        plan.notes.append(
            "Apple Silicon — unified memory via Metal; all layers on GPU."
        )
    else:  # cpu
        plan.n_gpu_layers = 0
        plan.split_mode = "none"
        plan.tensor_split = ""
        plan.notes.append("CPU-only inference (no accelerator detected).")

    # -- model -------------------------------------------------------------
    if model_key:
        from .models import get_model

        chosen = get_model(model_key)
        if chosen is None:
            raise ValueError(f"Unknown model key: {model_key!r}")
        plan.model = chosen
        plan.notes.append(f"Model forced to {chosen.key}.")
    else:
        plan.model = _pick_model(system)
        plan.notes.append(
            f"Auto-selected {plan.model.key} as the best agentic-AI candidate "
            f"that fits (agentic score {plan.model.agentic_score}; "
            f"{system.total_vram_gb} GB VRAM / {system.ram_gb} GB RAM)."
        )

    # -- context -----------------------------------------------------------
    plan.ctx_size = ctx_size or _pick_ctx(system, plan.model)

    # -- master YAML config (NR-LLM-005) ------------------------------------
    # The provisioned server is launched from this config; the installer
    # renders it to <install_dir>/llama.yaml.
    from .llama_config import validate_llama_config

    plan.llama_config = validate_llama_config(
        {
            "version": 1,
            "server": {
                "model": str(plan.model_file),
                "model_key": plan.model.key,
                "host": plan.host,
                "port": plan.port,
                "n_gpu_layers": plan.n_gpu_layers,
                "split_mode": plan.split_mode,
                "tensor_split": plan.tensor_split,
                "ctx_size": plan.ctx_size,
                "parallel": plan.parallel,
                "batch_size": plan.batch_size,
                "ubatch_size": plan.ubatch_size,
                "flash_attn": plan.flash_attn,
                "cache_type_k": plan.cache_type_k,
                "cache_type_v": plan.cache_type_v,
                "no_mtp": plan.no_mtp,
                "no_reasoning_preserve": plan.no_reasoning_preserve,
                "metrics": plan.metrics,
            },
        }
    )

    return plan
