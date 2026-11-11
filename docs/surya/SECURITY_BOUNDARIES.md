# AAA Engine — Security Boundaries

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)
**Reviewer:** Karthik (Security)

---

## Overview

This document defines the security boundaries, controls, and requirements for AAA Engine. It establishes the trust model, data protection requirements, and security controls at each layer.

---

## 1. Trust Model

### Trust Zones

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UNTRUSTED ZONE                                   │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │   End User       │  │   Attacker       │                         │
│  │   (Browser/App)  │  │   (Any source)   │                         │
│  └────────┬─────────┘  └──────────────────┘                         │
└───────────┼─────────────────────────────────────────────────────────┘
            │ HTTPS
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SEMI-TRUSTED ZONE                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │   Host Application (Banking Shield / CallGuard)              │   │
│  │   - Authenticated via JWT                                    │   │
│  │   - Authorized for specific tenant                           │   │
│  └────────┬─────────────────────────────────────────────────────┘   │
└───────────┼─────────────────────────────────────────────────────────┘
            │ JWT + API calls
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     TRUSTED ZONE                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      AAA ENGINE                               │   │
│  │   - Validates all inputs                                      │   │
│  │   - Enforces tenant isolation                                 │   │
│  │   - Makes authentication decisions                            │   │
│  └────────┬─────────────────────────────────────────────────────┘   │
│           │                                                          │
│  ┌────────▼─────────────────────────────────────────────────────┐   │
│  │                     PostgreSQL                                │   │
│  │   - Encrypted at rest                                         │   │
│  │   - Access controlled                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Trust Assumptions

| Entity | Trust Level | Assumption |
|--------|-------------|------------|
| End User | Untrusted | May be attacker or victim |
| User Audio | Untrusted | May be deepfake or replay |
| Host Application | Semi-trusted | Authenticated, tenant-scoped |
| AAA Engine | Trusted | Correctly implemented |
| Database | Trusted | Encrypted, access-controlled |
| Model Outputs | Trusted | But fallible |

---

## 2. Authentication Controls

### 2.1 Host Application Authentication

**Mechanism:** JWT Bearer Token (RS256)

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Required Claims:**

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | Tenant identifier |
| `aud` | string | Must be "aaa-engine" |
| `exp` | number | Expiration timestamp |
| `iat` | number | Issued at timestamp |
| `scope` | string[] | Authorized operations |

**Validation:**
1. Verify signature against tenant's public key
2. Check `aud` matches "aaa-engine"
3. Check `exp` not exceeded
4. Extract tenant ID from `sub`

### 2.2 Challenge Token Authentication

**Mechanism:** HMAC-SHA256 signed token

**Token Structure:**
```
{nonce}.{expires_timestamp}.{signature}
```

**Validation:**
1. Parse token components
2. Verify signature matches recomputed HMAC
3. Check expiration not exceeded
4. Check token not already consumed
5. Atomic consumption

### 2.3 Capture Grant Authentication

**Mechanism:** Short-lived JWT

**Purpose:** Authorize single audio upload

**Validation:**
1. Verify JWT signature
2. Check `aud` is "aaa-capture"
3. Check `exp` not exceeded
4. Check `sub` matches challenge ID

---

## 3. Authorization Controls

### 3.1 Tenant Isolation

**Requirement:** Complete separation between tenants

**Implementation:**
- Tenant ID extracted from JWT
- All database queries scoped to tenant
- Cross-tenant access prevented at repository level

```python
# Repository layer enforces tenant scoping
async def get_voiceprint(tenant_id: UUID, user_id: UUID) -> Voiceprint:
    return await db.query(Voiceprint).filter(
        Voiceprint.tenant_id == tenant_id,
        Voiceprint.user_id == user_id
    ).first()
```

### 3.2 Operation Scopes

| Scope | Permitted Operations |
|-------|---------------------|
| `enroll` | POST /v1/enroll |
| `verify` | POST /v1/challenges, POST /v1/verify |
| `revoke` | POST /v1/voiceprints/{id}/revoke |
| `risk` | POST /v1/risk/transcript |
| `admin` | All operations |

---

## 4. Data Protection

### 4.1 Data Classification

| Data Type | Classification | Retention | Encryption |
|-----------|---------------|-----------|------------|
| Raw Audio | Sensitive | Not retained | N/A |
| Voice Embeddings | Biometric | Indefinite | AES-256-GCM |
| Challenge Phrases | Internal | 24 hours | At rest |
| User Identifiers | PII | Per policy | At rest |
| Audit Logs | Operational | 90 days | At rest |
| Model Scores | Internal | Not exposed | N/A |

### 4.2 Voiceprint Encryption

**Algorithm:** AES-256-GCM

**Key Management:**
- Per-tenant encryption keys (future)
- Keys stored in secure key management service
- Key rotation supported

**Implementation:**

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_voiceprint(embedding: list[float], key: bytes) -> bytes:
    """Encrypt voiceprint embedding."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(embedding).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext

def decrypt_voiceprint(encrypted: bytes, key: bytes) -> list[float]:
    """Decrypt voiceprint embedding."""
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)
```

**Status:** NOT IMPLEMENTED — Mandatory for production

### 4.3 Audio Handling

**Requirement:** Raw audio must not be retained

**Implementation:**
- Audio processed in memory only
- No logging of audio content
- No database storage of audio
- Immediate disposal after inference

---

## 5. Secret Management

### 5.1 Required Secrets

| Secret | Purpose | Source |
|--------|---------|--------|
| `L3_HMAC_SECRET` | Challenge token signing | Environment |
| `CAPTURE_GRANT_SECRET` | Capture grant signing | Environment |
| `DATABASE_URL` | PostgreSQL connection | Environment |
| `VOICEPRINT_KEY` | Embedding encryption | Key vault (future) |
| `JWT_PUBLIC_KEY` | Host app JWT validation | Environment |

### 5.2 Secret Requirements

| Requirement | Implementation |
|-------------|----------------|
| No hardcoded secrets | Environment variables only |
| No fallback defaults | Fail on missing secret |
| No secret logging | Excluded from logs |
| Rotation support | Hot reload capability |

### 5.3 Fallback Secret Issue (CRITICAL)

**Current Code (layer3_adaptive.py:16):**
```python
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026").encode()
```

**Issue:** Hardcoded fallback enables token forgery if env var not set.

**Required Fix:**
```python
SECRET_KEY = os.environ["L3_HMAC_SECRET"].encode()  # Fail if not set
```

---

## 6. Input Validation

### 6.1 Audio Validation

| Property | Requirement | Validation |
|----------|-------------|------------|
| Format | WAV (PCM) | Magic bytes |
| Sample Rate | 16000 Hz | Header parsing |
| Channels | Mono (1) | Header parsing |
| Duration | 2-10 seconds | Sample count |
| File Size | < 5 MB | Content-Length |

### 6.2 Request Validation

| Field | Validation |
|-------|------------|
| user_id | UUID format |
| token | Non-empty, structure check |
| challenge_id | UUID format |
| phrase | Non-empty, max 200 chars |

### 6.3 Response Sanitization

**Excluded from public responses:**
- Raw model scores
- Internal confidence values
- Embedding vectors
- System paths
- Stack traces

---

## 7. Rate Limiting

### 7.1 Endpoint Limits

| Endpoint | Requests | Window | Scope |
|----------|----------|--------|-------|
| POST /v1/challenges | 10 | 1 min | Per user |
| POST /v1/verify | 5 | 1 min | Per user |
| POST /v1/enroll | 3 | 5 min | Per user |
| Other | 100 | 1 min | Per tenant |

### 7.2 Implementation

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/challenges")
@limiter.limit("10/minute")
async def create_challenge(...):
    ...
```

**Status:** NOT IMPLEMENTED — Required for production

---

## 8. Fail-Closed Behavior

### 8.1 Principle

> When in doubt, DENY. Never approve on uncertainty.

### 8.2 Failure Scenarios

| Scenario | Required Behavior |
|----------|-------------------|
| Model unavailable | UNAVAILABLE, not APPROVE |
| Model timeout | UNAVAILABLE, not APPROVE |
| Database error | Return error, not APPROVE |
| Missing configuration | Fail startup |
| Invalid token | DENY |
| Expired token | DENY |

### 8.3 Implementation

```python
try:
    result = await model.predict(audio)
except ModelNotAvailableError:
    return Decision.UNAVAILABLE
except ModelTimeoutError:
    return Decision.UNAVAILABLE
except Exception:
    # Log error, but never approve
    return Decision.UNAVAILABLE
```

---

## 9. Audit Logging

### 9.1 Logged Events

| Event | Fields |
|-------|--------|
| Challenge created | tenant_id, user_id, challenge_id |
| Verification started | tenant_id, user_id, challenge_id |
| Verification completed | decision, gates_passed |
| Token consumed | challenge_id |
| Enrollment completed | tenant_id, user_id |
| Voiceprint revoked | tenant_id, voiceprint_id |
| Authentication failed | reason, layer_blocked |

### 9.2 Excluded from Logs

- Raw audio content
- Voice embeddings
- Challenge tokens (full)
- API keys / secrets
- Personal names (hash if needed)

### 9.3 Log Format

```json
{
  "timestamp": "2026-11-11T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "abc123",
  "event": "verification_completed",
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid",
  "decision": "APPROVE",
  "duration_ms": 1250
}
```

---

## 10. CORS Configuration

### 10.1 Current Issues

```python
# INSECURE: Wildcard patterns
"https://*.onrender.com",
"https://*.hf.space"
```

### 10.2 Required Configuration

```python
# SECURE: Explicit origins only
ALLOWED_ORIGINS = [
    "https://aaa-frontend.onrender.com",
    "https://banking-shield.example.com",
    "https://callguard.example.com",
]

if DEBUG:
    ALLOWED_ORIGINS.extend([
        "http://localhost:5173",
        "http://localhost:3000",
    ])
```

---

## 11. Security Checklist

### Implemented

- [x] HMAC token signing
- [x] 90-second token TTL
- [x] Single-use token enforcement (in-memory)
- [x] EMA voiceprint protection
- [x] Audio not stored
- [x] Model scores logged internally

### Not Implemented (Day-2+)

- [ ] Database-backed token persistence
- [ ] Remove fallback secret
- [ ] Restrict CORS origins
- [ ] Rate limiting
- [ ] Voiceprint encryption (AES-256-GCM)
- [ ] JWT validation for host apps
- [ ] Structured security audit logs
- [ ] Input size validation
- [ ] Request timeout enforcement

---

## 12. Threat Model Summary

| Threat | Mitigation | Status |
|--------|------------|--------|
| Token forgery | HMAC signature | ✅ |
| Token replay | Single-use + TTL | ⚠️ In-memory |
| Deepfake audio | AAA-AD detection | ✅ |
| Voice cloning | Challenge phrases | ✅ |
| Cross-tenant access | Tenant scoping | ⚠️ Incomplete |
| Brute force | Rate limiting | ❌ Not implemented |
| Embedding theft | Encryption | ❌ Not implemented |
| Secret exposure | Env vars | ⚠️ Has fallback |

---

**Document Version:** 1.0
**Classification:** Security Documentation
