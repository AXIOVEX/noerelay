"""Tests for the master llama-server YAML config (NR-LLM-005, T-LLM-005).

A single ``llama.yaml`` must carry **all** llama-server settings, generate the
exact reference argument set (matching ``start-llama-server.ps1``), and reject
unknown keys.  The loader must work with pyyaml present *and* with the stdlib
mini-parser fallback.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay import llama_config as _lc  # noqa: E402
from noerelay.llama_config import (  # noqa: E402
    LlamaConfigError,
    load_llama_config,
    render_llama_config,
    server_args_from_config,
    validate_llama_config,
)

# The canonical reference argument set from C:\LLM\start-llama-server.ps1
# (llama.cpp b10894).  Note: there is NO --no-mtp flag in the reference.
REFERENCE_MODEL = r"C:\Models\qwen3.8-27b.gguf"
REFERENCE_ARGS = [
    "-m", REFERENCE_MODEL,
    "--host", "127.0.0.1",
    "--port", "8080",
    "--n-gpu-layers", "999",
    "--split-mode", "layer",
    "--tensor-split", "10,15",
    "--ctx-size", "131072",
    "--parallel", "1",
    "--batch-size", "512",
    "--ubatch-size", "256",
    "--flash-attn", "auto",
    "--cache-type-k", "q4_0",
    "--cache-type-v", "q4_0",
    "--no-reasoning-preserve",
    "--metrics",
]


def _reference_config() -> dict:
    return validate_llama_config({
        "version": 1,
        "server": {
            "model": REFERENCE_MODEL,
            "model_key": "qwen3.8-27b",
            "host": "127.0.0.1",
            "port": 8080,
            "n_gpu_layers": 999,
            "split_mode": "layer",
            "tensor_split": "10,15",
            "ctx_size": 131072,
            "parallel": 1,
            "batch_size": 512,
            "ubatch_size": 256,
            "flash_attn": "auto",
            "cache_type_k": "q4_0",
            "cache_type_v": "q4_0",
            "no_mtp": False,
            "no_reasoning_preserve": True,
            "metrics": True,
        },
    })


class ReferenceArgSetTests(unittest.TestCase):
    def test_args_match_reference_ps1(self):
        self.assertEqual(server_args_from_config(_reference_config()), REFERENCE_ARGS)

    def test_no_mtp_absent_by_default(self):
        self.assertNotIn("--no-mtp", server_args_from_config(_reference_config()))

    def test_n_gpu_layers_always_emitted(self):
        cfg = validate_llama_config({"server": {"model": "x.gguf", "n_gpu_layers": 0}})
        args = server_args_from_config(cfg)
        self.assertEqual(args[args.index("--n-gpu-layers") + 1], "0")

    def test_no_model_raises(self):
        with self.assertRaises(LlamaConfigError):
            server_args_from_config(validate_llama_config({"server": {}}))


class UnknownKeyRejectionTests(unittest.TestCase):
    def test_unknown_top_level_key(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"version": 1, "server": {}, "bogus": 1})

    def test_unknown_server_key(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"server": {"model": "x", "nonsense": True}})

    def test_bad_enum_split_mode(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"server": {"split_mode": "diagonal"}})

    def test_bad_enum_flash_attn(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"server": {"flash_attn": "maybe"}})

    def test_bad_tensor_split(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"server": {"tensor_split": "10,abc"}})

    def test_bad_type_port(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config({"server": {"port": "8080"}})

    def test_non_dict_top_level(self):
        with self.assertRaises(LlamaConfigError):
            validate_llama_config(["not", "a", "dict"])


class RenderLoadRoundTripTests(unittest.TestCase):
    def test_round_trip_preserves_args(self):
        text = render_llama_config(_reference_config())
        self.assertEqual(server_args_from_config(load_llama_config(text)), REFERENCE_ARGS)

    def test_round_trip_values(self):
        reloaded = load_llama_config(render_llama_config(_reference_config()))
        self.assertEqual(reloaded["server"]["model"], REFERENCE_MODEL)
        self.assertEqual(reloaded["server"]["n_gpu_layers"], 999)
        self.assertEqual(reloaded["server"]["tensor_split"], "10,15")
        self.assertFalse(reloaded["server"]["no_mtp"])
        self.assertTrue(reloaded["server"]["metrics"])

    def test_windows_path_survives_render(self):
        # Double-quoted Windows paths are invalid YAML escapes under PyYAML;
        # the renderer must emit single-quoted strings so PyYAML and the
        # mini-parser agree.
        text = render_llama_config(_reference_config())
        self.assertIn(f"model: '{REFERENCE_MODEL}'", text)
        self.assertNotIn(f'model: "{REFERENCE_MODEL}"', text)


class MiniParserFallbackTests(unittest.TestCase):
    def test_mini_parser_matches_reference(self):
        data = _lc._mini_yaml_load(render_llama_config(_reference_config()))
        self.assertEqual(server_args_from_config(validate_llama_config(data)), REFERENCE_ARGS)

    def test_mini_parser_scalars(self):
        data = _lc._mini_yaml_load(
            "version: 1\n"
            "server:\n"
            "  host: 127.0.0.1\n"
            "  port: 8080\n"
            "  ctx_size: 131072\n"
            "  no_mtp: false\n"
            "  metrics: true\n"
            "  tensor_split: '10,15'\n"
        )
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["server"]["host"], "127.0.0.1")
        self.assertEqual(data["server"]["port"], 8080)
        self.assertEqual(data["server"]["ctx_size"], 131072)
        self.assertFalse(data["server"]["no_mtp"])
        self.assertTrue(data["server"]["metrics"])
        self.assertEqual(data["server"]["tensor_split"], "10,15")

    def test_mini_parser_inline_list(self):
        data = _lc._mini_yaml_load("server:\n  extra_args: [--foo, bar]\n")
        self.assertEqual(data["server"]["extra_args"], ["--foo", "bar"])

    def test_mini_parser_block_list(self):
        data = _lc._mini_yaml_load("server:\n  extra_args:\n    - --foo\n    - bar\n")
        self.assertEqual(data["server"]["extra_args"], ["--foo", "bar"])

    def test_mini_parser_rejects_tabs(self):
        with self.assertRaises(LlamaConfigError):
            _lc._mini_yaml_load("server:\n\tmodel: x\n")


if __name__ == "__main__":
    unittest.main()
