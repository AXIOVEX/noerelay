"""Tests for ``ProvisionPlan.server_args`` (NR-LLM-005).

The fallback (no master config) path must emit the long ``--n-gpu-layers``
flag (never the legacy ``-ngl``), and a plan carrying a master config must
delegate to the YAML-derived argument set.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay.models import default_model  # noqa: E402
from noerelay.provision import ProvisionPlan  # noqa: E402
from noerelay.system_info import SystemInfo  # noqa: E402


def _plan(backend, n_gpu_layers=0, llama_config=None):
    return ProvisionPlan(
        system=SystemInfo(backend=backend),
        backend=backend,
        n_gpu_layers=n_gpu_layers,
        model=default_model(),
        llama_config=llama_config,
    )


class FallbackArgTests(unittest.TestCase):
    def test_cpu_emits_long_flag_zero(self):
        args = _plan("cpu", 0).server_args()
        self.assertIn("--n-gpu-layers", args)
        self.assertEqual(args[args.index("--n-gpu-layers") + 1], "0")
        self.assertNotIn("-ngl", args)

    def test_cuda_emits_long_flag_999(self):
        args = _plan("cuda", 999).server_args()
        self.assertEqual(args[args.index("--n-gpu-layers") + 1], "999")
        self.assertNotIn("-ngl", args)

    def test_multi_gpu_split_flags(self):
        p = _plan("cuda", 999)
        p.split_mode = "layer"
        p.tensor_split = "10,15"
        args = p.server_args()
        self.assertEqual(args[args.index("--split-mode") + 1], "layer")
        self.assertEqual(args[args.index("--tensor-split") + 1], "10,15")

    def test_no_mtp_flag_only_when_set(self):
        p = _plan("cpu", 0)
        p.no_mtp = False
        self.assertNotIn("--no-mtp", p.server_args())
        p.no_mtp = True
        self.assertIn("--no-mtp", p.server_args())


class MasterConfigDelegationTests(unittest.TestCase):
    def test_delegates_to_yaml(self):
        from noerelay.llama_config import validate_llama_config
        cfg = validate_llama_config({
            "version": 1,
            "server": {
                "model": "C:\\Models\\m.gguf",
                "n_gpu_layers": 7,
                "ctx_size": 4096,
            },
        })
        p = _plan("cuda", 999, llama_config=cfg)
        args = p.server_args()
        self.assertEqual(args[0], "-m")
        # The plan's own model file is used for -m (model_path override)...
        self.assertEqual(args[1], str(p.model_file))
        # ...but every other setting comes from the master YAML.
        self.assertEqual(args[args.index("--n-gpu-layers") + 1], "7")
        self.assertEqual(args[args.index("--ctx-size") + 1], "4096")


if __name__ == "__main__":
    unittest.main()
