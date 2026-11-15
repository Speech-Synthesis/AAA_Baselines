"""
AAA Engine Common Schemas
Shared Pydantic models for API requests and responses.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Decision(StrEnum):
    """Authentication decision outcomes."""

    APPROVE = "APPROVE"
    DENY = "DENY"
    STEP_UP = "STEP_UP"
    REVIEW = "REVIEW"
    UNAVAILABLE = "UNAVAILABLE"


class RiskLevel(StrEnum):
    """Risk assessment levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ModelStatus(StrEnum):
    """Model availability status."""

    OK = "ok"
    LOADING = "loading"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class CheckStatus(StrEnum):
    """Readiness check status."""

    OK = "ok"
    ERROR = "error"


# Health Check Schemas
class HealthResponse(BaseModel):
    """Response for /v1/health endpoint."""

    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelChecks(BaseModel):
    """Model availability checks."""

    speaker_verification: ModelStatus = ModelStatus.UNAVAILABLE
    deepfake_detection: ModelStatus = ModelStatus.UNAVAILABLE
    asr: ModelStatus = ModelStatus.UNAVAILABLE
    vishing_risk: ModelStatus = ModelStatus.UNAVAILABLE


class SecurityChecks(BaseModel):
    """Security component checks."""

    jwt_secret: CheckStatus = CheckStatus.ERROR
    voiceprint_encryption: CheckStatus = CheckStatus.ERROR
    rate_limiting: CheckStatus = CheckStatus.ERROR


class PoolStatus(BaseModel):
    """Database connection pool status."""

    type: str = "unknown"
    pooled: bool = False
    size: int | None = None
    checked_in: int | None = None
    checked_out: int | None = None
    overflow: int | None = None


class ReadinessChecks(BaseModel):
    """All readiness checks."""

    database: CheckStatus = CheckStatus.ERROR
    pool: PoolStatus = Field(default_factory=PoolStatus)
    models: ModelChecks = Field(default_factory=ModelChecks)
    security: SecurityChecks = Field(default_factory=SecurityChecks)
    configuration: CheckStatus = CheckStatus.ERROR


class ReadinessResponse(BaseModel):
    """Response for /v1/ready endpoint."""

    status: str = "not_ready"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: ReadinessChecks = Field(default_factory=ReadinessChecks)


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


# Common Request/Response Fields
class RequestIdMixin(BaseModel):
    """Mixin for request ID tracking."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
