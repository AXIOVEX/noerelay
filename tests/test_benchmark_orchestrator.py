"""Recovery tests use mocks only; never touch the live server."""
import importlib.util
from pathlib import Path
from unittest.mock import Mock
import pytest

spec = importlib.util.spec_from_file_location("benchmark_orchestrator", Path(__file__).resolve().parents[1] / "scripts/run_tllm003_benchmark.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

@pytest.mark.parametrize("failure", ["stop", "vram", "benchmark", "restart", None])
def test_recovery_on_every_failure(monkeypatch, tmp_path, failure):
    monkeypatch.setattr(mod, "REPO", tmp_path)
    monkeypatch.setattr(mod, "set_maintenance", Mock())
    clear = Mock()
    monkeypatch.setattr(mod, "clear_maintenance", clear)
    monkeypatch.setattr(mod, "wait_healthy", Mock(return_value=True))
    for name, stage in [("run", "stop"), ("call", "benchmark"), ("Popen", "restart")]:
        monkeypatch.setattr(mod.subprocess, name, Mock(side_effect=RuntimeError(stage) if failure == stage else None, return_value=0))
    monkeypatch.setattr(mod, "wait_vram_free", Mock(side_effect=RuntimeError("vram") if failure == "vram" else None))
    if failure:
        with pytest.raises(RuntimeError):
            mod.main()
    else:
        assert mod.main() == 0
    mod.subprocess.Popen.assert_called_once()
    clear.assert_called_once()
    if failure in ("stop", "vram"):
        mod.subprocess.call.assert_not_called()

def test_busy_gpu_aborts(monkeypatch):
    monkeypatch.setattr(mod, "vram_total_mib", lambda: 5000)
    with pytest.raises(TimeoutError):
        mod.wait_vram_free(timeout=0)

bench_spec = importlib.util.spec_from_file_location("local_benchmark", Path(__file__).resolve().parents[1] / "scripts/benchmark_local_models.py")
bench = importlib.util.module_from_spec(bench_spec)
bench_spec.loader.exec_module(bench)

def test_benchmark_stop_uses_sanctioned_script(monkeypatch):
    run = Mock()
    monkeypatch.setattr(bench.subprocess, "run", run)
    proc = Mock()
    proc.poll.return_value = None
    bench.stop_server(proc)
    assert run.call_args.args[0][-1] == r"C:\LLM\stop-llama-server.ps1"
    proc.terminate.assert_not_called()
    proc.kill.assert_not_called()

@pytest.mark.parametrize("choice,exit_code,expected", [("Q4_K_M", 0, 0), ("Q6_K", 0, 1), ("Q4_K_M", 1, 1), (None, 0, 1)])
def test_artifact_rejects_invalid_choice_or_quality(tmp_path, choice, exit_code, expected):
    import json
    results = [dict(quant=q, ttft_s=1, tokens_per_s=10, perplexity=2, perplexity_exit_code=exit_code, vram_mib={"delta": [i+1]}) for i, q in enumerate(bench.QUANT_FILES)]
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps(dict(model=bench.MODEL_NAME, environment={}, results=results, chosen_quant=choice, rationale="test")))
    assert bench.verify_artifact(artifact) == expected
