"""
Model catalog for NoeRelay provisioning.

Each entry carries:

* ``min_vram_gb`` — VRAM needed to run fully on GPU (Q4_K_M class quant).
* ``min_ram_gb``  — system RAM needed for a CPU-only / offloaded run.
* ``agentic_score`` — a 0-100 suitability rating for **agentic AI** (tool /
  function calling, instruction following, structured output, reasoning).

The auto-provisioner (see :mod:`noerelay.provision`) walks this list and picks
the **highest-scoring agentic model that fits** the machine's usable memory —
not simply the largest. This is what makes the default land on a strong
agentic model (e.g. Qwen3.8 27B) rather than a bigger-but-weaker one.

Quantization note: sizes/VRAM figures are for the ``Q4_K_M`` quant, the best
quality-per-byte default for local inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelEntry:
    key: str
    name: str
    repo_id: str
    quant: str
    size_gb: float
    min_vram_gb: float
    min_ram_gb: float
    notes: str
    default: bool = False
    cpu_friendly: bool = False  # safe to run on CPU / low-memory machines
    agentic_score: int = 50     # 0-100 suitability for agentic AI


MODEL_CATALOG: list[ModelEntry] = [
    # --- Small / CPU-friendly -------------------------------------------
    ModelEntry(
        key="qwen2.5-1.5b",
        name="Qwen2.5 1.5B (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-1.5B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=1.1,
        min_vram_gb=2,
        min_ram_gb=4,
        notes="Tiny. Great for CPU-only or very low VRAM. Fast.",
        cpu_friendly=True,
        agentic_score=30,
    ),
    ModelEntry(
        key="qwen2.5-3b",
        name="Qwen2.5 3B (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-3B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=2.0,
        min_vram_gb=4,
        min_ram_gb=6,
        notes="Small but capable. Good CPU/low-VRAM default.",
        cpu_friendly=True,
        agentic_score=42,
    ),
    ModelEntry(
        key="qwen2.5-7b",
        name="Qwen2.5 7B (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-7B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=4.7,
        min_vram_gb=6,
        min_ram_gb=10,
        notes="Solid single-GPU / CPU workhorse.",
        cpu_friendly=True,
        agentic_score=58,
    ),
    ModelEntry(
        key="qwen2.5-14b",
        name="Qwen2.5 14B (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-14B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=9.0,
        min_vram_gb=10,
        min_ram_gb=16,
        notes="Strong quality. Needs ~10 GB VRAM or 16 GB RAM.",
        agentic_score=72,
    ),
    # --- Mid / single large GPU -----------------------------------------
    ModelEntry(
        key="mistral-24b",
        name="Mistral Small 24B (Q4_K_M)",
        repo_id="unsloth/Mistral-Small-3.1-24B-Instruct-2507-GGUF",
        quant="Q4_K_M",
        size_gb=14.5,
        min_vram_gb=16,
        min_ram_gb=24,
        notes="Fast, efficient, strong for its size.",
        agentic_score=76,
    ),
    ModelEntry(
        key="qwen3.8-27b",
        name="Qwen3.8 27B (Q4_K_M)",
        repo_id="unsloth/Qwen3.8-27B-GGUF",
        quant="Q4_K_M",
        size_gb=15.3,
        min_vram_gb=18,
        min_ram_gb=28,
        notes="Default. Best agentic all-rounder: strong tool-use, "
              "instruction-following, and structured output. Fits a 16 GB "
              "GPU with offload or dual-GPU.",
        default=True,
        agentic_score=90,
    ),
    ModelEntry(
        key="qwen3-32b",
        name="Qwen3 32B (Q4_K_M)",
        repo_id="unsloth/Qwen3-32B-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        min_vram_gb=22,
        min_ram_gb=32,
        notes="Larger, higher raw quality. Needs most of a 24 GB GPU.",
        agentic_score=85,
    ),
    ModelEntry(
        key="qwen2.5-32b",
        name="Qwen2.5 32B Instruct (Q4_K_M)",
        repo_id="unsloth/Qwen2.5-32B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        min_vram_gb=22,
        min_ram_gb=32,
        notes="Solid instruct model, good tool-use.",
        agentic_score=80,
    ),
    ModelEntry(
        key="deepseek-r1-32b",
        name="DeepSeek-R1 Distill Qwen 32B (Q4_K_M)",
        repo_id="bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF",
        quant="Q4_K_M",
        size_gb=20.0,
        min_vram_gb=22,
        min_ram_gb=32,
        notes="Reasoning-focused (chain-of-thought).",
        agentic_score=78,
    ),
    # --- Large / multi-GPU ----------------------------------------------
    ModelEntry(
        key="llama-3.3-70b",
        name="Llama 3.3 70B (Q4_K_M)",
        repo_id="unsloth/Llama-3.3-70B-Instruct-GGUF",
        quant="Q4_K_M",
        size_gb=42.0,
        min_vram_gb=44,
        min_ram_gb=64,
        notes="LARGE. Needs multi-GPU or heavy CPU offload.",
        agentic_score=88,
    ),
]


def get_model(key: str) -> Optional[ModelEntry]:
    for m in MODEL_CATALOG:
        if m.key == key:
            return m
    return None


def default_model() -> ModelEntry:
    return next((m for m in MODEL_CATALOG if m.default), MODEL_CATALOG[0])
