"""
AAA Engine - Verification API v1
Endpoint for voice authentication verification.
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
from ...layer1_speaker import verify_speaker
from ...layer2_deepfake import detect_spoof
from ...layer3_adaptive import (
    get_token_phrase,
    update_voiceprint,
    validate_and_consume_token,
)
from ...layer3_asr import verify_phrase
from ...models import AuthLog, User, Voiceprint
from ...schemas.common import Decision

router = APIRouter(prefix="/verify", tags=["authentication"])

settings = get_settings()


class VerificationResult(BaseModel):
    """Verification result returned to the caller."""

    request_id: str = Field(..., description="Request tracking ID")
    decision: Decision = Field(..., description="Authentication decision")
    session_id: str = Field(..., description="Unique session ID for this attempt")
    reason: str = Field(..., description="Human-readable reason for decision")
    # Note: No raw scores exposed to prevent information leakage


class VerificationResultInternal(BaseModel):
    """Internal verification result with full details for logging."""

    request_id: str
    decision: Decision
    session_id: str
    reason: str
    l2_label: str
    l2_confidence: float
    l1_score: float
    layer_blocked: int | None
    asr_transcript: str | None
    asr_similarity: float | None


@router.post(
    "",
    response_model=VerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Verify Voice Authentication",
    description="Verifies user's voice against enrolled voiceprint and challenge phrase.",
)
@limiter.limit(settings.RATE_LIMIT_VERIFY)
async def verify_authentication(
    request: Request,
    user_id: str = Form(..., description="User UUID"),
    token: str = Form(..., description="Challenge token from /v1/challenges"),
    audio: UploadFile = File(..., description="Audio file (WAV format preferred)"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
) -> VerificationResult:
    """
    Verify user's voice authentication.

    Pipeline: L2 (deepfake) → L3A (ASR phrase) → L1 (speaker) → L3B (token)

    Returns only safe decision information - no raw scores or embeddings.
    """
    req_id = x_request_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    # Get voiceprint
    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user_id).first()
    if not voiceprint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_VOICEPRINT", "message": "User has no enrolled voiceprint"},
        )

    # Read audio
    audio_bytes = await audio.read()

    # Validate audio size (prevent resource exhaustion)
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

    # === LAYER 2: Deepfake Detection ===
    l2_result = detect_spoof(audio_bytes)
    l2_label = l2_result["label"]
    l2_confidence = l2_result["confidence"]

    if l2_label == "spoof" and l2_confidence > settings.L2_SPOOF_THRESHOLD:
        _log_attempt(
            db,
            user_id=user_id,
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            result="REJECT",
            layer_blocked=2,
        )
        return VerificationResult(
            request_id=req_id,
            decision=Decision.DENY,
            session_id=session_id,
            reason="Authentication failed",  # Generic message for security
        )

    # === LAYER 3A: ASR Phrase Verification ===
    expected_phrase = get_token_phrase(token, db)
    if not expected_phrase:
        _log_attempt(
            db,
            user_id=user_id,
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            result="REJECT",
            layer_blocked=3,
        )
        return VerificationResult(
            request_id=req_id,
            decision=Decision.DENY,
            session_id=session_id,
            reason="Invalid or expired challenge",
        )

    asr_match, asr_similarity, asr_transcript = verify_phrase(
        audio_bytes, expected_phrase, settings.ASR_PHRASE_THRESHOLD
    )

    if not asr_match:
        _log_attempt(
            db,
            user_id=user_id,
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            result="REJECT",
            layer_blocked=4,
        )
        return VerificationResult(
            request_id=req_id,
            decision=Decision.DENY,
            session_id=session_id,
            reason="Challenge phrase mismatch",
        )

    # === LAYER 1: Speaker Verification ===
    l1_result = verify_speaker(audio_bytes, voiceprint.embedding)
    l1_score = l1_result["score"]
    new_embedding = l1_result["embedding"]

    if l1_score < settings.L1_SIMILARITY_THRESHOLD:
        _log_attempt(
            db,
            user_id=user_id,
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
            result="REJECT",
            layer_blocked=1,
        )
        return VerificationResult(
            request_id=req_id,
            decision=Decision.DENY,
            session_id=session_id,
            reason="Speaker verification failed",
        )

    # === LAYER 3B: Token Verification and Consumption ===
    challenge_data = validate_and_consume_token(token, db)
    if not challenge_data:
        _log_attempt(
            db,
            user_id=user_id,
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
            result="REJECT",
            layer_blocked=3,
        )
        return VerificationResult(
            request_id=req_id,
            decision=Decision.DENY,
            session_id=session_id,
            reason="Token already used or expired",
        )

    # === SUCCESS: Update voiceprint with EMA ===
    updated_embedding = update_voiceprint(voiceprint.embedding, new_embedding)
    voiceprint.embedding = updated_embedding
    voiceprint.sample_count += 1
    voiceprint.updated_at = datetime.utcnow()

    # Log success
    _log_attempt(
        db,
        user_id=user_id,
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        result="ACCEPT",
        layer_blocked=None,
        challenge_id=challenge_data.get("id") if isinstance(challenge_data, dict) else None,
    )

    db.commit()

    return VerificationResult(
        request_id=req_id,
        decision=Decision.APPROVE,
        session_id=session_id,
        reason="Authentication successful",
    )


def _log_attempt(
    db: Session,
    user_id: str,
    l2_label: str,
    l2_confidence: float,
    l1_score: float,
    result: str,
    layer_blocked: int | None,
    challenge_id: str | None = None,
) -> None:
    """Log authentication attempt to database."""
    log = AuthLog(
        user_id=uuid.UUID(user_id),
        challenge_id=uuid.UUID(challenge_id) if challenge_id else None,
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        result=result,
        layer_blocked=layer_blocked,
    )
    db.add(log)
    db.commit()
