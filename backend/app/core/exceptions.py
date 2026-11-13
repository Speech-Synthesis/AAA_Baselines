"""
AAA Engine Custom Exceptions
Typed exceptions for consistent error handling.
"""



class AAAEngineError(Exception):
    """Base exception for AAA Engine."""
    def __init__(self, message: str, code: str = "internal_error"):
        self.message = message
        self.code = code
        super().__init__(message)


# Authentication Errors
class AuthenticationError(AAAEngineError):
    """Base authentication error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "unauthorized")


class InvalidTokenError(AuthenticationError):
    """Token validation failed."""
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class TokenAlreadyUsedError(AuthenticationError):
    """Token has already been consumed."""
    def __init__(self, message: str = "Token has already been used"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Token TTL exceeded."""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


# Challenge Errors
class ChallengeError(AAAEngineError):
    """Base challenge error."""
    def __init__(self, message: str, code: str = "challenge_error"):
        super().__init__(message, code)


class ChallengeNotFoundError(ChallengeError):
    """Challenge does not exist."""
    def __init__(self, message: str = "Challenge not found"):
        super().__init__(message, "not_found")


class ChallengeExpiredError(ChallengeError):
    """Challenge TTL exceeded."""
    def __init__(self, message: str = "Challenge has expired"):
        super().__init__(message, "expired")


class InvalidChallengeStateError(ChallengeError):
    """Challenge in wrong state for operation."""
    def __init__(self, message: str = "Challenge is in invalid state"):
        super().__init__(message, "invalid_state")


# Model Errors
class ModelError(AAAEngineError):
    """Base model error."""
    def __init__(self, message: str, code: str = "model_error"):
        super().__init__(message, code)


class ModelNotAvailableError(ModelError):
    """Model is not loaded or available."""
    def __init__(self, model_id: str = "unknown"):
        super().__init__(f"Model {model_id} is not available", "model_unavailable")
        self.model_id = model_id


class ModelInferenceError(ModelError):
    """Error during model inference."""
    def __init__(self, message: str = "Model inference failed"):
        super().__init__(message, "inference_error")


class ModelTimeoutError(ModelError):
    """Model inference exceeded timeout."""
    def __init__(self, model_id: str = "unknown", timeout: float = 10.0):
        super().__init__(
            f"Model {model_id} inference timed out after {timeout}s",
            "model_timeout"
        )
        self.model_id = model_id
        self.timeout = timeout


# Validation Errors
class ValidationError(AAAEngineError):
    """Input validation failed."""
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "validation_error")
        self.field = field


class AudioValidationError(ValidationError):
    """Audio input validation failed."""
    def __init__(self, message: str = "Invalid audio format"):
        super().__init__(message, "audio")


# User/Voiceprint Errors
class UserNotFoundError(AAAEngineError):
    """User does not exist."""
    def __init__(self, user_id: str = "unknown"):
        super().__init__(f"User {user_id} not found", "not_found")
        self.user_id = user_id


class VoiceprintNotFoundError(AAAEngineError):
    """User has no enrolled voiceprint."""
    def __init__(self, user_id: str = "unknown"):
        super().__init__(f"No voiceprint enrolled for user {user_id}", "not_found")
        self.user_id = user_id


# Configuration Errors
class ConfigurationError(AAAEngineError):
    """Configuration validation failed."""
    def __init__(self, message: str = "Invalid configuration"):
        super().__init__(message, "configuration_error")


class MissingSecretError(ConfigurationError):
    """Required secret not configured."""
    def __init__(self, secret_name: str):
        super().__init__(f"Required secret {secret_name} is not configured")
        self.secret_name = secret_name
