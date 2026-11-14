"""
AAA Engine API - Navadeep
Orchestrates L2 → L1 → L3 pipeline

Updated by Surya (Nov 11, 2026):
- Added v1 API router with health/readiness endpoints
- Centralized configuration via core.config
- Legacy routes preserved for backward compatibility
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

# Import v1 API router
from .api.v1 import router as v1_router
from .core.config import get_settings
from .core.ratelimit import limiter, rate_limit_exceeded_handler
from .db import Base, engine, get_db
from .layer1_speaker import enroll_speaker, verify_speaker
from .layer2_deepfake import detect_spoof
from .layer3_adaptive import generate_challenge, get_token_phrase, update_voiceprint, verify_token
from .layer3_asr import verify_phrase
from .models import AuthLog, Challenge, User, Voiceprint
from .security.jwt_auth import router as auth_router

# Create tables on startup
Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(
    title="AAA Engine",
    description="Adaptive Audio Authentication with Deepfake Detection",
    version="1.0.0",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include v1 API router
app.include_router(v1_router)

# Include JWT authentication router
app.include_router(auth_router)

# CORS for frontend - explicit allowed origins only
# Wildcard patterns are NOT allowed for security
def get_allowed_origins() -> list[str]:
    """Get CORS allowed origins from settings, filtering out wildcards."""
    import logging

    logger = logging.getLogger("aaa_engine.cors")

    # Start with configured origins
    origins: list[str] = []
    if settings.CORS_ORIGINS:
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

    # Add explicit localhost origins for development
    if settings.DEBUG:
        dev_origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
        ]
        for origin in dev_origins:
            if origin not in origins:
                origins.append(origin)

    # Filter out any wildcard patterns and log warning
    safe_origins = []
    for origin in origins:
        if "*" in origin:
            logger.warning(
                f"SECURITY: Wildcard CORS origin '{origin}' rejected. "
                "Use explicit origins only."
            )
        else:
            safe_origins.append(origin)

    return safe_origins


cors_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# Serve static frontend files (for production deployment)
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

# Thresholds - now configurable via environment
L2_SPOOF_THRESHOLD = settings.L2_SPOOF_THRESHOLD
L1_SIMILARITY_THRESHOLD = settings.L1_SIMILARITY_THRESHOLD
ASR_PHRASE_THRESHOLD = settings.ASR_PHRASE_THRESHOLD


# === Request/Response Models ===


class RegisterRequest(BaseModel):
    name: str
    email: str


class RegisterResponse(BaseModel):
    user_id: str


class EnrollResponse(BaseModel):
    status: str
    sample_count: int


class ChallengeResponse(BaseModel):
    phrase: str
    token: str
    expires_at: datetime


class VerifyResponse(BaseModel):
    result: str  # "ACCEPT" | "REJECT"
    confidence: float
    layer_blocked: int | None
    session_id: str
    reason: str
    l2_label: str
    l2_confidence: float
    l1_score: float
    asr_transcript: str | None = None
    asr_similarity: float | None = None


class VoiceprintHistory(BaseModel):
    updated_at: datetime
    sample_count: int


class AuthLogResponse(BaseModel):
    id: str
    user_id: str
    l2_label: str | None
    l2_confidence: float
    l1_score: float
    result: str
    layer_blocked: int | None
    created_at: datetime
    reason: str | None = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    has_voiceprint: bool = False


# === Routes ===


@app.get("/")
async def root():
    return {"message": "AAA Engine API", "status": "running"}


@app.get("/users", response_model=list[UserResponse])
async def get_all_users(db: Session = Depends(get_db)):
    """Get all registered users."""
    users = db.query(User).order_by(User.created_at.desc()).all()

    result = []
    for user in users:
        voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user.id).first()
        result.append(
            UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                created_at=user.created_at,
                has_voiceprint=voiceprint is not None,
            )
        )
    return result


@app.post("/auth/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(name=request.name, email=request.email)
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(user_id=str(user.id))


@app.post("/auth/enroll", response_model=EnrollResponse)
@limiter.limit(settings.RATE_LIMIT_ENROLL)
async def enroll(
    request: Request,
    user_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Enroll user's voice (create/update voiceprint)."""
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Read audio
    audio_bytes = await audio.read()

    # L1: Extract embedding
    result = enroll_speaker(audio_bytes)
    embedding = result["embedding"]

    # Check for existing voiceprint
    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user_id).first()

    if voiceprint:
        # Update with EMA
        updated_embedding = update_voiceprint(voiceprint.embedding, embedding)
        voiceprint.embedding = updated_embedding
        voiceprint.sample_count += 1
        voiceprint.updated_at = datetime.utcnow()
    else:
        # Create new voiceprint
        voiceprint = Voiceprint(user_id=uuid.UUID(user_id), embedding=embedding, sample_count=1)
        db.add(voiceprint)

    db.commit()
    db.refresh(voiceprint)

    return EnrollResponse(status="enrolled", sample_count=voiceprint.sample_count)


@app.get("/auth/challenge", response_model=ChallengeResponse)
@limiter.limit(settings.RATE_LIMIT_CHALLENGES)
async def get_challenge(request: Request, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Generate a challenge phrase for authentication."""
    # Validate user exists and has voiceprint
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user_id).first()
    if not voiceprint:
        raise HTTPException(status_code=400, detail="User has no enrolled voiceprint")

    # Generate challenge
    challenge_data = generate_challenge(user_id)

    # Store in DB
    challenge = Challenge(
        user_id=uuid.UUID(user_id),
        phrase=challenge_data["phrase"],
        token=challenge_data["token"],
        expires_at=challenge_data["expires_at"],
    )
    db.add(challenge)
    db.commit()

    return ChallengeResponse(**challenge_data)


@app.post("/auth/verify", response_model=VerifyResponse)
@limiter.limit(settings.RATE_LIMIT_VERIFY)
async def verify(
    request: Request,
    user_id: str = Form(...),
    token: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Verify user's voice against challenge.
    Pipeline: L2 (deepfake) → L1 (speaker) → L3 (token + EMA update)
    """
    session_id = str(uuid.uuid4())

    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get voiceprint
    voiceprint = db.query(Voiceprint).filter(Voiceprint.user_id == user_id).first()
    if not voiceprint:
        raise HTTPException(status_code=400, detail="User has no enrolled voiceprint")

    # Read audio
    audio_bytes = await audio.read()

    # === LAYER 2: Deepfake Detection ===
    l2_result = detect_spoof(audio_bytes)
    l2_label = l2_result["label"]
    l2_confidence = l2_result["confidence"]

    if l2_label == "spoof" and l2_confidence > L2_SPOOF_THRESHOLD:
        # Log and reject
        log = AuthLog(
            user_id=uuid.UUID(user_id),
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            result="REJECT",
            layer_blocked=2,
        )
        db.add(log)
        db.commit()

        return VerifyResponse(
            result="REJECT",
            confidence=l2_confidence,
            layer_blocked=2,
            session_id=session_id,
            reason="Deepfake/spoof detected",
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
        )

    # === LAYER 3A: ASR Phrase Verification (before speaker check) ===
    expected_phrase = get_token_phrase(token)
    asr_match, asr_similarity, asr_transcript = verify_phrase(
        audio_bytes, expected_phrase or "", ASR_PHRASE_THRESHOLD
    )

    if not asr_match:
        # Log and reject - wrong phrase spoken
        log = AuthLog(
            user_id=uuid.UUID(user_id),
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            result="REJECT",
            layer_blocked=4,  # Layer 4 = ASR phrase mismatch
        )
        db.add(log)
        db.commit()

        return VerifyResponse(
            result="REJECT",
            confidence=asr_similarity,
            layer_blocked=4,
            session_id=session_id,
            reason=f"Phrase mismatch: expected '{expected_phrase}', heard '{asr_transcript}'",
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=0.0,
            asr_transcript=asr_transcript,
            asr_similarity=asr_similarity,
        )

    # === LAYER 1: Speaker Verification ===
    l1_result = verify_speaker(audio_bytes, voiceprint.embedding)
    l1_score = l1_result["score"]
    new_embedding = l1_result["embedding"]

    if l1_score < L1_SIMILARITY_THRESHOLD:
        # Log and reject
        log = AuthLog(
            user_id=uuid.UUID(user_id),
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
            result="REJECT",
            layer_blocked=1,
        )
        db.add(log)
        db.commit()

        return VerifyResponse(
            result="REJECT",
            confidence=l1_score,
            layer_blocked=1,
            session_id=session_id,
            reason="Speaker verification failed",
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
            asr_transcript=asr_transcript,
            asr_similarity=asr_similarity,
        )

    # === LAYER 3B: Token Verification ===
    if not verify_token(token):
        # Log and reject
        log = AuthLog(
            user_id=uuid.UUID(user_id),
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
            result="REJECT",
            layer_blocked=3,
        )
        db.add(log)
        db.commit()

        return VerifyResponse(
            result="REJECT",
            confidence=0.0,
            layer_blocked=3,
            session_id=session_id,
            reason="Invalid or expired token",
            l2_label=l2_label,
            l2_confidence=l2_confidence,
            l1_score=l1_score,
        )

    # Mark challenge as used in database
    challenge = db.query(Challenge).filter(Challenge.token == token).first()
    if challenge:
        challenge.used = True

    # === SUCCESS: Update voiceprint with EMA ===
    updated_embedding = update_voiceprint(voiceprint.embedding, new_embedding)
    voiceprint.embedding = updated_embedding
    voiceprint.sample_count += 1
    voiceprint.updated_at = datetime.utcnow()

    # Log success
    log = AuthLog(
        user_id=uuid.UUID(user_id),
        challenge_id=challenge.id if challenge else None,
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        result="ACCEPT",
        layer_blocked=None,
    )
    db.add(log)
    db.commit()

    return VerifyResponse(
        result="ACCEPT",
        confidence=l1_score,
        layer_blocked=None,
        session_id=session_id,
        reason="Authentication successful",
        l2_label=l2_label,
        l2_confidence=l2_confidence,
        l1_score=l1_score,
        asr_transcript=asr_transcript,
        asr_similarity=asr_similarity,
    )


@app.get("/users/{user_id}/voiceprint-history", response_model=list[VoiceprintHistory])
async def voiceprint_history(user_id: str, db: Session = Depends(get_db)):
    """Get voiceprint update history for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    voiceprints = (
        db.query(Voiceprint)
        .filter(Voiceprint.user_id == user_id)
        .order_by(Voiceprint.updated_at.desc())
        .all()
    )

    return [
        VoiceprintHistory(updated_at=vp.updated_at, sample_count=vp.sample_count)
        for vp in voiceprints
    ]


@app.get("/users/{user_id}/auth-logs", response_model=list[AuthLogResponse])
async def get_auth_logs(user_id: str, db: Session = Depends(get_db)):
    """Get authentication logs for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logs = (
        db.query(AuthLog)
        .filter(AuthLog.user_id == user_id)
        .order_by(AuthLog.created_at.desc())
        .limit(50)
        .all()
    )

    # Map layer_blocked to reason
    def get_reason(log):
        if log.result == "ACCEPT":
            return "Authentication successful"
        if log.layer_blocked == 1:
            return "Speaker verification failed"
        if log.layer_blocked == 2:
            return "Deepfake/spoof detected"
        if log.layer_blocked == 3:
            return "Invalid or expired token"
        if log.layer_blocked == 4:
            return "Challenge phrase mismatch"
        return "Unknown"

    return [
        AuthLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            l2_label=log.l2_label,
            l2_confidence=log.l2_confidence or 0.0,
            l1_score=log.l1_score or 0.0,
            result=log.result,
            layer_blocked=log.layer_blocked,
            created_at=log.created_at,
            reason=get_reason(log),
        )
        for log in logs
    ]


# Serve frontend for all non-API routes (must be at the end)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve React frontend for client-side routing."""
    if STATIC_DIR.exists():
        # Try to serve the exact file first
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Fall back to index.html for client-side routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    return {"message": "AAA Engine API", "status": "running"}
