"""
AAA Engine Health and Readiness Endpoints
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.config import validate_production_config
from ...db import get_db
from ...schemas.common import (
    CheckStatus,
    HealthResponse,
    ModelChecks,
    ModelStatus,
    ReadinessChecks,
    ReadinessResponse,
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
    Readiness check.

    Checks:
    - Database connectivity
    - Configuration validity
    - Model availability (lazy check)

    Returns 503 if any required dependency is unavailable.
    """
    checks = ReadinessChecks()
    all_ready = True

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks.database = CheckStatus.OK
    except Exception:
        checks.database = CheckStatus.ERROR
        all_ready = False

    # Check configuration
    config_errors = validate_production_config()
    if config_errors:
        checks.configuration = CheckStatus.ERROR
        all_ready = False
    else:
        checks.configuration = CheckStatus.OK

    # Check models (lazy - just check if modules can be imported)
    model_checks = ModelChecks()

    # Speaker Verification
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

    # Deepfake Detection
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

    # ASR
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

    checks.models = model_checks

    # Set response status
    status = "ready" if all_ready else "not_ready"
    if not all_ready:
        response.status_code = 503

    return ReadinessResponse(status=status, timestamp=datetime.utcnow(), checks=checks)
