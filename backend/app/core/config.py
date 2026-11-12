"""
AAA Engine Core Configuration
Centralized configuration management with environment variable support.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "AAA Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./aaa_engine.db"

    # Security - No fallback defaults for secrets in production
    L3_HMAC_SECRET: Optional[str] = None

    # Model Configuration
    WHISPER_MODEL: str = "base"

    # Thresholds (configurable via environment)
    L2_SPOOF_THRESHOLD: float = 0.5
    L1_SIMILARITY_THRESHOLD: float = 0.5
    ASR_PHRASE_THRESHOLD: float = 0.6

    # Challenge Configuration
    CHALLENGE_TTL_SECONDS: int = 90

    # Rate Limiting
    RATE_LIMIT_CHALLENGES: str = "10/minute"
    RATE_LIMIT_VERIFY: str = "5/minute"
    RATE_LIMIT_ENROLL: str = "3/5minutes"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow unknown env vars to pass through


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def validate_production_config() -> list[str]:
    """
    Validate configuration for production use.
    Returns list of validation errors.
    """
    settings = get_settings()
    errors = []

    # Critical: HMAC secret must be set in production
    if not settings.DEBUG and not settings.L3_HMAC_SECRET:
        errors.append("L3_HMAC_SECRET must be set in production")

    # Warn if using SQLite in production
    if not settings.DEBUG and settings.DATABASE_URL.startswith("sqlite"):
        errors.append("SQLite should not be used in production")

    return errors
