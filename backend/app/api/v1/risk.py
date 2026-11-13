"""
AAA Engine - Transcript Risk API (AAA-VR)
Endpoint for CallGuard and host application fraud analysis.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, status

from ...security.jwt_auth import get_current_tenant, enforce_rate_limit
from ...schemas.risk import TranscriptRiskRequest, TranscriptRiskResponse
from ...adapters.vr import TranscriptRiskAdapter

router = APIRouter(prefix="/risk", tags=["risk"])

# Singleton adapter instance
_risk_adapter = TranscriptRiskAdapter()


@router.post(
    "/transcript",
    response_model=TranscriptRiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Transcript for Risk Analysis (AAA-VR)",
    description="Analyzes conversational transcript for vishing, coercion, and fraud indicators."
)
def evaluate_transcript_risk(
    request: TranscriptRiskRequest,
    tenant_id: str = Depends(get_current_tenant),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    _: None = Depends(enforce_rate_limit),
) -> TranscriptRiskResponse:
    """
    Zero-trust risk endpoint:
    - Verifies Bearer JWT for tenant scoping
    - Enforces rate limiting
    - Returns only approved public reason codes and safe metadata
    """
    req_id = x_request_id or str(uuid.uuid4())
    return _risk_adapter.predict(request=request, request_id=req_id)
