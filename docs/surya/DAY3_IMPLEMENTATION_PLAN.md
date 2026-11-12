# Surya — Day 3 Implementation Plan

**Date:** November 13, 2026
**Sprint Day:** 3 of 4
**Focus:** Security hardening and API completion

---

## Priority Order

| Priority | Task | Effort | Blocker |
|----------|------|--------|---------|
| P0 | CORS origin restriction | 1h | None |
| P0 | API v1 endpoint implementation | 4h | None |
| P1 | Voiceprint encryption | 3h | None |
| P1 | JWT host app authentication | 2h | Karthik confirmation |
| P2 | Structured logging | 2h | None |
| P2 | Adapter integration | 2h | Team confirmations |

---

## Task 1: CORS Origin Restriction (P0)

**Current Issue:** Wildcard patterns allow any subdomain

```python
cors_origins.extend([
    "https://*.onrender.com",  # Too permissive
    "https://*.hf.space"       # Too permissive
])
```

**Target:**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://aaa-frontend.onrender.com",
    # Add specific allowed origins
]
```

**Implementation:**
1. Move CORS config to Settings
2. Remove wildcard patterns
3. Add origin validation middleware
4. Update documentation

---

## Task 2: API v1 Endpoint Implementation (P0)

**Endpoints to implement:**

### POST /v1/enroll
```python
@router.post("/enroll")
async def enroll_user(
    request: Request,
    user_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Use adapter pattern for model calls
    # Return standardized response
```

### POST /v1/challenges
```python
@router.post("/challenges")
async def create_challenge(
    request: Request,
    body: ChallengeRequest,
    db: Session = Depends(get_db)
):
    # Create challenge with DB persistence
    # Return challenge_id in response
```

### POST /v1/verify
```python
@router.post("/verify")
async def verify_authentication(
    request: Request,
    challenge_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Use validate_and_consume_token
    # Return Decision enum, not raw scores
```

---

## Task 3: Voiceprint Encryption (P1)

**Target:** AES-256-GCM encryption for embeddings at rest

**Implementation:**

```python
# app/core/crypto.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class VoiceprintEncryptor:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)

    def encrypt(self, embedding: list[float]) -> tuple[bytes, bytes]:
        """Encrypt embedding, return (ciphertext, nonce)"""
        nonce = os.urandom(12)
        data = json.dumps(embedding).encode()
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> list[float]:
        """Decrypt embedding"""
        data = self.aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(data)
```

**Database Changes:**
- Add `embedding_encrypted` (BLOB) column
- Add `embedding_nonce` (BLOB) column
- Deprecate plain `embedding` column

---

## Task 4: JWT Host App Authentication (P1)

**Blocked by:** Karthik's confirmation on JWT public key format

**Proposed Implementation:**

```python
# app/core/jwt.py
from jose import jwt, JWTError

class HostAppAuthenticator:
    def __init__(self, public_key: str, issuer: str):
        self.public_key = public_key
        self.issuer = issuer

    def validate_token(self, token: str) -> dict:
        """Validate host app JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                issuer=self.issuer
            )
            return payload
        except JWTError as e:
            raise InvalidHostTokenError(str(e))
```

**Middleware:**
```python
@app.middleware("http")
async def verify_host_app(request: Request, call_next):
    # Skip for health/ready endpoints
    if request.url.path in ["/v1/health", "/v1/ready"]:
        return await call_next(request)

    # Validate Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing host app token")

    # Validate JWT
    authenticator.validate_token(auth_header[7:])
    return await call_next(request)
```

---

## Task 5: Structured Logging (P2)

**Replace print statements with structured logging:**

```python
# app/core/logging.py
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
        return json.dumps(log_record)
```

**Usage:**
```python
logger.info("Challenge created", extra={
    "user_id": user_id,
    "challenge_id": challenge_id,
    "expires_at": expires_at.isoformat()
})
```

---

## Task 6: Adapter Integration (P2)

**After team confirmations:**

1. Update main.py to use adapters
2. Add dependency injection for adapters
3. Create adapter factory

```python
# app/core/dependencies.py
def get_speaker_adapter() -> SpeakerVerificationAdapter:
    if settings.DEBUG:
        return MockSpeakerAdapter()
    return EcapaSpeakerAdapter()

def get_deepfake_adapter() -> DeepfakeDetectionAdapter:
    if settings.DEBUG:
        return MockDeepfakeAdapter()
    return Wav2VecDeepfakeAdapter()
```

---

## Schedule

| Time | Task | Status |
|------|------|--------|
| 09:00-10:00 | CORS restriction | |
| 10:00-14:00 | API v1 endpoints | |
| 14:00-17:00 | Voiceprint encryption | |
| 17:00-18:00 | Structured logging | |

---

## Success Criteria

- [ ] No wildcard CORS patterns
- [ ] `/v1/enroll` endpoint working
- [ ] `/v1/challenges` endpoint working
- [ ] `/v1/verify` endpoint working
- [ ] Voiceprint encryption implemented
- [ ] All tests passing (60+)
- [ ] No raw scores in v1 responses

---

## Dependencies to Collect

### Morning Sync

1. **Karthik:**
   - JWT public key format (PEM? JWK?)
   - Expected JWT claims (iss, aud, exp)
   - Required scopes

2. **Team:**
   - Confirm adapter interfaces
   - Any API contract changes

---

**Document Version:** 1.0
