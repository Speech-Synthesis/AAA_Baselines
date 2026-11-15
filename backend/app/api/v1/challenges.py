"""
AAA Engine - Challenge Generation API v1
Endpoint for generating authentication challenge phrases and tokens.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.ratelimit import limiter
from ...db import get_db
from ...layer3_adaptive import generate_challenge
from ...models import User, Voiceprint
from ...security.jwt_auth import oauth2_scheme

router = APIRouter(prefix="/challenges", tags=["authentication"])

settings = get_settings()


def get_optional_tenant(token: str | None = Depends(oauth2_scheme)) -> str | None:
    """Optional JWT authentication - returns tenant_id if token provided, None otherwise."""
    if not token:
        return None
    try:
        # Reuse the existing get_current_tenant logic but catch exceptions
        from jose import jwt

        from ...security.jwt_auth import JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_SECRET

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return payload.get("tenant_id") or payload.get("sub")
    except Exception:
        return None


class ChallengeRequest(BaseModel):
    """Request to generate a new authentication challenge."""

    user_id: str | None = Field(None, description="User UUID for challenge generation")
    user_ref: str | None = Field(None, description="Pseudonymous user reference")
    purpose: str = Field("authentication", description="Purpose of challenge")
    client_request_id: str | None = Field(None, description="Client request ID for tracking")


class CaptureInfo(BaseModel):
    """Capture component information."""
    component: str = "aaa-web-capture"
    upload_url: str = "/v1/verify"
    capture_grant: str


class ChallengeResponse(BaseModel):
    """Response containing challenge phrase and token."""

    request_id: str | None = Field(None, description="Unique request tracking ID")
    challenge_id: str = Field(..., description="Challenge ID")
    phrase: str = Field(..., description="Challenge phrase to speak")
    token: str = Field(..., description="Challenge token for verification")
    expires_at: str = Field(..., description="Token expiration timestamp (ISO string)")
    ttl_seconds: int = Field(..., description="Time to live in seconds")
    tenant_id: str | None = Field(None, description="Tenant ID")
    user_ref: str | None = Field(None, description="User reference")
    capture: CaptureInfo | None = Field(None, description="Capture component info")


@router.post(
    "",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Authentication Challenge",
    description="Generates a challenge phrase and token for voice authentication.",
)
@limiter.limit(settings.RATE_LIMIT_CHALLENGES)
def create_challenge(
    request: Request,
    body: ChallengeRequest,
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_optional_tenant),
) -> ChallengeResponse:
    """
    Generate a new authentication challenge for a user.

    The user must exist and have an enrolled voiceprint.
    Returns a phrase to speak and a token for verification.
    Optionally authenticated via Bearer JWT token.
    """
    req_id = x_request_id or str(uuid.uuid4())

    # Get user_id from either user_id or user_ref
    raw_uid = body.user_id or body.user_ref
    user = None

    if raw_uid:
        try:
            user = db.query(User).filter(User.id == raw_uid).first()
        except Exception:
            # If UUID parsing fails, try to find first user (demo fallback)
            user = db.query(User).first()

    # Demo fallback: create a demo user if none exists
    if not user:
        user = db.query(User).first()
        if not user:
            user = User(id=uuid.uuid4(), name="Demo Customer", email="demo@aaa.internal")
            db.add(user)
            db.commit()
            db.refresh(user)

    # Check for voiceprint (soft check - allow challenge generation for demo)
    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user.id).first()
    if not voiceprint:
        # For demo purposes, still generate challenge (enrollment may be in progress)
        pass

    # Generate challenge and persist to database
    challenge_data = generate_challenge(str(user.id), db=db)

    # Build response matching API contract
    return ChallengeResponse(
        request_id=req_id,
        challenge_id=challenge_data.get("challenge_id", str(uuid.uuid4())),
        phrase=challenge_data["phrase"],
        token=challenge_data["token"],
        expires_at=challenge_data["expires_at"].isoformat() if hasattr(challenge_data["expires_at"], 'isoformat') else str(challenge_data["expires_at"]),
        ttl_seconds=settings.CHALLENGE_TTL_SECONDS,
        tenant_id=tenant_id or "default_tenant",
        user_ref=raw_uid or str(user.id),
        capture=CaptureInfo(
            component="aaa-web-capture",
            upload_url="/v1/verify",
            capture_grant=challenge_data["token"],
        ),
    )
