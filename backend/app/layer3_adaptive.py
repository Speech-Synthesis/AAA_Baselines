"""
Layer 3 — Challenge-Response + EMA - Aditya
Handles dynamic challenges, HMAC-signed token verification with 90s TTL,
single-use enforcement, and adaptive EMA voiceprint updates.
"""

import os
import secrets
import hmac
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional

# Secret key for HMAC token signing (can be loaded from environment)
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026").encode()

# Dynamic challenge templates & word pools
NUMBERS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
COLOURS = ["red", "blue", "green", "amber", "silver", "crimson", "golden", "violet"]
OBJECTS = ["falcon", "phoenix", "panther", "sapphire", "nexus", "echo", "matrix", "shield"]

STATIC_PHRASES = [
    "The quick brown fox jumps over the lazy dog",
    "My voice is my secure biometric key",
    "Authenticate me with this adaptive challenge phrase",
    "Zero trust voice verification protocol",
    "Security verification in progress now",
]

# In-memory token store: maps token_str -> token_metadata
_token_store: dict[str, dict] = {}


def _generate_dynamic_phrase() -> str:
    """Generate dynamic randomized phrase e.g. 'Say: 7 Crimson Falcon 4' or static challenge."""
    if random.random() < 0.6:
        n1 = random.choice(NUMBERS)
        col = random.choice(COLOURS)
        obj = random.choice(OBJECTS)
        n2 = random.choice(NUMBERS)
        return f"Say: {n1} {col} {obj} {n2}"
    return random.choice(STATIC_PHRASES)


def generate_challenge(user_id: str) -> dict:
    """
    Generate a dynamic challenge phrase and single-use HMAC-SHA256 signed token with 90s TTL.

    Args:
        user_id: UUID of the user requesting authentication

    Returns:
        {"phrase": str, "token": str, "expires_at": datetime}
    """
    phrase = _generate_dynamic_phrase()
    
    # Expiration: strictly 90 seconds (per shared contract section 6 & layer3 spec)
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=90)
    expires_timestamp = str(int(expires_at.timestamp()))
    
    # Create raw payload and sign with HMAC-SHA256
    raw_nonce = secrets.token_hex(16)
    raw_payload = f"{user_id}:{expires_timestamp}:{phrase}:{raw_nonce}"
    signature = hmac.new(SECRET_KEY, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # URL-safe HMAC token
    token = f"{raw_nonce}.{expires_timestamp}.{signature}"

    # Store token for single-use & tracking
    _token_store[token] = {
        "user_id": user_id,
        "phrase": phrase,
        "expires_at": expires_at,
        "payload": raw_payload,
        "signature": signature,
        "used": False
    }

    return {
        "phrase": phrase,
        "token": token,
        "expires_at": expires_at
    }


def verify_token(token: str) -> bool:
    """
    Verify token is valid (exists, HMAC valid, not expired, not used).
    Enforces single-use by marking token as used immediately.

    Args:
        token: Challenge token to verify

    Returns:
        True if token is valid and now consumed, False otherwise
    """
    if not token or token not in _token_store:
        return False

    token_data = _token_store[token]

    # 1. Single-use check
    if token_data.get("used", False):
        return False

    # 2. TTL Expiration check (90s limit)
    now = datetime.utcnow()
    if now > token_data["expires_at"]:
        # Remove expired token
        del _token_store[token]
        return False

    # 3. HMAC Signature integrity check
    raw_payload = token_data.get("payload", "")
    expected_sig = hmac.new(SECRET_KEY, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token_data.get("signature", ""), expected_sig):
        return False

    # Consume token (single-use enforcement)
    token_data["used"] = True

    return True


def get_token_user_id(token: str) -> Optional[str]:
    """Get the user_id associated with a token."""
    if token in _token_store:
        return _token_store[token]["user_id"]
    return None


def update_voiceprint(
    old_embedding: list[float],
    new_embedding: list[float],
    alpha: float = 0.2
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
        for old_val, new_val in zip(old_embedding, new_embedding)
    ]

    return updated

