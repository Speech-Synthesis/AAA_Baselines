# Surya — Day 4 Implementation Plan

**Date:** November 14, 2026
**Sprint Day:** 4 of 4 (Final Day)
**Branch:** `feat/surya-day3-integration` (pending merge)
**Author:** Surya (Project Lead — AAA Core + System Integration)

---

## Executive Summary

Day 4 is the final day of the 4-day sprint. The focus is on completing integration, addressing technical debt, finalizing documentation, and ensuring production readiness.

**Current State:**
- 324 tests passing
- PR #14 (Karthik Security) and PR #15 (Nandan ASR) merged to main
- Day 3 branch has 8 commits ahead of main (not yet merged)
- All critical security features implemented

**Day 4 Objectives:**
- Merge Day 3 integration work to main
- Address remaining technical debt
- Complete monitoring infrastructure (Issue #6)
- Finalize production readiness checklist
- Prepare final deliverables

---

## Table of Contents

1. [Project Progress Summary (Day 1–3)](#1-project-progress-summary-day-1-3)
2. [Current System Architecture](#2-current-system-architecture)
3. [Team Contribution Overview](#3-team-contribution-overview)
4. [Remaining Tasks and Technical Debt](#4-remaining-tasks-and-technical-debt)
5. [Day 4 Objectives and Scope](#5-day-4-objectives-and-scope)
6. [Implementation Tasks](#6-implementation-tasks)
7. [Files and Modules Affected](#7-files-and-modules-affected)
8. [Team Dependencies](#8-team-dependencies)
9. [API, Security, and Integration Considerations](#9-api-security-and-integration-considerations)
10. [Testing Strategy](#10-testing-strategy)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Risks and Mitigation](#12-risks-and-mitigation)
13. [Day 4 Completion Checklist](#13-day-4-completion-checklist)

---

## 1. Project Progress Summary (Day 1–3)

### Day 1: Foundation (November 11, 2026)

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| Repository Audit | ✅ Complete | `docs/surya/DAY1_REPOSITORY_AUDIT.md` |
| API v1 Contract | ✅ Complete | `docs/surya/API_V1_CONTRACT.md` |
| OpenAPI Specification | ✅ Complete | `docs/surya/openapi.yaml` |
| Architecture Documentation | ✅ Complete | `docs/surya/ARCHITECTURE.md` |
| Health/Readiness Endpoints | ✅ Implemented | `backend/app/api/v1/health.py` |
| Modular Backend Structure | ✅ Complete | `backend/app/api/`, `core/`, `schemas/` |
| Challenge Phrase Enhancement | ✅ Complete | Millions of unique combinations |
| Test Infrastructure | ✅ Complete | `backend/tests/conftest.py`, `pytest.ini` |

**Branch:** `feat/surya-aaa-core` → Merged via PR #8

---

### Day 2: Security Infrastructure (November 12, 2026)

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| Token Persistence (SEC-001) | ✅ Complete | `layer3_adaptive.py` → Database |
| Fallback Secret Removal (SEC-002) | ✅ Complete | Fail-fast validation |
| Rate Limiting | ✅ Complete | `core/ratelimit.py`, SlowAPI |
| CI/CD Pipeline | ✅ Complete | `.github/workflows/test.yml` |
| Model Adapters (Mock) | ✅ Complete | `backend/app/adapters/` |
| Integration Tests | ✅ Complete | `test_token_persistence.py` |

**Tests:** 57 passing
**Branch:** `feat/surya-day2-security` → Merged via PR #9

---

### Day 3: Integration (November 13–14, 2026)

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| CORS Restriction | ✅ Complete | `main.py:58-91` — Wildcards rejected |
| API v1 Endpoints | ✅ Complete | `api/v1/enroll.py`, `verify.py`, `challenges.py` |
| JWT Auth Integration | ✅ Complete | `get_optional_tenant()` in all v1 endpoints |
| Voiceprint Encryption Service | ✅ Complete | `services/voiceprint_service.py` |
| Encryption in Pipeline | ✅ Complete | `enroll.py`, `verify.py` use encrypt/decrypt |
| Rate Limiting Tests | ✅ Complete | `test_rate_limiting.py` (211 lines) |
| E2E Integration Tests | ✅ Complete | `test_e2e_integration.py` (344 lines) |
| API v1 Tests | ✅ Complete | `test_api_v1.py` (546 lines) |
| Voiceprint Service Tests | ✅ Complete | `test_voiceprint_service.py` (196 lines) |

**Tests:** 324 passing
**Branch:** `feat/surya-day3-integration` → **NOT YET MERGED**

---

### Merged Team Contributions

| PR | Author | Title | Status | Date |
|----|--------|-------|--------|------|
| #8 | Surya | Day 1 AAA Core Foundation | ✅ Merged | Nov 11 |
| #9 | Surya | Day 2 Security Infrastructure | ✅ Merged | Nov 11 |
| #10 | Nandan | AAA-ASR Phrase Matching + CallGuard Day 1 | ✅ Merged | Nov 12 |
| #14 | Karthik | Security Banking (JWT, Crypto, Host Auth) | ✅ Merged | Nov 14 |
| #15 | Nandan | ASR CallGuard Day 2 Deliverables | ✅ Merged | Nov 14 |

---

## 2. Current System Architecture

### 2.1 Backend Structure

```
backend/app/
├── api/
│   └── v1/
│       ├── __init__.py          # V1 router aggregation
│       ├── health.py             # Health/readiness endpoints
│       ├── challenges.py         # Challenge generation (JWT optional)
│       ├── enroll.py             # Voice enrollment (JWT optional, encrypted)
│       ├── verify.py             # Verification pipeline (JWT optional, encrypted)
│       └── risk.py               # CallGuard risk transcript analysis
├── adapters/
│   ├── base.py                   # Abstract interfaces
│   ├── sv.py                     # ECAPA-TDNN speaker verification
│   ├── ad.py                     # Wav2Vec2 deepfake detection
│   ├── asr.py                    # Whisper ASR
│   ├── vr.py                     # Transcript risk adapter
│   └── mock.py                   # Mock implementations for testing
├── aaa_asr/
│   └── phrase_matcher.py         # Phrase matching logic (Nandan)
├── core/
│   ├── config.py                 # Pydantic settings
│   ├── exceptions.py             # Custom exceptions
│   ├── ratelimit.py              # SlowAPI rate limiting
│   ├── logging.py                # Structured security logging
│   └── crypto.py                 # Legacy crypto utilities
├── security/
│   ├── jwt_auth.py               # JWT authentication + /auth/token endpoint
│   ├── voiceprint_crypto.py      # AES-256-GCM encryption (Karthik)
│   ├── host_auth.py              # Host app authentication (Karthik)
│   └── challenge_lifecycle.py    # Challenge state machine (Karthik)
├── services/
│   ├── __init__.py
│   └── voiceprint_service.py     # Encryption service layer
├── schemas/
│   └── common.py                 # Shared Pydantic models
├── layer1_speaker.py             # Speaker verification wrapper
├── layer2_deepfake.py            # Deepfake detection wrapper
├── layer3_adaptive.py            # Challenge generation, token validation, EMA
├── layer3_asr.py                 # ASR phrase verification
├── models.py                     # SQLAlchemy ORM models
├── db.py                         # Database engine
└── main.py                       # FastAPI application
```

### 2.2 Authentication Pipeline

```
                            ┌─────────────────────┐
                            │   Client Request    │
                            │  POST /v1/verify    │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Optional JWT Auth  │
                            │  get_optional_tenant │
                            └──────────┬──────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                           VERIFICATION PIPELINE                              │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Layer 2   │───▶│   Layer 3A  │───▶│   Layer 1   │───▶│   Layer 3B  │  │
│  │  Deepfake   │    │   ASR       │    │   Speaker   │    │   Token     │  │
│  │  Detection  │    │   Phrase    │    │   Verify    │    │   Consume   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │          │
│        │                  │           ┌──────▼──────┐           │          │
│        │                  │           │  Decrypt    │           │          │
│        │                  │           │  Voiceprint │           │          │
│        │                  │           └─────────────┘           │          │
│        │                  │                                     │          │
│        ▼                  ▼                                     ▼          │
│    Reject if          Reject if                             Reject if      │
│    spoof > 0.5        mismatch                             token invalid   │
│                                                                            │
│                    ┌──────────────────────────────────┐                    │
│                    │           SUCCESS                │                    │
│                    │  Update Voiceprint (EMA)         │                    │
│                    │  Encrypt + Store                 │                    │
│                    └──────────────────────────────────┘                    │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Encryption Architecture

| Component | Algorithm | Key Source |
|-----------|-----------|------------|
| Challenge Tokens | HMAC-SHA256 | `L3_HMAC_SECRET` environment variable |
| Voiceprint Storage | AES-256-GCM | `VOICEPRINT_KEY` + tenant key derivation |
| JWT Tokens | HS256 (internal) / RS256 (host apps) | `AAA_JWT_SECRET` / PEM public keys |

---

## 3. Team Contribution Overview

### 3.1 Responsibilities by Team Member

| Team Member | Role | Modules Owned |
|-------------|------|---------------|
| **Surya** | Project Lead, AAA Core | `api/v1/`, `services/`, `main.py`, integration |
| **Karthik** | Security & Perimeter Defense | `security/`, `core/logging.py`, encryption |
| **Nandan** | ASR & CallGuard | `aaa_asr/`, `layer3_asr.py`, `api/v1/risk.py` |
| **Navadeep** | Infrastructure & Backend | `main.py` (legacy), `db.py`, `models.py` |
| **Aditya** | Frontend & Layer 3 | `layer3_adaptive.py`, `frontend/` |

### 3.2 Contribution Status

| Member | Day 1 | Day 2 | Day 3 | Day 4 |
|--------|-------|-------|-------|-------|
| Surya | PR #8 merged | PR #9 merged | 8 commits (pending) | This plan |
| Karthik | — | — | PR #14 merged | Security review |
| Nandan | — | PR #10 merged | PR #15 merged | ASR review |
| Navadeep | Baseline | — | — | — |
| Aditya | Baseline | — | — | Frontend (if needed) |

---

## 4. Remaining Tasks and Technical Debt

### 4.1 Incomplete Tasks from Day 3

| Task | Planned | Status | Notes |
|------|---------|--------|-------|
| Structured Logging | DAY3 §Task 5 | ⚠️ Partial | `StructuredSecurityFormatter` exists but not wired to all endpoints |
| Adapter Integration | DAY3 §Task 6 | ⚠️ Partial | Adapters exist but `main.py` uses direct layer functions |
| Day 3 PR | — | ❌ Not Created | 8 commits ahead of main |

### 4.2 Technical Debt

| ID | Category | Description | Severity | Location |
|----|----------|-------------|----------|----------|
| TD-001 | Architecture | Legacy `/auth/*` routes coexist with `/v1/*` | Medium | `main.py:204-470` |
| TD-002 | Logging | Not all endpoints use structured logging | Low | Various |
| TD-003 | Adapters | Adapters not wired into main pipeline | Low | `main.py` |
| TD-004 | Monitoring | No Prometheus metrics endpoint | Medium | Issue #6 |
| TD-005 | Testing | Layer 1 speaker verification unit tests missing | Low | Issue #3 |

### 4.3 Open GitHub Issues

| Issue | Title | Status | Day 4 Candidate |
|-------|-------|--------|-----------------|
| #7 | Rate limiting for brute force prevention | ✅ **Implemented** | Close issue |
| #6 | Logging and metrics for authentication | ⚠️ Partial | **YES** |
| #3 | Unit tests for Layer 1 speaker verification | ❌ Open | Maybe |
| #4 | Keyboard navigation and screen reader | ❌ Open | Frontend (out of scope) |
| #1 | Real-time audio waveform visualization | ❌ Open | Frontend (out of scope) |

---

## 5. Day 4 Objectives and Scope

### 5.1 Primary Objectives (P0)

| Objective | Description | Effort |
|-----------|-------------|--------|
| **Merge Day 3** | Create PR, merge to main | 1h |
| **Close Issue #7** | Rate limiting already implemented | 15min |
| **Production Readiness** | Verify all critical paths | 2h |
| **Final Deliverables** | Completion report, documentation | 2h |

### 5.2 Secondary Objectives (P1) — *Requires Confirmation*

| Objective | Description | Effort | Confirmed |
|-----------|-------------|--------|-----------|
| **Metrics Endpoint** | Prometheus `/metrics` (Issue #6) | 3h | ⚠️ PENDING |
| **Structured Logging Wiring** | Apply to all v1 endpoints | 2h | ⚠️ PENDING |
| **Legacy Route Deprecation** | Add deprecation warnings | 1h | ⚠️ PENDING |

### 5.3 Out of Scope

| Item | Reason |
|------|--------|
| Frontend accessibility (Issue #4) | Requires Aditya |
| Audio waveform visualization (Issue #1) | Frontend feature |
| Adapter rewiring in main.py | Risk of regression on final day |
| New ML model integration | No team bandwidth |

---

## 6. Implementation Tasks

### Task 1: Merge Day 3 Branch (P0)

**Priority:** P0 — Must complete
**Effort:** 1 hour
**Owner:** Surya

#### Description

Create and merge PR for `feat/surya-day3-integration` branch containing 8 commits:
- Voiceprint encryption service
- JWT authentication integration
- V1 API endpoints
- CORS restriction
- Rate limiting tests
- E2E integration tests
- API v1 tests
- Voiceprint service tests

#### Steps

1. Run full test suite to verify 324 tests pass
2. Run ruff lint check
3. Create PR with summary of all Day 3 changes
4. Request review (if required)
5. Merge to main
6. Tag release candidate

#### Acceptance Criteria

- [ ] All 324 tests pass
- [ ] No lint errors
- [ ] PR created and merged
- [ ] Main branch updated

---

### Task 2: Close Issue #7 (P0)

**Priority:** P0 — Quick win
**Effort:** 15 minutes
**Owner:** Surya

#### Description

Issue #7 requests rate limiting for brute force prevention. This is already implemented:

- `backend/app/core/ratelimit.py` — SlowAPI limiter
- `main.py:47-48` — Rate limit handler
- All authentication endpoints have decorators:
  - `/auth/challenge` — 10/minute
  - `/auth/verify` — 5/minute
  - `/auth/enroll` — 3/5minutes
  - `/v1/challenges` — 10/minute
  - `/v1/verify` — 5/minute
  - `/v1/enroll` — 3/5minutes

#### Steps

1. Verify rate limiting tests pass (`test_rate_limiting.py`)
2. Close issue with implementation reference
3. Update issue comment with test evidence

#### Acceptance Criteria

- [ ] Issue #7 closed
- [ ] Comment references implementation files

---

### Task 3: Prometheus Metrics Endpoint (P1) ⚠️ REQUIRES CONFIRMATION

**Priority:** P1 — Secondary
**Effort:** 3 hours
**Owner:** Surya
**Blocked By:** Project lead confirmation

#### Description

Implement `/metrics` endpoint for Prometheus scraping per Issue #6.

**Proposed Metrics:**
```
aaa_auth_attempts_total{result="accept|reject", layer="l1|l2|l3|asr"}
aaa_auth_latency_seconds{layer="l1|l2|l3|asr"}
aaa_active_challenges_total
aaa_voiceprints_total
```

#### Technical Implementation

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

AUTH_ATTEMPTS = Counter(
    "aaa_auth_attempts_total",
    "Total authentication attempts",
    ["result", "layer"]
)

AUTH_LATENCY = Histogram(
    "aaa_auth_latency_seconds",
    "Authentication latency by layer",
    ["layer"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_CHALLENGES = Gauge(
    "aaa_active_challenges_total",
    "Number of unexpired challenges"
)
```

#### Files Affected

- `backend/app/core/metrics.py` (new)
- `backend/app/main.py` (add `/metrics` endpoint)
- `backend/app/api/v1/verify.py` (instrument)
- `backend/requirements.txt` (add `prometheus-client`)

#### Acceptance Criteria

- [ ] `/metrics` endpoint returns Prometheus format
- [ ] Auth attempts tracked by result and layer
- [ ] Latency histograms for each layer
- [ ] Tests for metrics endpoint

---

### Task 4: Structured Logging Wiring (P1) ⚠️ REQUIRES CONFIRMATION

**Priority:** P1 — Secondary
**Effort:** 2 hours
**Owner:** Surya
**Blocked By:** Project lead confirmation

#### Description

Wire `StructuredSecurityFormatter` (already implemented by Karthik) to all v1 endpoints.

#### Current State

`core/logging.py` contains `StructuredSecurityFormatter` but it's not applied to:
- API endpoint handlers
- Authentication middleware
- Database operations

#### Technical Implementation

```python
# backend/app/main.py additions
import logging
from .core.logging import StructuredSecurityFormatter

# Configure root logger
handler = logging.StreamHandler()
handler.setFormatter(StructuredSecurityFormatter())
logging.getLogger("aaa_engine").addHandler(handler)
logging.getLogger("aaa_engine").setLevel(logging.INFO)
```

```python
# In endpoint handlers
logger = logging.getLogger("aaa_engine.verify")
logger.info("Verification attempt", extra={
    "user_id": user_id,
    "session_id": session_id,
    "result": "ACCEPT",
    "layer_blocked": None
})
```

#### Files Affected

- `backend/app/main.py`
- `backend/app/api/v1/verify.py`
- `backend/app/api/v1/enroll.py`
- `backend/app/api/v1/challenges.py`

#### Acceptance Criteria

- [ ] All v1 endpoints log in JSON format
- [ ] Sensitive fields (embeddings, audio) excluded
- [ ] Log level configurable via environment

---

### Task 5: Legacy Route Deprecation Warnings (P1) ⚠️ REQUIRES CONFIRMATION

**Priority:** P1 — Secondary
**Effort:** 1 hour
**Owner:** Surya
**Blocked By:** Project lead confirmation

#### Description

Add deprecation warnings to legacy `/auth/*` endpoints pointing to `/v1/*` equivalents.

#### Technical Implementation

```python
# In legacy endpoint handlers
import warnings

@app.post("/auth/enroll", response_model=EnrollResponse, deprecated=True)
async def enroll(...):
    warnings.warn(
        "POST /auth/enroll is deprecated. Use POST /v1/enroll instead.",
        DeprecationWarning
    )
    # ... existing logic
```

#### Files Affected

- `backend/app/main.py` (lines 220-470)

#### Acceptance Criteria

- [ ] Legacy endpoints marked `deprecated=True` in OpenAPI
- [ ] Warning logged on each legacy endpoint call
- [ ] v1 equivalents documented in response headers

---

### Task 6: Production Readiness Verification (P0)

**Priority:** P0 — Must complete
**Effort:** 2 hours
**Owner:** Surya

#### Description

Comprehensive verification of all production requirements.

#### Checklist

**Security:**
- [ ] No fallback secrets in production mode
- [ ] JWT validation enforced
- [ ] Voiceprint encryption active
- [ ] CORS restricted to explicit origins
- [ ] Rate limiting on all auth endpoints
- [ ] No raw scores in v1 responses

**Database:**
- [ ] Challenge tokens persisted
- [ ] Atomic token consumption working
- [ ] Voiceprints stored encrypted

**API:**
- [ ] All v1 endpoints functional
- [ ] Error responses standardized
- [ ] Request ID tracking working

**Testing:**
- [ ] All 324 tests pass
- [ ] No lint errors
- [ ] CI/CD pipeline green

---

### Task 7: Final Deliverables (P0)

**Priority:** P0 — Must complete
**Effort:** 2 hours
**Owner:** Surya

#### Description

Prepare final sprint deliverables.

#### Deliverables

1. **Day 4 Completion Report** (`docs/surya/DAY4_COMPLETION_REPORT.md`)
   - Summary of all 4 days
   - Test coverage metrics
   - Known limitations
   - Deployment instructions

2. **Final Test Report** (`04_FINAL_DELIVERABLES/DAY4/TEST_REPORT.md`)
   - Test execution results
   - Coverage breakdown
   - Performance benchmarks

3. **Release Notes** (`CHANGELOG.md` update)
   - Version increment
   - Feature summary
   - Breaking changes (if any)

#### Acceptance Criteria

- [ ] Day 4 completion report written
- [ ] Test report generated
- [ ] CHANGELOG updated

---

## 7. Files and Modules Affected

### 7.1 Files to Create (if P1 tasks confirmed)

| File | Purpose | Task |
|------|---------|------|
| `backend/app/core/metrics.py` | Prometheus metrics | Task 3 |
| `docs/surya/DAY4_COMPLETION_REPORT.md` | Completion report | Task 7 |
| `04_FINAL_DELIVERABLES/DAY4/TEST_REPORT.md` | Test report | Task 7 |

### 7.2 Files to Modify (if P1 tasks confirmed)

| File | Modification | Task |
|------|--------------|------|
| `backend/app/main.py` | Add deprecation warnings, metrics endpoint | Tasks 3, 4, 5 |
| `backend/app/api/v1/verify.py` | Add structured logging, metrics | Tasks 3, 4 |
| `backend/app/api/v1/enroll.py` | Add structured logging | Task 4 |
| `backend/app/api/v1/challenges.py` | Add structured logging | Task 4 |
| `backend/requirements.txt` | Add prometheus-client | Task 3 |
| `CHANGELOG.md` | Add release notes | Task 7 |

### 7.3 Files Read-Only (No Modifications)

| File | Reason |
|------|--------|
| `backend/app/security/*` | Karthik's domain |
| `backend/app/aaa_asr/*` | Nandan's domain |
| `backend/app/layer1_speaker.py` | Working, no changes needed |
| `backend/app/layer2_deepfake.py` | Working, no changes needed |

---

## 8. Team Dependencies

### 8.1 Required Confirmations

| From | Question | Blocking |
|------|----------|----------|
| **Project Lead** | Approve P1 tasks (metrics, logging, deprecation) | Yes |
| **Karthik** | Review security implementation before merge | No |
| **Nandan** | Review ASR integration | No |

### 8.2 Resolved Dependencies

All Day 3 dependencies resolved per `SURYA_DAY3_DEPENDENCY_RESPONSE.md`:
- ✅ DEP-SEC-001: Tenant Authentication Contract
- ✅ DEP-SEC-002: JWT Public Keys
- ✅ DEP-SEC-003: VR Interface
- ✅ DEP-SEC-004: Banking Shield Integration
- ✅ DEP-SEC-005: Security Review
- ✅ DEP-SEC-006: Encryption Key Management

---

## 9. API, Security, and Integration Considerations

### 9.1 API Considerations

| Endpoint | Consideration |
|----------|---------------|
| `/v1/*` | All endpoints support optional JWT authentication |
| `/metrics` | Should NOT require authentication |
| Legacy `/auth/*` | Deprecation warnings only, not removal |

### 9.2 Security Considerations

| Area | Requirement |
|------|-------------|
| Metrics | No sensitive data in metrics |
| Logging | Embeddings and audio bytes excluded |
| Deprecation | No breaking changes to legacy endpoints |

### 9.3 Integration Considerations

| System | Status |
|--------|--------|
| Banking Shield | Integration ready via `/v1/verify` |
| CallGuard | Integration ready via `/v1/risk/transcript` |
| Frontend | Uses legacy `/auth/*` routes |

---

## 10. Testing Strategy

### 10.1 Current Test Coverage

| Test File | Tests | Category |
|-----------|-------|----------|
| `test_day1_foundation.py` | 23 | Foundation |
| `test_token_persistence.py` | 17 | Challenge lifecycle |
| `test_adapters.py` | 17 | Mock adapters |
| `test_api_v1.py` | 26 | API endpoints |
| `test_e2e_integration.py` | 22 | End-to-end |
| `test_rate_limiting.py` | 10 | Rate limiting |
| `test_voiceprint_service.py` | 21 | Encryption service |
| `test_jwt_auth.py` | 10 | JWT authentication |
| `test_voiceprint_crypto.py` | 5 | AES-256-GCM |
| `test_challenge_lifecycle.py` | 5 | Challenge state |
| `test_host_auth.py` | 4 | Host app auth |
| `test_risk_transcript.py` | 4 | Risk analysis |
| `test_phrase_matcher.py` | 56 | Phrase matching |
| **Total** | **324** | |

### 10.2 Day 4 Test Additions (if P1 confirmed)

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_metrics.py` | ~8 | Prometheus endpoint |
| `test_structured_logging.py` | ~5 | Log format verification |

### 10.3 Test Execution

```bash
# Run all tests
cd backend
python -m pytest -v

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific category
python -m pytest tests/test_api_v1.py -v
```

---

## 11. Acceptance Criteria

### 11.1 Task 1: Merge Day 3 Branch

- [ ] `pytest` passes with 324+ tests
- [ ] `ruff check .` returns no errors
- [ ] PR created with descriptive title and body
- [ ] PR merged to main
- [ ] Branch deleted after merge

### 11.2 Task 2: Close Issue #7

- [ ] Issue #7 closed with comment
- [ ] Comment includes:
  - Reference to `core/ratelimit.py`
  - Reference to `test_rate_limiting.py`
  - List of rate-limited endpoints

### 11.3 Task 3: Prometheus Metrics (if confirmed)

- [ ] `/metrics` returns valid Prometheus format
- [ ] `aaa_auth_attempts_total` counter increments
- [ ] `aaa_auth_latency_seconds` histogram populated
- [ ] Tests pass for metrics endpoint
- [ ] Grafana dashboard template created (optional)

### 11.4 Task 4: Structured Logging (if confirmed)

- [ ] All v1 endpoints log JSON format
- [ ] Log entries include: timestamp, level, logger, message
- [ ] Sensitive fields excluded (embedding, audio_bytes)
- [ ] Log level configurable via `LOG_LEVEL` env var

### 11.5 Task 5: Legacy Deprecation (if confirmed)

- [ ] Legacy endpoints show `deprecated: true` in OpenAPI
- [ ] Deprecation warning logged on each call
- [ ] No functional changes to legacy endpoints

### 11.6 Task 6: Production Readiness

- [ ] All security controls verified
- [ ] Database persistence verified
- [ ] API functionality verified
- [ ] CI/CD pipeline passing

### 11.7 Task 7: Final Deliverables

- [ ] `DAY4_COMPLETION_REPORT.md` created
- [ ] Test report with coverage metrics
- [ ] `CHANGELOG.md` updated with release notes

---

## 12. Risks and Mitigation

### 12.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Merge conflicts | Low | Medium | Run git fetch before merge |
| Test failures after merge | Low | High | Run full test suite before PR |
| P1 tasks not confirmed | Medium | Low | Focus on P0 tasks first |
| Team availability for reviews | Medium | Medium | Async reviews acceptable |
| Time overrun | Medium | Medium | Skip P1 if time-constrained |

### 12.2 Blockers

| Blocker | Status | Resolution |
|---------|--------|------------|
| P1 task confirmation | ⚠️ PENDING | Awaiting project lead |
| Team review availability | Unknown | Async acceptable |

---

## 13. Day 4 Completion Checklist

### P0 Tasks (Must Complete)

- [ ] **Task 1:** Create and merge Day 3 PR
- [ ] **Task 2:** Close Issue #7 (rate limiting)
- [ ] **Task 6:** Verify production readiness
- [ ] **Task 7:** Write final deliverables

### P1 Tasks (If Confirmed)

- [ ] **Task 3:** Implement Prometheus metrics endpoint
- [ ] **Task 4:** Wire structured logging to v1 endpoints
- [ ] **Task 5:** Add legacy route deprecation warnings

### Final Verification

- [ ] All tests pass (324+)
- [ ] No lint errors
- [ ] Main branch updated
- [ ] Documentation complete
- [ ] Release candidate tagged

---

## Schedule

| Time | Task | Duration |
|------|------|----------|
| 09:00–09:30 | Review plan, confirm P1 tasks with lead | 30min |
| 09:30–10:30 | **Task 1:** Merge Day 3 branch | 1h |
| 10:30–10:45 | **Task 2:** Close Issue #7 | 15min |
| 10:45–12:45 | **Task 6:** Production readiness verification | 2h |
| 12:45–13:30 | Lunch | — |
| 13:30–16:30 | **Tasks 3–5:** P1 tasks (if confirmed) | 3h |
| 16:30–18:00 | **Task 7:** Final deliverables | 1.5h |

---

## Appendix: Commands Reference

### Git Operations

```bash
# Fetch latest from remote
git fetch origin main

# Check commits ahead of main
git log --oneline main..HEAD

# Create PR
gh pr create --title "feat: Day 3 Integration" --body "..."

# Merge PR
gh pr merge <PR_NUMBER> --merge
```

### Test Execution

```bash
# Full test suite
cd backend && python -m pytest -v

# With coverage
python -m pytest --cov=app --cov-report=html

# Lint check
python -m ruff check .
```

### Server Startup

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

**Document Version:** 1.0
**Created:** November 14, 2026
**Status:** Awaiting Project Lead Confirmation for P1 Tasks
