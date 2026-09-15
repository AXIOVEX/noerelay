"""Tests for the model catalog tier metadata (NR-LLM-001/002).

The catalog must carry distinct tier metadata for the two local-plane models
and expose a machine-readable supported-model list.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay.models import (  # noqa: E402
    MODEL_CATALOG,
    default_model,
    get_model,
    models_by_tier,
    supported_models,
)


class TierMetadataTests(unittest.TestCase):
    def test_fast_tier_models(self):
        keys = {m.key for m in models_by_tier("fast")}
        self.assertIn("gpt-oss-20b", keys)
        self.assertIn("gpt-oss-20b-q5", keys)
        self.assertIn("gpt-oss-20b-q6", keys)

    def test_hard_tier_models(self):
        self.assertEqual({m.key for m in models_by_tier("hard")}, {"qwen3.8-27b"})

    def test_tiers_are_disjoint(self):
        fast = {m.key for m in models_by_tier("fast")}
        hard = {m.key for m in models_by_tier("hard")}
        self.assertFalse(fast & hard)

    def test_invalid_tier_raises(self):
        with self.assertRaises(ValueError):
            models_by_tier("bogus")

    def test_default_is_fast_gpt_oss(self):
        d = default_model()
        self.assertEqual(d.key, "gpt-oss-20b-q5")
        self.assertTrue(d.default)
        self.assertEqual(d.tier, "fast")

    def test_gpt_oss_filename(self):
        self.assertEqual(get_model("gpt-oss-20b").filename, "gpt-oss-20b-Q4_K_M.gguf")

    def test_qwen_filename_and_tier(self):
        m = get_model("qwen3.8-27b")
        self.assertEqual(m.filename, "qwen3.8-27b.gguf")
        self.assertEqual(m.tier, "hard")


class SupportedModelsTests(unittest.TestCase):
    def test_returns_list_of_dicts(self):
        rows = supported_models()
        self.assertIsInstance(rows, list)
        self.assertTrue(all(isinstance(r, dict) for r in rows))

    def test_covers_entire_catalog(self):
        self.assertEqual(len(supported_models()), len(MODEL_CATALOG))

    def test_required_fields_present(self):
        required = {"key", "name", "repo_id", "quant", "size_gb",
                    "min_vram_gb", "min_ram_gb", "tier", "filename",
                    "agentic_score", "default"}
        for r in supported_models():
            self.assertTrue(required.issubset(r.keys()), r["key"])

    def test_both_tier_models_present_with_tier(self):
        by_key = {r["key"]: r for r in supported_models()}
        self.assertEqual(by_key["gpt-oss-20b"]["tier"], "fast")
        self.assertEqual(by_key["qwen3.8-27b"]["tier"], "hard")

    def test_machine_readable_json_serializable(self):
        s = json.dumps(supported_models())
        self.assertIn("gpt-oss-20b", s)
        self.assertIn("qwen3.8-27b", s)


if __name__ == "__main__":
    unittest.main()
