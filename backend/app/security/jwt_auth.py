"""
AAA Engine - Security & JWT Authentication Module
Module Purpose: API perimeter defense, tenant isolation, and strict client authentication for the AAA Middleware.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import os
import time
import uuid
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError

load_dotenv()

logger = logging.getLogger("aaa_engine.security.jwt_auth")

DISALLOWED_WEAK_SECRETS = frozenset([
    "secret",
    "changeme",
    "test",
    "password",
    "admin",
    "12345678",
    "1234567890",
    "aaa-engine-secret-key-change-in-production",
    "your-secret-key-here",
    "default",
    "development",
    "supersecret",
    "jwtsecret",
    "qwerty",
    "letmein",
    "root",
    "tokensecret",
    "keyboardcat",
])

MINIMUM_KEY_LENGTH = 32
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "aaa-engine"
JWT_ISSUER = "aaa-auth-service"
TOKEN_EXPIRATION_SECONDS = 900

_UNSET = object()

def validate_jwt_secret(secret_candidate: Any = _UNSET) -> str:
    key = os.getenv("AAA_JWT_SECRET") if secret_candidate is _UNSET else secret_candidate
    if key is None or not str(key).strip():
        raise RuntimeError(
            "FATAL SECURITY FAILURE: 'AAA_JWT_SECRET' environment variable is missing or empty. "
            "Server startup aborted. Cryptographic keys must be explicitly provided in deployment."
        )
    key_str = str(key).strip()
    if len(key_str) < MINIMUM_KEY_LENGTH:
        raise RuntimeError(
            f"FATAL SECURITY FAILURE: 'AAA_JWT_SECRET' length is {len(key_str)} chars, which is under "
            f"the required minimum of {MINIMUM_KEY_LENGTH} characters (256-bit entropy). "
            "Server startup aborted."
        )
    key_lower = key_str.lower()
    for weak_pattern in DISALLOWED_WEAK_SECRETS:
        if weak_pattern in key_lower:
            raise RuntimeError(
                f"FATAL SECURITY FAILURE: 'AAA_JWT_SECRET' contains forbidden weak keyword '{weak_pattern}'. "
                "Server startup aborted. Production keys must be randomly generated."
            )
    unique_chars = len(set(key_str))
    if unique_chars < 6:
        raise RuntimeError(
            "FATAL SECURITY FAILURE: 'AAA_JWT_SECRET' entropy is dangerously low (insufficient unique characters). "
            "Server startup aborted."
        )
    return key_str

JWT_SECRET: str = validate_jwt_secret()

class TokenRequest(BaseModel):
    client_id: str = Field(..., description="Unique host application client identifier")
    client_secret: str = Field(..., description="Pre-shared host application secret")
    tenant_id: str = Field(..., description="Target tenant ID for database isolation")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT access token binding tenant claims")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=TOKEN_EXPIRATION_SECONDS, description="Token lifespan in seconds (900s / 15m)")

class TokenPayload(BaseModel):
    tenant_id: str
    client_id: str
    sub: str
    aud: str
    iss: str
    iat: int
    exp: int
    jti: str

_MOCK_API_CLIENTS: Dict[str, Dict[str, Any]] = {
    "banking-shield-core": {
        "secret_hash": hashlib.sha256("banking-shield-super-secure-production-secret-2026".encode()).hexdigest(),
        "allowed_tenants": ["bank-alpha-001", "bank-beta-002", "tenant-test-default"],
    },
    "callguard-agent": {
        "secret_hash": hashlib.sha256("callguard-telecom-perimeter-secret-key-9988".encode()).hexdigest(),
        "allowed_tenants": ["telco-omega-99", "tenant-test-default"],
    },
    "test-client-id": {
        "secret_hash": hashlib.sha256("test-client-secret-key-32-characters-long!!".encode()).hexdigest(),
        "allowed_tenants": ["tenant-test-default", "tenant-alpha"],
    },
}

def register_mock_api_client(client_id: str, client_secret: str, allowed_tenants: List[str]) -> None:
    _MOCK_API_CLIENTS[client_id] = {
        "secret_hash": hashlib.sha256(client_secret.encode()).hexdigest(),
        "allowed_tenants": allowed_tenants,
    }

def verify_client_credentials(client_id: str, client_secret: str, tenant_id: str) -> bool:
    client_record = _MOCK_API_CLIENTS.get(client_id)
    if not client_record:
        dummy_hash = hashlib.sha256(b"dummy").hexdigest()
        hmac.compare_digest(dummy_hash, dummy_hash)
        return False
    computed_hash = hashlib.sha256(client_secret.encode()).hexdigest()
    is_secret_valid = hmac.compare_digest(client_record["secret_hash"], computed_hash)
    allowed_tenants = client_record.get("allowed_tenants", [])
    is_tenant_valid = tenant_id in allowed_tenants or "*" in allowed_tenants
    return is_secret_valid and is_tenant_valid

def create_tenant_token(tenant_id: str, client_id: str, expires_in_seconds: int = TOKEN_EXPIRATION_SECONDS) -> str:
    now = int(time.time())
    payload = {
        "sub": tenant_id,
        "tenant_id": tenant_id,
        "client_id": client_id,
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + expires_in_seconds,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

router = APIRouter(tags=["auth"])

@router.post(
    "/v1/auth/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Client-Credential Token Exchange",
    description="Exchanges host application client credentials for a tenant-scoped 15-minute JWT."
)
@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def exchange_token(request: TokenRequest) -> TokenResponse:
    is_authenticated = verify_client_credentials(
        client_id=request.client_id,
        client_secret=request.client_secret,
        tenant_id=request.tenant_id,
    )
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CLIENT_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_tenant_token(
        tenant_id=request.tenant_id,
        client_id=request.client_id,
        expires_in_seconds=TOKEN_EXPIRATION_SECONDS,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRATION_SECONDS,
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token", auto_error=False)

def get_current_tenant(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTClaimsError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id: Optional[str] = payload.get("tenant_id") or payload.get("sub")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return tenant_id
