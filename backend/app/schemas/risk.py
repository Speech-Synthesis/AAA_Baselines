"""
AAA-VR Common Risk Schemas and Frozen Public Reason Codes
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Frozen risk severity tiers for CallGuard panel."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAction(str, Enum):
    """Approved operational decisions for downstream callers."""

    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    STEP_UP = "STEP_UP"
    DENY = "DENY"


class RiskIndicator(str, Enum):
    """Frozen public risk categories safe for UI display."""

    URGENT_TRANSFER_REQUEST = "URGENT_TRANSFER_REQUEST"
    PRESSURE_TACTICS_DETECTED = "PRESSURE_TACTICS_DETECTED"
    ACCOUNT_NUMBER_MENTIONED = "ACCOUNT_NUMBER_MENTIONED"
    CREDENTIAL_HARVESTING_ATTEMPT = "CREDENTIAL_HARVESTING_ATTEMPT"
    UNVERIFIED_BENEFICIARY = "UNVERIFIED_BENEFICIARY"
    IMPERSONATION_ATTEMPT = "IMPERSONATION_ATTEMPT"
    VOICE_STRESS_ANOMALY = "VOICE_STRESS_ANOMALY"


class TranscriptRiskRequest(BaseModel):
    """Request payload for /v1/risk/transcript."""

    session_id: str = Field(..., description="Unique call session reference")
    transcript: str = Field(
        ..., min_length=1, description="Spoken transcript string for acoustic/vishing analysis"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Optional call metadata like call_type or claimed_identity"
    )


class TranscriptRiskResponse(BaseModel):
    """Safe metadata response returned to host applications (CallGuard/Banking Shield)."""

    request_id: str = Field(..., description="Unique request tracing UUID")
    session_id: str = Field(..., description="Correlated call session reference")
    risk_level: RiskLevel = Field(..., description="Assessed risk classification")
    risk_indicators: list[str] = Field(
        ..., description="Safe, public reason codes without threshold leakage"
    )
    recommended_action: str = Field(
        ..., description="Recommended mitigation action (APPROVE/REVIEW/STEP_UP/DENY)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Risk assessment confidence score")
    model_version: str = Field(
        default="aaa-vr-transcript-risk-v1", description="Model engine version identifier"
    )
    analyzed_at: str = Field(..., description="ISO 8601 analysis timestamp")
