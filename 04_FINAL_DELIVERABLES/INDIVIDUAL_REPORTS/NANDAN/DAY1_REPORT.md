# AAA Engine Day 1 Individual Implementation Report

**Author:** Nandan (Member 5)  
**Assigned Work Packages:**  
1. AAA-ASR — Automatic Speech Recognition & Challenge Phrase Verifier  
2. Strict Challenge Phrase Matching  
3. CallGuard Application Development  
4. CallGuard Mock API Integration Preparation  

**Sprint Date:** 11 November 2026  
**Independent Peer Reviewer:** Aditya  
**Project Lead:** Surya  

---

## 1. Environment & Setup Report

### 1.1 Runtimes & Versions Verified
- **Python:** `Python 3.8.2` (Verified via `python --version`)
- **Node.js:** `v22.22.1` (Verified via `node --version`)
- **npm:** `10.8.1` (Verified via `npm --version`)
- **Git:** `2.53.0.windows.1` (Verified via `git --version`)

### 1.2 Strict E: Drive Compliance
All virtual environments, packages, caches, temporary files, and generated deliverables have been strictly confined to the `E:` drive:
- **Python Virtualenv:** `E:\AAA_Project\AAA_Baselines\.venv`
- **Pip Cache:** `E:\AAA_Project\AAA_Baselines\.cache\pip`
- **Temporary Directory:** `E:\AAA_Project\AAA_Baselines\.tmp`
- **npm Node Modules:** `E:\AAA_Project\AAA_Baselines\apps\callguard\node_modules`
- **npm Cache:** `E:\AAA_Project\AAA_Baselines\.cache\npm`
- **Whisper Staging Directory:** `E:\AAA_Project\AAA_Baselines\.models\whisper`
- **Confirmation:** Zero project dependencies or caches were written to `C:`.

---

## 2. Git Repository & Ownership Verification

### 2.1 Repository Status
- **Repository:** `Speech-Synthesis/AAA_Baselines`
- **Local Path:** `E:\AAA_Project\AAA_Baselines`
- **Remote Origin:** `https://github.com/Speech-Synthesis/AAA_Baselines.git`
- **Base Branch:** `main` (verified at commit `568370b`)
- **Working Feature Branch:** `feat/nandan-asr-callguard` (created and active)

### 2.2 Strict Ownership Boundary Audit
In accordance with the strict ownership rules:
- **Modified/Created Files:**
  - `backend/app/aaa_asr/__init__.py`
  - `backend/app/aaa_asr/phrase_matcher.py`
  - `backend/app/aaa_asr/transcriber.py`
  - `backend/app/layer3_asr.py` (updated to delegate to deterministic verifier)
  - `backend/tests/__init__.py`
  - `backend/tests/test_phrase_matcher.py`
  - `apps/callguard/*` (CallGuard React/Vite application)
  - `04_FINAL_DELIVERABLES/*` (Reports and evidence)
- **Untouched Teammate Files:**
  - Surya: Core API, middleware orchestration, DB schema, capture integration.
  - Karthik: Security modules, AAA-VR engine, Banking Shield.
  - Navadeep: ECAPA-TDNN speaker verification models (`AAA_Layer1`).
  - Aditya: Wav2Vec2 deepfake detector (`AAA_Layer2`), SVG red-team lab, `layer3_adaptive.py`.

---

## 3. AAA-ASR Phrase Matcher Implementation

### 3.1 Architectural Separation
- `backend/app/aaa_asr/transcriber.py`: Dedicated to local Whisper audio transcription, tensor management, and log-probability feature extraction.
- `backend/app/aaa_asr/phrase_matcher.py`: Pure deterministic verification engine. Receives expected phrase, transcript hypothesis, and supporting signals (`confidence`, `no_speech_prob`, `audio_duration`, expiry/timeout flags).

### 3.2 Deterministic Normalization Pipeline
Applied identically to expected phrase $P$ and recognized transcript $H$:
1. Unicode NFKC normalization + lowercase conversion.
2. Contraction expansion (`don't` → `do not`, `can't` → `cannot`).
3. Punctuation and symbol stripping (replaces non-alphanumeric characters with spaces).
4. Whitespace collapsing (multi-space, tabs, newlines collapsed to single space, trimmed).
5. Removal of approved hesitation fillers: `um`, `uh`, `er`, `hmm`, `erm`, `ah`.
6. Curated digit-to-word conversion (`0`–`9` ↔ `zero`–`nine`, `20` ↔ `twenty`).
7. Word aliases (`oh` → `zero` in digit contexts).
8. British/American spelling harmonization (`colour` → `color`, `centre` → `center`).
9. **No Repeated Word Collapsing:** Stuttering or duplicate words are preserved as real speech errors and strictly cause mismatches.

### 3.3 Strict Security Verification Invariants
- **Exact Equality:** The comparison between normalized expected and recognized phrases is strict equality (`normalized_expected == normalized_hyp`).
- **Zero Fuzzy Tolerance:** Difflib `SequenceMatcher`, Levenshtein distance thresholds, and fuzzy ratios are completely removed from the authentication gate.
- **Fail Closed:** High confidence cannot override a text mismatch. Insufficient confidence (`< 0.5`) rejects a matching phrase as `LOW_CONF`. Expired challenges immediately reject with `EXPIRED_CHALLENGE`. High no-speech probability (`> 0.8`) or empty text rejects as `NO_SPEECH`. Audio under `0.5s` rejects as `TOO_SHORT`.

---

## 4. Test Suite Execution & Results

- **Test Suite Path:** `backend/tests/test_phrase_matcher.py`
- **Total Test Cases Executed:** **158**
- **Passed:** **158** (100%)
- **Failed:** **0**
- **Skipped:** **0**
- **Execution Time:** **0.36 seconds**
- **Categories Covered:** 30 comprehensive categories including exact matches, near-misses, character case, whitespaces, filler words, digit forms, missing words, extra words, reordered words, expired tokens, homophones, and regression tests against the old fuzzy matcher.

---

## 5. CallGuard Application Development

### 5.1 Architecture & Tech Stack
- Built in `apps/callguard/` using **React 18.2** and **Vite 5.0**.
- Lightweight enterprise dark theme design system without unvetted external library bloat.
- Prominent compliance indicator: `⚠️ SIMULATED CALL — DEMO DATA ONLY`.

### 5.2 Screens & Components Implemented
1. **Agent Login (`src/pages/AgentLogin.jsx`):**
   - Seeded demo agents: Sarah Jenkins (`agent.sarah`), David Chen (`agent.david`).
   - Demo credential validation; active agent session tracking.
2. **Agent Dashboard (`src/pages/Dashboard.jsx`):**
   - Priority queue of simulated calls displaying Customer Reference IDs, Call IDs, and channels.
   - Vishing risk preview badges (`LOW` vs `HIGH`).
   - One-click "Open Call Console" action.
3. **Active Call Console (`src/pages/ActiveCall.jsx`):**
   - Live elapsed call timer and customer pseudonymous metadata.
   - Dual-channel message stream with distinct caller/agent bubbles.
   - Dynamic Voice Challenge verification trigger.
4. **Vishing Risk Panel (`src/components/RiskPanel.jsx`):**
   - Displays real-time risk level (`LOW` / `MEDIUM` / `HIGH`), public reason codes, and recommended operator protocols.
5. **Escalation Panel (`src/components/EscalationPanel.jsx`):**
   - One-click escalation to Tier 2 Fraud Supervisor with non-sensitive notes.
6. **Audit History (`src/components/AuditHistory.jsx`):**
   - Security audit trail recording Request IDs, Tenant ID (`callcentre_demo`), public outcomes, and timestamps.
   - Adheres to biometric privacy rules: zero exposure of raw embeddings or confidence floats.

### 5.3 Three Seeded Demo Scenarios
- **Scenario 1 (Routine Transfer):** Normal customer inquiry (`customer_001`). Low vishing risk. Step-up voice challenge succeeds with exact phrase match.
- **Scenario 2 (Executive Vishing Attack):** Caller impersonating finance director (`customer_002`), exhibiting high urgency and demanding OTP bypass. Risk panel flags `HIGH` (`URGENT_CREDENTIAL_SOLICITATION`). Challenge fails on near-miss.
- **Scenario 3 (Security Warning Hard Negative):** Agent reminds client *"Never share your OTP"* (`customer_003`). AAA-VR mock rules confirm no false positive is triggered.

---

## 6. Mock API Integration Preparation

- **Client File:** `apps/callguard/src/services/api.js`
- **Configurable Mode:** Reads `VITE_USE_MOCK_API` (defaults to mock mode for Day 1).
- **Target Endpoints Modeled:**
  - `POST /v1/challenges`: Returns challenge ID, unpredictable phrase, 90s TTL, and short-lived capture grant.
  - `POST /v1/risk/transcript`: Analyzes transcript segments for vishing risk.
  - `GET /v1/verification-requests/{request_id}`: Retrieves final safe outcome.
  - `GET /v1/ready`: Health check probe.
- **Audio Privacy Guardrail:** CallGuard frontend and host backend do not capture or forward raw audio. Audio uploads directly from the AAA capture component to AAA Engine.

---

## 7. Observations & Questions for Teammates

### For Surya (Project Lead & Core API):
1. **Python 3.8 Compatibility:** In the baseline repo, `backend/app/layer3_adaptive.py` line 32 uses `_token_store: dict[str, dict] = {}`. In Python 3.8.2, this throws `TypeError: 'type' object is not subscriptable`. Adding `from __future__ import annotations` or `typing.Dict` fixes it. We did not edit Aditya's file per strict ownership rules.
2. **Capture Component SDK:** Please confirm the mount mechanism for embedding the AAA web capture component into CallGuard on Day 2.

### For Karthik (Security & AAA-VR):
1. Confirm the final list of public reason categories for `/v1/risk/transcript` (e.g., `URGENT_CREDENTIAL_SOLICITATION`, `AUTHORITY_PRESSURE`).

### For Aditya (Peer Reviewer):
1. The AAA-ASR phrase verifier test suite (`backend/tests/test_phrase_matcher.py`) has 158 automated tests passing.
2. CallGuard is ready for your initial usability review at `http://localhost:5174`.
