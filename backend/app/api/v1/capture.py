"""
AAA Engine - Capture Grant API v1
Endpoint for issuing short-lived capture authorizations.

The AAA-controlled capture component uses these grants to:
1. Validate it's authorized to record
2. Display the challenge phrase
3. Upload audio directly to AAA (not through host app)
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...db import get_db
from ...models import Challenge, User
from ...security.jwt_auth import get_current_tenant

router = APIRouter(prefix="/capture", tags=["capture"])
settings = get_settings()

# In-memory grant store (production would use Redis/DB)
# Format: {grant_id: {tenant_id, user_id, challenge_id, phrase, expires_at, consumed}}
_capture_grants: dict[str, dict] = {}


class CaptureGrantRequest(BaseModel):
    """Request to create a capture authorization."""

    user_id: str = Field(..., description="User UUID")
    challenge_id: str = Field(..., description="Challenge ID from /v1/challenges")


class CaptureGrantResponse(BaseModel):
    """Capture grant issued to host app for embedding AAA capture component."""

    grant_id: str = Field(..., description="Single-use capture grant ID")
    capture_url: str = Field(..., description="URL to embed AAA capture component")
    expires_at: str = Field(..., description="ISO timestamp when grant expires")
    ttl_seconds: int = Field(..., description="Time-to-live in seconds")


class CaptureStatus(BaseModel):
    """Status information returned to capture component."""

    valid: bool
    phrase: str | None = None
    user_id: str | None = None
    challenge_id: str | None = None
    expires_in_seconds: int | None = None
    error: str | None = None


def _generate_grant_signature(grant_id: str, tenant_id: str, challenge_id: str) -> str:
    """Generate HMAC signature for grant verification."""
    message = f"{grant_id}:{tenant_id}:{challenge_id}"
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:32]


@router.post(
    "/grants",
    response_model=CaptureGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Capture Grant",
    description="Issues a short-lived, single-use capture authorization for the AAA capture component.",
)
async def create_capture_grant(
    request: CaptureGrantRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> CaptureGrantResponse:
    """
    Create a capture authorization grant.

    The host backend calls this after creating a challenge.
    The grant is passed to the AAA capture component (iframe/widget).
    The capture component validates the grant and records/uploads audio directly.
    """
    # Validate user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    # Validate challenge exists and is valid
    challenge = db.query(Challenge).filter(
        Challenge.id == request.challenge_id,
        Challenge.user_id == request.user_id,
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CHALLENGE_NOT_FOUND", "message": "Challenge not found"},
        )

    if challenge.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHALLENGE_CONSUMED", "message": "Challenge already used"},
        )

    if challenge.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHALLENGE_EXPIRED", "message": "Challenge has expired"},
        )

    # Generate grant
    grant_id = secrets.token_urlsafe(32)
    signature = _generate_grant_signature(grant_id, tenant_id, request.challenge_id)

    # Grant TTL matches remaining challenge time, max 90s
    remaining_seconds = int((challenge.expires_at - datetime.utcnow()).total_seconds())
    ttl_seconds = min(remaining_seconds, 90)
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    # Store grant
    _capture_grants[grant_id] = {
        "tenant_id": tenant_id,
        "user_id": request.user_id,
        "challenge_id": request.challenge_id,
        "phrase": challenge.phrase,
        "expires_at": expires_at,
        "consumed": False,
        "signature": signature,
    }

    # Build capture URL
    capture_url = f"/static/capture/index.html?grant={grant_id}&sig={signature}"

    return CaptureGrantResponse(
        grant_id=grant_id,
        capture_url=capture_url,
        expires_at=expires_at.isoformat() + "Z",
        ttl_seconds=ttl_seconds,
    )


@router.get(
    "/grants/{grant_id}/status",
    response_model=CaptureStatus,
    summary="Validate Capture Grant",
    description="Called by the capture component to validate a grant and get challenge info.",
)
async def get_capture_status(
    grant_id: str,
    sig: str | None = None,
) -> CaptureStatus:
    """
    Validate a capture grant and return challenge info.

    Called by the AAA capture component (not by host app).
    Returns the phrase to display and remaining time.
    """
    grant = _capture_grants.get(grant_id)

    if not grant:
        return CaptureStatus(valid=False, error="GRANT_NOT_FOUND")

    # Verify signature
    expected_sig = grant.get("signature")
    if sig != expected_sig:
        return CaptureStatus(valid=False, error="INVALID_SIGNATURE")

    # Check expiry
    if grant["expires_at"] < datetime.utcnow():
        return CaptureStatus(valid=False, error="GRANT_EXPIRED")

    # Check if already consumed
    if grant["consumed"]:
        return CaptureStatus(valid=False, error="GRANT_CONSUMED")

    # Calculate remaining time
    remaining = int((grant["expires_at"] - datetime.utcnow()).total_seconds())

    return CaptureStatus(
        valid=True,
        phrase=grant["phrase"],
        user_id=grant["user_id"],
        challenge_id=grant["challenge_id"],
        expires_in_seconds=remaining,
    )


@router.post(
    "/grants/{grant_id}/consume",
    summary="Mark Capture Grant Consumed",
    description="Called internally after successful audio upload to prevent grant reuse.",
)
async def consume_capture_grant(grant_id: str) -> dict:
    """Mark a capture grant as consumed (single-use enforcement)."""
    grant = _capture_grants.get(grant_id)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "GRANT_NOT_FOUND"},
        )

    if grant["consumed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_CONSUMED"},
        )

    grant["consumed"] = True
    return {"status": "consumed"}


def get_grant_info(grant_id: str) -> dict | None:
    """Get grant info for internal use (e.g., verify endpoint)."""
    grant = _capture_grants.get(grant_id)
    if not grant:
        return None
    if grant["consumed"]:
        return None
    if grant["expires_at"] < datetime.utcnow():
        return None
    return grant


def cleanup_expired_grants():
    """Remove expired grants (call periodically)."""
    now = datetime.utcnow()
    expired = [gid for gid, g in _capture_grants.items() if g["expires_at"] < now]
    for gid in expired:
        del _capture_grants[gid]
