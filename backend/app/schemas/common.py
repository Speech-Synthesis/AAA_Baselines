"""
AAA Engine Common Schemas
Shared Pydantic models for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class Decision(str, Enum):
    """Authentication decision outcomes."""
    APPROVE = "APPROVE"
    DENY = "DENY"
    STEP_UP = "STEP_UP"
    REVIEW = "REVIEW"
    UNAVAILABLE = "UNAVAILABLE"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ModelStatus(str, Enum):
    """Model availability status."""
    OK = "ok"
    LOADING = "loading"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class CheckStatus(str, Enum):
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


class ReadinessChecks(BaseModel):
    """All readiness checks."""
    database: CheckStatus = CheckStatus.ERROR
    models: ModelChecks = Field(default_factory=ModelChecks)
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
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Common Request/Response Fields
class RequestIdMixin(BaseModel):
    """Mixin for request ID tracking."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
