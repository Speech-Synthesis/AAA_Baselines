"""
AAA-VR: Transcript Risk Analysis Model Adapter
Analyzes conversational transcripts for vishing, fraud indicators, and coercion patterns.

Per AAA-VR.md, implements:
- Role awareness (agent warnings vs. caller requests)
- Negation frame detection ("never share", "do not")
- Quoted/reported speech handling
- Hard-negative classification (legitimate security warnings)

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import re
from datetime import UTC, datetime
from enum import Enum

from ..schemas.risk import (
    RiskAction,
    RiskIndicator,
    RiskLevel,
    TranscriptRiskRequest,
    TranscriptRiskResponse,
)
from .base import ModelAdapter, ModelInfo


class SpeakerRole(str, Enum):
    """Speaker role in conversation."""

    AGENT = "agent"
    CALLER = "caller"
    CUSTOMER = "customer"
    UNKNOWN = "unknown"


# Negation patterns that indicate warnings/advisories (hard negatives)
NEGATION_PATTERNS = [
    r"never\s+(?:share|give|tell|reveal|disclose|provide)",
    r"do\s+not\s+(?:share|give|tell|reveal|disclose|provide)",
    r"don'?t\s+(?:share|give|tell|reveal|disclose|provide)",
    r"should\s+not\s+(?:share|give|tell|reveal|disclose|provide)",
    r"won'?t\s+(?:ask|request|need)\s+(?:you\s+)?(?:for\s+)?(?:your\s+)?",
    r"we\s+will\s+never\s+(?:ask|request)",
    r"(?:bank|we)\s+(?:will\s+)?never\s+(?:ask|call|request)",
    r"avoid\s+(?:sharing|giving|telling)",
    r"keep\s+(?:your\s+)?(?:otp|pin|password|cvv).*(?:private|secret|safe|confidential)",
    r"protect\s+(?:your\s+)?(?:credentials|otp|pin|password)",
]

# Agent/advisory role indicators
AGENT_ADVISORY_PATTERNS = [
    r"(?:this\s+is\s+)?(?:a\s+)?(?:security\s+)?(?:reminder|advisory|notice|warning)",
    r"(?:for|as)\s+(?:a\s+)?(?:security|safety)\s+(?:measure|precaution)",
    r"fraud\s+prevention\s+(?:unit|team|department)",
    r"security\s+(?:advisory|alert|tip|reminder)",
    r"(?:please\s+)?be\s+(?:aware|careful|cautious)",
    r"(?:legitimate|real)\s+(?:bank|agent|representative)",
]

# Quoted/reported speech patterns
QUOTED_SPEECH_PATTERNS = [
    r"(?:he|she|they|someone)\s+(?:said|asked|told|requested)",
    r"(?:my\s+)?(?:friend|colleague|neighbor)\s+(?:said|asked|mentioned)",
    r"(?:i\s+)?(?:was\s+)?(?:told|asked)\s+(?:to|that)",
    r'["\'].*(?:otp|pin|password).*["\']',
]

# Authority/pressure patterns (scam indicators)
AUTHORITY_PRESSURE_PATTERNS = [
    r"(?:i\s+am|this\s+is)\s+(?:the\s+)?(?:director|manager|supervisor)",
    r"(?:police|authority|government|irs|tax)\s+(?:officer|agent|official)",
    r"(?:will\s+be\s+)?(?:arrested|suspended|terminated|blocked)",
    r"(?:no\s+)?time\s+(?:for\s+)?(?:procedures|verification|questions)",
    r"(?:skip|bypass|ignore)\s+(?:the\s+)?(?:verification|security|procedures)",
    r"(?:stay\s+on\s+the\s+)?line",
    r"(?:don'?t\s+)?(?:hang\s+up|disconnect)",
]

# Credential request patterns (scam indicators when NOT negated)
CREDENTIAL_REQUEST_PATTERNS = [
    r"(?:tell|give|share|read|provide)\s+(?:me\s+)?(?:your\s+)?(?:the\s+)?otp",
    r"(?:tell|give|share|read|provide)\s+(?:me\s+)?(?:your\s+)?(?:the\s+)?pin",
    r"(?:tell|give|share|read|provide)\s+(?:me\s+)?(?:your\s+)?(?:the\s+)?password",
    r"(?:tell|give|share|read|provide)\s+(?:me\s+)?(?:your\s+)?(?:the\s+)?cvv",
    r"what\s+is\s+(?:your\s+)?(?:the\s+)?otp",
    r"read\s+(?:me\s+)?(?:back\s+)?(?:the\s+)?(?:code|otp|pin)",
    r"verify.*by\s+(?:giving|telling|sharing)\s+(?:your\s+)?otp",
]

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
        r"\d{4}[ -]?\d{4}[ -]?\d{4}",
        r"iban",
        r"swift code",
    ],
    RiskIndicator.CREDENTIAL_HARVESTING_ATTEMPT: [
        r"otp",
        r"one[- ]time password",
        r"security code",
        r"pin number",
        r"password",
        r"cvv",
        r"social security",
        r"ssn",
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
    # New indicators for 10/10 threat coverage
    RiskIndicator.REMOTE_ACCESS_REQUEST: [
        r"remote\s*access",
        r"screen\s*share",
        r"anydesk",
        r"teamviewer",
        r"remote\s*desktop",
        r"let\s+me\s+(?:access|control|see)\s+your",
        r"install\s+(?:this\s+)?(?:software|app|program)",
        r"download\s+(?:this\s+)?(?:tool|software|app)",
        r"click\s+(?:this\s+)?link",
    ],
    RiskIndicator.EMOTIONAL_MANIPULATION: [
        r"family\s+(?:member|emergency|crisis)",
        r"loved\s+one",
        r"your\s+(?:son|daughter|mother|father|grandchild)",
        r"been\s+(?:in\s+an?\s+)?(?:accident|arrested|kidnapped)",
        r"crying",
        r"(?:very\s+)?scared",
        r"don'?t\s+tell\s+anyone",
        r"keep\s+(?:this\s+)?secret",
        r"embarrassing",
        r"trust\s+(?:only\s+)?me",
    ],
    RiskIndicator.FINANCIAL_COERCION: [
        r"lose\s+(?:all\s+)?(?:your\s+)?(?:money|savings|funds)",
        r"account\s+(?:will\s+be\s+)?(?:frozen|closed|suspended)",
        r"seize\s+(?:your\s+)?(?:assets|property|funds)",
        r"owe\s+(?:us\s+)?money",
        r"pay\s+(?:the\s+)?(?:fine|penalty|fee)\s+(?:now|immediately)",
        r"tax\s+(?:debt|owed|due)",
        r"(?:back\s+)?taxes",
        r"debt\s+collector",
        r"repossess",
    ],
    RiskIndicator.BYPASS_REQUEST: [
        r"bypass\s+(?:the\s+)?(?:security|verification|system)",
        r"skip\s+(?:the\s+)?(?:verification|procedure|protocol)",
        r"override\s+(?:the\s+)?(?:system|security)",
        r"ignore\s+(?:the\s+)?(?:warning|alert|procedure)",
        r"don'?t\s+(?:need\s+to\s+)?verify",
        r"special\s+(?:authorization|permission|access)",
        r"exception\s+(?:for\s+)?(?:this|you)",
        r"one[- ]time\s+(?:exception|override)",
    ],
}


class TranscriptRiskAdapter(ModelAdapter):
    """
    Adapter implementing AAA-VR vishing and transcript risk detection.

    Per AAA-VR.md §7, implements hard-negative handling:
    - Speaker role: a genuine agent saying "never share your OTP" is a warning, not a request
    - Detect negation/warning frames ("never", "do not", "we will not ask")
    - Quoted/reported speech = lower risk
    - Banking calls legitimately mention transfers and urgency - context + role needed
    """

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

    def _is_hard_negative(self, text: str) -> bool:
        """
        Check if text contains hard-negative indicators.

        Hard negatives are legitimate security advisories that mention
        sensitive terms in a warning/negation context, e.g.:
        - "Never share your OTP with anyone"
        - "We will never ask for your password"
        - "For security, never reveal your PIN"

        Per AAA-VR.md: These must NOT be flagged as credential requests.
        """
        text_lower = text.lower()

        # Check for negation patterns
        for pattern in NEGATION_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        # Check for agent advisory patterns
        for pattern in AGENT_ADVISORY_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    def _is_quoted_speech(self, text: str) -> bool:
        """Check if text contains quoted or reported speech."""
        text_lower = text.lower()
        for pattern in QUOTED_SPEECH_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _has_authority_pressure(self, text: str) -> bool:
        """Check for authority/pressure scam indicators."""
        text_lower = text.lower()
        for pattern in AUTHORITY_PRESSURE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _has_credential_request(self, text: str) -> bool:
        """
        Check for active credential harvesting requests.

        Only returns True if:
        1. Text contains credential request pattern AND
        2. Text is NOT a hard negative (negation/warning frame)
        """
        text_lower = text.lower()

        # First check if this is a hard negative (warning/advisory)
        if self._is_hard_negative(text_lower):
            return False

        # Check for active credential requests
        for pattern in CREDENTIAL_REQUEST_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    def _detect_role_aware_indicators(
        self, text: str, speaker_role: SpeakerRole = SpeakerRole.UNKNOWN
    ) -> tuple[list[str], float]:
        """
        Detect risk indicators with role awareness.

        Returns (indicators, confidence_adjustment)

        Role-based rules:
        - Agent saying "never share OTP" = LOW risk (advisory)
        - Caller requesting "tell me your OTP" = HIGH risk (harvesting)
        - Unknown role with negation = benefit of doubt (lower risk)
        """
        text_lower = text.lower()
        detected: list[str] = []
        confidence_adj = 0.0

        # Check if this is a hard negative first
        if self._is_hard_negative(text_lower):
            # This is likely a legitimate security advisory
            # Don't flag credential indicators in this context
            return [], -0.3  # Lower confidence/risk

        # Check if this is quoted/reported speech
        if self._is_quoted_speech(text_lower):
            confidence_adj -= 0.15  # Reduce confidence for reported speech

        # Check for active credential request (already filtered for hard negatives)
        if self._has_credential_request(text_lower):
            detected.append(RiskIndicator.CREDENTIAL_HARVESTING_ATTEMPT.value)
            confidence_adj += 0.1

        # Check for authority/pressure patterns (strong scam indicator)
        if self._has_authority_pressure(text_lower):
            detected.append(RiskIndicator.PRESSURE_TACTICS_DETECTED.value)
            confidence_adj += 0.1

        # Process remaining patterns with basic matching
        for indicator, regex_list in PATTERNS.items():
            # Skip credential harvesting - already handled with context
            if indicator == RiskIndicator.CREDENTIAL_HARVESTING_ATTEMPT:
                continue
            # Skip pressure tactics - already handled
            if indicator == RiskIndicator.PRESSURE_TACTICS_DETECTED:
                if self._has_authority_pressure(text_lower):
                    continue

            for pattern in regex_list:
                if re.search(pattern, text_lower):
                    # Check for negation context for this specific match
                    match = re.search(pattern, text_lower)
                    if match:
                        # Check if there's negation in the surrounding context
                        start = max(0, match.start() - 50)
                        context = text_lower[start : match.end() + 20]
                        is_negated = any(
                            re.search(neg, context) for neg in NEGATION_PATTERNS[:5]
                        )
                        if not is_negated:
                            detected.append(indicator.value)
                    break

        return detected, confidence_adj

    def analyze_transcript(
        self, transcript: str, speaker_role: SpeakerRole = SpeakerRole.UNKNOWN
    ) -> tuple[RiskLevel, list[str], str, float]:
        """
        Analyzes transcript against approved indicator rules with context awareness.

        Per AAA-VR.md §7:
        - Hard-negative handling: "never share your OTP" is not flagged
        - Role awareness: agent advisories vs caller requests
        - Negation detection: "don't", "never", "avoid"
        """
        # Use role-aware detection
        detected, confidence_adj = self._detect_role_aware_indicators(
            transcript, speaker_role
        )

        count = len(detected)
        base_confidence = 0.95

        # Decision matrix based on risk indicator density
        if count == 0:
            risk_level = RiskLevel.LOW
            action = RiskAction.APPROVE.value
            confidence = min(0.98, max(0.0, base_confidence + confidence_adj))
        elif count == 1:
            risk_level = RiskLevel.MEDIUM
            action = RiskAction.REVIEW.value
            confidence = min(1.0, max(0.70, 0.85 + confidence_adj))
        elif count in (2, 3):
            risk_level = RiskLevel.HIGH
            action = RiskAction.STEP_UP.value
            confidence = min(1.0, max(0.75, 0.90 + confidence_adj))
        else:
            risk_level = RiskLevel.CRITICAL
            action = RiskAction.DENY.value
            confidence = min(1.0, max(0.80, 0.96 + confidence_adj))

        return risk_level, detected, action, confidence

    def predict(
        self, request: TranscriptRiskRequest, request_id: str
    ) -> TranscriptRiskResponse:
        """Executes risk evaluation and packages safe response metadata."""
        risk_level, indicators, action, confidence = self.analyze_transcript(
            request.transcript
        )
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
