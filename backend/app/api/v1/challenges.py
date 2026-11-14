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

    user_id: str = Field(..., description="User UUID for challenge generation")


class ChallengeResponse(BaseModel):
    """Response containing challenge phrase and token."""

    request_id: str = Field(..., description="Unique request tracking ID")
    phrase: str = Field(..., description="Challenge phrase to speak")
    token: str = Field(..., description="Challenge token for verification")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    ttl_seconds: int = Field(..., description="Time to live in seconds")


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

    # Validate user exists
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    # Validate user has voiceprint
    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == body.user_id).first()
    if not voiceprint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_VOICEPRINT",
                "message": "User has no enrolled voiceprint",
            },
        )

    # Generate challenge and persist to database
    challenge_data = generate_challenge(body.user_id, db=db)

    return ChallengeResponse(
        request_id=req_id,
        phrase=challenge_data["phrase"],
        token=challenge_data["token"],
        expires_at=challenge_data["expires_at"],
        ttl_seconds=settings.CHALLENGE_TTL_SECONDS,
    )
