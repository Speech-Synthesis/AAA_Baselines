"""
AAA Engine Rate Limiting
Configurable rate limiting for API endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from .config import get_settings


def _get_client_ip(request: Request) -> str:
    """
    Get client IP address, respecting X-Forwarded-For header.
    Falls back to direct connection IP.
    """
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (client's original IP)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(key_func=_get_client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns a standardized JSON response.
    """
    settings = get_settings()

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, "retry_after", 60),
            "details": {
                "limit": str(exc.detail) if hasattr(exc, "detail") else "Unknown",
                "documentation": "See API documentation for rate limit details"
            }
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60)),
            "X-RateLimit-Limit": str(exc.detail) if hasattr(exc, "detail") else "Unknown"
        }
    )


# Rate limit decorators for common use cases
def challenge_rate_limit():
    """Rate limit for challenge generation endpoint."""
    settings = get_settings()
    return limiter.limit(settings.RATE_LIMIT_CHALLENGES)


def verify_rate_limit():
    """Rate limit for verification endpoint."""
    settings = get_settings()
    return limiter.limit(settings.RATE_LIMIT_VERIFY)


def enroll_rate_limit():
    """Rate limit for enrollment endpoint."""
    settings = get_settings()
    return limiter.limit(settings.RATE_LIMIT_ENROLL)
