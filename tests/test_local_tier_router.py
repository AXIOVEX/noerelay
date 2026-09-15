"""Tests for the two-model local plane router (NR-LLM-002, T-LLM-002).

The fast tier is the default.  The hard tier is selected **only** under a
declared escalation condition (risk class high/critical, or an
:class:`EscalationPolicy` signal such as a local-model failure).
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gateway.escalation_policy import EscalationPolicy  # noqa: E402
from gateway.local_tier_router import (  # noqa: E402
    DEFAULT_LOCAL_TIERS,
    FAST_TIER,
    HARD_TIER,
    LocalTierRouter,
)


class DefaultRoutingTests(unittest.TestCase):
    def setUp(self):
        self.r = LocalTierRouter()

    def test_fast_is_default(self):
        d = self.r.route()
        self.assertEqual(d["tier"], FAST_TIER)
        self.assertEqual(d["model"], "gpt-oss-20b-Q5_K_M")
        self.assertFalse(d["escalated"])

    def test_low_risk_stays_fast(self):
        d = self.r.route(risk_class="low")
        self.assertEqual(d["tier"], FAST_TIER)
        self.assertFalse(d["escalated"])

    def test_medium_risk_stays_fast(self):
        d = self.r.route(risk_class="medium")
        self.assertEqual(d["tier"], FAST_TIER)
        self.assertFalse(d["escalated"])


class EscalationRoutingTests(unittest.TestCase):
    def setUp(self):
        self.r = LocalTierRouter()

    def test_high_risk_escalates(self):
        d = self.r.route(risk_class="high")
        self.assertEqual(d["tier"], HARD_TIER)
        self.assertEqual(d["model"], "qwen3.8-27b")
        self.assertTrue(d["escalated"])
        self.assertEqual(d["reason"], "risk_class_high")

    def test_critical_risk_escalates(self):
        d = self.r.route(risk_class="critical")
        self.assertEqual(d["tier"], HARD_TIER)
        self.assertTrue(d["escalated"])

    def test_policy_local_model_failed_escalates(self):
        d = self.r.route(escalation_policy=EscalationPolicy(), local_model_failed=True)
        self.assertEqual(d["tier"], HARD_TIER)
        self.assertTrue(d["escalated"])
        self.assertEqual(d["reason"], "local_model_failed")

    def test_policy_no_failure_stays_fast(self):
        d = self.r.route(escalation_policy=EscalationPolicy(),
                         local_model_failed=False, risk_class="low")
        self.assertEqual(d["tier"], FAST_TIER)
        self.assertFalse(d["escalated"])

    def test_risk_class_overrides_fast_default(self):
        d = self.r.route(risk_class="high")
        self.assertNotEqual(d["model"], self.r.model_for_tier(FAST_TIER))


class TierMetadataTests(unittest.TestCase):
    def test_default_tiers_carry_distinct_metadata(self):
        self.assertEqual(DEFAULT_LOCAL_TIERS["gpt-oss-20b"]["tier"], FAST_TIER)
        self.assertEqual(DEFAULT_LOCAL_TIERS["qwen3.8-27b"]["tier"], HARD_TIER)

    def test_model_for_tier(self):
        r = LocalTierRouter()
        self.assertEqual(r.model_for_tier(FAST_TIER), "gpt-oss-20b-Q5_K_M")
        self.assertEqual(r.model_for_tier(HARD_TIER), "qwen3.8-27b")

    def test_tier_of(self):
        r = LocalTierRouter()
        self.assertEqual(r.tier_of("qwen3.8-27b"), HARD_TIER)
        self.assertIsNone(r.tier_of("unknown-model"))

    def test_custom_tiers_merged(self):
        r = LocalTierRouter(tiers={"custom-fast": {"tier": FAST_TIER, "note": "x"}})
        self.assertEqual(r.tier_of("custom-fast"), FAST_TIER)
        self.assertIn("custom-fast", r.tiers)
        # The default fast model remains first in catalog order.
        self.assertEqual(r.model_for_tier(FAST_TIER), "gpt-oss-20b-Q5_K_M")


if __name__ == "__main__":
    unittest.main()
