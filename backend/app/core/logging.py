"""
AAA Engine - Structured Security Logging
Formats audit records into structured JSON omitting sensitive biometric/audio payloads.

Per DATA_SECURITY.md §8:
- Never log raw biometric embeddings or audio
- Redact authorization headers and tokens
- Mask PII fields (email, phone, SSN patterns)
- Log only safe metadata for audit trail

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

# Fields to completely omit from logs
SENSITIVE_FIELDS = frozenset(
    [
        "embedding",
        "audio",
        "audio_bytes",
        "audio_data",
        "voiceprint",
        "biometric",
        "client_secret",
        "password",
        "secret",
        "private_key",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "jwt",
        "bearer",
        "authorization",
        "x-api-key",
        "cvv",
        "pin",
        "ssn",
        "social_security",
    ]
)

# Headers to redact in log messages
REDACT_HEADERS = frozenset(
    [
        "authorization",
        "x-api-key",
        "x-capture-grant",
        "cookie",
        "set-cookie",
    ]
)

# Patterns to mask in log messages
REDACT_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]*"), "Bearer [REDACTED]"),
    (re.compile(r"password[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+"), "password: [REDACTED]"),
    (re.compile(r"secret[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+"), "secret: [REDACTED]"),
    (re.compile(r"token[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+"), "token: [REDACTED]"),
    (re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+", re.I), "api_key: [REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[CARD_REDACTED]"),
    (re.compile(r"embedding[\"']?\s*[:=]\s*\[[^\]]+\]"), "embedding: [BIOMETRIC_REDACTED]"),
]


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive patterns from log messages.

    Per DATA_SECURITY.md §8:
    - Mask JWTs, API keys, passwords
    - Mask email addresses, phone numbers, SSNs
    - Mask credit card numbers
    - Mask biometric embeddings
    """
    result = text
    for pattern, replacement in REDACT_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """
    Recursively redact sensitive fields from a dictionary.

    Args:
        data: Dictionary to redact
        depth: Current recursion depth (max 5 to prevent infinite loops)

    Returns:
        Dictionary with sensitive fields redacted
    """
    if depth > 5:
        return {"_truncated": "max depth exceeded"}

    result = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Completely omit sensitive fields
        if key_lower in SENSITIVE_FIELDS:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1)
        elif isinstance(value, list):
            if key_lower in {"embedding", "embeddings", "voiceprint", "biometric"}:
                result[key] = f"[BIOMETRIC_ARRAY_REDACTED len={len(value)}]"
            elif len(value) > 100:
                result[key] = f"[ARRAY_TRUNCATED len={len(value)}]"
            else:
                result[key] = [
                    redact_dict(v, depth + 1) if isinstance(v, dict) else v
                    for v in value[:20]
                ]
        elif isinstance(value, str):
            result[key] = redact_sensitive_data(value)
        else:
            result[key] = value

    return result


class StructuredSecurityFormatter(logging.Formatter):
    """
    JSON log formatter adhering to AAA Security Boundaries.

    Per DATA_SECURITY.md §8:
    - Structured JSON output for log aggregation
    - Automatic redaction of sensitive patterns
    - Safe metadata only (no raw biometrics)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_data(record.getMessage()),
        }

        # Safely extract extra fields while redacting sensitive data
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            redacted_extra = redact_dict(record.extra)
            for k, v in redacted_extra.items():
                if k.lower() not in SENSITIVE_FIELDS:
                    log_entry[k] = v

        if record.exc_info:
            log_entry["exception"] = redact_sensitive_data(
                self.formatException(record.exc_info)
            )

        return json.dumps(log_entry)


def get_security_logger(name: str) -> logging.Logger:
    """
    Get a logger configured with the security formatter.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger with StructuredSecurityFormatter
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredSecurityFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
