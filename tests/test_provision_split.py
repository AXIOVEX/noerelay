"""Tests for the multi-GPU tensor-split recommendation (NR-LLM-001).

The provisioner must treat the faster (higher memory-bandwidth) GPU as the
primary tensor owner. LLM token generation is memory-bandwidth-bound, so a
RTX 4070 SUPER (~504 GB/s) should hold more layers than a RTX 5060 Ti
(~448 GB/s) even though the 5060 Ti has more VRAM.
"""

import unittest

from noerelay.provision import _recommend_split, _gpu_bandwidth_gbs
from noerelay.system_info import GPU, SystemInfo


def _sys(gpus, backend="cuda"):
    return SystemInfo(gpus=gpus, backend=backend)


class RecommendSplitTests(unittest.TestCase):
    def test_single_gpu_returns_empty(self):
        s = _sys([GPU(0, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia")])
        self.assertEqual(_recommend_split(s), "")

    def test_no_nvidia_returns_empty(self):
        s = _sys([GPU(0, "Apple M4", 0, 0, False, "", "apple")])
        self.assertEqual(_recommend_split(s), "")

    def test_unknown_vram_fallback(self):
        # Unknown names -> VRAM-proportional weights.
        s = _sys([
            GPU(0, "Mystery A", 10000, 0, False, "", "nvidia"),
            GPU(1, "Mystery B", 20000, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertEqual(len(parts), 2)
        self.assertGreater(parts[1], parts[0])  # larger VRAM gets more

    def test_zero_vram_unknown_gives_equal_split(self):
        # Unknown names with 0 VRAM fall back to the clamped base weight of 1
        # each -> an even split.
        s = _sys([
            GPU(0, "Mystery A", 0, 0, False, "", "nvidia"),
            GPU(1, "Mystery B", 0, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], parts[1])


class BandwidthWeightingTests(unittest.TestCase):
    """The reference two-GPU host: 4070 SUPER (idx0) + 5060 Ti (idx1)."""

    def test_4070_super_is_primary(self):
        s = _sys([
            GPU(0, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia"),
            GPU(1, "NVIDIA GeForce RTX 5060 Ti", 16311, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertEqual(len(parts), 2)
        # Faster 4070 SUPER must hold >= the 5060 Ti's share.
        self.assertGreaterEqual(parts[0], parts[1])

    def test_primary_survives_index_swap(self):
        # 5060 Ti at idx0, 4070 SUPER at idx1 -> 4070 SUPER still wins.
        s = _sys([
            GPU(0, "NVIDIA GeForce RTX 5060 Ti", 16311, 0, False, "", "nvidia"),
            GPU(1, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertGreater(parts[1], parts[0])

    def test_display_gpu_penalized(self):
        # 5060 Ti drives the display -> it gets penalized, 4070 SUPER primary.
        s = _sys([
            GPU(0, "NVIDIA GeForce RTX 5060 Ti", 16311, 0, True, "", "nvidia"),
            GPU(1, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertGreater(parts[1], parts[0])

    def test_weights_sum_near_25(self):
        s = _sys([
            GPU(0, "NVIDIA GeForce RTX 4070 SUPER", 12282, 0, False, "", "nvidia"),
            GPU(1, "NVIDIA GeForce RTX 5060 Ti", 16311, 0, False, "", "nvidia"),
        ])
        parts = [int(x) for x in _recommend_split(s).split(",")]
        self.assertGreaterEqual(sum(parts), 20)
        self.assertLessEqual(sum(parts), 30)


class BandwidthLookupTests(unittest.TestCase):
    def test_known_names(self):
        self.assertEqual(_gpu_bandwidth_gbs("NVIDIA GeForce RTX 4070 SUPER"), 504.0)
        self.assertEqual(_gpu_bandwidth_gbs("NVIDIA GeForce RTX 5060 Ti"), 448.0)
        self.assertEqual(_gpu_bandwidth_gbs("NVIDIA GeForce RTX 4090"), 1008.0)

    def test_substring_specificity(self):
        # "4070 SUPER" must not be matched by the plain "4070" entry first.
        self.assertEqual(_gpu_bandwidth_gbs("RTX 4070 SUPER"), 504.0)
        self.assertEqual(_gpu_bandwidth_gbs("RTX 4070"), 504.0)
        self.assertEqual(_gpu_bandwidth_gbs("RTX 4070 Ti"), 672.0)

    def test_unknown_returns_none(self):
        self.assertIsNone(_gpu_bandwidth_gbs("Some Unknown Accelerator"))


if __name__ == "__main__":
    unittest.main()
