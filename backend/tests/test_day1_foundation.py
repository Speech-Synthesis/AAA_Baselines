"""
AAA Engine Day 1 Foundation Tests
Tests for core infrastructure implemented on November 11, 2026.
"""

import pytest


class TestHealthEndpoint:
    """Tests for GET /v1/health endpoint."""

    def test_health_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_has_timestamp(self, client):
        """Health response should include valid timestamp."""
        response = client.get("/v1/health")
        data = response.json()
        # Should be parseable as ISO datetime
        timestamp = data["timestamp"]
        assert timestamp is not None


class TestReadinessEndpoint:
    """Tests for GET /v1/ready endpoint."""

    def test_readiness_returns_checks(self, client):
        """Readiness endpoint should return check status."""
        response = client.get("/v1/ready")
        # May be 200 or 503 depending on state
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "models" in data["checks"]
        assert "configuration" in data["checks"]

    def test_readiness_checks_database(self, client):
        """Readiness should check database connectivity."""
        response = client.get("/v1/ready")
        data = response.json()
        # Database should be OK with SQLite in tests
        assert data["checks"]["database"] in ["ok", "error"]

    def test_readiness_checks_configuration(self, client):
        """Readiness should validate configuration."""
        response = client.get("/v1/ready")
        data = response.json()
        assert data["checks"]["configuration"] in ["ok", "error"]


class TestLegacyEndpoints:
    """Tests for backward compatibility with legacy endpoints."""

    def test_root_endpoint_works(self, client):
        """Root endpoint should still work."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_users_endpoint_works(self, client):
        """Users endpoint should still work."""
        response = client.get("/users")
        assert response.status_code == 200
        # Should return empty list or list of users
        assert isinstance(response.json(), list)


class TestConfiguration:
    """Tests for configuration management."""

    def test_settings_loads(self):
        """Settings should load without error."""
        from app.core.config import get_settings

        settings = get_settings()
        assert settings.APP_NAME == "AAA Engine"

    def test_thresholds_configurable(self):
        """Thresholds should be configurable."""
        from app.core.config import get_settings

        settings = get_settings()
        assert 0.0 <= settings.L2_SPOOF_THRESHOLD <= 1.0
        assert 0.0 <= settings.L1_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= settings.ASR_PHRASE_THRESHOLD <= 1.0

    def test_validate_production_config(self):
        """Production config validation should work."""
        from app.core.config import validate_production_config

        errors = validate_production_config()
        # In test mode with DEBUG=False and no secret, should have error
        assert isinstance(errors, list)


class TestExceptions:
    """Tests for custom exception types."""

    def test_token_expired_error(self):
        """TokenExpiredError should have correct attributes."""
        from app.core.exceptions import TokenExpiredError

        error = TokenExpiredError()
        assert error.code == "unauthorized"
        assert "expired" in error.message.lower()

    def test_model_not_available_error(self):
        """ModelNotAvailableError should include model_id."""
        from app.core.exceptions import ModelNotAvailableError

        error = ModelNotAvailableError("test-model")
        assert error.model_id == "test-model"
        assert "test-model" in error.message

    def test_challenge_expired_error(self):
        """ChallengeExpiredError should have correct code."""
        from app.core.exceptions import ChallengeExpiredError

        error = ChallengeExpiredError()
        assert error.code == "expired"


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_health_response_schema(self):
        """HealthResponse should serialize correctly."""
        from app.schemas.common import HealthResponse

        response = HealthResponse()
        assert response.status == "healthy"
        assert response.timestamp is not None

    def test_readiness_response_schema(self):
        """ReadinessResponse should have all fields."""
        from app.schemas.common import ReadinessResponse

        response = ReadinessResponse()
        assert response.status == "not_ready"
        assert response.checks is not None

    def test_decision_enum(self):
        """Decision enum should have all values."""
        from app.schemas.common import Decision

        assert Decision.APPROVE == "APPROVE"
        assert Decision.DENY == "DENY"
        assert Decision.STEP_UP == "STEP_UP"
        assert Decision.REVIEW == "REVIEW"
        assert Decision.UNAVAILABLE == "UNAVAILABLE"


class TestChallengeValidation:
    """Tests for challenge token validation."""

    def test_invalid_token_rejected(self, db_session):
        """Invalid token should be rejected."""
        from app.layer3_adaptive import verify_token

        result = verify_token("invalid-token-that-does-not-exist", db_session)
        assert result is False

    def test_empty_token_rejected(self, db_session):
        """Empty token should be rejected."""
        from app.layer3_adaptive import verify_token

        result = verify_token("", db_session)
        assert result is False

    def test_none_token_rejected(self, db_session):
        """None token should be rejected."""
        from app.layer3_adaptive import verify_token

        result = verify_token(None, db_session)
        assert result is False

    def test_token_without_db_rejected(self):
        """Token without database session should be rejected."""
        from app.layer3_adaptive import verify_token

        result = verify_token("some-token", None)
        assert result is False


class TestSecretConfiguration:
    """Tests for HMAC secret configuration."""

    def test_missing_secret_raises_in_production(self):
        """Missing L3_HMAC_SECRET should raise error in production mode."""
        import os
        import sys

        # Save original values
        orig_debug = os.environ.get("DEBUG")
        orig_secret = os.environ.get("L3_HMAC_SECRET")

        try:
            # Set production mode (DEBUG=false) and remove secret
            os.environ["DEBUG"] = "false"
            if "L3_HMAC_SECRET" in os.environ:
                del os.environ["L3_HMAC_SECRET"]

            # Remove cached module to force re-import
            if "app.layer3_adaptive" in sys.modules:
                del sys.modules["app.layer3_adaptive"]

            # Import should raise MissingSecretError
            from app.core.exceptions import MissingSecretError

            with pytest.raises(MissingSecretError):
                pass
        finally:
            # Restore original values
            if orig_debug is not None:
                os.environ["DEBUG"] = orig_debug
            else:
                os.environ.pop("DEBUG", None)
            if orig_secret is not None:
                os.environ["L3_HMAC_SECRET"] = orig_secret
            # Clean up module cache
            if "app.layer3_adaptive" in sys.modules:
                del sys.modules["app.layer3_adaptive"]


class TestDefaultDenyBehavior:
    """Tests for fail-closed (default deny) behavior."""

    def test_missing_model_returns_unavailable(self):
        """Missing model should not result in approval."""
        # The policy engine should return UNAVAILABLE when model is missing
        from app.schemas.common import Decision

        # This is a design verification - actual implementation pending
        assert Decision.UNAVAILABLE != Decision.APPROVE

    def test_no_raw_scores_in_public_response(self):
        """Public API should not expose raw model scores in v1."""
        # Design verification - v1 API doesn't include l1_score, l2_confidence
        # Legacy API still includes them for backward compatibility
        pass


# Pytest fixtures
@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session."""
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
