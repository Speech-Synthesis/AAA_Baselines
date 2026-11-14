# AAA Engine — Day 3 Task 4: Consolidated Defect Audit, Evidence Verification and Retest Plan

**Document ID:** `NANDAN_DAY3_TASK4_CONSOLIDATED_DEFECT_AUDIT`  
**Execution Date:** 2026-11-14  
**Audit Lead:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Target Repository:** `E:\AAA_PROJECT\AAA_Baselines`  
**Active Branch:** `feat/nandan-asr-callguard-day2`  
**Integrated HEAD Commit:** `e90be917f542bc86b0b91a2e4de64427f1888afc` (Synchronized with `origin/main`)  
**Mode:** STRICT READ-ONLY CONSOLIDATION AUDIT (No application files modified)

---

## 1. Executive Summary

This consolidated audit synthesizes the findings from Step 1 (Independent Phrase Matcher Verification) and Step 2 (Independent CallGuard Frontend Verification) under Day 3 Task 4. 

The audit rigorously verifies physical evidence on disk, investigates the exact technical causes of identified environment and contract defects, evaluates the four seeded CallGuard scenarios and their visual presentation, compares API schemas against backend specifications, and formulates the comprehensive Day 3 Defect and Retest Register.

### High-Level Audit Findings:
1. **Report Verification:** Both previous independent reports exist on the E: drive, are non-empty, and their referenced evidence artifacts are validated on disk.
2. **Phrase Matcher Logic:** The core phrase matcher implementation (`backend/app/aaa_asr/phrase_matcher.py`) achieved a **100% PASS** rate across 62 independent test cases spanning exact matching, casing, punctuation, whitespace, approved/unapproved fillers, digit conversion, stutter rejection, boundary thresholds, and adversarial injection resistance.
3. **Automated Pytest Blocker (`DEF-D3-003`):** The automated pytest suite (`test_phrase_matcher.py`, 160 items) cannot execute in the standard Python 3.8 environment due to an upstream syntax error in teammate-owned `backend/app/core/config.py:28` (`str | None` PEP 604 union type), which crashes pytest at fixture setup.
4. **CallGuard Frontend Verification:** The CallGuard application (`apps/callguard`) runs smoothly in mock mode, successfully loads all 4 seeded scenarios (including Scenario 4: Address Change), and **strictly purges all numerical confidence percentages (0% certainty leakage)**.
5. **Live API Contract Mismatch (`DEF-D3-001`):** While mock mode functions cleanly, CallGuard’s live API client (`api.js:256`) sends `{ tenant_id, segments }` in the JSON body, whereas the backend schema (`TranscriptRiskRequest`) requires `{ session_id, transcript }` with tenant scoping via Bearer JWT.

---

## 2. Report Files Existence and Evidence Audit (Phase A)

Both expected report files were inspected on disk:

| Report File | Absolute Path | Size (Bytes) | Last Modified Timestamp | Evidence & Internal Consistency |
|:---|:---|:---:|:---:|:---|
| **Step 1: Phrase Matcher** | `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\TEST_REPORTS\NANDAN_DAY3_INDEPENDENT_PHRASE_MATCHER_VERIFICATION.md` | 22,077 | 2026-11-14 22:15:01 IST | **Consistent.** Details 62 independent test cases, Pytest 160 error output, and exact traceback for `DEF-D3-003`. |
| **Step 2: CallGuard Frontend** | `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\TEST_REPORTS\NANDAN_DAY3_INDEPENDENT_CALLGUARD_VERIFICATION.md` | 11,906 | 2026-11-14 22:24:38 IST | **Consistent.** Details 4 seeded calls, zero numerical confidence verification, and links to host-observed screenshot evidence. |

### Supporting Evidence File Audit:
- **Pytest Output Capture (Day 1):** `04_FINAL_DELIVERABLES/TEST_REPORTS/DEVELOPER_TESTS/01_phrase_matcher_pytest_output.txt` (Confirmed present, 160 passed).
- **Independent Verification Script:** `E:\AAA_PROJECT\AAA_Baselines\scratch_independent_phrase_matcher_audit.py` (Confirmed present on E:, 62/62 passed).
- **Host-Verified Browser Screenshot:** `C:\Users\DELL\.gemini\antigravity\brain\a009ad38-be4d-4ee7-a7a3-4adaf61d47f6\browser_evidence\16b35c20-2309-4ce3-9734-dfe8b5714f77\final_step_53.png` (Confirmed present, 45,587 bytes).

---

## 3. Phrase Matcher Technical Review (Phase B)

### Investigation of `DEF-D3-003`:
- **Source Location:** `backend/app/core/config.py:28`
  ```python
  # Security - No fallback defaults for secrets in production
  L3_HMAC_SECRET: str | None = None
  ```
- **Root Cause:** The `|` operator for type union expressions was introduced in Python 3.10 (PEP 604). In Python 3.8.2, evaluating `str | None` at module import time raises:
  `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`
- **Failure Propagation in Pytest:**
  `backend/tests/conftest.py` declares an autouse fixture:
  ```python
  @pytest.fixture(autouse=True)
  def clear_settings_cache():
      from app.core.config import get_settings
      get_settings.cache_clear()
      yield
      get_settings.cache_clear()
  ```
  Because this fixture runs automatically for every test in `backend/tests/`, pytest fails before executing any test in `test_phrase_matcher.py`, producing **160 errors in 3.59s**.
- **Module Isolation:** `backend/app/aaa_asr/phrase_matcher.py` includes `from __future__ import annotations` (line 24) and imports only standard libraries (`unicodedata`, `re`, `dataclasses`). It does not import `config.py` or `conftest.py`.
- **Core Behavioral Verification:** The 62 independent test cases run directly against `phrase_matcher.py` verified 100% of all required functional and security invariants:
  - Exact phrase match: 4/4 PASS
  - Case folding (lower/upper/mixed): 4/4 PASS
  - Punctuation & Contraction expansion: 5/5 PASS
  - Whitespace collapsing: 4/4 PASS
  - Approved/Unapproved fillers: 5/5 PASS (unapproved filler `like` correctly rejected)
  - Word omission & extra words: 8/8 PASS (strictly fail-closed)
  - Bidirectional digit normalization: 6/6 PASS
  - Stutter rejection: 3/3 PASS (repeated tokens NOT collapsed)
  - Empty, whitespace, punctuation, None inputs: 7/7 PASS (fails safely as `NO_SPEECH` / `MISMATCH`)
  - Challenge validity (expired / timeout): 2/2 PASS
  - Confidence & boundary gating: 8/8 PASS (high confidence $0.99$ cannot override text mismatch)
  - Adversarial & homoglyph injection: 6/6 PASS (Cyrillic homoglyphs strictly rejected; control characters sanitized).

---

## 4. CallGuard Frontend Technical Review (Phase C)

### 1. Risk Level and Action Mapping Consistency:
- Supported risk tiers: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- Supported protocol actions: `APPROVE`, `REVIEW`, `STEP_UP`, `DENY`.
- Action mapping definitions in `RiskPanel.jsx` align with the frozen API contract:
  - `APPROVE`: Normal call flow; no abnormal signals.
  - `REVIEW`: Single risk marker present (e.g. Unverified Beneficiary).
  - `STEP_UP`: Multiple risk markers present; trigger voice challenge.
  - `DENY`: Severe threat / credential harvesting detected; escalate to Fraud Operations.

### 2. Discrepancy Analysis:
- **`CALL-2026-1002` (High vs Critical):**
  - In `mockData.js`, `CALL-2026-1002` has static preview `riskLevel: "HIGH"`.
  - In `api.js:analyzeTranscriptRisk`, the dynamic transcript analyzer evaluates the text ("bypass OTP immediately", "terminate you") and elevates the assessment to `risk_level: "CRITICAL"`.
  - Consequently, the Dashboard priority queue displays `HIGH RISK`, while the detailed ActiveCall `RiskPanel` renders `CRITICAL RISK (THREAT DETECTED)` with alert styling. This is an intended dynamic upgrade by the risk engine, but constitutes an informational discrepancy against static mock metadata (`DEF-D3-005`).
- **`CALL-2026-1004` (Medium Risk Styling in Queue Table):**
  - In `apps/callguard/src/pages/Dashboard.jsx:56, 74`:
    ```javascript
    const isHighRisk = call.riskLevel === 'HIGH';
    <span className={`badge ${isHighRisk ? 'badge-high' : 'badge-low'}`}>
      {call.riskLevel} RISK
    </span>
    ```
  - Because `call.riskLevel === 'MEDIUM'`, `isHighRisk` evaluates to `false`. The badge applies CSS class `badge-low` (green) with text "MEDIUM RISK".
  - In `ActiveCall`'s `RiskPanel`, `getRiskBadge('MEDIUM')` correctly applies `badge-medium` (yellow). This is a cosmetic styling bug in `Dashboard.jsx` (`DEF-D3-004`).

### 3. Removal of Numerical Confidence:
- Operator RiskPanel was thoroughly audited. Confirmed **zero occurrences** of numerical confidence percentages, certainty meters, or raw probabilities (e.g. `96%` previously in Day 2 was completely removed).

### 4. Null and Unknown Value Handling:
- In `RiskPanel.jsx:27`, `if (!riskData)` returns a safe fallback card.
- Defensive defaults (`risk_level || 'UNKNOWN'`, `riskData.risk_indicators || []`) prevent rendering crashes on partial payloads.

---

## 5. API Contract Consistency Analysis (Phase D)

Comparison between CallGuard Frontend Client (`apps/callguard/src/services/api.js`), UI Component (`RiskPanel.jsx`), and Backend API (`backend/app/api/v1/risk.py` / `backend/app/schemas/risk.py`):

| Contract Dimension | CallGuard Client (`api.js`) | Backend Schema (`risk.py` / `schemas/risk.py`) | Status | Impact / Notes |
|:---|:---|:---|:---:|:---|
| **Endpoint URL** | `POST /v1/risk/transcript` | `POST /v1/risk/transcript` | **MATCH** | Router prefix `/risk` under `/v1`. |
| **Request: Session ID** | Missing in live request body (`body: { tenant_id, segments }`) | `session_id: str` (Required) | **MISMATCH (`DEF-D3-001`)** | Backend returns 422 if `session_id` omitted. |
| **Request: Transcript** | Sends `segments: Array<{speaker, text, timestamp}>` | `transcript: str` (Required, min_length=1) | **MISMATCH (`DEF-D3-001`)** | Backend expects flattened string, not array. |
| **Request: Tenant Auth** | Sends `tenant_id` in JSON body | Injected via Bearer JWT (`Depends(get_current_tenant)`) | **MISMATCH (`DEF-D3-001`)** | Backend rejects body tenant; requires JWT header. |
| **Response: Request ID** | `request_id` | `request_id: str` | **MATCH** | UUID string. |
| **Response: Risk Level** | `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) | `risk_level: RiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) | **MATCH** | Enums match identically. |
| **Response: Indicators** | `risk_indicators` (array of strings) | `risk_indicators: list[str]` | **MATCH** | Safe public reason codes. |
| **Response: Action** | `recommended_action` (`APPROVE`, `REVIEW`, `STEP_UP`, `DENY`) | `recommended_action: str` (`APPROVE`, `REVIEW`, `STEP_UP`, `DENY`) | **MATCH** | Exact string matching. |
| **Response: Confidence** | `confidence: float` (Present in response, excluded from UI) | `confidence: float` (0.0 - 1.0) | **MATCH** | Backend sends score; frontend safely does not display it. |
| **Response: Model Version**| `model_version: "aaa-vr-transcript-risk-v1"` | `model_version: "aaa-vr-transcript-risk-v1"` | **MATCH** | Aligned. |
| **Response: Timestamp** | `analyzed_at` (ISO 8601) | `analyzed_at: str` (ISO 8601) | **MATCH** | Aligned. |

### Contract Summary:
- **Mock Mode:** 100% compatible. Mock adapter in `api.js` returns fields matching the backend response schema.
- **Live Mode:** Blocked by `DEF-D3-001`. Client `POST` body format does not match `TranscriptRiskRequest`.

---

## 6. Security and Privacy Review (Phase E)

| Security Control | Requirement | Audit Finding | Verdict |
|:---|:---|:---|:---:|
| **Raw Audio Exclusion** | No audio streams, PCM, WebM, or WAV buffers in CallGuard. | Zero audio capture or audio transport in `apps/callguard`. Audio is handled directly by AAA Web Capture over `/v1/verify`. | **PASS** |
| **Biometric Privacy** | Zero voiceprint embeddings or raw acoustic vectors in frontend. | State and mock objects contain only pseudonymous references (`customer_001`). No biometric embeddings present. | **PASS** |
| **Certainty Purge** | No numerical confidence or probability presented to operator. | Verified in rendered DOM: 0% confidence leakage. Only qualitative operational tiers shown. | **PASS** |
| **Default Mock Isolation**| Application must default to mock mode to prevent live calls. | `api.js:14` enforces `VITE_USE_MOCK_API=true` by default. | **PASS** |
| **Secret Sanitization** | No API keys, JWT secrets, or tokens in source or logs. | Zero hardcoded credentials in `apps/callguard`. Console logs remain clean. | **PASS** |
| **Network Confinement** | No unintentional outbound requests to live backends in mock mode. | Verified in browser audit: 0 external/backend network requests made. | **PASS** |

---

## 7. Consolidated Defect Register (Phase F)

| Defect ID | Component | Severity | Evidence | Impact | Status | Owner |
|:---:|:---|:---:|:---|:---|:---:|:---:|
| **DEF-D3-001** | `apps/callguard/src/services/api.js:256` | High (Live) / Low (Mock) | Live `POST` body sends `{ tenant_id, segments }` instead of `{ session_id, transcript }` and lacks Bearer JWT header. | Blocks live backend integration (returns 422/401). Mock mode is unaffected. | **OPEN** | Nandan / Karthik |
| **DEF-D3-002** | `apps/callguard/src/components/RiskPanel.jsx` | Medium | Historic RiskPanel displayed "Threat Assessment Certainty: 96%". | Operator over-reliance on synthetic score. | **FIXED — VERIFIED** | Nandan (Commit `da2d2ff`) |
| **DEF-D3-003** | `backend/app/core/config.py:28` | Medium (Test Harness) | `L3_HMAC_SECRET: str | None = None` uses PEP 604 union syntax in Python 3.8. | Crashes `pytest` at fixture setup (`conftest.py:68`) for all 160 tests. Standalone matcher passes 62/62. | **OPEN** (Upstream Teammate File) | Bhavan Surya / Karthik |
| **DEF-D3-004** | `apps/callguard/src/pages/Dashboard.jsx:56, 74` | Low (Cosmetic) | Binary badge toggle (`isHighRisk ? 'badge-high' : 'badge-low'`) lacks `MEDIUM` condition. | `CALL-2026-1004` displays green `badge-low` style in Dashboard queue instead of yellow `badge-medium`. | **OPEN** | Nandan |
| **DEF-D3-005** | `apps/callguard/src/data/mockData.js:84` | Low (Informational) | `mockData.js` sets preview `riskLevel: "HIGH"`, but `analyzeTranscriptRisk` evaluates text to `"CRITICAL"`. | Queue shows `HIGH RISK`, while detail RiskPanel displays `CRITICAL RISK`. | **OPEN** | Nandan |

---

## 8. Missing Evidence Audit

1. **Aditya Peer Testing Evidence:**
   - As documented in Section 1 of the audit, **zero commits, reports, defect logs, or screenshots exist from Aditya**. All test evidence on disk was authored and executed by Nandan.
2. **Missing Repository Artifacts:**
   - No artifacts referenced in `NANDAN_DAY3_INDEPENDENT_PHRASE_MATCHER_VERIFICATION.md` or `NANDAN_DAY3_INDEPENDENT_CALLGUARD_VERIFICATION.md` are missing. All referenced script outputs, screenshots, and logs are present and verified on disk.

---

## 9. Retest Recommendations

1. **Retest 1: Automated Pytest Suite (`test_phrase_matcher.py`)**
   - **Prerequisite:** Upstream teammate resolves `DEF-D3-003` in `backend/app/core/config.py` (either by adding `from __future__ import annotations` or changing `str | None` to `Optional[str]`), or test runner is upgraded to Python 3.10+.
   - **Action:** Re-run `python -m pytest backend/tests/test_phrase_matcher.py -v` and record all 160 test results.
2. **Retest 2: Dashboard Queue Medium Badge (`DEF-D3-004`)**
   - **Prerequisite:** Update `Dashboard.jsx` to map `call.riskLevel === 'MEDIUM'` to `badge-medium`.
   - **Action:** Open Dashboard in browser and verify `CALL-2026-1004` renders yellow badge.
3. **Retest 3: Live API Client Contract Alignment (`DEF-D3-001`)**
   - **Prerequisite:** Update `api.js:analyzeTranscriptRisk` to serialize `session_id`, flattened `transcript`, and include Bearer token header.
   - **Action:** Execute integration test against running live FastAPI backend.

---

## 10. Official Day 3 Task 4 Acceptance Verdict

### **VERDICT: PARTIAL**

#### Acceptance Rationale:
- **Phrase Matcher Functional Verification:** **PASS** (62/62 independent test cases verified across all 13 categories).
- **CallGuard Frontend Verification:** **PASS** (4/4 scenarios verified in live UI, 0% numerical leakage, mock mode confirmed).
- **Automated Test Suite Execution:** **BLOCKED** by upstream `backend/app/core/config.py:28` (`DEF-D3-003`).
- **Independent Peer Testing (Aditya):** **UNVERIFIED / NOT DELIVERED** (Aditya has submitted zero test reports or defect logs to date).
- **Overall Day 3 Task 4 Status:** **PARTIAL**, pending upstream fix of `DEF-D3-003` and delivery of Aditya's peer testing report.
