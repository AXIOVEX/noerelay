#!/usr/bin/env python3
"""T-LLM-003 — gpt-oss-20b quantization benchmark (NR-LLM-003).

Benchmarks the three gpt-oss-20b GGUF quants (Q4_K_M / Q5_K_M / Q6_K) on the
reference two-GPU host (RTX 4070 SUPER idx0 + RTX 5060 Ti idx1) using the
canonical server argument set (the same one the master ``llama.yaml`` carries):

  * llama-server     — time-to-first-token (TTFT) and sustained tokens/s via
                       streaming /v1/chat/completions (median of 3)
  * llama-perplexity — quality proxy: perplexity over a fixed corpus
                       (evidence/LLM-01/quality-corpus.txt)
  * nvidia-smi       — per-GPU VRAM footprint before/after load

Why not llama-bench: this build's multi-value syntax interprets ``-ts 10,15``
as *two* single-GPU tensor splits (10 and 15), so it cannot express the
canonical dual-GPU split. Throughput is therefore measured on the real server
path, which is also what the production stack serves.

Outputs (all under the repo root):
  evidence/LLM-01/T-LLM-003-benchmark.json   reproducible result artifact
  evidence/LLM-01/T-LLM-003.json             EvidenceEnvelope (written via
                                              noerelay.reqtest.write_envelope)
  evidence/LLM-01/T-LLM-003-<quant>-server.log
  evidence/LLM-01/T-LLM-003-<quant>-perplexity.log
  evidence/LLM-01/T-LLM-003-run.log

Usage:
  python scripts/benchmark_local_models.py                  # all three quants
  python scripts/benchmark_local_models.py --quant Q4_K_M   # one quant
  python scripts/benchmark_local_models.py --verify         # validate artifact

The benchmark requires exclusive GPU access (a 12 GB model does not fit
alongside another loaded model under the canonical split). Pass
--allow-shared to override the guard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Canonical configuration (mirrors the master llama.yaml / reference config)
# --------------------------------------------------------------------------- #
LLAMA_DIR = Path(r"C:\LLM\llama")
MODEL_DIR = Path(r"C:\Models")
MODEL_NAME = "gpt-oss-20b"
QUANT_FILES = {
    "Q4_K_M": "gpt-oss-20b-Q4_K_M.gguf",
    "Q5_K_M": "gpt-oss-20b-Q5_K_M.gguf",
    "Q6_K": "gpt-oss-20b-Q6_K.gguf",
}
TENSOR_SPLIT = "10,15"  # 4070 SUPER : 5060 Ti (reference operator config)
N_GPU_LAYERS = 999
CTX_SIZE = 131072
BATCH = 512
UBATCH = 256
CACHE_TYPE_K = "q4_0"
CACHE_TYPE_V = "q4_0"
FLASH_ATTN = "on"
PARALLEL = 1
HOST = "127.0.0.1"
PORT = 8123  # keep clear of the operator's server on 8080

TTFT_REPETITIONS = 3
TTFT_MAX_TOKENS = 128
PPL_OFFSET = 0
PPL_TOKENS = 4096
READY_TIMEOUT_S = 600.0
GPU_BUSY_THRESHOLD_MIB = 4096

WORK_PACKAGE_ID = "LLM-01"
TEST_ID = "T-LLM-003"
REQUIREMENT_ID = "NR-LLM-003"
CORPUS_RELPATH = Path("evidence") / "LLM-01" / "quality-corpus.txt"
ARTIFACT_RELPATH = Path("evidence") / "LLM-01" / "T-LLM-003-benchmark.json"
RUN_LOG_RELPATH = Path("evidence") / "LLM-01" / "T-LLM-003-run.log"

RUN_LOG: List[str] = []


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    RUN_LOG.append(line)


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _import_reqtest():
    """Load ``noerelay.reqtest`` directly by file path.

    ``scripts/noerelay.py`` shadows the ``src/noerelay`` package on this
    interpreter's path (the script's own directory is ``sys.path[0]``), so
    ``from noerelay import reqtest`` resolves to the standalone script module
    and fails. Loading the file directly sidesteps the name collision entirely.
    ``reqtest.py`` is stdlib-only, so it imports cleanly on its own.
    """
    import importlib.util
    reqtest_path = Path(__file__).resolve().parents[1] / "src" / "noerelay" / "reqtest.py"
    spec = importlib.util.spec_from_file_location("_noerelay_reqtest", reqtest_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Environment probes
# --------------------------------------------------------------------------- #
def vram_used_mib() -> List[int]:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=30,
    )
    used: List[int] = []
    for line in out.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[1].isdigit():
            used.append(int(parts[1]))
    return used


def gpu_inventory() -> List[Dict[str, Any]]:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=30,
    )
    gpus: List[Dict[str, Any]] = []
    for line in out.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and parts[0].isdigit():
            gpus.append({"index": int(parts[0]), "name": parts[1], "total_mib": int(parts[2])})
    return gpus


def check_gpus_free(allow_shared: bool) -> None:
    used = vram_used_mib()
    if not used:
        raise SystemExit("nvidia-smi returned no GPUs; cannot benchmark")
    if sum(used) > GPU_BUSY_THRESHOLD_MIB and not allow_shared:
        raise SystemExit(
            f"GPUs are busy (memory used MiB: {used}). The gpt-oss-20b quants need "
            "exclusive GPU access for the canonical tensor split. Stop other "
            "llama-server instances first, or pass --allow-shared to proceed."
        )
    _log(f"GPU free check passed (memory used MiB: {used})")


def _llama_build_from_log(log_path: Path) -> Optional[str]:
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(r"llama\.cpp version\s+(\d+)\s+\(([0-9a-fA-F]+)\)", text)
    if m:
        return f"{m.group(1)} ({m.group(2)})"
    m = re.search(r"version\s+(\d+)\s+\(([0-9a-fA-F]+)\)", text)
    if m:
        return f"{m.group(1)} ({m.group(2)})"
    return None


# --------------------------------------------------------------------------- #
# llama-server lifecycle (benchmark instance only)
# --------------------------------------------------------------------------- #
def server_args(model: Path) -> List[str]:
    return [
        "--model", str(model),
        "--host", HOST,
        "--port", str(PORT),
        "--n-gpu-layers", str(N_GPU_LAYERS),
        "--tensor-split", TENSOR_SPLIT,
        "--ctx-size", str(CTX_SIZE),
        "--parallel", str(PARALLEL),
        "--batch-size", str(BATCH),
        "--ubatch-size", str(UBATCH),
        "--flash-attn", FLASH_ATTN,
        "--cache-type-k", CACHE_TYPE_K,
        "--cache-type-v", CACHE_TYPE_V,
    ]


def start_server(model: Path, log_path: Path) -> subprocess.Popen:
    exe = LLAMA_DIR / "llama-server.exe"
    args = [str(exe)] + server_args(model)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "w", encoding="utf-8")
    logf.write("$ " + " ".join(args) + "\n")
    logf.flush()
    proc = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT, cwd=str(LLAMA_DIR))
    return proc


def wait_for_health(base_url: str, timeout: float = READY_TIMEOUT_S, proc: Optional[subprocess.Popen] = None) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"llama-server exited during startup: {proc.returncode}")
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=5) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(2)
    return False


def get_model_id(base_url: str) -> str:
    with urllib.request.urlopen(base_url + "/v1/models", timeout=10) as resp:
        data = json.load(resp)
    return data["data"][0]["id"]


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             r"C:\LLM\stop-llama-server.ps1"],
            check=True, timeout=120,
        )
        proc.wait(timeout=30)


def wait_port_free(port: int, timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
        except OSError:
            s.close()
            return
        s.close()
        time.sleep(1)
    raise TimeoutError(f"port {port} still occupied after {timeout:.0f}s")


# --------------------------------------------------------------------------- #
# TTFT / throughput measurement
# --------------------------------------------------------------------------- #
def build_ttft_prompt(corpus: Path) -> str:
    text = corpus.read_text(encoding="utf-8")
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    passage = "\n\n".join(paras[:3])
    return "Summarize the following passage in exactly three short bullet points.\n\n" + passage


def measure_ttft(base_url: str, model_id: str, prompt: str) -> Dict[str, Any]:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": TTFT_MAX_TOKENS,
        "temperature": 0.0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(
        base_url + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    ttft: Optional[float] = None
    n_content_chunks = 0
    usage: Dict[str, Any] = {}
    with urllib.request.urlopen(req, timeout=900) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            if chunk.get("usage"):
                usage = chunk["usage"]
            choices = chunk.get("choices") or []
            if choices:
                delta = choices[0].get("delta") or {}
                if delta.get("content"):
                    n_content_chunks += 1
                    if ttft is None:
                        ttft = time.perf_counter() - t0
    t_end = time.perf_counter()
    gen_span = (t_end - (t0 + ttft)) if ttft is not None else 0.0
    completion_tokens = usage.get("completion_tokens") or n_content_chunks
    return {
        "ttft_s": round(ttft, 4) if ttft is not None else None,
        "total_s": round(t_end - t0, 4),
        "completion_tokens": completion_tokens,
        "prompt_tokens": usage.get("prompt_tokens"),
        "tokens_per_s": round(completion_tokens / gen_span, 3) if gen_span > 0 else None,
    }


# --------------------------------------------------------------------------- #
# Quality proxy (llama-perplexity over the fixed corpus)
# --------------------------------------------------------------------------- #
def perplexity_args(model: Path, corpus: Path) -> List[str]:
    return [
        "-m", str(model),
        "-f", str(corpus),
        "-ngl", str(N_GPU_LAYERS),
        "-ts", TENSOR_SPLIT,
        "-b", str(BATCH),
        "-ub", str(UBATCH),
        "-ctk", CACHE_TYPE_K,
        "-ctv", CACHE_TYPE_V,
        "-fa", FLASH_ATTN,
        "-s", str(PPL_OFFSET),
        "-n", str(PPL_TOKENS),
    ]


def run_perplexity(model: Path, corpus: Path, log_path: Path) -> Dict[str, Any]:
    exe = LLAMA_DIR / "llama-perplexity.exe"
    args = [str(exe)] + perplexity_args(model, corpus)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(args, capture_output=True, text=True, cwd=str(LLAMA_DIR), timeout=1800)
    elapsed = time.time() - t0
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(args) + "\n\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr + "\n")
    out = proc.stdout + "\n" + proc.stderr
    ppl: Optional[float] = None
    m = re.search(r"perplexity\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", out)
    if m:
        ppl = float(m.group(1))
    eval_ms: Optional[float] = None
    m = re.search(r"llama_eval_time_ms\s*=\s*([0-9.]+)", out)
    if m:
        eval_ms = float(m.group(1))
    tps: Optional[float] = None
    rates = re.findall(r"([0-9.]+)\s+t/s", out)
    if rates:
        tps = float(rates[-1])
    return {
        "exit_code": proc.returncode,
        "perplexity": ppl,
        "eval_time_ms": eval_ms,
        "eval_tokens_per_s": tps,
        "wall_time_s": round(elapsed, 1),
    }


# --------------------------------------------------------------------------- #
# Per-quant benchmark
# --------------------------------------------------------------------------- #
def benchmark_quant(quant: str, root: Path, base_url: str) -> Dict[str, Any]:
    model = MODEL_DIR / QUANT_FILES[quant]
    if not model.is_file():
        raise FileNotFoundError(f"model file not found: {model}")
    corpus = root / CORPUS_RELPATH
    if not corpus.is_file():
        raise FileNotFoundError(f"quality corpus not found: {corpus}")
    wp_dir = root / "evidence" / WORK_PACKAGE_ID
    server_log = wp_dir / f"T-LLM-003-{quant}-server.log"
    ppl_log = wp_dir / f"T-LLM-003-{quant}-perplexity.log"

    _log(f"--- {quant}: {model.name} ({model.stat().st_size / 1e9:.2f} GB) ---")
    vram_before = vram_used_mib()

    proc = start_server(model, server_log)
    runs: List[Dict[str, Any]] = []
    try:
        if not wait_for_health(base_url, proc=proc):
            raise TimeoutError(f"llama-server did not become ready for {quant} (see {server_log})")
        _log(f"  server ready; model id: {get_model_id(base_url)}")
        time.sleep(2)
        vram_loaded = vram_used_mib()

        model_id = get_model_id(base_url)
        prompt = build_ttft_prompt(corpus)
        for i in range(TTFT_REPETITIONS):
            r = measure_ttft(base_url, model_id, prompt)
            _log(f"  ttft run {i + 1}: {r['ttft_s']} s, {r['tokens_per_s']} tok/s "
                 f"(prompt {r['prompt_tokens']} tok)")
            runs.append(r)
    finally:
        stop_server(proc)
        wait_port_free(PORT)
        time.sleep(5)

    _log(f"  running perplexity quality proxy ...")
    ppl = run_perplexity(model, corpus, ppl_log)
    _log(f"  perplexity: {ppl['perplexity']} (exit {ppl['exit_code']}, {ppl['wall_time_s']} s)")
    vram_after = vram_used_mib()

    ttfts = [r["ttft_s"] for r in runs if r["ttft_s"] is not None]
    tps = [r["tokens_per_s"] for r in runs if r["tokens_per_s"] is not None]
    delta = [l - b for l, b in zip(vram_loaded, vram_before)]

    return {
        "quant": quant,
        "file": str(model),
        "file_size_bytes": model.stat().st_size,
        "ttft_s": round(statistics.median(ttfts), 4) if ttfts else None,
        "tokens_per_s": round(statistics.median(tps), 3) if tps else None,
        "ttft_runs": runs,
        "perplexity": ppl["perplexity"],
        "perplexity_eval_time_ms": ppl["eval_time_ms"],
        "perplexity_eval_tokens_per_s": ppl["eval_tokens_per_s"],
        "perplexity_exit_code": ppl["exit_code"],
        "vram_mib": {
            "before": vram_before,
            "loaded": vram_loaded,
            "delta": delta,
            "after_perplexity": vram_after,
        },
        "commands": {
            "server": " ".join([str(LLAMA_DIR / "llama-server.exe")] + server_args(model)),
            "perplexity": " ".join([str(LLAMA_DIR / "llama-perplexity.exe")]
                                   + perplexity_args(model, corpus)),
        },
        "logs": {
            "server": str(server_log.relative_to(root)),
            "perplexity": str(ppl_log.relative_to(root)),
        },
        "llama_build": _llama_build_from_log(server_log),
    }


# --------------------------------------------------------------------------- #
# Artifact + envelope
# --------------------------------------------------------------------------- #
def choose_quant(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    ok = [r for r in results if r.get("perplexity") is not None]
    if not ok:
        return {"chosen_quant": None, "rationale": "no perplexity data recorded", "perplexity_spread": None}
    best = min(r["perplexity"] for r in ok)
    worst = max(r["perplexity"] for r in ok)
    spread = (worst - best) / best
    if spread < 0.02:
        chosen = min(ok, key=lambda r: sum(r["vram_mib"]["delta"]))
        rationale = (
            f"perplexity spread across quants is {spread:.2%} (< 2%), i.e. within "
            "measurement noise; choose the quant with the smallest VRAM footprint "
            "to keep the most headroom for context and concurrency."
        )
    else:
        chosen = min(ok, key=lambda r: r["perplexity"])
        rationale = f"perplexity spread is {spread:.2%}; choose the best-quality quant."
    return {"chosen_quant": chosen["quant"], "rationale": rationale, "perplexity_spread": round(spread, 5)}


def write_artifact(root: Path, results: Dict[str, Dict[str, Any]],
                   llama_build: Optional[str]) -> Path:
    artifact = {
        "artifact": "T-LLM-003-benchmark",
        "requirement_id": REQUIREMENT_ID,
        "test_id": TEST_ID,
        "model": MODEL_NAME,
        "generated_at": _now_rfc3339(),
        "environment": {
            "gpus": gpu_inventory(),
            "llama_dir": str(LLAMA_DIR),
            "llama_build": llama_build,
            "server_config": {
                "tensor_split": TENSOR_SPLIT,
                "n_gpu_layers": N_GPU_LAYERS,
                "ctx_size": CTX_SIZE,
                "parallel": PARALLEL,
                "batch": BATCH,
                "ubatch": UBATCH,
                "flash_attn": FLASH_ATTN,
                "cache_type_k": CACHE_TYPE_K,
                "cache_type_v": CACHE_TYPE_V,
                "host": HOST,
                "port": PORT,
            },
        },
        "method": {
            "throughput": (
                f"llama-server /v1/chat/completions, streaming, temperature=0, "
                f"max_tokens={TTFT_MAX_TOKENS}, median of {TTFT_REPETITIONS} runs; "
                "prompt = fixed instruction + first 3 paragraphs of "
                "evidence/LLM-01/quality-corpus.txt"
            ),
            "ttft": "wall time from request send to first streamed content token",
            "quality_proxy": (
                "llama-perplexity over evidence/LLM-01/quality-corpus.txt "
                f"(-s {PPL_OFFSET}, -n {PPL_TOKENS}) under the same tensor split "
                "and cache settings as the server"
            ),
            "vram": "nvidia-smi memory.used per GPU, before/after server load",
            "note": (
                "llama-bench cannot express the dual-GPU tensor split '10,15' "
                "(its multi-value syntax would split it into two single-GPU "
                "configs), so throughput is measured on the real server path"
            ),
        },
        "results": [results[q] for q in QUANT_FILES if q in results],
    }
    choice = choose_quant(artifact["results"])
    artifact["chosen_quant"] = choice["chosen_quant"]
    artifact["rationale"] = choice["rationale"]
    artifact["perplexity_spread"] = choice["perplexity_spread"]

    path = root / ARTIFACT_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return path


def verify_artifact(path: Path) -> int:
    if not path.is_file():
        print(f"FAIL: artifact not found: {path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: artifact is not valid JSON: {exc}")
        return 1
    problems: List[str] = []
    for field in ("model", "environment", "results", "chosen_quant", "rationale"):
        if field not in data:
            problems.append(f"missing field: {field}")
    quants = {r.get("quant") for r in data.get("results", [])}
    missing = set(QUANT_FILES) - quants
    if missing:
        problems.append(f"missing quants: {sorted(missing)}")
    for r in data.get("results", []):
        for f in ("ttft_s", "tokens_per_s", "perplexity", "vram_mib"):
            if r.get(f) in (None, {}):
                problems.append(f"{r.get('quant')}: missing {f}")
    if not problems:
        if data.get("chosen_quant") != choose_quant(data["results"])["chosen_quant"]:
            problems.append("chosen_quant does not match the selection rule")
        if any(r.get("perplexity_exit_code") != 0 for r in data["results"]):
            problems.append("perplexity command failed")
    digest = _sha256_file(path)
    print(f"artifact: {path}")
    print(f"sha256:   {digest}")
    print(f"model:    {data.get('model')}")
    print(f"chosen:   {data.get('chosen_quant')}")
    for r in data.get("results", []):
        print(f"  {r['quant']:<8} ttft={r.get('ttft_s')} s  "
              f"{r.get('tokens_per_s')} tok/s  ppl={r.get('perplexity')}")
    if problems:
        print("FAIL:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS: T-LLM-003 artifact is complete; the quant choice is reproducible from it.")
    return 0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T-LLM-003 gpt-oss-20b quant benchmark")
    parser.add_argument("--quant", action="append", choices=list(QUANT_FILES),
                        help="benchmark one or more quants (default: all)")
    parser.add_argument("--root", default=None, help="repo root (default: auto-detect)")
    parser.add_argument("--allow-shared", action="store_true",
                        help="proceed even if other processes use the GPUs")
    parser.add_argument("--no-envelope", action="store_true",
                        help="update the artifact but do not write the evidence envelope")
    parser.add_argument("--verify", action="store_true",
                        help="validate the existing artifact and print its digest")
    args = parser.parse_args(argv)

    reqtest = _import_reqtest()
    root = Path(args.root) if args.root else reqtest.find_repo_root()
    artifact_path = root / ARTIFACT_RELPATH

    if args.verify:
        return verify_artifact(artifact_path)

    quants = args.quant or list(QUANT_FILES)
    check_gpus_free(args.allow_shared)
    base_url = f"http://{HOST}:{PORT}"

    results: Dict[str, Dict[str, Any]] = {}
    if artifact_path.is_file():
        try:
            old = json.loads(artifact_path.read_text(encoding="utf-8"))
            results = {r["quant"]: r for r in old.get("results", []) if "quant" in r}
        except (json.JSONDecodeError, OSError):
            results = {}

    started_at = _now_rfc3339()
    failures: List[str] = []
    llama_build: Optional[str] = None
    for quant in quants:
        try:
            results[quant] = benchmark_quant(quant, root, base_url)
            llama_build = llama_build or results[quant].get("llama_build")
        except Exception as exc:  # noqa: BLE001 — record and continue
            _log(f"  [FAIL] {quant}: {exc}")
            failures.append(f"{quant}: {exc}")

    artifact_path = write_artifact(root, results, llama_build)
    _log(f"artifact written: {artifact_path}")

    covered = [q for q in QUANT_FILES if q in results]
    if verify_artifact(artifact_path):
        failures.append("artifact validation failed")
    complete = len(covered) == len(QUANT_FILES) and not failures
    if not args.no_envelope:
        finished_at = _now_rfc3339()
        run_log_path = root / RUN_LOG_RELPATH
        run_log_path.parent.mkdir(parents=True, exist_ok=True)
        run_log_path.write_text("\n".join(RUN_LOG) + "\n", encoding="utf-8")
        envelope_path = reqtest.write_envelope(
            root,
            work_package_id=WORK_PACKAGE_ID,
            test_id=TEST_ID,
            command=f"python scripts/benchmark_local_models.py --root {root}",
            requirement_ids=[REQUIREMENT_ID],
            status="observed_pass" if complete else "observed_fail",
            result_artifact_sha256=_sha256_file(artifact_path),
            logs_artifact_sha256=_sha256_file(run_log_path),
            started_at=started_at,
            finished_at=finished_at,
            artifact_digests={artifact_path.name: _sha256_file(artifact_path)},
            exceptions=failures,
            notes=f"quants covered: {', '.join(covered)}; chosen: "
                  f"{results and choose_quant([results[q] for q in covered])['chosen_quant']}",
        )
        _log(f"envelope written: {envelope_path}")

    _log("summary:")
    for q in QUANT_FILES:
        if q in results:
            r = results[q]
            _log(f"  {q:<8} ttft={r['ttft_s']} s  {r['tokens_per_s']} tok/s  "
                 f"ppl={r['perplexity']}")
    if failures:
        _log(f"FAILURES: {failures}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
