"""
Layer 3 — Challenge-Response + EMA - Aditya
Handles dynamic challenges, token verification, and voiceprint updates
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

# Challenge phrases pool (can be expanded)
CHALLENGE_PHRASES = [
    "The quick brown fox jumps over the lazy dog",
    "Please verify my identity now",
    "My voice is my password",
    "Authenticate me with this phrase",
    "Security verification in progress",
    "The weather is nice today",
    "I confirm this is my voice",
    "Random numbers seven four two",
    "Blue sky and green grass",
    "Voice authentication enabled",
]

# In-memory token store (Phase 1)
# Phase 2: Use Redis or database for distributed systems
_token_store: dict[str, dict] = {}


def generate_challenge(user_id: str) -> dict:
    """
    Generate a random challenge phrase and single-use token.

    Args:
        user_id: UUID of the user requesting authentication

    Returns:
        {"phrase": str, "token": str, "expires_at": datetime}
    """
    import random

    phrase = random.choice(CHALLENGE_PHRASES)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Store token for verification
    _token_store[token] = {
        "user_id": user_id,
        "phrase": phrase,
        "expires_at": expires_at,
        "used": False
    }

    return {
        "phrase": phrase,
        "token": token,
        "expires_at": expires_at
    }


def verify_token(token: str) -> bool:
    """
    Verify token is valid (exists, not expired, not used).
    Marks token as used if valid.

    Args:
        token: Challenge token to verify

    Returns:
        True if token is valid and now consumed, False otherwise
    """
    if token not in _token_store:
        return False

    token_data = _token_store[token]

    # Check expiration
    if datetime.utcnow() > token_data["expires_at"]:
        del _token_store[token]
        return False

    # Check if already used
    if token_data["used"]:
        return False

    # Mark as used (single-use)
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
    new_voiceprint = (1 - alpha) * old + alpha * new

    Default alpha=0.2 means:
    - 80% weight to existing voiceprint (stability)
    - 20% weight to new sample (adaptation)

    Args:
        old_embedding: Current stored 192-dim embedding
        new_embedding: New 192-dim embedding from successful auth
        alpha: Learning rate (0.0-1.0), default 0.2

    Returns:
        Updated 192-dim embedding
    """
    if len(old_embedding) != len(new_embedding):
        raise ValueError(
            f"Embedding dimension mismatch: {len(old_embedding)} vs {len(new_embedding)}"
        )

    updated = [
        (1 - alpha) * old + alpha * new
        for old, new in zip(old_embedding, new_embedding)
    ]

    return updated
