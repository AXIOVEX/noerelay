"""Tests for the offline Hugging Face autocomplete (NR-LLM-006, T-LLM-006).

Catalog and quant completions must work with **no network access**.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay.hf import (  # noqa: E402
    KNOWN_QUANTS,
    catalog_completions,
    complete,
    quant_completions,
)


class KnownQuantsTests(unittest.TestCase):
    def test_no_duplicates(self):
        self.assertEqual(len(KNOWN_QUANTS), len(set(KNOWN_QUANTS)))

    def test_common_quants_present(self):
        for q in ("Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "F16"):
            self.assertIn(q, KNOWN_QUANTS)


class QuantCompletionsTests(unittest.TestCase):
    def test_prefix_q4(self):
        out = quant_completions("Q4")
        self.assertIn("Q4_0", out)
        self.assertIn("Q4_K_M", out)
        self.assertTrue(all(o.startswith("Q4") for o in out))

    def test_case_insensitive_prefix(self):
        self.assertIn("Q4_K_M", quant_completions("q4"))

    def test_empty_returns_all(self):
        self.assertEqual(len(quant_completions("")), len(KNOWN_QUANTS))


class CatalogCompletionsTests(unittest.TestCase):
    def test_prefix_gpt_oss(self):
        self.assertIn("gpt-oss-20b", catalog_completions("gpt-oss"))

    def test_prefix_qwen(self):
        self.assertIn("qwen3.8-27b", catalog_completions("qwen3.8"))

    def test_filename_completion(self):
        self.assertIn("gpt-oss-20b-Q4_K_M.gguf", catalog_completions("gpt-oss-20b-Q4"))

    def test_empty_returns_catalog(self):
        self.assertIn("gpt-oss-20b", catalog_completions(""))


class CompleteHeuristicTests(unittest.TestCase):
    def test_short_caps_token_is_quant(self):
        out = complete("Q4")
        self.assertIn("Q4_K_M", out)
        self.assertNotIn("gpt-oss-20b", out)

    def test_model_token_is_catalog(self):
        self.assertIn("gpt-oss-20b-Q4_K_M.gguf", complete("gpt-oss-20b"))

    def test_repo_token_is_catalog(self):
        out = complete("unsloth/gpt-oss")
        self.assertTrue(any("unsloth/gpt-oss" in c for c in out))


if __name__ == "__main__":
    unittest.main()
