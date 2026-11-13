"""
AAA Engine - Challenge Lifecycle Security Module
Target 2: Challenge State Machine, Capture Grants, and Atomic Consumption.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import os
import time
import uuid
import hmac
import hashlib
import secrets
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone

from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError

CHALLENGE_TTL_SECONDS = 90
CAPTURE_GRANT_AUDIENCE = "aaa-capture"


class ChallengeState(str, Enum):
    """Lifecycle states of an acoustic authentication challenge."""
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURE_RECEIVED = "CAPTURE_RECEIVED"
    CONSUMED = "CONSUMED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


class ChallengeLifecycleError(Exception):
    """Base exception for challenge lifecycle failures."""
    pass


class InvalidStateTransitionError(ChallengeLifecycleError):
    """Raised when an invalid state transition is attempted."""
    pass


VALID_TRANSITIONS: Dict[ChallengeState, List[ChallengeState]] = {
    ChallengeState.CREATED: [ChallengeState.AUTHORIZED, ChallengeState.EXPIRED, ChallengeState.TERMINATED],
    ChallengeState.AUTHORIZED: [ChallengeState.CAPTURE_RECEIVED, ChallengeState.EXPIRED, ChallengeState.TERMINATED],
    ChallengeState.CAPTURE_RECEIVED: [ChallengeState.CONSUMED, ChallengeState.EXPIRED, ChallengeState.TERMINATED],
    ChallengeState.CONSUMED: [ChallengeState.COMPLETED, ChallengeState.TERMINATED],
    ChallengeState.EXPIRED: [ChallengeState.TERMINATED],
    ChallengeState.COMPLETED: [],
    ChallengeState.TERMINATED: [],
}


def can_transition(current_state: ChallengeState, new_state: ChallengeState) -> bool:
    """Verifies whether transition from current_state to new_state is permissible."""
    return new_state in VALID_TRANSITIONS.get(current_state, [])


def generate_challenge_token(
    user_id: str,
    phrase: str,
    secret_key: Optional[bytes] = None,
    ttl_seconds: int = CHALLENGE_TTL_SECONDS,
) -> Tuple[str, int]:
    """
    Generates a cryptographically signed, unguessable challenge token.
    Token format: {nonce}.{expires_timestamp}.{signature}
    """
    secret = secret_key or os.environ.get("SECRET_KEY", "fallback-secret-for-signing-token!!").encode()
    now_ts = int(time.time())
    expires_ts = now_ts + ttl_seconds
    nonce = secrets.token_hex(16)  # 32 hex characters

    payload = f"{user_id}:{expires_ts}:{phrase}:{nonce}"
    signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    token = f"{nonce}.{expires_ts}.{signature}"

    return token, expires_ts
