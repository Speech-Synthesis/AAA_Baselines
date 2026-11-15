"""
AAA Engine - Consent Management API v1

Per DATA_SECURITY.md §5:
- Track user consent for biometric data collection
- Support consent withdrawal (GDPR Article 7)
- Maintain audit trail of consent changes
"""

import hashlib
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import ConsentRecord, User, Voiceprint, VoiceprintHistory
from ...security.jwt_auth import get_current_tenant

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentGrantRequest(BaseModel):
    """Request to grant consent for biometric processing."""

    user_id: str = Field(..., description="User UUID")
    consent_type: str = Field(
        "biometric_enrollment",
        description="Type: biometric_enrollment, data_processing",
    )
    consent_version: str = Field("1.0", description="Policy version being consented to")


class ConsentGrantResponse(BaseModel):
    """Response after consent is granted."""

    consent_id: str
    user_id: str
    consent_type: str
    consent_version: str
    granted_at: str
    status: str = "active"


class ConsentWithdrawRequest(BaseModel):
    """Request to withdraw consent."""

    user_id: str = Field(..., description="User UUID")
    consent_type: str = Field(
        "biometric_enrollment",
        description="Type of consent to withdraw",
    )
    reason: str | None = Field(None, description="Optional reason for withdrawal")
    delete_biometrics: bool = Field(
        True, description="Also delete associated biometric data"
    )


class ConsentWithdrawResponse(BaseModel):
    """Response after consent withdrawal."""

    consent_id: str
    user_id: str
    withdrawn_at: str
    biometrics_deleted: bool
    status: str = "withdrawn"


class ConsentStatusResponse(BaseModel):
    """Current consent status for a user."""

    user_id: str
    consents: list[dict]
    has_active_biometric_consent: bool


def _hash_ip(ip: str | None) -> str | None:
    """Hash IP address for privacy-preserving audit."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _hash_ua(ua: str | None) -> str | None:
    """Hash user agent for privacy-preserving audit."""
    if not ua:
        return None
    return hashlib.sha256(ua.encode()).hexdigest()[:16]


@router.post(
    "/grant",
    response_model=ConsentGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant Consent",
    description="Record user consent for biometric data processing.",
)
async def grant_consent(
    request: Request,
    body: ConsentGrantRequest,
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> ConsentGrantResponse:
    """Grant consent for biometric processing."""
    # Validate user exists
    try:
        user_uuid = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_USER_ID", "message": "Invalid user ID format"},
        ) from None

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    # Check for existing active consent of same type
    existing = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user_uuid,
            ConsentRecord.consent_type == body.consent_type,
            ConsentRecord.withdrawn_at.is_(None),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONSENT_EXISTS",
                "message": "Active consent already exists for this type",
            },
        )

    # Create consent record
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    consent = ConsentRecord(
        id=uuid.uuid4(),
        user_id=user_uuid,
        tenant_id=tenant_id,
        consent_type=body.consent_type,
        consent_version=body.consent_version,
        granted_at=datetime.utcnow(),
        ip_address_hash=_hash_ip(client_ip),
        user_agent_hash=_hash_ua(user_agent),
    )
    db.add(consent)
    db.commit()

    return ConsentGrantResponse(
        consent_id=str(consent.id),
        user_id=str(consent.user_id),
        consent_type=consent.consent_type,
        consent_version=consent.consent_version,
        granted_at=consent.granted_at.isoformat() + "Z",
        status="active",
    )


@router.post(
    "/withdraw",
    response_model=ConsentWithdrawResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw Consent",
    description="Withdraw consent and optionally delete associated biometric data.",
)
async def withdraw_consent(
    body: ConsentWithdrawRequest,
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> ConsentWithdrawResponse:
    """
    Withdraw consent per GDPR Article 7.

    If delete_biometrics is True, also:
    - Delete voiceprint data
    - Record deletion in voiceprint history
    """
    try:
        user_uuid = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_USER_ID", "message": "Invalid user ID format"},
        ) from None

    # Find active consent
    consent = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user_uuid,
            ConsentRecord.consent_type == body.consent_type,
            ConsentRecord.withdrawn_at.is_(None),
        )
        .first()
    )

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CONSENT_NOT_FOUND",
                "message": "No active consent found for this type",
            },
        )

    # Mark consent as withdrawn
    withdrawn_at = datetime.utcnow()
    consent.withdrawn_at = withdrawn_at

    biometrics_deleted = False

    # Delete biometrics if requested
    if body.delete_biometrics and body.consent_type == "biometric_enrollment":
        voiceprints = db.query(Voiceprint).filter(Voiceprint.user_id == user_uuid).all()

        for vp in voiceprints:
            # Record in history before deletion
            history = VoiceprintHistory(
                id=uuid.uuid4(),
                voiceprint_id=vp.id,
                user_id=user_uuid,
                tenant_id=tenant_id,
                action="revoked",
                sample_count_before=vp.sample_count,
                sample_count_after=0,
                reason=body.reason or "Consent withdrawn",
                actor_id="consent_withdrawal",
            )
            db.add(history)
            db.delete(vp)

        biometrics_deleted = len(voiceprints) > 0

    db.commit()

    return ConsentWithdrawResponse(
        consent_id=str(consent.id),
        user_id=str(consent.user_id),
        withdrawn_at=withdrawn_at.isoformat() + "Z",
        biometrics_deleted=biometrics_deleted,
        status="withdrawn",
    )


@router.get(
    "/{user_id}",
    response_model=ConsentStatusResponse,
    summary="Get Consent Status",
    description="Get current consent status for a user.",
)
async def get_consent_status(
    user_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
) -> ConsentStatusResponse:
    """Get all consent records for a user."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_USER_ID", "message": "Invalid user ID format"},
        ) from None

    consents = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user_uuid)
        .order_by(ConsentRecord.granted_at.desc())
        .all()
    )

    consent_list = []
    has_active_biometric = False

    for c in consents:
        is_active = c.withdrawn_at is None
        consent_list.append(
            {
                "consent_id": str(c.id),
                "consent_type": c.consent_type,
                "consent_version": c.consent_version,
                "granted_at": c.granted_at.isoformat() + "Z",
                "withdrawn_at": c.withdrawn_at.isoformat() + "Z" if c.withdrawn_at else None,
                "status": "active" if is_active else "withdrawn",
            }
        )
        if c.consent_type == "biometric_enrollment" and is_active:
            has_active_biometric = True

    return ConsentStatusResponse(
        user_id=user_id,
        consents=consent_list,
        has_active_biometric_consent=has_active_biometric,
    )
