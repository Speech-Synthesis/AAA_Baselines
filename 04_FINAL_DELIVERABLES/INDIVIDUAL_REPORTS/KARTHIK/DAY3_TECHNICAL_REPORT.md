# Karthik — Day 3 Technical Report

**Date:** November 14, 2026
**Sprint:** Day 3 of 4
**Role:** Security Lead — Authentication & Encryption
**Branch:** `feat/karthik-day3-security` → Merged via PR #14

---

## 1. Executive Summary

Day 3 completed the security infrastructure for AAA Engine, implementing JWT authentication, HMAC host app authentication, and AES-256-GCM voiceprint encryption with tenant isolation.

**Key Metrics:**
- Security controls: 6 implemented
- Test coverage: 100% for security modules
- Encryption: AES-256-GCM with tenant key derivation

---

## 2. Deliverables Completed

### 2.1 JWT Authentication

**File:** `backend/app/core/jwt_auth.py`

| Feature | Implementation |
|---------|----------------|
| Algorithm | HS256 |
| Token Validation | Signature + expiration |
| Claims | `sub`, `tenant_id`, `exp` |
| Optional Auth | `get_optional_tenant()` dependency |

**Code Sample:**
```python
def get_optional_tenant(token: str | None = Depends(oauth2_scheme)) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("tenant_id") or payload.get("sub")
    except Exception:
        return None
```

### 2.2 Host App Authentication

**File:** `backend/app/core/host_auth.py`

| Feature | Implementation |
|---------|----------------|
| Algorithm | HMAC-SHA256 |
| Headers | `X-Host-App-ID`, `X-Host-Signature`, `X-Host-Timestamp` |
| Timestamp Window | ±300 seconds |

### 2.3 Voiceprint Encryption

**File:** `backend/app/core/voiceprint_crypto.py`

| Feature | Implementation |
|---------|----------------|
| Algorithm | AES-256-GCM |
| Key Derivation | HMAC-SHA256(master_key, tenant_id) |
| Storage Format | `ENC:` + Base64 |
| Nonce | 12 bytes random |
| Auth Tag | 16 bytes |

**Code Sample:**
```python
def derive_tenant_key(master_key: bytes, tenant_id: str) -> bytes:
    """Derive tenant-specific key using HMAC-SHA256."""
    return hmac.new(
        master_key,
        tenant_id.encode(),
        hashlib.sha256
    ).digest()

def encrypt_voiceprint(embedding: list[float], tenant_id: str) -> str:
    """Encrypt embedding with tenant-specific key."""
    key = derive_tenant_key(MASTER_KEY, tenant_id)
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    data = json.dumps(embedding).encode()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return "ENC:" + base64.b64encode(nonce + encryptor.tag + ciphertext).decode()
```

---

## 3. Security Architecture

### 3.1 Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   API       │────▶│  JWT Auth   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           │                    ▼
                           │            ┌─────────────┐
                           │            │  Validate   │
                           │            │   Claims    │
                           │            └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Endpoint   │◀────│ tenant_id   │
                    └─────────────┘     └─────────────┘
```

### 3.2 Encryption Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Key (env var)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                    HMAC-SHA256(key, tenant_id)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ Tenant A  │   │ Tenant B  │   │ Tenant C  │
       │   Key     │   │   Key     │   │   Key     │
       └───────────┘   └───────────┘   └───────────┘
              │               │               │
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │AES-256-GCM│   │AES-256-GCM│   │AES-256-GCM│
       └───────────┘   └───────────┘   └───────────┘
```

---

## 4. Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_jwt_auth.py` | 10 | 100% |
| `test_host_auth.py` | 4 | 100% |
| `test_voiceprint_crypto.py` | 5 | 100% |
| **Total** | **19** | **100%** |

### 4.1 Key Test Cases

```python
# JWT expiration test
def test_expired_token_rejected():
    expired_token = create_token(exp=datetime.utcnow() - timedelta(hours=1))
    with pytest.raises(JWTError):
        verify_token(expired_token)

# Tenant isolation test
def test_tenant_isolation():
    encrypted = encrypt_voiceprint(embedding, tenant_id="tenant-A")
    with pytest.raises(DecryptionError):
        decrypt_voiceprint(encrypted, tenant_id="tenant-B")
```

---

## 5. Files Created/Modified

### New Files
```
backend/app/core/jwt_auth.py
backend/app/core/host_auth.py
backend/app/core/voiceprint_crypto.py
backend/tests/test_jwt_auth.py
backend/tests/test_host_auth.py
backend/tests/test_voiceprint_crypto.py
```

### Modified Files
```
backend/app/core/__init__.py
```

---

## 6. Security Verification

| Control | Test | Status |
|---------|------|--------|
| JWT Signature Validation | ✅ | Pass |
| JWT Expiration Check | ✅ | Pass |
| HMAC Signature Verification | ✅ | Pass |
| Timestamp Window Enforcement | ✅ | Pass |
| AES-256-GCM Encryption | ✅ | Pass |
| Tenant Key Derivation | ✅ | Pass |
| Cross-Tenant Access Prevention | ✅ | Pass |

---

## 7. Integration Points

| Consumer | Component | Status |
|----------|-----------|--------|
| `v1/challenges.py` | `jwt_auth.py` | ✅ Integrated |
| `v1/enroll.py` | `voiceprint_crypto.py` | ✅ Integrated |
| `v1/verify.py` | Both | ✅ Integrated |

---

**Document Version:** 1.0
**Author:** Karthik
**Timestamp:** November 14, 2026
