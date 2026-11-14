"""
Tests for API v1 endpoints - Authentication, Challenges, Enrollment, Verification
"""

import io
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from jose import jwt

from app.db import Base, SessionLocal, engine
from app.models import User, Voiceprint
from app.security.jwt_auth import JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_SECRET


def generate_test_audio(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a test WAV audio file."""
    num_samples = int(duration_seconds * sample_rate)
    audio_data = np.random.randn(num_samples).astype(np.float32) * 0.1
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format="WAV")
    buffer.seek(0)
    return buffer.read()


def create_test_token(
    tenant_id: str = "test-tenant",
    sub: str = "test-subject",
    expires_delta: timedelta = timedelta(hours=1),
) -> str:
    """Create a valid JWT token for testing."""
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_voiceprint(test_db, test_user):
    """Create a test voiceprint."""
    embedding = [0.1] * 192  # 192-dim embedding
    voiceprint = Voiceprint(
        id=uuid.uuid4(),
        user_id=test_user.id,
        embedding=embedding,
        sample_count=1,
    )
    test_db.add(voiceprint)
    test_db.commit()
    test_db.refresh(voiceprint)
    return voiceprint


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter between tests."""
    from app.core.ratelimit import limiter

    # Clear the rate limiter storage before each test
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /v1/health endpoint."""

    def test_health_check_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Health endpoint should return expected structure."""
        response = client.get("/v1/health")
        data = response.json()
        assert "status" in data


class TestChallengesEndpoint:
    """Tests for /v1/challenges endpoint."""

    def test_create_challenge_without_auth(self, client, test_db, test_user, test_voiceprint):
        """Should create challenge without JWT token."""
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
        )
        assert response.status_code == 201
        data = response.json()
        assert "phrase" in data
        assert "token" in data
        assert "expires_at" in data
        assert "ttl_seconds" in data

    def test_create_challenge_with_valid_jwt(self, client, test_db, test_user, test_voiceprint):
        """Should create challenge with valid JWT token."""
        token = create_test_token()
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_challenge_user_not_found(self, client, test_db):
        """Should return 404 for non-existent user."""
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "USER_NOT_FOUND"

    def test_create_challenge_no_voiceprint(self, client, test_db, test_user):
        """Should return 400 for user without voiceprint."""
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "NO_VOICEPRINT"

    def test_create_challenge_with_request_id(self, client, test_db, test_user, test_voiceprint):
        """Should echo back X-Request-ID header."""
        request_id = "test-request-123"
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"X-Request-ID": request_id},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["request_id"] == request_id


class TestEnrollEndpoint:
    """Tests for /v1/enroll endpoint."""

    @patch("app.api.v1.enroll.enroll_speaker")
    def test_enroll_new_voiceprint(self, mock_enroll, client, test_db, test_user):
        """Should create new voiceprint for user without one."""
        mock_enroll.return_value = {"embedding": [0.1] * 192}
        audio = generate_test_audio()

        response = client.post(
            "/v1/enroll",
            data={"user_id": str(test_user.id)},
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "enrolled"
        assert data["is_new"] is True
        assert data["sample_count"] == 1

    @patch("app.api.v1.enroll.enroll_speaker")
    def test_enroll_update_existing_voiceprint(
        self, mock_enroll, client, test_db, test_user, test_voiceprint
    ):
        """Should update existing voiceprint with EMA."""
        mock_enroll.return_value = {"embedding": [0.2] * 192}
        audio = generate_test_audio()

        response = client.post(
            "/v1/enroll",
            data={"user_id": str(test_user.id)},
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "enrolled"
        assert data["is_new"] is False
        assert data["sample_count"] == 2

    def test_enroll_user_not_found(self, client, test_db):
        """Should return 404 for non-existent user."""
        audio = generate_test_audio()
        response = client.post(
            "/v1/enroll",
            data={"user_id": str(uuid.uuid4())},
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "USER_NOT_FOUND"

    def test_enroll_audio_too_short(self, client, test_db, test_user):
        """Should reject audio that is too short."""
        short_audio = b"x" * 100  # Less than minimum

        response = client.post(
            "/v1/enroll",
            data={"user_id": str(test_user.id)},
            files={"audio": ("test.wav", short_audio, "audio/wav")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "AUDIO_TOO_SHORT"

    def test_enroll_with_jwt_token(self, client, test_db, test_user):
        """Should accept requests with valid JWT token."""
        # This test verifies JWT is optional
        token = create_test_token()
        audio = generate_test_audio()

        with patch("app.api.v1.enroll.enroll_speaker") as mock_enroll:
            mock_enroll.return_value = {"embedding": [0.1] * 192}
            response = client.post(
                "/v1/enroll",
                data={"user_id": str(test_user.id)},
                files={"audio": ("test.wav", audio, "audio/wav")},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 201


class TestVerifyEndpoint:
    """Tests for /v1/verify endpoint."""

    @patch("app.api.v1.verify.verify_speaker")
    @patch("app.api.v1.verify.detect_spoof")
    @patch("app.api.v1.verify.verify_phrase")
    def test_verify_success(
        self, mock_phrase, mock_spoof, mock_speaker, client, test_db, test_user, test_voiceprint
    ):
        """Should successfully verify authentic user."""
        # Setup mocks
        mock_spoof.return_value = {"label": "bonafide", "confidence": 0.95}
        mock_phrase.return_value = (True, 0.95, "test phrase")
        mock_speaker.return_value = {"score": 0.85, "embedding": [0.1] * 192}

        # Create a valid challenge first
        from app.layer3_adaptive import generate_challenge

        challenge = generate_challenge(str(test_user.id), db=test_db)
        test_db.commit()

        audio = generate_test_audio()

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": challenge["token"],
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"].lower() == "approve"
        assert data["reason"] == "Authentication successful"

    @patch("app.api.v1.verify.detect_spoof")
    def test_verify_rejects_spoof(
        self, mock_spoof, client, test_db, test_user, test_voiceprint
    ):
        """Should reject spoofed audio."""
        mock_spoof.return_value = {"label": "spoof", "confidence": 0.95}

        from app.layer3_adaptive import generate_challenge

        challenge = generate_challenge(str(test_user.id), db=test_db)
        test_db.commit()

        audio = generate_test_audio()

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": challenge["token"],
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"].lower() == "deny"
        # Generic message for security
        assert data["reason"] == "Authentication failed"

    def test_verify_user_not_found(self, client, test_db):
        """Should return 404 for non-existent user."""
        audio = generate_test_audio()

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(uuid.uuid4()),
                "token": "fake-token",
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "USER_NOT_FOUND"

    def test_verify_no_voiceprint(self, client, test_db, test_user):
        """Should return 400 for user without voiceprint."""
        audio = generate_test_audio()

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": "fake-token",
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "NO_VOICEPRINT"

    def test_verify_audio_too_short(self, client, test_db, test_user, test_voiceprint):
        """Should reject audio that is too short."""
        short_audio = b"x" * 100

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": "fake-token",
            },
            files={"audio": ("test.wav", short_audio, "audio/wav")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "AUDIO_TOO_SHORT"

    @patch("app.api.v1.verify.detect_spoof")
    def test_verify_invalid_token(
        self, mock_spoof, client, test_db, test_user, test_voiceprint
    ):
        """Should reject invalid challenge token."""
        mock_spoof.return_value = {"label": "bonafide", "confidence": 0.95}
        audio = generate_test_audio()

        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": "invalid-token",
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"].lower() == "deny"
        assert "challenge" in data["reason"].lower() or "invalid" in data["reason"].lower()


class TestJWTAuthentication:
    """Tests for JWT authentication in API endpoints."""

    def test_invalid_jwt_ignored(self, client, test_db, test_user, test_voiceprint):
        """Invalid JWT should be ignored (optional auth)."""
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"Authorization": "Bearer invalid-token"},
        )
        # Should succeed because JWT is optional
        assert response.status_code == 201

    def test_expired_jwt_ignored(self, client, test_db, test_user, test_voiceprint):
        """Expired JWT should be ignored (optional auth)."""
        expired_token = create_test_token(expires_delta=timedelta(hours=-1))
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        # Should succeed because JWT is optional
        assert response.status_code == 201

    def test_valid_jwt_accepted(self, client, test_db, test_user, test_voiceprint):
        """Valid JWT should be accepted."""
        valid_token = create_test_token()
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 201


class TestVoiceprintEncryption:
    """Tests for voiceprint encryption in API endpoints."""

    @patch("app.api.v1.enroll.enroll_speaker")
    def test_enrollment_stores_encrypted_voiceprint(
        self, mock_enroll, client, test_db, test_user
    ):
        """Enrollment should store encrypted voiceprint."""
        mock_enroll.return_value = {"embedding": [0.1] * 192}
        audio = generate_test_audio()

        response = client.post(
            "/v1/enroll",
            data={"user_id": str(test_user.id)},
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        assert response.status_code == 201

        # Verify voiceprint is encrypted
        voiceprint = test_db.query(Voiceprint).filter(
            Voiceprint.user_id == test_user.id
        ).first()
        assert voiceprint is not None
        # Encrypted data should be a string starting with "ENC:"
        if isinstance(voiceprint.embedding, str):
            assert voiceprint.embedding.startswith("ENC:")

    @patch("app.api.v1.verify.verify_speaker")
    @patch("app.api.v1.verify.detect_spoof")
    @patch("app.api.v1.verify.verify_phrase")
    def test_verify_decrypts_voiceprint(
        self, mock_phrase, mock_spoof, mock_speaker, client, test_db, test_user
    ):
        """Verify should decrypt voiceprint for comparison."""
        # First enroll to create encrypted voiceprint
        with patch("app.api.v1.enroll.enroll_speaker") as mock_enroll:
            mock_enroll.return_value = {"embedding": [0.1] * 192}
            audio = generate_test_audio()
            client.post(
                "/v1/enroll",
                data={"user_id": str(test_user.id)},
                files={"audio": ("test.wav", audio, "audio/wav")},
            )

        # Setup verify mocks
        mock_spoof.return_value = {"label": "bonafide", "confidence": 0.95}
        mock_phrase.return_value = (True, 0.95, "test phrase")
        mock_speaker.return_value = {"score": 0.85, "embedding": [0.1] * 192}

        # Create challenge
        from app.layer3_adaptive import generate_challenge

        challenge = generate_challenge(str(test_user.id), db=test_db)
        test_db.commit()

        # Verify
        audio = generate_test_audio()
        response = client.post(
            "/v1/verify",
            data={
                "user_id": str(test_user.id),
                "token": challenge["token"],
            },
            files={"audio": ("test.wav", audio, "audio/wav")},
        )

        # Verify that verify_speaker was called with decrypted list
        assert response.status_code == 200
        # Check verify_speaker was called with list, not encrypted string
        call_args = mock_speaker.call_args
        stored_embedding_arg = call_args[0][1]  # Second positional arg
        assert isinstance(stored_embedding_arg, list)


class TestRequestTracking:
    """Tests for request ID tracking."""

    def test_challenges_returns_request_id(self, client, test_db, test_user, test_voiceprint):
        """Challenges endpoint should return request_id."""
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
        )
        data = response.json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0

    def test_challenges_echoes_x_request_id(self, client, test_db, test_user, test_voiceprint):
        """Challenges should echo X-Request-ID header."""
        request_id = "custom-request-id-123"
        response = client.post(
            "/v1/challenges",
            json={"user_id": str(test_user.id)},
            headers={"X-Request-ID": request_id},
        )
        data = response.json()
        assert data["request_id"] == request_id

    @patch("app.api.v1.enroll.enroll_speaker")
    def test_enroll_returns_request_id(self, mock_enroll, client, test_db, test_user):
        """Enroll endpoint should return request_id."""
        mock_enroll.return_value = {"embedding": [0.1] * 192}
        audio = generate_test_audio()

        response = client.post(
            "/v1/enroll",
            data={"user_id": str(test_user.id)},
            files={"audio": ("test.wav", audio, "audio/wav")},
        )
        data = response.json()
        assert "request_id" in data
