"""
AAA Engine Health and Readiness Endpoints

Per SYSTEM.md §5:
- /v1/health: Liveness probe (process alive)
- /v1/ready: Readiness probe (all dependencies available)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.config import get_settings, validate_production_config
from ...db import get_db, get_pool_status
from ...schemas.common import (
    CheckStatus,
    HealthResponse,
    ModelChecks,
    ModelStatus,
    PoolStatus,
    ReadinessChecks,
    ReadinessResponse,
    SecurityChecks,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Liveness check.

    Returns 200 if the process is alive.
    Does not check dependencies.
    """
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Readiness check per SYSTEM.md §5.

    Checks:
    - Database connectivity
    - Configuration validity
    - Model availability (SV, AD, ASR, VR)
    - Security components (JWT, encryption, rate limiting)

    Returns 503 if any required dependency is unavailable.
    """
    checks = ReadinessChecks()
    all_ready = True
    settings = get_settings()

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks.database = CheckStatus.OK
    except Exception:
        checks.database = CheckStatus.ERROR
        all_ready = False

    # Check connection pool status
    try:
        pool_info = get_pool_status()
        checks.pool = PoolStatus(**pool_info)
    except Exception:
        checks.pool = PoolStatus(type="unknown", pooled=False)

    # Check configuration
    config_errors = validate_production_config()
    if config_errors:
        checks.configuration = CheckStatus.ERROR
        all_ready = False
    else:
        checks.configuration = CheckStatus.OK

    # Check models (lazy - just check if modules can be imported)
    model_checks = ModelChecks()

    # Speaker Verification (AAA-SV)
    try:
        from ...layer1_speaker import MODEL

        if MODEL is not None:
            model_checks.speaker_verification = ModelStatus.OK
        else:
            model_checks.speaker_verification = ModelStatus.LOADING
    except ImportError:
        model_checks.speaker_verification = ModelStatus.UNAVAILABLE
    except Exception:
        model_checks.speaker_verification = ModelStatus.ERROR

    # Deepfake Detection (AAA-AD)
    try:
        from ...layer2_deepfake import _MODEL

        if _MODEL is not None:
            model_checks.deepfake_detection = ModelStatus.OK
        else:
            model_checks.deepfake_detection = ModelStatus.LOADING
    except ImportError:
        model_checks.deepfake_detection = ModelStatus.UNAVAILABLE
    except Exception:
        model_checks.deepfake_detection = ModelStatus.ERROR

    # ASR (AAA-ASR)
    try:
        from ...layer3_asr import _whisper_model

        if _whisper_model is not None:
            model_checks.asr = ModelStatus.OK
        else:
            model_checks.asr = ModelStatus.LOADING
    except ImportError:
        model_checks.asr = ModelStatus.UNAVAILABLE
    except Exception:
        model_checks.asr = ModelStatus.ERROR

    # Vishing Risk (AAA-VR)
    try:
        from ...adapters.vr import TranscriptRiskAdapter

        vr_adapter = TranscriptRiskAdapter()
        if vr_adapter is not None:
            model_checks.vishing_risk = ModelStatus.OK
        else:
            model_checks.vishing_risk = ModelStatus.UNAVAILABLE
    except ImportError:
        model_checks.vishing_risk = ModelStatus.UNAVAILABLE
    except Exception:
        model_checks.vishing_risk = ModelStatus.ERROR

    checks.models = model_checks

    # Check security components
    security_checks = SecurityChecks()

    # JWT Secret validation
    try:
        from ...security.jwt_auth import JWT_SECRET

        # JWT_SECRET is validated at module load time
        if JWT_SECRET and len(JWT_SECRET) >= 32:
            security_checks.jwt_secret = CheckStatus.OK
        else:
            security_checks.jwt_secret = CheckStatus.ERROR
            all_ready = False
    except Exception:
        security_checks.jwt_secret = CheckStatus.ERROR
        all_ready = False

    # Voiceprint encryption
    try:
        from ...security.voiceprint_crypto import VoiceprintEncryptor

        encryptor = VoiceprintEncryptor()
        if encryptor is not None:
            security_checks.voiceprint_encryption = CheckStatus.OK
        else:
            security_checks.voiceprint_encryption = CheckStatus.ERROR
    except Exception:
        security_checks.voiceprint_encryption = CheckStatus.ERROR

    # Rate limiting
    try:
        from ...core.ratelimit import limiter

        if limiter is not None:
            security_checks.rate_limiting = CheckStatus.OK
        else:
            security_checks.rate_limiting = CheckStatus.ERROR
    except Exception:
        security_checks.rate_limiting = CheckStatus.ERROR

    checks.security = security_checks

    # Set response status
    status = "ready" if all_ready else "not_ready"
    if not all_ready:
        response.status_code = 503

    return ReadinessResponse(status=status, timestamp=datetime.utcnow(), checks=checks)
