"""Tests for the installer's ``write_llama_yaml`` (NR-LLM-005, T-LLM-005).

The installer must write a valid ``llama.yaml`` at ``<install_dir>/llama.yaml``
whose content is the canonical render of ``plan.llama_config``.  The file must
round-trip through ``load_llama_config`` and produce the same server-argument
set that ``plan.server_args()`` would emit.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay.installer import write_llama_yaml  # noqa: E402
from noerelay.llama_config import (  # noqa: E402
    load_llama_config,
    render_llama_config,
    server_args_from_config,
    validate_llama_config,
)
from noerelay.models import default_model  # noqa: E402
from noerelay.provision import ProvisionPlan, make_plan  # noqa: E402
from noerelay.system_info import GPU, SystemInfo  # noqa: E402


def _make_plan(tmpdir: Path, backend="cuda", gpus=None):
    """Build a minimal ProvisionPlan rooted at *tmpdir*."""
    if gpus is None:
        gpus = [GPU(0, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia")]
    system = SystemInfo(os="windows", arch="x86_64", backend=backend, gpus=gpus, ram_gb=32.0)
    plan = ProvisionPlan(
        system=system,
        backend=backend,
        os="windows",
        arch="x86_64",
        install_dir=tmpdir,
        model=default_model(),
    )
    # Populate llama_config the same way make_plan does.
    from noerelay.llama_config import validate_llama_config as _v
    plan.llama_config = _v({
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
    })
    return plan


class WriteLlamaYamlTests(unittest.TestCase):
    """Core write + round-trip behaviour."""

    def test_writes_file_at_install_dir(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            write_llama_yaml(plan)
            yaml_path = Path(td) / "llama.yaml"
            self.assertTrue(yaml_path.is_file(), "llama.yaml was not created")

    def test_content_matches_render(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            write_llama_yaml(plan)
            text = (Path(td) / "llama.yaml").read_text(encoding="utf-8")
            expected = render_llama_config(plan.llama_config)
            self.assertEqual(text, expected)

    def test_roundtrip_load(self):
        """Load the written YAML back and verify it validates."""
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            write_llama_yaml(plan)
            text = (Path(td) / "llama.yaml").read_text(encoding="utf-8")
            loaded = load_llama_config(text)
            # Server keys must match the plan's config.
            self.assertEqual(loaded["server"]["model"], plan.llama_config["server"]["model"])
            self.assertEqual(loaded["server"]["port"], plan.llama_config["server"]["port"])
            self.assertEqual(loaded["server"]["n_gpu_layers"], plan.llama_config["server"]["n_gpu_layers"])
            self.assertEqual(loaded["server"]["ctx_size"], plan.llama_config["server"]["ctx_size"])

    def test_server_args_match_plan(self):
        """Args generated from the written YAML must equal plan.server_args()."""
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            write_llama_yaml(plan)
            text = (Path(td) / "llama.yaml").read_text(encoding="utf-8")
            loaded = load_llama_config(text)
            yaml_args = server_args_from_config(loaded)
            plan_args = plan.server_args()
            self.assertEqual(yaml_args, plan_args)

    def test_skips_when_no_config(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            plan.llama_config = None
            write_llama_yaml(plan)
            self.assertFalse((Path(td) / "llama.yaml").exists())

    def test_multi_gpu_split_in_yaml(self):
        """A multi-GPU plan must carry split_mode and tensor_split in the YAML."""
        with tempfile.TemporaryDirectory() as td:
            gpus = [
                GPU(0, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia"),
                GPU(1, "NVIDIA GeForce RTX 5060 Ti", 16384, 0, False, "", "nvidia"),
            ]
            plan = _make_plan(Path(td), gpus=gpus)
            # Simulate what make_plan does for multi-GPU.
            plan.n_gpu_layers = 999
            plan.split_mode = "layer"
            plan.tensor_split = "14,11"
            from noerelay.llama_config import validate_llama_config as _v
            plan.llama_config = _v({
                "version": 1,
                "server": {
                    "model": str(plan.model_file),
                    "model_key": plan.model.key,
                    "host": plan.host,
                    "port": plan.port,
                    "n_gpu_layers": 999,
                    "split_mode": "layer",
                    "tensor_split": "14,11",
                    "ctx_size": plan.ctx_size,
                    "parallel": plan.parallel,
                },
            })
            write_llama_yaml(plan)
            text = (Path(td) / "llama.yaml").read_text(encoding="utf-8")
            self.assertIn("split_mode: layer", text)
            self.assertIn("tensor_split: '14,11'", text)
            loaded = load_llama_config(text)
            args = server_args_from_config(loaded)
            self.assertIn("--split-mode", args)
            self.assertEqual(args[args.index("--split-mode") + 1], "layer")
            self.assertIn("--tensor-split", args)
            self.assertEqual(args[args.index("--tensor-split") + 1], "14,11")


class ProvisionCallsWriteLlamaYamlTests(unittest.TestCase):
    """The top-level provision() must call write_llama_yaml."""

    def test_provision_invokes_write_llama_yaml(self):
        """Mock the heavy steps and verify write_llama_yaml is called."""
        with tempfile.TemporaryDirectory() as td:
            plan = _make_plan(Path(td))
            # make_plan and generate_scripts are imported lazily inside
            # provision(), so patch them at their source modules.
            with mock.patch("noerelay.installer.detect_system", return_value=plan.system), \
                 mock.patch("noerelay.provision.make_plan", return_value=plan), \
                 mock.patch("noerelay.installer.ensure_llama_build"), \
                 mock.patch("noerelay.installer.ensure_venv"), \
                 mock.patch("noerelay.installer.install_noerelay"), \
                 mock.patch("noerelay.installer.ensure_model"), \
                 mock.patch("noerelay.installer.write_config"), \
                 mock.patch("noerelay.installer.write_readme"), \
                 mock.patch("noerelay.installer.configure_noerelay"), \
                 mock.patch("noerelay.scripts.generate_scripts"), \
                 mock.patch("noerelay.installer.write_llama_yaml") as mock_wly:
                from noerelay.installer import provision
                provision(
                    install_dir=Path(td),
                    skip_download=True,
                    skip_venv=True,
                )
                mock_wly.assert_called_once_with(plan)


if __name__ == "__main__":
    unittest.main()
