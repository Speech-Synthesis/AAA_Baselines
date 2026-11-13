"""
AAA-VR: Transcript Risk Analysis Model Adapter
Analyzes conversational transcripts for vishing, fraud indicators, and coercion patterns.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import re
from datetime import UTC, datetime

from ..schemas.risk import (
    RiskAction,
    RiskIndicator,
    RiskLevel,
    TranscriptRiskRequest,
    TranscriptRiskResponse,
)
from .base import ModelAdapter, ModelInfo

PATTERNS: dict[RiskIndicator, list[str]] = {
    RiskIndicator.URGENT_TRANSFER_REQUEST: [
        r"urgent(ly)?",
        r"immediately",
        r"right now",
        r"emergency wire",
        r"transfer.*immediately",
        r"rush.*transfer",
        r"asap",
        r"deadline",
    ],
    RiskIndicator.PRESSURE_TACTICS_DETECTED: [
        r"arrest",
        r"police",
        r"law enforcement",
        r"legal action",
        r"warrant",
        r"suspended",
        r"lawsuit",
        r"penalty",
        r"jail",
    ],
    RiskIndicator.ACCOUNT_NUMBER_MENTIONED: [
        r"account.*ending.*in",
        r"routing.*number",
        r"wire.*to",
        r"\d{4}[ -]?\d{4}[ -]?\d{4}",
        r"iban",
        r"swift code",
    ],
    RiskIndicator.CREDENTIAL_HARVESTING_ATTEMPT: [
        r"otp",
        r"one[- ]time password",
        r"security code",
        r"pin number",
        r"password",
        r"cvv",
        r"social security",
        r"ssn",
    ],
    RiskIndicator.UNVERIFIED_BENEFICIARY: [
        r"new account",
        r"unlisted beneficiary",
        r"third[- ]party account",
        r"bitcoin",
        r"crypto",
        r"gift card",
    ],
    RiskIndicator.IMPERSONATION_ATTEMPT: [
        r"fraud department",
        r"security team",
        r"internal affairs",
        r"federal agent",
        r"bank manager",
        r"irs agent",
    ],
}


class TranscriptRiskAdapter(ModelAdapter):
    """Adapter implementing AAA-VR vishing and transcript risk detection."""

    def __init__(self, model_version: str = "aaa-vr-transcript-risk-v1"):
        self._model_version = model_version
        self._is_loaded = True

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="AAA-VR Transcript Risk Engine",
            version="1.0.0",
            model_id=self._model_version,
            is_loaded=self._is_loaded,
        )

    def is_ready(self) -> bool:
        return self._is_loaded

    def load(self) -> bool:
        self._is_loaded = True
        return True

    def unload(self) -> None:
        self._is_loaded = False

    def analyze_transcript(self, transcript: str) -> tuple[RiskLevel, list[str], str, float]:
        """Analyzes transcript against approved indicator rules."""
        text = transcript.lower()
        detected: list[str] = []

        for indicator, regex_list in PATTERNS.items():
            for pattern in regex_list:
                if re.search(pattern, text):
                    detected.append(indicator.value)
                    break

        count = len(detected)

        # Decision matrix based on risk indicator density
        if count == 0:
            return RiskLevel.LOW, [], RiskAction.APPROVE.value, 0.95
        elif count == 1:
            return RiskLevel.MEDIUM, detected, RiskAction.REVIEW.value, 0.85
        elif count in (2, 3):
            return RiskLevel.HIGH, detected, RiskAction.STEP_UP.value, 0.90
        else:
            return RiskLevel.CRITICAL, detected, RiskAction.DENY.value, 0.96

    def predict(self, request: TranscriptRiskRequest, request_id: str) -> TranscriptRiskResponse:
        """Executes risk evaluation and packages safe response metadata."""
        risk_level, indicators, action, confidence = self.analyze_transcript(request.transcript)
        return TranscriptRiskResponse(
            request_id=request_id,
            session_id=request.session_id,
            risk_level=risk_level,
            risk_indicators=indicators,
            recommended_action=action,
            confidence=confidence,
            model_version=self._model_version,
            analyzed_at=datetime.now(UTC).isoformat(),
        )
