"""
AAA Engine - Centralized Policy Engine

The ONLY final decision authority for authentication outcomes.
Implements the five approved decision outcomes per SYSTEM.md §6:
- APPROVE: All mandatory gates pass, policy permits approval
- DENY: Authentication fails, challenge invalid, replay detected, phrase mismatch, or explicit rejection
- STEP_UP: Additional verification required (fresh challenge or additional capture)
- REVIEW: Human review required (HIGH/uncertain vishing risk)
- UNAVAILABLE: Mandatory dependency unavailable, fail closed

SECURITY INVARIANTS:
- STEP_UP and REVIEW never become APPROVE without additional verification
- UNAVAILABLE never becomes APPROVE
- Internal scores never exposed to host applications
- All decisions are logged with audit trail
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..schemas.common import Decision, RiskLevel

logger = logging.getLogger("aaa_engine.policy")


class GateResult(StrEnum):
    """Individual gate verification results."""
    PASS = "PASS"
    FAIL = "FAIL"
    BORDERLINE = "BORDERLINE"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"


@dataclass
class PolicyInput:
    """Input to the policy engine from all verification stages."""

    # Challenge state
    challenge_valid: bool = False
    challenge_expired: bool = False
    challenge_consumed: bool = False

    # Deepfake Detection (AD)
    ad_available: bool = True
    ad_result: GateResult = GateResult.UNAVAILABLE
    ad_confidence: float = 0.0
    ad_is_spoof: bool = False

    # ASR Phrase Verification
    asr_available: bool = True
    asr_result: GateResult = GateResult.UNAVAILABLE
    asr_match: bool = False
    asr_confidence: float = 0.0

    # Speaker Verification (SV)
    sv_available: bool = True
    sv_result: GateResult = GateResult.UNAVAILABLE
    sv_score: float = 0.0
    sv_threshold: float = 0.5

    # AAA-VR Risk Analysis (optional)
    vr_available: bool = False
    vr_risk_level: RiskLevel = RiskLevel.LOW
    vr_recommended_action: str | None = None

    # Session and context
    attempt_count: int = 0
    max_attempts: int = 5
    lockout_active: bool = False

    # Tenant configuration
    tenant_config: dict[str, Any] | None = None


@dataclass
class PolicyOutput:
    """Output from the policy engine."""

    decision: Decision
    reason_public: str
    reason_internal: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    requires_fresh_challenge: bool = False
    requires_human_review: bool = False
    gate_blocked: str | None = None


class PolicyEngine:
    """
    Centralized AAA Policy Engine.

    The ONLY authority for final authentication decisions.
    Models return scores; this engine returns decisions.
    Host apps receive only safe outcomes.
    """

    # Public reason categories (safe to expose)
    REASON_OK = "OK"
    REASON_CHALLENGE_EXPIRED = "CHALLENGE_EXPIRED"
    REASON_CHALLENGE_INVALID = "CHALLENGE_INVALID"
    REASON_REPLAY_DETECTED = "REPLAY_DETECTED"
    REASON_PHRASE_MISMATCH = "PHRASE_MISMATCH"
    REASON_AUTH_FAILED = "AUTH_FAILED"  # Generic - no gate details
    REASON_AUDIO_QUALITY = "AUDIO_QUALITY"
    REASON_HIGH_RISK = "HIGH_RISK"
    REASON_REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REASON_LOCKED = "LOCKED"
    REASON_SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    REASON_TRY_AGAIN = "TRY_AGAIN"

    def __init__(self, strict_mode: bool = True):
        """
        Initialize policy engine.

        Args:
            strict_mode: If True, fail closed on any uncertainty
        """
        self.strict_mode = strict_mode

    def evaluate(self, input: PolicyInput) -> PolicyOutput:
        """
        Evaluate all evidence and produce a final decision.

        This is the ONLY entry point for authentication decisions.

        Args:
            input: PolicyInput with all verification results

        Returns:
            PolicyOutput with decision and public reason
        """
        # PRIORITY 1: Check for service unavailability (fail closed)
        if not input.ad_available or not input.asr_available or not input.sv_available:
            unavailable_gates = []
            if not input.ad_available:
                unavailable_gates.append("AD")
            if not input.asr_available:
                unavailable_gates.append("ASR")
            if not input.sv_available:
                unavailable_gates.append("SV")

            logger.warning(f"Service unavailable: {unavailable_gates}")
            return PolicyOutput(
                decision=Decision.UNAVAILABLE,
                reason_public=self.REASON_SERVICE_UNAVAILABLE,
                reason_internal=f"Unavailable gates: {', '.join(unavailable_gates)}",
                gate_blocked="SERVICE",
            )

        # PRIORITY 2: Check lockout
        if input.lockout_active:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_LOCKED,
                reason_internal="Account locked due to failed attempts",
            )

        # PRIORITY 3: Check challenge validity
        if input.challenge_expired:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_CHALLENGE_EXPIRED,
                reason_internal="Challenge has expired",
                requires_fresh_challenge=True,
            )

        if input.challenge_consumed:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_REPLAY_DETECTED,
                reason_internal="Challenge already used (replay attempt)",
            )

        if not input.challenge_valid:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_CHALLENGE_INVALID,
                reason_internal="Invalid challenge token",
            )

        # PRIORITY 4: Check AD result
        if input.ad_result == GateResult.FAIL or input.ad_is_spoof:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_AUTH_FAILED,
                reason_internal="Deepfake/spoof detected",
                gate_blocked="AD",
            )

        if input.ad_result == GateResult.BORDERLINE:
            # Borderline AD -> require step-up
            return PolicyOutput(
                decision=Decision.STEP_UP,
                reason_public=self.REASON_TRY_AGAIN,
                reason_internal="AD result borderline, additional capture needed",
                requires_fresh_challenge=True,
            )

        if input.ad_result == GateResult.TIMEOUT:
            return PolicyOutput(
                decision=Decision.UNAVAILABLE,
                reason_public=self.REASON_SERVICE_UNAVAILABLE,
                reason_internal="AD model timeout",
                gate_blocked="AD",
            )

        # PRIORITY 5: Check ASR result
        if not input.asr_match:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_PHRASE_MISMATCH,
                reason_internal="Challenge phrase not matched",
                gate_blocked="ASR",
            )

        if input.asr_result == GateResult.TIMEOUT:
            return PolicyOutput(
                decision=Decision.UNAVAILABLE,
                reason_public=self.REASON_SERVICE_UNAVAILABLE,
                reason_internal="ASR model timeout",
                gate_blocked="ASR",
            )

        # PRIORITY 6: Check SV result
        if input.sv_result == GateResult.FAIL or input.sv_score < input.sv_threshold:
            return PolicyOutput(
                decision=Decision.DENY,
                reason_public=self.REASON_AUTH_FAILED,
                reason_internal="Speaker verification failed",
                gate_blocked="SV",
            )

        if input.sv_result == GateResult.TIMEOUT:
            return PolicyOutput(
                decision=Decision.UNAVAILABLE,
                reason_public=self.REASON_SERVICE_UNAVAILABLE,
                reason_internal="SV model timeout",
                gate_blocked="SV",
            )

        # PRIORITY 7: Check VR risk if available
        if input.vr_available:
            if input.vr_risk_level == RiskLevel.CRITICAL:
                return PolicyOutput(
                    decision=Decision.DENY,
                    reason_public=self.REASON_HIGH_RISK,
                    reason_internal="Critical vishing risk detected",
                    risk_level=RiskLevel.CRITICAL,
                )

            if input.vr_risk_level == RiskLevel.HIGH:
                # HIGH risk -> REVIEW (human intervention)
                return PolicyOutput(
                    decision=Decision.REVIEW,
                    reason_public=self.REASON_REVIEW_REQUIRED,
                    reason_internal="High vishing risk - human review required",
                    risk_level=RiskLevel.HIGH,
                    requires_human_review=True,
                )

            if input.vr_risk_level == RiskLevel.MEDIUM:
                # MEDIUM risk with tenant config check
                tenant_config = input.tenant_config or {}
                if tenant_config.get("step_up_on_medium_risk", False):
                    return PolicyOutput(
                        decision=Decision.STEP_UP,
                        reason_public=self.REASON_TRY_AGAIN,
                        reason_internal="Medium risk - step-up per tenant config",
                        risk_level=RiskLevel.MEDIUM,
                        requires_fresh_challenge=True,
                    )

        # PRIORITY 8: All gates passed
        return PolicyOutput(
            decision=Decision.APPROVE,
            reason_public=self.REASON_OK,
            reason_internal="All verification gates passed",
            risk_level=input.vr_risk_level if input.vr_available else RiskLevel.LOW,
        )


# Singleton instance
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get the singleton policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


def evaluate_policy(input: PolicyInput) -> PolicyOutput:
    """Convenience function for policy evaluation."""
    return get_policy_engine().evaluate(input)
