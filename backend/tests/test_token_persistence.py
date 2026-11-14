"""
AAA Engine Token Persistence Tests
Tests for database-backed challenge token lifecycle.
"""

import uuid
from datetime import datetime, timedelta


class TestChallengeGeneration:
    """Tests for challenge generation with database persistence."""

    def test_generate_challenge_without_db(self):
        """Challenge generation works without database (legacy mode)."""
        from app.layer3_adaptive import generate_challenge

        user_id = str(uuid.uuid4())
        result = generate_challenge(user_id)

        assert "phrase" in result
        assert "token" in result
        assert "expires_at" in result
        assert "challenge_id" not in result  # No DB, no ID

    def test_generate_challenge_with_db(self, db_session):
        """Challenge generation persists to database."""
        from app.layer3_adaptive import generate_challenge
        from app.models import Challenge, User

        # Create a test user first
        user = User(id=uuid.uuid4(), name="Test User", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        assert "phrase" in result
        assert "token" in result
        assert "expires_at" in result
        assert "challenge_id" in result

        # Verify in database
        challenge = db_session.query(Challenge).filter(Challenge.token == result["token"]).first()
        assert challenge is not None
        assert challenge.phrase == result["phrase"]
        assert challenge.used is False

    def test_challenge_has_unique_phrase(self, db_session):
        """Each challenge should have a unique phrase."""
        from app.layer3_adaptive import generate_challenge
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        # Generate 10 challenges
        phrases = set()
        for _ in range(10):
            result = generate_challenge(str(user.id), db_session)
            phrases.add(result["phrase"])

        # With millions of combinations, 10 should all be unique
        assert len(phrases) == 10

    def test_challenge_expires_in_90_seconds(self, db_session):
        """Challenge should expire in exactly 90 seconds."""
        from app.layer3_adaptive import generate_challenge
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        before = datetime.utcnow()
        result = generate_challenge(str(user.id), db_session)
        after = datetime.utcnow()

        # Expiration should be within 90 seconds (+/- 1 second tolerance)
        expected_min = before + timedelta(seconds=89)
        expected_max = after + timedelta(seconds=91)

        assert expected_min <= result["expires_at"] <= expected_max


class TestTokenVerification:
    """Tests for token verification with database."""

    def test_valid_token_accepted(self, db_session):
        """Valid token should be accepted and consumed."""
        from app.layer3_adaptive import generate_challenge, verify_token
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        # Token should be valid
        assert verify_token(result["token"], db_session) is True

    def test_token_single_use(self, db_session):
        """Token should only be usable once (replay prevention)."""
        from app.layer3_adaptive import generate_challenge, verify_token
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        # First use should succeed
        assert verify_token(result["token"], db_session) is True

        # Second use should fail (replay attack)
        assert verify_token(result["token"], db_session) is False

    def test_expired_token_rejected(self, db_session):
        """Expired token should be rejected."""
        from app.layer3_adaptive import generate_challenge, verify_token
        from app.models import Challenge, User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        # Manually expire the token
        challenge = db_session.query(Challenge).filter(Challenge.token == result["token"]).first()
        challenge.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db_session.commit()

        # Expired token should be rejected
        assert verify_token(result["token"], db_session) is False

    def test_invalid_token_rejected(self, db_session):
        """Invalid token should be rejected."""
        from app.layer3_adaptive import verify_token

        assert verify_token("totally-fake-token", db_session) is False
        assert verify_token("", db_session) is False
        assert verify_token(None, db_session) is False


class TestValidateAndConsumeToken:
    """Tests for the validate_and_consume_token function."""

    def test_returns_challenge_data(self, db_session):
        """Should return challenge data for valid token."""
        from app.layer3_adaptive import generate_challenge, validate_and_consume_token
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        challenge_data = validate_and_consume_token(result["token"], db_session)

        assert challenge_data is not None
        assert challenge_data["user_id"] == str(user.id)
        assert challenge_data["phrase"] == result["phrase"]
        assert challenge_data["challenge_id"] == result["challenge_id"]

    def test_returns_none_for_invalid(self, db_session):
        """Should return None for invalid token."""
        from app.layer3_adaptive import validate_and_consume_token

        assert validate_and_consume_token("fake-token", db_session) is None
        assert validate_and_consume_token("", db_session) is None
        assert validate_and_consume_token(None, db_session) is None

    def test_returns_none_for_replay(self, db_session):
        """Should return None for replay attempt."""
        from app.layer3_adaptive import generate_challenge, validate_and_consume_token
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        # First call succeeds
        assert validate_and_consume_token(result["token"], db_session) is not None

        # Replay fails
        assert validate_and_consume_token(result["token"], db_session) is None


class TestTokenCleanup:
    """Tests for expired token cleanup."""

    def test_cleanup_removes_expired(self, db_session):
        """Cleanup should remove expired tokens."""
        from app.layer3_adaptive import cleanup_expired_tokens, generate_challenge
        from app.models import Challenge, User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        # Create a challenge and expire it
        result = generate_challenge(str(user.id), db_session)
        challenge = db_session.query(Challenge).filter(Challenge.token == result["token"]).first()
        challenge.expires_at = datetime.utcnow() - timedelta(seconds=100)
        db_session.commit()

        # Run cleanup
        deleted = cleanup_expired_tokens(db_session)

        assert deleted >= 1

        # Verify it's gone
        remaining = db_session.query(Challenge).filter(Challenge.token == result["token"]).first()
        assert remaining is None

    def test_cleanup_preserves_valid(self, db_session):
        """Cleanup should preserve valid tokens."""
        from app.layer3_adaptive import cleanup_expired_tokens, generate_challenge
        from app.models import Challenge, User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        # Create a valid challenge
        result = generate_challenge(str(user.id), db_session)

        # Run cleanup
        cleanup_expired_tokens(db_session)

        # Valid token should still exist
        remaining = db_session.query(Challenge).filter(Challenge.token == result["token"]).first()
        assert remaining is not None


class TestTokenHelperFunctions:
    """Tests for get_token_user_id and get_token_phrase."""

    def test_get_token_user_id(self, db_session):
        """Should return user_id for valid token."""
        from app.layer3_adaptive import generate_challenge, get_token_user_id
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        assert get_token_user_id(result["token"], db_session) == str(user.id)

    def test_get_token_phrase(self, db_session):
        """Should return phrase for valid token."""
        from app.layer3_adaptive import generate_challenge, get_token_phrase
        from app.models import User

        user = User(id=uuid.uuid4(), name="Test", email=f"test_{uuid.uuid4()}@example.com")
        db_session.add(user)
        db_session.commit()

        result = generate_challenge(str(user.id), db_session)

        assert get_token_phrase(result["token"], db_session) == result["phrase"]

    def test_returns_none_for_invalid(self, db_session):
        """Should return None for invalid tokens."""
        from app.layer3_adaptive import get_token_phrase, get_token_user_id

        assert get_token_user_id("fake-token", db_session) is None
        assert get_token_phrase("fake-token", db_session) is None

    def test_returns_none_without_db(self):
        """Should return None without database session."""
        from app.layer3_adaptive import get_token_phrase, get_token_user_id

        assert get_token_user_id("any-token", None) is None
        assert get_token_phrase("any-token", None) is None
