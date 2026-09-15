"""Two-model local plane routing (NR-LLM-002).

The local profile runs two models with distinct tier metadata:

* **fast** — ``gpt-oss-20b`` for routine work (default routing),
* **hard** — ``qwen3.8-27b`` for difficult work (only under a declared
  escalation condition).

Routing is explicit and auditable: every decision returns the chosen tier,
the model key, and a machine-readable reason.  The escalation condition is
declared up front (risk class or an :class:`EscalationPolicy` signal) — the
router never picks the hard tier implicitly.  Dependency-free (stdlib only).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

#: Tier names for the two-model local plane.
FAST_TIER = "fast"
HARD_TIER = "hard"

#: Risk classes that declare escalation to the hard tier.
ESCALATING_RISK_CLASSES = ("high", "critical")

#: Default tier metadata for the two-model plane.  Keys are model keys from
#: the noerelay catalog; values carry the tier and a short routing note.
DEFAULT_LOCAL_TIERS: Dict[str, Dict[str, str]] = {
    "gpt-oss-20b-Q5_K_M": {"tier": FAST_TIER, "note": "operator-selected default Q5_K_M"},
    "gpt-oss-20b": {"tier": FAST_TIER, "note": "routine work (default)"},
    "gpt-oss-20b-q5": {"tier": FAST_TIER, "note": "routine work, Q5 quant"},
    "gpt-oss-20b-q6": {"tier": FAST_TIER, "note": "routine work, Q6 quant"},
    "qwen3.8-27b": {"tier": HARD_TIER, "note": "difficult work (escalation only)"},
}


class LocalTierRouter:
    """Routes local requests between the fast and hard model tiers.

    The fast tier is the default.  The hard tier is selected only when a
    declared escalation condition holds:

    * ``risk_class`` is ``high`` or ``critical``, or
    * a supplied :class:`EscalationPolicy` (or any object exposing
      ``should_escalate_to_cloud``) reports escalation for the request.

    Every decision is a dict with ``tier``, ``model``, ``escalated``, and
    ``reason`` so routing stays explicit and auditable.
    """

    def __init__(self, tiers: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        self._tiers = dict(DEFAULT_LOCAL_TIERS)
        if tiers:
            self._tiers.update(tiers)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def tiers(self) -> Dict[str, Dict[str, str]]:
        """Tier metadata (copy) for every known local model key."""
        return {k: dict(v) for k, v in self._tiers.items()}

    def tier_of(self, model_key: str) -> Optional[str]:
        meta = self._tiers.get(model_key)
        return meta.get("tier") if meta else None

    def model_for_tier(self, tier: str) -> Optional[str]:
        """First model key classified into *tier* (catalog order)."""
        for key, meta in self._tiers.items():
            if meta.get("tier") == tier:
                return key
        return None

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route(
        self,
        risk_class: str = "low",
        escalation_policy: Optional[Any] = None,
        local_model_failed: bool = False,
        request: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Choose the local model tier for one request.

        Returns a dict::

            {"tier": "fast"|"hard", "model": <key>, "escalated": bool,
             "reason": <machine-readable str>}
        """
        fast_model = self.model_for_tier(FAST_TIER)
        hard_model = self.model_for_tier(HARD_TIER)

        # Declared escalation condition 1: risk class.
        if risk_class in ESCALATING_RISK_CLASSES and hard_model:
            return self._decision(HARD_TIER, hard_model, True, f"risk_class_{risk_class}")

        # Declared escalation condition 2: policy signal (HIR/RR or failure).
        if escalation_policy is not None:
            try:
                should, reason = escalation_policy.should_escalate_to_cloud(
                    local_model_failed=local_model_failed, risk_class=risk_class
                )
            except Exception:  # noqa: BLE001
                should, reason = False, "policy_unavailable"
            if should and hard_model:
                return self._decision(HARD_TIER, hard_model, True, reason)

        # Default: fast tier.
        if fast_model:
            return self._decision(FAST_TIER, fast_model, False, "default_fast_tier")
        if hard_model:
            return self._decision(HARD_TIER, hard_model, False, "only_hard_tier_available")
        raise LookupError("no local tier models configured")

    # ------------------------------------------------------------------

    @staticmethod
    def _decision(tier: str, model: str, escalated: bool, reason: str) -> Dict[str, Any]:
        return {"tier": tier, "model": model, "escalated": escalated, "reason": reason}
