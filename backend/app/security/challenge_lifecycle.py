"""
AAA Engine - Challenge Lifecycle Security Module
Target 2: Challenge State Machine, Capture Grants, and Atomic Consumption.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import hashlib
import hmac
import os
import secrets
import time
from enum import Enum
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt
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


VALID_TRANSITIONS: dict[ChallengeState, list[ChallengeState]] = {
    ChallengeState.CREATED: [
        ChallengeState.AUTHORIZED,
        ChallengeState.EXPIRED,
        ChallengeState.TERMINATED,
    ],
    ChallengeState.AUTHORIZED: [
        ChallengeState.CAPTURE_RECEIVED,
        ChallengeState.EXPIRED,
        ChallengeState.TERMINATED,
    ],
    ChallengeState.CAPTURE_RECEIVED: [
        ChallengeState.CONSUMED,
        ChallengeState.EXPIRED,
        ChallengeState.TERMINATED,
    ],
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
    secret_key: bytes | None = None,
    ttl_seconds: int = CHALLENGE_TTL_SECONDS,
) -> tuple[str, int]:
    """
    Generates a cryptographically signed, unguessable challenge token.
    Token format: {nonce}.{expires_timestamp}.{signature}
    """
    secret = (
        secret_key or os.environ.get("SECRET_KEY", "fallback-secret-for-signing-token!!").encode()
    )
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
    jwt_secret: str | None = None,
) -> str:
    """
    Issues a short-lived capture grant JWT authorizing single audio upload.
    Binds challenge_id as subject and 'aaa-capture' as audience.
    """
    secret = jwt_secret or os.environ.get(
        "AAA_JWT_SECRET", "default-fallback-key-32-characters-min!!"
    )
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
    jwt_secret: str | None = None,
) -> dict[str, Any]:
    """
    Validates a capture grant token against challenge and audience restrictions.
    """
    secret = jwt_secret or os.environ.get(
        "AAA_JWT_SECRET", "default-fallback-key-32-characters-min!!"
    )
    try:
        claims = jwt.decode(
            grant_token,
            secret,
            algorithms=["HS256"],
            audience=CAPTURE_GRANT_AUDIENCE,
        )
    except ExpiredSignatureError as err:
        raise ChallengeLifecycleError("CAPTURE_GRANT_EXPIRED") from err
    except (JWTClaimsError, JWTError) as err:
        raise ChallengeLifecycleError("INVALID_CAPTURE_GRANT") from err

    if claims.get("sub") != str(expected_challenge_id):
        raise ChallengeLifecycleError("CAPTURE_GRANT_CHALLENGE_MISMATCH")

    return claims


def validate_and_consume_challenge(
    token: str,
    stored_user_id: str,
    stored_phrase: str,
    current_state: ChallengeState,
    expires_at_ts: int,
    secret_key: bytes | None = None,
) -> tuple[ChallengeState, dict[str, Any]]:
    """
    Atomically validates HMAC signature, expiration, and enforces single-use semantics.
    Transitions state to CONSUMED upon success.
    """
    now_ts = int(time.time())

    # 1. Check TTL Expiration
    if now_ts > expires_at_ts or current_state == ChallengeState.EXPIRED:
        raise ChallengeLifecycleError("TOKEN_EXPIRED")

    # 2. Check Single-Use State (Anti-Replay)
    if current_state in (ChallengeState.CONSUMED, ChallengeState.COMPLETED):
        raise ChallengeLifecycleError("TOKEN_ALREADY_USED")

    if not can_transition(current_state, ChallengeState.CONSUMED):
        raise InvalidStateTransitionError(f"Cannot transition from {current_state} to CONSUMED")

    # 3. Parse Token
    parts = token.split(".")
    if len(parts) != 3:
        raise ChallengeLifecycleError("MALFORMED_TOKEN_STRUCTURE")

    nonce, exp_str, signature = parts
    try:
        token_exp = int(exp_str)
    except ValueError as err:
        raise ChallengeLifecycleError("INVALID_TOKEN_EXPIRATION") from err

    if now_ts > token_exp:
        raise ChallengeLifecycleError("TOKEN_EXPIRED")

    # 4. Constant-Time HMAC Signature Verification
    secret = (
        secret_key or os.environ.get("SECRET_KEY", "fallback-secret-for-signing-token!!").encode()
    )
    expected_payload = f"{stored_user_id}:{exp_str}:{stored_phrase}:{nonce}"
    expected_sig = hmac.new(secret, expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise ChallengeLifecycleError("INVALID_TOKEN_SIGNATURE")

    # 5. Atomic state update
    new_state = ChallengeState.CONSUMED
    metadata = {
        "nonce": nonce,
        "consumed_at": now_ts,
        "user_id": stored_user_id,
        "phrase": stored_phrase,
    }
    return new_state, metadata
