"""
AAA Engine - Structured Security Logging
Formats audit records into structured JSON omitting sensitive biometric/audio payloads.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

SENSITIVE_FIELDS = frozenset(
    [
        "embedding",
        "audio",
        "audio_bytes",
        "client_secret",
        "password",
        "secret",
        "private_key",
        "token",
    ]
)


class StructuredSecurityFormatter(logging.Formatter):
    """JSON log formatter adhering to AAA Security Boundaries."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Safely extract extra fields while omitting sensitive biometric data
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for k, v in record.extra.items():
                if k.lower() not in SENSITIVE_FIELDS:
                    log_entry[k] = v

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)
