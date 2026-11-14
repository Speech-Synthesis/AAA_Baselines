# AAA Engine — Security Control Matrix

**Date:** November 14, 2026
**Version:** 1.0
**Security Lead:** Karthik
**Project Lead:** Surya

---

## 1. Security Controls Overview

| Control ID | Category | Control Name | Status | Implementation |
|------------|----------|--------------|--------|----------------|
| SEC-001 | Authentication | JWT Token Validation | ✅ Implemented | `jwt_auth.py` |
| SEC-002 | Authentication | Host App HMAC Auth | ✅ Implemented | `host_auth.py` |
| SEC-003 | Encryption | Voiceprint AES-256-GCM | ✅ Implemented | `voiceprint_crypto.py` |
| SEC-004 | Encryption | Tenant Key Derivation | ✅ Implemented | HMAC-SHA256 |
| SEC-005 | Access Control | CORS Hardening | ✅ Implemented | `main.py` |
| SEC-006 | Rate Limiting | SlowAPI Integration | ✅ Implemented | `main.py` |
| SEC-007 | Token Security | Challenge Single-Use | ✅ Implemented | `token_persistence.py` |
| SEC-008 | Token Security | HMAC Token Signing | ✅ Implemented | `challenge_token.py` |
| SEC-009 | Data Protection | No Raw Scores in V1 | ✅ Implemented | `verify.py` |
| SEC-010 | Logging | Security Event Logging | ✅ Implemented | All endpoints |

---

## 2. Threat/Control Matrix

| Threat | STRIDE Category | Controls | Mitigation Status |
|--------|-----------------|----------|-------------------|
| Token Replay Attack | Spoofing | SEC-007, SEC-008 | ✅ Mitigated |
| Unauthorized API Access | Spoofing | SEC-001, SEC-002 | ✅ Mitigated |
| Voiceprint Theft | Information Disclosure | SEC-003, SEC-004 | ✅ Mitigated |
| Cross-Tenant Data Access | Elevation of Privilege | SEC-003, SEC-004 | ✅ Mitigated |
| CORS Bypass | Spoofing | SEC-005 | ✅ Mitigated |
| Brute Force Attack | Denial of Service | SEC-006 | ✅ Mitigated |
| Score Manipulation | Tampering | SEC-009 | ✅ Mitigated |
| Deepfake Audio | Spoofing | L2 Layer | ✅ Mitigated |

---

## 3. Security Control Details

### 3.1 SEC-001: JWT Token Validation

**File:** `backend/app/core/jwt_auth.py`

| Attribute | Value |
|-----------|-------|
| Algorithm | HS256 |
| Secret Source | Environment variable |
| Expiration | Configurable (default 30 min) |
| Claims Validated | `exp`, `sub`, `tenant_id` |

**Test Coverage:**
- `test_jwt_auth.py` — 10 tests
- Token expiration validation
- Invalid signature rejection
- Missing claims handling

### 3.2 SEC-002: Host App HMAC Authentication

**File:** `backend/app/core/host_auth.py`

| Attribute | Value |
|-----------|-------|
| Algorithm | HMAC-SHA256 |
| Headers Required | `X-Host-App-ID`, `X-Host-Signature`, `X-Host-Timestamp` |
| Timestamp Window | ±300 seconds |

**Test Coverage:**
- `test_host_auth.py` — 4 tests
- Signature validation
- Timestamp window enforcement

### 3.3 SEC-003: Voiceprint AES-256-GCM Encryption

**File:** `backend/app/core/voiceprint_crypto.py`

| Attribute | Value |
|-----------|-------|
| Algorithm | AES-256-GCM |
| Key Size | 256 bits |
| Nonce Size | 12 bytes |
| Auth Tag | 16 bytes |
| Storage Format | `ENC:` + Base64 |

**Test Coverage:**
- `test_voiceprint_crypto.py` — 5 tests
- `test_voiceprint_service.py` — 21 tests
- Encrypt/decrypt roundtrip
- Tenant isolation verification

### 3.4 SEC-004: Tenant Key Derivation

**Implementation:** HMAC-SHA256 based key derivation

```
tenant_key = HMAC-SHA256(master_key, tenant_id)
```

**Security Properties:**
- Cryptographic isolation between tenants
- Single master key storage
- Deterministic derivation

### 3.5 SEC-005: CORS Hardening

**File:** `backend/app/main.py:58-91`

| Control | Implementation |
|---------|----------------|
| Wildcard Rejection | `*` patterns filtered out |
| Origin Validation | Explicit allow-list only |
| Security Logging | Rejected origins logged |

### 3.6 SEC-006: Rate Limiting

**File:** `backend/app/main.py`

| Endpoint | Limit |
|----------|-------|
| `/v1/challenges` | 10/minute |
| `/v1/enroll` | 5/minute |
| `/v1/verify` | 20/minute |

**Test Coverage:**
- `test_rate_limiting.py` — 10 tests
- 429 response verification
- Retry-After header validation

### 3.7 SEC-007: Challenge Single-Use Tokens

**File:** `backend/app/core/token_persistence.py`

| Property | Implementation |
|----------|----------------|
| Token Consumption | Atomic database update |
| Replay Prevention | `consumed_at` timestamp |
| Expiration | 5 minutes default |

**Test Coverage:**
- `test_token_persistence.py` — 17 tests
- `test_challenge_lifecycle.py` — 5 tests

### 3.8 SEC-008: HMAC Token Signing

**File:** `backend/app/core/challenge_token.py`

| Attribute | Value |
|-----------|-------|
| Algorithm | HMAC-SHA256 |
| Token Format | `{data}.{signature}` |
| Validation | Constant-time comparison |

---

## 4. Attack Test Results

### 4.1 Token Replay Attack

| Test Case | Expected | Result |
|-----------|----------|--------|
| Reuse valid token | Rejected | ✅ Pass |
| Reuse expired token | Rejected | ✅ Pass |
| Modified token payload | Rejected | ✅ Pass |
| Invalid signature | Rejected | ✅ Pass |

### 4.2 Cross-Tenant Access

| Test Case | Expected | Result |
|-----------|----------|--------|
| Decrypt with wrong tenant | Error | ✅ Pass |
| Access other tenant's voiceprint | Denied | ✅ Pass |

### 4.3 CORS Bypass Attempts

| Test Case | Expected | Result |
|-----------|----------|--------|
| Wildcard origin `*` | Rejected | ✅ Pass |
| Pattern `*.example.com` | Rejected | ✅ Pass |
| Unlisted origin | No CORS headers | ✅ Pass |

### 4.4 Rate Limit Bypass

| Test Case | Expected | Result |
|-----------|----------|--------|
| Exceed limit | 429 Response | ✅ Pass |
| Different IPs | Separate limits | ✅ Pass |
| Retry-After header | Present | ✅ Pass |

---

## 5. Security Verification Summary

| Category | Tests | Passed | Coverage |
|----------|-------|--------|----------|
| JWT Authentication | 10 | 10 | 100% |
| Host App Auth | 4 | 4 | 100% |
| Voiceprint Crypto | 26 | 26 | 100% |
| Token Lifecycle | 22 | 22 | 100% |
| Rate Limiting | 10 | 10 | 100% |
| **Total** | **72** | **72** | **100%** |

---

## 6. Compliance Checklist

- [x] No secrets in source code
- [x] Environment-based configuration
- [x] Encryption at rest (voiceprints)
- [x] Secure token generation (CSPRNG)
- [x] Rate limiting on all endpoints
- [x] CORS properly configured
- [x] No verbose error messages in production
- [x] Security event logging
- [x] Tenant isolation enforced
- [x] Input validation on all endpoints

---

**Document Version:** 1.0
**Security Lead:** Karthik
**Reviewed By:** Surya
**Timestamp:** November 14, 2026
