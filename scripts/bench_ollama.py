"""Benchmark local Ollama models for prompt-processing and generation throughput.

Uses the Ollama HTTP API (no external deps). For each model it:
  1. Loads the model (measures load time).
  2. Runs a fixed prompt + fixed num_predict generation (stream=false).
  3. Reads Ollama's own timing fields (prompt_eval_*, eval_*) to compute t/s.

Usage:
    python scripts/bench_ollama.py [model ...]
    (default: both Qwen3.8-27B IQ3_S and Q4_K_M)
"""

from __future__ import annotations

import json
import time
import urllib.request

HOST = "http://127.0.0.1:11434"
DEFAULT_MODELS = [
    "hf.co/unsloth/Qwen3.8-27B-GGUF:UD-IQ3_S",
    "hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_M",
]

PROMPT = (
    "Explain, in a few sentences, how a transformer attention layer works, "
    "including the roles of the query, key, and value tensors."
)
NUM_PREDICT = 256  # tokens to generate per run (decode throughput)


def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode())


def bench_model(model: str) -> dict:
    # Warm-up / load: a tiny generation forces the model onto the GPUs.
    t0 = time.perf_counter()
    _post(
        "/api/generate",
        {
            "model": model,
            "prompt": "Say ok.",
            "stream": False,
            "options": {"num_predict": 8, "temperature": 0},
        },
    )
    load_s = time.perf_counter() - t0

    # Measured run.
    t0 = time.perf_counter()
    res = _post(
        "/api/generate",
        {
            "model": model,
            "prompt": PROMPT,
            "stream": False,
            "options": {"num_predict": NUM_PREDICT, "temperature": 0},
        },
    )
    wall_s = time.perf_counter() - t0

    prompt_tokens = res.get("prompt_eval_count", 0)
    prompt_s = res.get("prompt_eval_duration", 0) / 1e9  # ns -> s
    gen_tokens = res.get("eval_count", 0)
    gen_s = res.get("eval_duration", 0) / 1e9  # ns -> s

    return {
        "model": model,
        "load_s": load_s,
        "wall_s": wall_s,
        "prompt_tokens": prompt_tokens,
        "prompt_tps": (prompt_tokens / prompt_s) if prompt_s else 0.0,
        "gen_tokens": gen_tokens,
        "gen_tps": (gen_tokens / gen_s) if gen_s else 0.0,
    }


def main() -> None:
    import sys

    models = sys.argv[1:] or DEFAULT_MODELS
    results = [bench_model(m) for m in models]

    print()
    print(f"{'model':<45} {'load':>7} {'prompt t/s':>11} {'gen t/s':>9}")
    print("-" * 80)
    for r in results:
        short = r["model"].split("/")[-1]
        print(
            f"{short:<45} {r['load_s']:>6.1f}s {r['prompt_tps']:>11.1f} {r['gen_tps']:>9.1f}"
        )
    print()
    print("gen t/s = decode throughput (higher is better).")
    print("prompt t/s = prompt-processing throughput (higher is better).")


if __name__ == "__main__":
    main()
