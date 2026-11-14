# Surya Day 3 Dependencies & Security Sign-Off Report

**To:** Surya (AAA Core Lead)  
**From:** Karthik Mallareddy (`mrkarthik1811@gmail.com`) — Security & Perimeter Defense Lead  
**Date:** November 13, 2026  
**Status:** **ALL DEPENDENCIES RESOLVED & IMPLEMENTED**  
**Branch:** `feat/karthik-security-banking`  

---

## Executive Summary

This document officially resolves and signs off on all six security dependencies (`DEP-SEC-001` through `DEP-SEC-006`) and the morning sync questions raised in `DAY3_IMPLEMENTATION_PLAN.md`. All underlying cryptographic implementations, adapters, and schemas are already live, tested, and committed to branch `feat/karthik-security-banking`.

---

## 1. Resolution of Morning Sync Questions (`DAY3_IMPLEMENTATION_PLAN.md`)

### Question 1: JWT Public Key & Signature Format
- **Decision:** **Dual-mode support (HS256 for internal middleware; RS256 with PEM for external host apps).**
- **Internal Server-to-Server Token Exchange:**
  - Endpoint: `POST /v1/auth/token`
  - Algorithm: `HS256` using high-entropy `AAA_JWT_SECRET` (evaluated at boot with fail-fast validation).
- **External Host Applications (Banking Shield / CallGuard):**
  - Algorithm: `RS256` using standard PEM public keys (`JWT_PUBLIC_KEY` in environment).
  - Implementation ready in: [`backend/app/security/host_auth.py`](../../backend/app/security/host_auth.py) (`HostAppAuthenticator`).

### Question 2: Expected JWT Claims
Every inbound token presented to `/v1/*` endpoints must contain:
```json
{
  "sub": "<tenant_id>",
  "tenant_id": "<tenant_id>",
  "client_id": "<host_application_id>",
  "iss": "aaa-auth-service",
  "aud": "aaa-engine",
  "iat": 1731510000,
  "exp": 1731510900,
  "jti": "<uuid-or-hex-nonce>",
  "scope": "voice:enroll voice:verify risk:transcript"
}
```
* **Strict Rule:** `aud` MUST be `"aaa-engine"`. Expiration `exp` is strictly capped at **15 minutes (900 seconds)**.

### Question 3: Required Scopes
The approved OAuth2 scope taxonomy for host applications:
- `voice:enroll` — Authorized to register voice embeddings (`POST /v1/enroll`).
- `voice:challenge` — Authorized to request dynamic phrases (`POST /v1/challenges`).
- `voice:verify` — Authorized to submit audio for speaker & liveness verification (`POST /v1/verify`).
- `risk:transcript` — Authorized for CallGuard transcript risk analysis (`POST /v1/risk/transcript`).

---

## 2. Audit of Surya's 6 Security Dependencies (`TEAM_DEPENDENCIES.md`)

| ID | Description | Status | Resolution / Implemented Component |
|---|---|:---:|---|
| **DEP-SEC-001** | Tenant Authentication Contract | **RESOLVED** | Implemented `POST /v1/auth/token` and zero-trust `get_current_tenant` dependency in `backend/app/security/jwt_auth.py`. |
| **DEP-SEC-002** | JWT Public Keys | **RESOLVED** | Supported RS256 PEM & HS256 validation in `backend/app/security/host_auth.py`. |
| **DEP-SEC-003** | VR Interface (CallGuard) | **RESOLVED** | Implemented `TranscriptRiskAdapter` in `backend/app/adapters/vr.py`, schemas in `backend/app/schemas/risk.py`, and endpoint in `backend/app/api/v1/risk.py`. |
| **DEP-SEC-004** | Banking Shield Integration | **RESOLVED** | Implemented `evaluate_banking_decision` and `BankingShieldPolicy` tiers in `backend/app/security/host_auth.py` with zero raw score leakage. |
| **DEP-SEC-005** | Security Review Schedule | **RESOLVED** | Comprehensive security audit completed below; all critical boundary checks verified. |
| **DEP-SEC-006** | Encryption Key Management | **RESOLVED** | Implemented `VoiceprintEncryptor` (AES-256-GCM) with 96-bit nonces and per-tenant HKDF/HMAC key derivation in `backend/app/security/voiceprint_crypto.py`. |

---

## 3. Comprehensive Security Review Sign-Off (`DEP-SEC-005`)

I have reviewed Surya's Day 1, Day 2, and Day 3 deliverables against `docs/surya/SECURITY_BOUNDARIES.md`. Here are the audit findings:

### Critical Vulnerabilities Cleared:
1. **Fallback Secret Removal (`SECURITY_BOUNDARIES.md § 5.3`)**:  
   * **Status:** **CLEARED.** `validate_jwt_secret()` in `jwt_auth.py` immediately crashes server startup if weak/fallback secrets are used.
2. **CORS Over-Permissiveness (`SECURITY_BOUNDARIES.md § 11.2`)**:  
   * **Status:** **CLEARED.** `configure_cors()` bans `*` wildcards, automatically defaulting to `[]` if detected.
3. **Biometric Embedding Theft at Rest (`SECURITY_BOUNDARIES.md § 4.2`)**:  
   * **Status:** **CLEARED.** AES-256-GCM authenticated cipher encrypts all 192-dim vectors at rest.
4. **Biometric Score Leakage to Host Apps (`SECURITY_BOUNDARIES.md § 4.1`)**:  
   * **Status:** **CLEARED.** Endpoints return high-level `Decision` enums (`APPROVE`, `DENY`, `STEP_UP`). Raw float scores are excluded from external responses.
5. **Token Replay Attacks (`SECURITY_BOUNDARIES.md § 12`)**:  
   * **Status:** **CLEARED.** Challenge tokens are atomically consumed upon first verification attempt.

---

## 4. Verification & Readiness

All 5 security targets are fully verified by automated unit tests:
```bash
# 28 passing unit & integration tests
python -m unittest discover -s backend/tests
```
- `backend/tests/test_jwt_auth.py` (10 tests)
- `backend/tests/test_challenge_lifecycle.py` (5 tests)
- `backend/tests/test_risk_transcript.py` (4 tests)
- `backend/tests/test_voiceprint_crypto.py` (5 tests)
- `backend/tests/test_host_auth.py` (4 tests)

Surya may unblock Day 3 Task 4 (JWT Host App Authentication) and Day 3 Task 3 (Voiceprint Encryption).
