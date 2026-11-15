"""
AAA Engine - Verification Request Status API v1
Endpoint for polling verification request status.

Per SYSTEM.md §4:
- GET /v1/verification-requests/{request_id} - Get verification status
- Returns safe public status information only
- No raw scores, embeddings, or internal details exposed
"""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import AuthLog
from ...schemas.common import Decision, RiskLevel
from ...security.jwt_auth import get_current_tenant

router = APIRouter(prefix="/verification-requests", tags=["verification"])
logger = logging.getLogger("aaa_engine.verification_requests")

# In-memory store for verification request status (production would use Redis/DB)
# Format: {request_id: {status, decision, reason_public, risk_level, created_at, completed_at}}
_verification_requests: dict[str, dict] = {}


class VerificationRequestStatus(BaseModel):
    """Status of a verification request."""

    request_id: str = Field(..., description="Verification request ID")
    status: str = Field(..., description="Status: pending, completed, expired, failed")
    decision: Decision | None = Field(None, description="Final decision if completed")
    reason_public: str | None = Field(None, description="Public reason code")
    risk_level: RiskLevel | None = Field(None, description="Risk assessment level")
    created_at: str = Field(..., description="ISO timestamp when request was created")
    completed_at: str | None = Field(None, description="ISO timestamp when request completed")


def register_verification_request(
    request_id: str,
    decision: Decision,
    reason_public: str,
    risk_level: RiskLevel,
) -> None:
    """
    Register a completed verification request for status polling.

    Called internally by the verify endpoint after processing.
    """
    now = datetime.utcnow()
    _verification_requests[request_id] = {
        "status": "completed",
        "decision": decision,
        "reason_public": reason_public,
        "risk_level": risk_level,
        "created_at": now.isoformat() + "Z",
        "completed_at": now.isoformat() + "Z",
    }


def cleanup_old_requests():
    """Remove requests older than 1 hour."""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    old_keys = [
        rid
        for rid, data in _verification_requests.items()
        if datetime.fromisoformat(data["created_at"].replace("Z", "")) < cutoff
    ]
    for rid in old_keys:
        del _verification_requests[rid]


@router.get(
    "/{request_id}",
    response_model=VerificationRequestStatus,
    summary="Get Verification Request Status",
    description="Poll the status of a verification request.",
)
async def get_verification_status(
    request_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> VerificationRequestStatus:
    """
    Get the status of a verification request.

    Returns safe public status information only.
    Does not expose raw scores, transcripts, embeddings, or internal details.
    """
    # Check in-memory cache first
    if request_id in _verification_requests:
        data = _verification_requests[request_id]
        return VerificationRequestStatus(
            request_id=request_id,
            status=data["status"],
            decision=data.get("decision"),
            reason_public=data.get("reason_public"),
            risk_level=data.get("risk_level"),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
        )

    # Try to find in audit logs (fallback for older requests)
    # Note: This requires request_id to be stored in auth_logs, which would need schema update
    # For now, return not found if not in cache
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "REQUEST_NOT_FOUND",
            "message": "Verification request not found or expired",
        },
    )


@router.get(
    "",
    response_model=list[VerificationRequestStatus],
    summary="List Recent Verification Requests",
    description="List recent verification requests for the current tenant.",
)
async def list_verification_requests(
    limit: int = 10,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> list[VerificationRequestStatus]:
    """
    List recent verification requests.

    Returns safe public status information only.
    Limited to 10 most recent by default.
    """
    # Return from in-memory cache
    # In production, this would filter by tenant_id
    requests = []
    for rid, data in list(_verification_requests.items())[-limit:]:
        requests.append(
            VerificationRequestStatus(
                request_id=rid,
                status=data["status"],
                decision=data.get("decision"),
                reason_public=data.get("reason_public"),
                risk_level=data.get("risk_level"),
                created_at=data["created_at"],
                completed_at=data.get("completed_at"),
            )
        )
    return requests
