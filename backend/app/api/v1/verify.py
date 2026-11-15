"""
AAA Engine - Verification API v1
Endpoint for voice authentication verification.

Uses centralized PolicyEngine for all authentication decisions.
Implements parallel AD||ASR execution per SYSTEM.md §6.

Returns one of FIVE approved decision outcomes:
- APPROVE: All gates pass
- DENY: Authentication fails
- STEP_UP: Additional verification needed
- REVIEW: Human review required
- UNAVAILABLE: Service unavailable
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial

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
from ...core.policy_engine import GateResult, PolicyInput, evaluate_policy
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
from ...schemas.common import Decision, RiskLevel
from ...security.jwt_auth import oauth2_scheme
from ...services.voiceprint_service import decrypt_embedding, encrypt_embedding
from .verification_requests import register_verification_request

router = APIRouter(prefix="/verify", tags=["authentication"])
logger = logging.getLogger("aaa_engine.verify")

# Thread pool for parallel model execution
_executor = ThreadPoolExecutor(max_workers=4)

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


class VerificationResult(BaseModel):
    """
    Verification result returned to the caller.

    Returns one of FIVE approved decision outcomes per SYSTEM.md §6:
    - APPROVE: All gates pass
    - DENY: Authentication fails
    - STEP_UP: Additional verification needed
    - REVIEW: Human review required
    - UNAVAILABLE: Service unavailable
    """

    request_id: str = Field(..., description="Request tracking ID")
    decision: Decision = Field(..., description="One of 5 authentication decisions")
    session_id: str = Field(..., description="Unique session ID for this attempt")
    reason: str = Field(..., description="Human-readable reason for decision")
    reason_public: str = Field(..., description="Public reason code (safe to expose)")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Risk assessment level")
    requires_fresh_challenge: bool = Field(False, description="True if STEP_UP requires new challenge")
    requires_human_review: bool = Field(False, description="True if REVIEW decision")
    # Note: No raw scores exposed to prevent information leakage


class VerificationResultInternal(BaseModel):
    """Internal verification result with full details for logging."""

    request_id: str
    decision: Decision
    session_id: str
    reason: str
    reason_public: str
    risk_level: RiskLevel
    l2_label: str
    l2_confidence: float
    l1_score: float
    layer_blocked: str | None
    asr_transcript: str | None
    asr_similarity: float | None


async def _run_in_executor(func, *args):
    """Run a synchronous function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, partial(func, *args))


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
    tenant_id: str | None = Depends(get_optional_tenant),
) -> VerificationResult:
    """
    Verify user's voice authentication.

    Pipeline (per SYSTEM.md §6):
    1. Validate challenge token
    2. AD (deepfake) || ASR (phrase) - executed in PARALLEL
    3. SV (speaker verification)
    4. Policy Engine → returns one of 5 decisions

    Returns only safe decision information - no raw scores or embeddings.
    Uses centralized PolicyEngine for all authentication decisions.
    """
    req_id = x_request_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Initialize policy input with defaults
    policy_input = PolicyInput()

    # === PRE-VALIDATION: User and Voiceprint ===
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

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

    # === CHALLENGE VALIDATION ===
    expected_phrase = get_token_phrase(token, db)
    if not expected_phrase:
        policy_input.challenge_valid = False
        policy_input.challenge_expired = True
    else:
        policy_input.challenge_valid = True

    # === PARALLEL EXECUTION: AD (Layer 2) || ASR (Layer 3A) ===
    # Run deepfake detection and ASR phrase verification concurrently
    logger.info(f"[{req_id}] Starting parallel AD||ASR execution")

    try:
        ad_task = _run_in_executor(detect_spoof, audio_bytes)
        asr_task = _run_in_executor(
            verify_phrase, audio_bytes, expected_phrase or "", settings.ASR_PHRASE_THRESHOLD
        )

        # Wait for both to complete
        l2_result, asr_result = await asyncio.gather(ad_task, asr_task, return_exceptions=True)

        # Handle AD result
        if isinstance(l2_result, Exception):
            logger.error(f"[{req_id}] AD layer failed: {l2_result}")
            policy_input.ad_available = False
            policy_input.ad_result = GateResult.TIMEOUT
            l2_label, l2_confidence = "error", 0.0
        else:
            l2_label = l2_result["label"]
            l2_confidence = l2_result["confidence"]
            policy_input.ad_available = True
            policy_input.ad_confidence = l2_confidence

            if l2_label == "spoof" and l2_confidence > settings.L2_SPOOF_THRESHOLD:
                policy_input.ad_result = GateResult.FAIL
                policy_input.ad_is_spoof = True
            elif l2_label == "spoof" and l2_confidence > 0.5:
                policy_input.ad_result = GateResult.BORDERLINE
            else:
                policy_input.ad_result = GateResult.PASS

        # Handle ASR result
        if isinstance(asr_result, Exception):
            logger.error(f"[{req_id}] ASR layer failed: {asr_result}")
            policy_input.asr_available = False
            policy_input.asr_result = GateResult.TIMEOUT
            asr_match, asr_similarity, _ = False, 0.0, ""
        else:
            asr_match, asr_similarity, _ = asr_result
            policy_input.asr_available = True
            policy_input.asr_confidence = asr_similarity
            policy_input.asr_match = asr_match
            policy_input.asr_result = GateResult.PASS if asr_match else GateResult.FAIL

    except TimeoutError:
        logger.error(f"[{req_id}] Parallel execution timeout")
        policy_input.ad_available = False
        policy_input.asr_available = False
        l2_label, l2_confidence = "timeout", 0.0
        asr_match, asr_similarity, _ = False, 0.0, ""

    logger.info(f"[{req_id}] Parallel execution complete: AD={policy_input.ad_result}, ASR={policy_input.asr_result}")

    # === SPEAKER VERIFICATION (Layer 1) ===
    # Only run if AD and ASR passed
    l1_score = 0.0
    new_embedding = None

    if policy_input.ad_result == GateResult.PASS and policy_input.asr_result == GateResult.PASS:
        try:
            stored_embedding = decrypt_embedding(
                voiceprint.embedding, tenant_id=tenant_id, user_id=user_id
            )
            l1_result = await _run_in_executor(verify_speaker, audio_bytes, stored_embedding)
            l1_score = l1_result["score"]
            new_embedding = l1_result["embedding"]

            policy_input.sv_available = True
            policy_input.sv_score = l1_score
            policy_input.sv_threshold = settings.L1_SIMILARITY_THRESHOLD

            if l1_score >= settings.L1_SIMILARITY_THRESHOLD:
                policy_input.sv_result = GateResult.PASS
            else:
                policy_input.sv_result = GateResult.FAIL

        except Exception as e:
            logger.error(f"[{req_id}] SV layer failed: {e}")
            policy_input.sv_available = False
            policy_input.sv_result = GateResult.TIMEOUT
    else:
        # Skip SV if earlier gates failed
        policy_input.sv_available = True
        policy_input.sv_result = GateResult.PASS  # Not blocking

    # === POLICY ENGINE EVALUATION ===
    policy_output = evaluate_policy(policy_input)

    logger.info(f"[{req_id}] Policy decision: {policy_output.decision} ({policy_output.reason_public})")

    # === TOKEN CONSUMPTION (only on APPROVE) ===
    challenge_id = None
    if policy_output.decision == Decision.APPROVE:
        challenge_data = validate_and_consume_token(token, db)
        if not challenge_data:
            # Token was consumed between validation and now (race condition)
            policy_input.challenge_consumed = True
            policy_output = evaluate_policy(policy_input)
        else:
            challenge_id = challenge_data.get("id") if isinstance(challenge_data, dict) else None

            # Update voiceprint with EMA
            if new_embedding is not None:
                stored_embedding = decrypt_embedding(
                    voiceprint.embedding, tenant_id=tenant_id, user_id=user_id
                )
                updated_embedding = update_voiceprint(stored_embedding, new_embedding)
                voiceprint.embedding = encrypt_embedding(
                    updated_embedding, tenant_id=tenant_id, user_id=user_id
                )
                voiceprint.sample_count += 1
                voiceprint.updated_at = datetime.utcnow()

    # === AUDIT LOGGING ===
    _log_attempt(
        db,
        user_id=user_id,
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        result=policy_output.decision.value,
        layer_blocked=policy_output.gate_blocked,
        challenge_id=challenge_id,
    )

    db.commit()

    # Register for status polling
    register_verification_request(
        request_id=req_id,
        decision=policy_output.decision,
        reason_public=policy_output.reason_public,
        risk_level=policy_output.risk_level,
    )

    return VerificationResult(
        request_id=req_id,
        decision=policy_output.decision,
        session_id=session_id,
        reason=policy_output.reason_internal or policy_output.reason_public,
        reason_public=policy_output.reason_public,
        risk_level=policy_output.risk_level,
        requires_fresh_challenge=policy_output.requires_fresh_challenge,
        requires_human_review=policy_output.requires_human_review,
    )


def _log_attempt(
    db: Session,
    user_id: str,
    l2_label: str,
    l2_confidence: float,
    l1_score: float,
    result: str,
    layer_blocked: str | None,
    challenge_id: str | None = None,
) -> None:
    """Log authentication attempt to database."""
    # Map gate names to layer numbers for backward compatibility
    layer_map = {"AD": 2, "ASR": 3, "SV": 1, "SERVICE": 0}
    layer_num = layer_map.get(layer_blocked) if layer_blocked else None

    log = AuthLog(
        user_id=uuid.UUID(user_id),
        challenge_id=uuid.UUID(challenge_id) if challenge_id else None,
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        result=result,
        layer_blocked=layer_num,
    )
    db.add(log)
    db.commit()
