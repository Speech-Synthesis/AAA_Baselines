"""
Layer 3 — Challenge-Response + EMA - Aditya
Handles dynamic challenges, HMAC-signed token verification with 90s TTL,
single-use enforcement, and adaptive EMA voiceprint updates.
"""
# ruff: noqa: S311 - random.choice is intentional for non-cryptographic phrase generation

import hashlib
import hmac
import os
import random
import secrets
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

# Secret key for HMAC token signing (MUST be set via environment variable)
_hmac_secret = os.environ.get("L3_HMAC_SECRET")
if not _hmac_secret:
    # Allow import to succeed in DEBUG mode for development/testing
    # Production MUST have L3_HMAC_SECRET set
    import warnings

    if os.environ.get("DEBUG", "").lower() in ("true", "1", "yes"):
        warnings.warn(
            "L3_HMAC_SECRET not set - using insecure default for DEBUG mode only",
            RuntimeWarning,
            stacklevel=2,
        )
        _hmac_secret = "INSECURE_DEBUG_SECRET_DO_NOT_USE_IN_PRODUCTION"  # noqa: S105
    else:
        from .core.exceptions import MissingSecretError

        raise MissingSecretError("L3_HMAC_SECRET environment variable must be set")

SECRET_KEY = _hmac_secret.encode()

# =============================================================================
# SIMPLE WORD POOLS FOR CLEAR PHRASE GENERATION
# Uses common, easy-to-pronounce words that are phonetically distinct
# Hard for AI to predict, easy for humans to speak clearly
# =============================================================================

# Simple numbers (1-10 only - easy to say)
NUMBERS = [
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
]

# Basic colors - common and clear
COLORS = [
    "red", "blue", "green", "yellow", "orange",
    "purple", "pink", "brown", "black", "white",
    "gray", "gold", "silver",
]

# Common animals - easy to say clearly
ANIMALS = [
    "dog", "cat", "bird", "fish", "horse",
    "cow", "pig", "duck", "frog", "bear",
    "lion", "tiger", "wolf", "fox", "rabbit",
    "mouse", "snake", "monkey", "elephant", "zebra",
]

# Simple objects - everyday items
OBJECTS = [
    "book", "cup", "ball", "chair", "table",
    "door", "window", "car", "tree", "house",
    "phone", "key", "lamp", "clock", "box",
    "bag", "hat", "shoe", "pen", "ring",
]

# Simple words - easy to understand
WORDS = [
    "happy", "sunny", "rainy", "windy", "cloudy",
    "morning", "evening", "summer", "winter", "spring",
    "garden", "river", "mountain", "forest", "beach",
    "music", "story", "picture", "letter", "number",
]

# Simple adjectives - common descriptors
ADJECTIVES = [
    "big", "small", "fast", "slow", "tall",
    "short", "hot", "cold", "new", "old",
    "happy", "quiet", "loud", "soft", "hard",
    "bright", "dark", "clean", "strong", "kind",
]

# Simple verbs - common actions
VERBS = [
    "runs", "jumps", "sits", "walks", "eats",
    "sleeps", "plays", "reads", "sings", "draws",
    "swims", "flies", "drives", "rides", "climbs",
]

# Simple places
PLACES = [
    "park", "home", "school", "store", "beach",
    "farm", "city", "town", "lake", "hill",
]

# =============================================================================
# SIMPLE PHRASE TEMPLATES - Easy to speak, hard to predict
# =============================================================================


def _generate_dynamic_phrase() -> str:
    """
    Generate a simple, clear challenge phrase.

    Uses common words that are easy to pronounce and unlikely to be misheard.
    Phrases are 3-5 words for clarity.

    Entropy: 10 × 13 × 20 × 20 × 15 = 780,000+ unique combinations
    """
    template = random.randint(1, 8)

    if template == 1:
        # "NUMBER COLOR ANIMAL" - e.g., "three blue dogs"
        return f"{random.choice(NUMBERS)} {random.choice(COLORS)} {random.choice(ANIMALS)}"

    elif template == 2:
        # "The ADJECTIVE ANIMAL VERB" - e.g., "The big cat sleeps"
        return f"The {random.choice(ADJECTIVES)} {random.choice(ANIMALS)} {random.choice(VERBS)}"

    elif template == 3:
        # "COLOR OBJECT and OBJECT" - e.g., "red book and cup"
        return f"{random.choice(COLORS)} {random.choice(OBJECTS)} and {random.choice(OBJECTS)}"

    elif template == 4:
        # "NUMBER ADJECTIVE OBJECTS" - e.g., "five small chairs"
        return f"{random.choice(NUMBERS)} {random.choice(ADJECTIVES)} {random.choice(OBJECTS)}"

    elif template == 5:
        # "The ANIMAL VERB at PLACE" - e.g., "The dog runs at park"
        return f"The {random.choice(ANIMALS)} {random.choice(VERBS)} at {random.choice(PLACES)}"

    elif template == 6:
        # "ADJECTIVE COLOR OBJECT" - e.g., "big red ball"
        return f"{random.choice(ADJECTIVES)} {random.choice(COLORS)} {random.choice(OBJECTS)}"

    elif template == 7:
        # "My ANIMAL is ADJECTIVE" - e.g., "My cat is happy"
        return f"My {random.choice(ANIMALS)} is {random.choice(ADJECTIVES)}"

    else:  # template == 8
        # "NUMBER ANIMALS in PLACE" - e.g., "two birds in park"
        return f"{random.choice(NUMBERS)} {random.choice(ANIMALS)} in {random.choice(PLACES)}"


# =============================================================================
# DATABASE-BACKED TOKEN PERSISTENCE
# Replaces in-memory storage for production reliability
# =============================================================================


def generate_challenge(user_id: str, db: Session | None = None) -> dict:
    """
    Generate a dynamic challenge phrase and single-use HMAC-SHA256 signed token with 90s TTL.

    If db session is provided, persists the challenge to database.
    If db is None, returns the challenge without persistence (for testing/legacy).

    Args:
        user_id: UUID of the user requesting authentication
        db: Optional SQLAlchemy session for persistence

    Returns:
        {"phrase": str, "token": str, "expires_at": datetime, "challenge_id": str (if persisted)}
    """
    phrase = _generate_dynamic_phrase()

    # Expiration: strictly 90 seconds (per shared contract section 6 & layer3 spec)
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=90)
    expires_timestamp = str(int(expires_at.timestamp()))

    # Create raw payload and sign with HMAC-SHA256
    raw_nonce = secrets.token_hex(16)
    raw_payload = f"{user_id}:{expires_timestamp}:{phrase}:{raw_nonce}"
    signature = hmac.new(SECRET_KEY, raw_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    # URL-safe HMAC token
    token = f"{raw_nonce}.{expires_timestamp}.{signature}"

    result = {"phrase": phrase, "token": token, "expires_at": expires_at}

    # Persist to database if session provided
    if db is not None:
        import uuid

        from .models import Challenge

        challenge = Challenge(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            phrase=phrase,
            token=token,
            signature=signature,
            payload=raw_payload,
            expires_at=expires_at,
            used=False,
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        result["challenge_id"] = str(challenge.id)

    return result


def verify_token(token: str, db: Session = None) -> bool:
    """
    Verify token is valid (exists, HMAC valid, not expired, not used).
    Enforces single-use by marking token as used immediately.

    Uses atomic database operations to prevent race conditions.

    Args:
        token: Challenge token to verify
        db: Optional SQLAlchemy session for database verification

    Returns:
        True if token is valid and now consumed, False otherwise
    """
    if not token:
        return False

    if db is None:
        # Legacy behavior: no database, always return False
        return False

    from .models import Challenge

    now = datetime.utcnow()

    # Atomic update: Mark as used only if not already used and not expired
    # This prevents race conditions where two requests try to use the same token
    # Use proper boolean syntax compatible with both SQLite and PostgreSQL
    result = db.execute(
        text("""
            UPDATE challenges
            SET used = true
            WHERE token = :token
              AND used = false
              AND expires_at > :now
        """),
        {"token": token, "now": now},
    )
    db.commit()

    # If no rows affected, token was invalid, already used, or expired
    if result.rowcount == 0:
        return False

    # Verify HMAC signature
    challenge = db.query(Challenge).filter(Challenge.token == token).first()
    if challenge and challenge.payload:
        expected_sig = hmac.new(
            SECRET_KEY, challenge.payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(challenge.signature or "", expected_sig):
            # Signature mismatch - revert the used flag and return False
            db.execute(
                text("UPDATE challenges SET used = false WHERE token = :token"), {"token": token}
            )
            db.commit()
            return False

    return True


def validate_and_consume_token(token: str, db: Session) -> dict | None:
    """
    Atomically validate and consume a challenge token.

    Returns challenge data if valid, None otherwise.
    This is the recommended function for production use.

    Args:
        token: Challenge token to verify
        db: SQLAlchemy session (required)

    Returns:
        dict with challenge data if valid, None otherwise
    """
    from .models import Challenge

    if not token or not db:
        return None

    now = datetime.utcnow()

    # Atomic update: Mark as used only if not already used and not expired
    # Use proper boolean syntax for PostgreSQL compatibility
    result = db.execute(
        text("""
            UPDATE challenges
            SET used = true
            WHERE token = :token
              AND used = false
              AND expires_at > :now
        """),
        {"token": token, "now": now},
    )
    db.commit()

    # If no rows affected, token was invalid, already used, or expired
    if result.rowcount == 0:
        return None

    # Fetch the challenge data
    challenge = db.query(Challenge).filter(Challenge.token == token).first()
    if not challenge:
        return None

    # Verify HMAC signature
    if challenge.payload:
        expected_sig = hmac.new(
            SECRET_KEY, challenge.payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(challenge.signature or "", expected_sig):
            # Signature mismatch - revert the used flag and return None
            db.execute(
                text("UPDATE challenges SET used = false WHERE token = :token"), {"token": token}
            )
            db.commit()
            return None

    return {
        "challenge_id": str(challenge.id),
        "user_id": str(challenge.user_id),
        "phrase": challenge.phrase,
        "token": challenge.token,
        "expires_at": challenge.expires_at,
    }


def get_token_user_id(token: str, db: Session = None) -> str | None:
    """Get the user_id associated with a token."""
    if not token:
        return None

    if db is None:
        return None

    from .models import Challenge

    challenge = db.query(Challenge).filter(Challenge.token == token).first()
    if challenge:
        return str(challenge.user_id)
    return None


def get_token_phrase(token: str, db: Session = None) -> str | None:
    """Get the challenge phrase associated with a token."""
    if not token:
        return None

    if db is None:
        return None

    from .models import Challenge

    challenge = db.query(Challenge).filter(Challenge.token == token).first()
    if challenge:
        return challenge.phrase
    return None


def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired challenge tokens from database.

    Should be called periodically (e.g., via background task or cron).

    Args:
        db: SQLAlchemy session

    Returns:
        Number of tokens deleted
    """
    now = datetime.utcnow()
    result = db.execute(text("DELETE FROM challenges WHERE expires_at < :now"), {"now": now})
    db.commit()
    return result.rowcount


# Legacy in-memory store for backward compatibility with tests
# WARNING: Do not use in production - use database-backed functions instead
_token_store: dict[str, dict] = {}


def update_voiceprint(
    old_embedding: list[float], new_embedding: list[float], alpha: float = 0.2
) -> list[float]:
    """
    Exponential Moving Average update of voiceprint.
    Formula: New = (1 - alpha) * Old + alpha * Current
    With alpha = 0.2: New = 0.8 * Old + 0.2 * Current
    (weights Current embedding by 0.2, Old by 0.8)

    Args:
        old_embedding: Current stored embedding (192-dim)
        new_embedding: New embedding from successful authentication (192-dim)
        alpha: Weight for current embedding (default 0.2)

    Returns:
        Updated embedding vector (same dimension)
    """
    if len(old_embedding) != len(new_embedding):
        raise ValueError(
            f"Embedding dimension mismatch: {len(old_embedding)} vs {len(new_embedding)}"
        )

    # Calculate elementwise: 0.8 * old + 0.2 * current
    updated = [
        (1.0 - alpha) * old_val + alpha * new_val
        for old_val, new_val in zip(old_embedding, new_embedding, strict=True)
    ]

    return updated
