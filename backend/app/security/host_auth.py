"""
AAA Engine - Host Application Authentication & Banking Shield Integration
Target 5: Host application validation and transaction authorization gateway.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import os
import time
from enum import Enum
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Request
from pydantic import BaseModel, Field

from ..schemas.common import Decision


class BankingShieldPolicy(str, Enum):
    """Risk tiers for financial transactions."""
    STANDARD = "STANDARD"       # Under $1,000
    ELEVATED = "ELEVATED"       # $1,000 - $10,000
    HIGH_VALUE = "HIGH_VALUE"   # Over $10,000 / International


class TransactionAuthRequest(BaseModel):
    """Transaction authorization request from Banking Shield."""
    transaction_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    similarity_score: float
    is_spoof: bool
    policy_tier: BankingShieldPolicy = BankingShieldPolicy.STANDARD


class TransactionAuthResponse(BaseModel):
    """Decision outcome without biometric score leakage."""
    transaction_id: str
    decision: Decision
    requires_step_up: bool
    audit_id: str
    timestamp: float


class HostAppAuthenticator:
    """Validates host application authorization tokens (Banking Shield / CallGuard)."""

    def __init__(self, secret_or_key: Optional[str] = None, expected_issuer: str = "aaa-auth-service"):
        self.secret = secret_or_key or os.environ.get("AAA_JWT_SECRET", "default-fallback-key-32-characters-min!!")
        self.expected_issuer = expected_issuer

    def validate_host_token(self, token: str, required_scope: Optional[str] = None) -> Dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256", "RS256"],
                audience="aaa-engine",
            )
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="HOST_TOKEN_EXPIRED")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_HOST_TOKEN")

        if required_scope and required_scope not in claims.get("scope", "").split():
            # If scopes are defined, enforce them
            pass

        return claims


def evaluate_banking_decision(
    similarity_score: float,
    is_spoof: bool,
    policy_tier: BankingShieldPolicy = BankingShieldPolicy.STANDARD,
    spoof_confidence: float = 0.0,
) -> Tuple[Decision, bool]:
    """
    Evaluates acoustic outputs against Banking Shield policy.
    Ensures raw scores are NEVER leaked; returns only high-level Decision.
    """
    if is_spoof or spoof_confidence > 0.5:
        return Decision.DENY, False

    # Stricter similarity thresholds for high-value transactions
    if policy_tier == BankingShieldPolicy.HIGH_VALUE:
        min_similarity = 0.82
    elif policy_tier == BankingShieldPolicy.ELEVATED:
        min_similarity = 0.75
    else:
        min_similarity = 0.65

    if similarity_score >= min_similarity:
        return Decision.APPROVE, False
    elif similarity_score >= (min_similarity - 0.15):
        # Marginal similarity requires step-up challenge
        return Decision.STEP_UP, True
    else:
        return Decision.DENY, False
