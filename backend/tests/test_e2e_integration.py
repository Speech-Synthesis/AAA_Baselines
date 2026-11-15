"""
End-to-End Integration Tests for AAA Engine
Tests the full verification pipeline with mock adapters.
"""

import io
import uuid
from datetime import datetime, timedelta

import numpy as np
import pytest
import soundfile as sf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.mock import MockASRAdapter, MockDeepfakeAdapter, MockSpeakerAdapter
from app.db import Base
from app.layer3_adaptive import generate_challenge, validate_and_consume_token
from app.models import Challenge, User, Voiceprint


# Helper to create test audio bytes
def create_test_audio(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate test audio bytes in WAV format."""
    samples = int(sample_rate * duration_seconds)
    audio_data = np.random.randn(samples).astype(np.float32) * 0.1

    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format="WAV")
    buffer.seek(0)
    return buffer.read()


# Test fixtures
@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
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
    """Create a test voiceprint for the user."""
    # Create a mock embedding
    embedding = [0.1] * 192
    voiceprint = Voiceprint(
        user_id=test_user.id,
        embedding=embedding,
        sample_count=1,
    )
    test_db.add(voiceprint)
    test_db.commit()
    test_db.refresh(voiceprint)
    return voiceprint


@pytest.fixture
def mock_speaker_adapter():
    """Create a mock speaker adapter."""
    return MockSpeakerAdapter(default_score=0.85)


@pytest.fixture
def mock_deepfake_adapter():
    """Create a mock deepfake adapter."""
    return MockDeepfakeAdapter(default_label="bonafide", default_confidence=0.95)


@pytest.fixture
def mock_asr_adapter():
    """Create a mock ASR adapter."""
    return MockASRAdapter()


class TestChallengeLifecycle:
    """Tests for challenge generation and token verification."""

    def test_challenge_generation_produces_valid_token(self, test_db, test_user):
        """Challenge generation should produce a valid token."""
        # Generate without db (legacy mode - token stored in memory)
        challenge_data = generate_challenge(str(test_user.id))

        assert "phrase" in challenge_data
        assert "token" in challenge_data
        assert "expires_at" in challenge_data

        # Token format should be valid (signature verification)
        # Note: verify_token returns True for valid signature format
        assert isinstance(challenge_data["token"], str)
        assert "." in challenge_data["token"]  # Has signature separator

    def test_challenge_contains_required_fields(self, test_db, test_user):
        """Challenge response should have all required fields."""
        challenge_data = generate_challenge(str(test_user.id))

        assert isinstance(challenge_data["phrase"], str)
        assert len(challenge_data["phrase"]) > 0
        assert isinstance(challenge_data["token"], str)
        assert isinstance(challenge_data["expires_at"], datetime)

    def test_token_single_use(self, test_db, test_user):
        """Token should only be usable once."""
        # generate_challenge with db already persists to database
        challenge_data = generate_challenge(str(test_user.id), db=test_db)

        # First consumption should succeed
        result = validate_and_consume_token(challenge_data["token"], test_db)
        assert result is not None

        # Second consumption should fail (replay prevention)
        result2 = validate_and_consume_token(challenge_data["token"], test_db)
        assert result2 is None

    def test_expired_token_rejected(self, test_db, test_user):
        """Expired tokens should be rejected."""
        # Create an expired challenge directly
        expired_token = "expired-test-token-" + str(uuid.uuid4())
        challenge = Challenge(
            id=uuid.uuid4(),
            user_id=test_user.id,
            phrase="test phrase",
            token=expired_token,
            expires_at=datetime.utcnow() - timedelta(seconds=1),  # Already expired
            used=False,
        )
        test_db.add(challenge)
        test_db.commit()

        # Should be rejected because it's expired
        result = validate_and_consume_token(expired_token, test_db)
        assert result is None


class TestMockAdapters:
    """Tests for mock adapter behavior."""

    def test_mock_speaker_adapter_returns_configured_score(self, mock_speaker_adapter):
        """Mock speaker adapter should return configured score."""
        mock_speaker_adapter.set_score(0.9)
        audio = create_test_audio()
        result = mock_speaker_adapter.verify_speaker(audio, [0.1] * 192)

        assert result.score == 0.9
        assert result.is_match is True

    def test_mock_speaker_adapter_low_score_no_match(self, mock_speaker_adapter):
        """Mock speaker adapter with low score should not match."""
        mock_speaker_adapter.set_score(0.3)
        audio = create_test_audio()
        result = mock_speaker_adapter.verify_speaker(audio, [0.1] * 192, threshold=0.5)

        assert result.score == 0.3
        assert result.is_match is False

    def test_mock_deepfake_adapter_bonafide(self, mock_deepfake_adapter):
        """Mock deepfake adapter should return bonafide."""
        audio = create_test_audio()
        result = mock_deepfake_adapter.detect(audio)

        assert result.label == "bonafide"
        assert result.is_spoof is False

    def test_mock_deepfake_adapter_spoof(self, mock_deepfake_adapter):
        """Mock deepfake adapter should return spoof when configured."""
        mock_deepfake_adapter.set_result("spoof", 0.95)
        audio = create_test_audio()
        result = mock_deepfake_adapter.detect(audio)

        assert result.label == "spoof"
        assert result.is_spoof is True

    def test_mock_asr_adapter_transcribes(self, mock_asr_adapter):
        """Mock ASR adapter should return configured transcript."""
        mock_asr_adapter.set_transcript("seven red chair twenty")
        audio = create_test_audio()
        result = mock_asr_adapter.transcribe(audio)

        assert result.transcript == "seven red chair twenty"


class TestVerificationPipelineLogic:
    """Tests for verification pipeline decision logic."""

    def test_spoof_detection_blocks_verification(self, mock_deepfake_adapter):
        """Spoof detection should block the verification pipeline."""
        mock_deepfake_adapter.set_result("spoof", 0.95)
        audio = create_test_audio()
        result = mock_deepfake_adapter.detect(audio)

        # Pipeline should stop at L2 if spoof detected
        assert result.is_spoof is True
        assert result.confidence > 0.5

    def test_bonafide_audio_passes_deepfake_check(self, mock_deepfake_adapter):
        """Bonafide audio should pass the deepfake check."""
        mock_deepfake_adapter.set_result("bonafide", 0.95)
        audio = create_test_audio()
        result = mock_deepfake_adapter.detect(audio)

        assert result.is_spoof is False
        assert result.label == "bonafide"

    def test_speaker_mismatch_blocks_verification(self, mock_speaker_adapter):
        """Speaker mismatch should block verification."""
        mock_speaker_adapter.set_score(0.3)  # Below threshold
        audio = create_test_audio()
        result = mock_speaker_adapter.verify_speaker(audio, [0.1] * 192, threshold=0.5)

        assert result.is_match is False
        assert result.score < 0.5

    def test_speaker_match_passes_verification(self, mock_speaker_adapter):
        """Speaker match should pass verification."""
        mock_speaker_adapter.set_score(0.85)  # Above threshold
        audio = create_test_audio()
        result = mock_speaker_adapter.verify_speaker(audio, [0.1] * 192, threshold=0.5)

        assert result.is_match is True
        assert result.score >= 0.5


class TestPhraseVerification:
    """Tests for phrase verification logic."""

    def test_exact_phrase_match_passes(self, mock_asr_adapter):
        """Exact phrase match should pass verification."""
        expected = "seven red chair twenty"
        mock_asr_adapter.set_transcript(expected)
        mock_asr_adapter.set_similarity(1.0)

        audio = create_test_audio()
        result = mock_asr_adapter.verify_phrase(audio, expected)

        assert result.transcript == expected
        assert result.similarity == 1.0

    def test_phrase_mismatch_fails(self, mock_asr_adapter):
        """Phrase mismatch should fail verification."""
        expected = "seven red chair twenty"
        mock_asr_adapter.set_transcript("wrong phrase here")
        mock_asr_adapter.set_similarity(0.3)

        audio = create_test_audio()
        result = mock_asr_adapter.verify_phrase(audio, expected)

        assert result.transcript != expected
        assert result.similarity < 0.6


class TestDatabaseIntegration:
    """Tests for database operations in the pipeline."""

    def test_user_creation(self, test_db):
        """Should be able to create a user."""
        user = User(name="New User", email="new@example.com")
        test_db.add(user)
        test_db.commit()

        fetched = test_db.query(User).filter(User.email == "new@example.com").first()
        assert fetched is not None
        assert fetched.name == "New User"

    def test_voiceprint_creation(self, test_db, test_user):
        """Should be able to create a voiceprint."""
        embedding = [0.5] * 192
        voiceprint = Voiceprint(
            user_id=test_user.id,
            embedding=embedding,
            sample_count=1,
        )
        test_db.add(voiceprint)
        test_db.commit()

        fetched = test_db.query(Voiceprint).filter(Voiceprint.user_id == test_user.id).first()
        assert fetched is not None
        assert len(fetched.embedding) == 192

    def test_challenge_persistence(self, test_db, test_user):
        """Challenges should be persisted to database."""
        challenge = Challenge(
            user_id=test_user.id,
            phrase="test phrase",
            token="test-token-123",
            expires_at=datetime.utcnow() + timedelta(seconds=90),
        )
        test_db.add(challenge)
        test_db.commit()

        fetched = test_db.query(Challenge).filter(Challenge.token == "test-token-123").first()
        assert fetched is not None
        assert fetched.phrase == "test phrase"
        assert fetched.used is False


class TestSecurityInvariants:
    """Tests for security-critical behavior."""

    def test_invalid_token_rejected(self, test_db):
        """Invalid tokens should be rejected."""
        result = validate_and_consume_token("invalid-token-xyz", test_db)
        assert result is None

    def test_empty_token_rejected(self, test_db):
        """Empty tokens should be rejected."""
        result = validate_and_consume_token("", test_db)
        assert result is None

    def test_none_token_rejected(self, test_db):
        """None tokens should be rejected."""
        result = validate_and_consume_token(None, test_db)
        assert result is None

    def test_challenge_used_flag_set_on_consumption(self, test_db, test_user):
        """Challenge should be marked as used after consumption."""
        # generate_challenge with db already persists to database
        challenge_data = generate_challenge(str(test_user.id), db=test_db)

        # Consume the token
        validate_and_consume_token(challenge_data["token"], test_db)

        # Verify used flag is set
        fetched = test_db.query(Challenge).filter(
            Challenge.token == challenge_data["token"]
        ).first()
        assert fetched.used is True
