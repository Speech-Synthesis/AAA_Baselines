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
    return str(key).strip()
