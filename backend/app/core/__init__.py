"""AAA Engine Core package."""

from .config import Settings, get_settings
from .exceptions import (
    AAAEngineError,
    AudioValidationError,
    AuthenticationError,
    ChallengeError,
    ChallengeExpiredError,
    ChallengeNotFoundError,
    ConfigurationError,
    InvalidTokenError,
    MissingSecretError,
    ModelError,
    ModelInferenceError,
    ModelNotAvailableError,
    ModelTimeoutError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    UserNotFoundError,
    ValidationError,
    VoiceprintNotFoundError,
)
from .policy_engine import (
    GateResult,
    PolicyEngine,
    PolicyInput,
    PolicyOutput,
    evaluate_policy,
    get_policy_engine,
)

__all__ = [
    # Config
    "get_settings",
    "Settings",
    # Policy Engine
    "PolicyEngine",
    "PolicyInput",
    "PolicyOutput",
    "GateResult",
    "evaluate_policy",
    "get_policy_engine",
    # Exceptions
    "AAAEngineError",
    "AuthenticationError",
    "InvalidTokenError",
    "TokenExpiredError",
    "TokenAlreadyUsedError",
    "ChallengeError",
    "ChallengeNotFoundError",
    "ChallengeExpiredError",
    "ModelError",
    "ModelNotAvailableError",
    "ModelInferenceError",
    "ModelTimeoutError",
    "ValidationError",
    "AudioValidationError",
    "UserNotFoundError",
    "VoiceprintNotFoundError",
    "ConfigurationError",
    "MissingSecretError",
]
