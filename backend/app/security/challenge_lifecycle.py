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


def issue_capture_grant(
    challenge_id: str,
    tenant_id: str,
    expires_at_ts: int,
    jwt_secret: Optional[str] = None,
) -> str:
    """
    Issues a short-lived capture grant JWT authorizing single audio upload.
    Binds challenge_id as subject and 'aaa-capture' as audience.
    """
    secret = jwt_secret or os.environ.get("AAA_JWT_SECRET", "default-fallback-key-32-characters-min!!")
    now_ts = int(time.time())
    payload = {
        "sub": str(challenge_id),
        "tenant_id": str(tenant_id),
        "aud": CAPTURE_GRANT_AUDIENCE,
        "iat": now_ts,
        "exp": expires_at_ts,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_capture_grant(
    grant_token: str,
    expected_challenge_id: str,
    jwt_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validates a capture grant token against challenge and audience restrictions.
    """
    secret = jwt_secret or os.environ.get("AAA_JWT_SECRET", "default-fallback-key-32-characters-min!!")
    try:
        claims = jwt.decode(
            grant_token,
            secret,
            algorithms=["HS256"],
            audience=CAPTURE_GRANT_AUDIENCE,
        )
    except ExpiredSignatureError:
        raise ChallengeLifecycleError("CAPTURE_GRANT_EXPIRED")
    except (JWTClaimsError, JWTError):
        raise ChallengeLifecycleError("INVALID_CAPTURE_GRANT")

    if claims.get("sub") != str(expected_challenge_id):
        raise ChallengeLifecycleError("CAPTURE_GRANT_CHALLENGE_MISMATCH")

    return claims
