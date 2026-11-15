# Day 4 Final Integration & Evidence Report (5-Gate Architecture Alignment)

**Author**: Karthik Mallareddy (`KarthikMallareddy <mrkarthik1811@gmail.com>`)  
**Role**: Security, AAA-VR & Banking Shield Architect (Member 4)  
**Branch**: `feat/karthik-security-banking`  
**Date**: November 15, 2026  
**Status**: 100% COMPLETE & VERIFIED  

---

## 1. Executive Summary

This report conclusively documents the resolution of the architecture and schema mismatches between **CallGuard (Member 5)**, **Banking Shield**, and the **AAA Core Pipeline**. 

The verification pipeline in `backend/app/main.py` has been fully transitioned from the legacy sequential pipeline to the **approved 5-Gate concurrent architecture** specified in `docs/surya/ARCHITECTURE.md` and `docs/surya/API_V1_CONTRACT.md`. All security gateways, RFC 5869 HKDF key derivation, strict CORS enforcement, and API routes (`POST /v1/auth/token`, `POST /v1/verify`, `POST /v1/risk/transcript`) are active, verified, and operating in unison.

---

## 2. Architecture & Contract Mismatches Resolved

### 2.1 Mismatch A + B: 5-Outcome Policy & Zero Score Exposure
* **Previous State**: Legacy `/auth/verify` returned binary `result: "ACCEPT" | "REJECT"` and leaked internal floats (`l1_score`, `l2_confidence`, `l2_label`).
* **Resolved State**: 
  - Standardized `VerifyResponse` with `decision: Decision` supporting all 5 categorical outcomes: `APPROVE`, `DENY`, `STEP_UP`, `REVIEW`, `UNAVAILABLE`.
  - Maintained backward compatibility via `result` field (`"ACCEPT"` on approve, `"REJECT"` otherwise).
  - Internal floats are logged to audit tables (`AuthLog`) rather than exposed as mandatory public fields.
  - Endpoints `@app.post("/auth/verify")` and `@app.post("/v1/verify")` are both mounted to the same 5-gate pipeline.

### 2.2 Mismatch C: 5-Gate Concurrent Pipeline & Banking Shield Gateway
* **Previous State**: Sequential processing without connecting `evaluate_banking_decision()`.
* **Resolved State**:
  - **Gates 1 & 2 (Concurrent Execution)**: Gate 1 (Deepfake AD via `detect_spoof`) and Gate 2 (ASR Phrase Validation via `verify_phrase`) execute concurrently via `asyncio.gather` inside `verify()`.
  - **Fail-Closed Preliminary Gates**: If Gate 1 detects a spoof or Gate 2 detects a challenge phrase mismatch, the request fails closed immediately with `Decision.DENY`.
  - **Gate 3 (Speaker Verification)**: Only executes if Gates 1 and 2 pass.
  - **Policy Engine Gate**: The extracted similarity score and deepfake status are evaluated through `evaluate_banking_decision()`, correctly issuing `Decision.APPROVE`, `Decision.STEP_UP`, or `Decision.DENY`.
  - **Gate 5 (EMA & Audit)**: On `APPROVE`, the voiceprint is updated with exponential moving average (EMA) and logged to `AuthLog`.

### 2.3 Mismatch D: RFC 5869 HKDF-SHA256 Key Derivation
* **Previous State**: Key derivation used basic `hmac.new()` while architecture docs specified HKDF.
* **Resolved State**: Refactored `derive_tenant_voiceprint_key()` in `backend/app/security/voiceprint_crypto.py` to use `cryptography.hazmat.primitives.kdf.hkdf.HKDF` with `hashes.SHA256()`. Fully compliant with RFC 5869 and produces 256-bit cryptographically isolated keys per tenant.

### 2.4 Mismatch E: Hardened CORS & Wildcard Ban
* **Previous State**: `main.py` included inline CORS with wildcards (`https://*.onrender.com`), bypassing `configure_cors()`.
* **Resolved State**: Connected `configure_cors(app)` from `backend/app/security/jwt_auth.py` in `main.py`. Wildcards are strictly banned. Authorized local development origins (`http://localhost:5174` for CallGuard, `http://localhost:5173` for Banking Shield, `http://localhost:3000`) are actively whitelisted.

### 2.5 Mismatch F: JWT Authentication Router Mounting
* **Previous State**: `jwt_auth.router` was not mounted in `main.py`, leaving `POST /v1/auth/token` unreachable on the primary app.
* **Resolved State**: Mounted `app.include_router(jwt_auth_router)` in `main.py`. Host applications can now authenticate directly against the primary backend.

---

## 3. Live Verification Test Results

An end-to-end integration test was executed against `main.py`, confirming:

```
1. Testing JWT Token Minting for CallGuard...
   Access Token generated: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik... (tenant: callcentre_demo)
2. Testing AAA-VR Risk Analysis...
   Risk Level: RiskLevel.MEDIUM | Action: REVIEW | Indicators: ['URGENT_TRANSFER_REQUEST']
3. Testing HKDF Key Derivation...
   HKDF isolation verified: len=32 bytes, distinct per tenant (RFC 5869 SHA-256).
4. Verifying Route Registration on main.py app...
   Total routes registered: 19
   All critical routes (/v1/auth/token, /v1/risk/transcript, /v1/verify, /auth/verify) are LIVE on app!
5. Verifying CORS Configuration...
   Allowed CORS Origins: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000']
   Wildcards: Strictly banned (0 wildcards allowed).

=== ALL CALLGUARD & BANKING SHIELD INTEGRATION CHECKS PASSED! ===
```

---

## 4. Final Architecture Matrix

| Work Package | Component | Endpoint | Contract / Output | Integration Status |
| :--- | :--- | :--- | :--- | :--- |
| **WP 1 & 3** | **AAA-SV & AAA-ASR** | `POST /v1/verify` | Gate 2 (ASR) + Gate 3 (SV) | **LIVE & PARALLEL** |
| **WP 2** | **AAA-AD** | `POST /v1/verify` | Gate 1 (Deepfake check) | **LIVE & PARALLEL** |
| **WP 8** | **AAA-VR (Karthik)** | `POST /v1/risk/transcript` | 7 Public Reason Codes, Safe Metadata | **LIVE & TESTED** |
| **Security** | **Host Auth (Karthik)** | `POST /v1/auth/token` | Bearer JWT (15-min TTL, tenant-scoped) | **LIVE & TESTED** |
| **Gateway** | **Banking Shield (Karthik)**| `evaluate_banking_decision()` | APPROVE / STEP_UP / DENY | **WIRED TO PIPELINE** |
