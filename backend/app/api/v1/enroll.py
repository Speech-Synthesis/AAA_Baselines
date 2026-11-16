"""
AAA Engine - Enrollment API v1
Endpoint for voice enrollment (voiceprint creation/update).
"""

import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.ratelimit import limiter
from ...db import get_db
from ...layer1_speaker import enroll_speaker
from ...layer3_adaptive import update_voiceprint
from ...models import User, Voiceprint
from ...security.jwt_auth import oauth2_scheme
from ...services.voiceprint_service import decrypt_embedding, encrypt_embedding

router = APIRouter(prefix="/enroll", tags=["enrollment"])

settings = get_settings()


def get_optional_tenant(token: str | None = Depends(oauth2_scheme)) -> str | None:
    """Optional JWT authentication - returns tenant_id if token provided, None otherwise."""
    if not token:
        return None
    try:
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


class EnrollmentResponse(BaseModel):
    """Response from enrollment endpoint."""

    request_id: str = Field(..., description="Request tracking ID")
    status: str = Field(..., description="Enrollment status")
    sample_count: int = Field(..., description="Total samples enrolled")
    is_new: bool = Field(..., description="True if this is a new enrollment")


@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll Voice Sample",
    description="Enrolls a voice sample to create or update user's voiceprint.",
)
@limiter.limit(settings.RATE_LIMIT_ENROLL)
async def enroll_voice(
    request: Request,
    user_id: str = Form(..., description="User UUID"),
    audio: UploadFile = File(..., description="Audio file (WAV format preferred)"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_optional_tenant),
) -> EnrollmentResponse:
    """
    Enroll a voice sample for a user.

    If the user already has a voiceprint, updates it using EMA.
    Otherwise, creates a new voiceprint.
    """
    req_id = x_request_id or str(uuid.uuid4())

    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Enroll request: user_id={user_id}, req_id={req_id}")

        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "USER_NOT_FOUND", "message": "User not found"},
            )

        # Read audio
        audio_bytes = await audio.read()
        logger.info(f"Audio size: {len(audio_bytes)} bytes")

        # Validate audio size
        max_audio_size = 10 * 1024 * 1024  # 10MB limit
        if len(audio_bytes) > max_audio_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "AUDIO_TOO_LARGE", "message": "Audio file exceeds 10MB limit"},
            )

        if len(audio_bytes) < 1000:  # Minimum ~50ms at 16kHz
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "AUDIO_TOO_SHORT", "message": "Audio file is too short"},
            )

        # Extract embedding using speaker verification model
        logger.info("Extracting embedding...")
        result = enroll_speaker(audio_bytes)
        embedding = result["embedding"]
        logger.info(f"Embedding extracted, type: {type(embedding)}")

        # Check for existing voiceprint
        voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user_id).first()
        is_new = voiceprint is None
        logger.info(f"Existing voiceprint: {not is_new}")

        if voiceprint:
            # Get existing embedding (may be list or encrypted string)
            logger.info("Getting existing embedding...")
            existing_embedding = voiceprint.embedding
            if isinstance(existing_embedding, str):
                # Handle encrypted format from legacy
                existing_embedding = decrypt_embedding(
                    existing_embedding, tenant_id=tenant_id, user_id=user_id
                )
            # Update existing voiceprint with EMA
            logger.info("Updating with EMA...")
            updated_embedding = update_voiceprint(existing_embedding, embedding)
            # Store as list (JSONEncodedList handles serialization)
            voiceprint.embedding = updated_embedding if isinstance(updated_embedding, list) else updated_embedding.tolist()
            voiceprint.sample_count += 1
            voiceprint.updated_at = datetime.utcnow()
        else:
            # Store embedding as list (JSONEncodedList handles serialization)
            logger.info("Storing new embedding...")
            embedding_list = embedding if isinstance(embedding, list) else embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            # Create new voiceprint
            voiceprint = Voiceprint(
                user_id=uuid.UUID(user_id),
                embedding=embedding_list,
                sample_count=1,
            )
            db.add(voiceprint)

        logger.info("Committing to database...")
        db.commit()
        db.refresh(voiceprint)
        logger.info("Enrollment complete!")

        return EnrollmentResponse(
            request_id=req_id,
            status="enrolled",
            sample_count=voiceprint.sample_count,
            is_new=is_new,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrollment failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ENROLLMENT_FAILED", "message": str(e)},
        )
