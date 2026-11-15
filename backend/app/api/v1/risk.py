"""
AAA Engine - Transcript Risk API (AAA-VR)
Endpoint for CallGuard and host application fraud analysis.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Header, status

from ...adapters.vr import TranscriptRiskAdapter
from ...schemas.risk import TranscriptRiskRequest, TranscriptRiskResponse

router = APIRouter(prefix="/risk", tags=["risk"])

# Singleton adapter instance
_risk_adapter = TranscriptRiskAdapter()


@router.post(
    "/transcript",
    response_model=TranscriptRiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Transcript for Risk Analysis (AAA-VR)",
    description="Analyzes conversational transcript for vishing, coercion, and fraud indicators.",
)
def evaluate_transcript_risk(
    request: TranscriptRiskRequest,
    tenant_id: str | None = None,
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    _: None = None,
) -> TranscriptRiskResponse:
    """
    Risk endpoint supporting both direct string payload and CallGuard segments payload.
    Returns only approved public reason codes and safe metadata for RiskPanel.
    """
    req_id = x_request_id if (isinstance(x_request_id, str) and x_request_id) else str(uuid.uuid4())
    sess_id = request.session_id or f"cg-sess-{uuid.uuid4().hex[:8]}"

    # Extract text from transcript string or CallGuard segments
    if request.transcript:
        text = request.transcript
    elif request.segments:
        text = " ".join(s.get("text", "") for s in request.segments if isinstance(s, dict))
    else:
        text = ""

    risk_level, indicators, action, confidence = _risk_adapter.analyze_transcript(text)
    now_iso = datetime.now(UTC).isoformat()
    primary_reason = indicators[0] if indicators else "ROUTINE_INQUIRY"

    return TranscriptRiskResponse(
        request_id=req_id,
        session_id=sess_id,
        risk_level=risk_level,
        risk_indicators=indicators,
        recommended_action=action,
        confidence=confidence,
        model_version=_risk_adapter.get_info().model_id,
        analyzed_at=now_iso,
        reason_public=primary_reason,
        detected_triggers=indicators,
        timestamp=now_iso,
    )
