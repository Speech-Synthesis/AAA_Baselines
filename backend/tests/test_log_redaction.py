"""
Tests for Log Redaction per DATA_SECURITY.md §8.

Verifies that sensitive data is properly redacted from logs:
- JWT tokens
- API keys and passwords
- Email addresses, phone numbers, SSNs
- Credit card numbers
- Biometric embeddings
"""

import json
import logging

import pytest

from app.core.logging import (
    StructuredSecurityFormatter,
    redact_dict,
    redact_sensitive_data,
)


class TestRedactSensitiveData:
    """Tests for the redact_sensitive_data function."""

    def test_redacts_jwt_bearer_token(self):
        """JWT Bearer tokens should be redacted."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = redact_sensitive_data(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[REDACTED]" in result

    def test_redacts_password_in_json(self):
        """Passwords in JSON-like strings should be redacted."""
        text = '{"username": "user", "password": "secret123"}'
        result = redact_sensitive_data(text)
        assert "secret123" not in result
        assert "[REDACTED]" in result

    def test_redacts_api_key(self):
        """API keys should be redacted."""
        text = "api_key: sk-1234567890abcdef"
        result = redact_sensitive_data(text)
        assert "sk-1234567890abcdef" not in result
        assert "[REDACTED]" in result

    def test_redacts_email_address(self):
        """Email addresses should be redacted."""
        text = "User email is test@example.com"
        result = redact_sensitive_data(text)
        assert "test@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_redacts_phone_number(self):
        """Phone numbers should be redacted."""
        text = "Contact: 555-123-4567"
        result = redact_sensitive_data(text)
        assert "555-123-4567" not in result
        assert "[PHONE_REDACTED]" in result

    def test_redacts_ssn(self):
        """Social Security Numbers should be redacted."""
        text = "SSN: 123-45-6789"
        result = redact_sensitive_data(text)
        assert "123-45-6789" not in result
        assert "[SSN_REDACTED]" in result

    def test_redacts_credit_card(self):
        """Credit card numbers should be redacted."""
        text = "Card: 1234-5678-9012-3456"
        result = redact_sensitive_data(text)
        assert "1234-5678-9012-3456" not in result
        assert "[CARD_REDACTED]" in result

    def test_redacts_embedding_array(self):
        """Biometric embedding arrays should be redacted."""
        text = 'embedding: [0.1, 0.2, 0.3, 0.4, 0.5]'
        result = redact_sensitive_data(text)
        assert "[0.1, 0.2, 0.3" not in result
        assert "[BIOMETRIC_REDACTED]" in result

    def test_preserves_safe_text(self):
        """Non-sensitive text should be preserved."""
        text = "User logged in successfully at 2026-11-15T10:00:00Z"
        result = redact_sensitive_data(text)
        assert result == text


class TestRedactDict:
    """Tests for the redact_dict function."""

    def test_redacts_password_field(self):
        """Password fields should be redacted."""
        data = {"username": "test", "password": "secret123"}
        result = redact_dict(data)
        assert result["username"] == "test"
        assert result["password"] == "[REDACTED]"

    def test_redacts_token_field(self):
        """Token fields should be redacted."""
        data = {"user_id": "123", "token": "abc123xyz"}
        result = redact_dict(data)
        assert result["user_id"] == "123"
        assert result["token"] == "[REDACTED]"

    def test_redacts_embedding_field(self):
        """Embedding arrays should be redacted."""
        data = {"user_id": "123", "embedding": [0.1] * 192}
        result = redact_dict(data)
        assert result["user_id"] == "123"
        assert result["embedding"] == "[REDACTED]"

    def test_redacts_nested_sensitive_fields(self):
        """Nested sensitive fields should be redacted."""
        data = {
            "user": {
                "id": "123",
                "credentials": {"password": "secret", "api_key": "key123"},
            }
        }
        result = redact_dict(data)
        assert result["user"]["id"] == "123"
        assert result["user"]["credentials"]["password"] == "[REDACTED]"
        assert result["user"]["credentials"]["api_key"] == "[REDACTED]"

    def test_redacts_biometric_array_in_list(self):
        """Biometric arrays in sensitive fields should be completely redacted."""
        # "voiceprint" is in SENSITIVE_FIELDS, so it's fully redacted
        data = {"voiceprint": [0.1] * 200}
        result = redact_dict(data)
        assert result["voiceprint"] == "[REDACTED]"

    def test_truncates_large_non_sensitive_arrays(self):
        """Large arrays in non-sensitive fields should be truncated with length info."""
        data = {"scores": [0.1] * 150}
        result = redact_dict(data)
        assert "ARRAY_TRUNCATED" in result["scores"]
        assert "len=150" in result["scores"]

    def test_handles_max_depth(self):
        """Should handle deeply nested structures without infinite loop."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep"}}}}}}}
        result = redact_dict(data)
        # Should complete without error and truncate at depth 5
        assert "_truncated" in str(result)

    def test_preserves_safe_fields(self):
        """Non-sensitive fields should be preserved."""
        data = {"request_id": "req-123", "status": "success", "timestamp": "2026-11-15"}
        result = redact_dict(data)
        assert result == data


class TestStructuredSecurityFormatter:
    """Tests for the StructuredSecurityFormatter."""

    @pytest.fixture
    def formatter(self):
        return StructuredSecurityFormatter()

    @pytest.fixture
    def logger(self, formatter):
        logger = logging.getLogger("test_security")
        logger.handlers = []
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def test_formats_as_json(self, formatter):
        """Output should be valid JSON."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed

    def test_redacts_sensitive_in_message(self, formatter):
        """Sensitive data in messages should be redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User password: secret123 logged in",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "secret123" not in parsed["message"]
        assert "[REDACTED]" in parsed["message"]

    def test_redacts_sensitive_in_extra(self, formatter):
        """Sensitive data in extra fields should be redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Auth attempt",
            args=(),
            exc_info=None,
        )
        record.extra = {"user_id": "123", "token": "secret-token"}
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "secret-token" not in str(parsed)

    def test_includes_timestamp(self, formatter):
        """Log entries should include ISO timestamp."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]  # ISO format


class TestIntegrationRedaction:
    """Integration tests for complete redaction flow."""

    def test_auth_log_redaction(self):
        """Full auth log should be properly redacted."""
        log_data = {
            "event": "authentication",
            "user_id": "user-123",
            "email": "test@example.com",
            "token": "Bearer abc123",
            "embedding": [0.1] * 192,
            "result": "success",
        }
        result = redact_dict(log_data)

        assert result["event"] == "authentication"
        assert result["user_id"] == "user-123"
        assert "test@example.com" not in str(result)
        assert result["token"] == "[REDACTED]"
        assert result["embedding"] == "[REDACTED]"
        assert result["result"] == "success"

    def test_verification_log_redaction(self):
        """Verification log should not leak biometrics or scores."""
        log_data = {
            "request_id": "req-456",
            "voiceprint": [0.2] * 192,
            "l1_score": 0.95,
            "l2_confidence": 0.88,
            "decision": "APPROVE",
            "password": "user-pass",
        }
        result = redact_dict(log_data)

        assert result["request_id"] == "req-456"
        assert result["voiceprint"] == "[REDACTED]"
        assert result["decision"] == "APPROVE"
        assert result["password"] == "[REDACTED]"
        # Scores are allowed (not in sensitive fields)
        assert result["l1_score"] == 0.95
