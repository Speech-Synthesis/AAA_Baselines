# Independent Peer Retest & Verification Sign-Off Form (Member 4 — Aditya)

**Deliverable Under Review:** AAA-ASR Exact Phrase Matcher & CallGuard Demonstration Host Application  
**Assigned Owner / Author:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Independent Peer Reviewer:** Aditya (Member 4 — Deepfake Detection & Red-Team Lead)  
**Target Repository:** `E:\AAA_PROJECT\AAA_Baselines`  
**Target Branch:** `feat/nandan-asr-callguard-day2`  
**Commit Evaluated:** `f7bc9cd9e80b5ea8420078394d65be5fc6f8417f`  
**Test Date:** [____________________]  
**Execution Environment:** [____________________]  

---

## 1. AAA-ASR Exact Phrase Matcher Test Matrix

**Execution Command:**  
`.\.venv311\Scripts\python.exe -m pytest backend/tests/test_phrase_matcher.py -v`

| Check ID | Verification Area | Expected Behavior | Actual Observed Result (Aditya) | Verdict (PASS / FAIL / BLOCKED) | Evidence / Notes |
|:---:|:---|:---|:---:|:---:|:---|
| **ASR-01** | **Exact Phrase Match** | Identical normalized words return `code="OK"`, `match=True`. | [ ] | [ ] | [ ] |
| **ASR-02** | **Case Normalization** | Uppercase, lowercase, and mixed-case phrases match identically. | [ ] | [ ] | [ ] |
| **ASR-03** | **Punctuation Stripping** | Commas, periods, question marks, and exclamation marks are stripped. | [ ] | [ ] | [ ] |
| **ASR-04** | **Whitespace Collapsing** | Leading, trailing, multi-space, tabs, and newlines normalized. | [ ] | [ ] | [ ] |
| **ASR-05** | **Approved Fillers** | Natural fillers (`um`, `uh`, `er`, `hmm`, `erm`, `ah`) safely omitted. | [ ] | [ ] | [ ] |
| **ASR-06** | **Digit / Number Normalization** | Digits convert bidirectionally (`7` $\leftrightarrow$ `seven`, `20` $\leftrightarrow$ `twenty`). | [ ] | [ ] | [ ] |
| **ASR-07** | **Missing Word Rejection** | Omission of any challenge token triggers `code="MISMATCH"`. | [ ] | [ ] | [ ] |
| **ASR-08** | **Extra Word Rejection** | Injected tokens or preambles trigger `code="MISMATCH"`. | [ ] | [ ] | [ ] |
| **ASR-09** | **Word Order Transposition** | Reordered words trigger `code="MISMATCH"` (deterministic order). | [ ] | [ ] | [ ] |
| **ASR-10** | **Substituted Word Near-Miss** | Near-miss token (e.g. `chair` $\to$ `couch`) triggers `MISMATCH`. | [ ] | [ ] | [ ] |
| **ASR-11** | **No-Speech / Empty Input** | Empty string or high `no_speech_prob` returns `NO_SPEECH`. | [ ] | [ ] | [ ] |
| **ASR-12** | **Expired Challenge Token** | Expired nonce returns `code="EXPIRED_CHALLENGE"`. | [ ] | [ ] | [ ] |
| **ASR-13** | **Low Confidence Gate** | Valid words with `confidence < 0.50` return `LOW_CONF`. | [ ] | [ ] | [ ] |
| **ASR-14** | **Zero Fuzzy Acceptance** | High confidence cannot override a token mismatch (Fail-Closed). | [ ] | [ ] | [ ] |
| **ASR-15** | **Total Test Count** | Exactly 160 unit tests collected and passing. | [ ] | [ ] | [ ] |

---

## 2. CallGuard Frontend & Security Workflow Matrix

**Execution Command:**  
`cd apps/callguard; $env:VITE_USE_MOCK_API="true"; npm run dev` (Access via `http://localhost:5174/`)

| Check ID | Verification Area | Expected Behavior | Actual Observed Result (Aditya) | Verdict (PASS / FAIL / BLOCKED) | Evidence / Notes |
|:---:|:---|:---|:---:|:---:|:---|
| **CG-01** | **Operator Login & Identity** | Operator selection (`Sarah Jenkins`, `David Chen`), shift ID, tenant. | [ ] | [ ] | [ ] |
| **CG-02** | **Main Dashboard Counters** | Overview cards render Active Calls (4), High Risk Threats, Health. | [ ] | [ ] | [ ] |
| **CG-03** | **Simulated Banner** | Persistent banner `⚠️ SIMULATED CALL — DEMO DATA ONLY` visible. | [ ] | [ ] | [ ] |
| **CG-04** | **Priority Call Queue** | All 4 seeded calls rendered with correct risk badges. | [ ] | [ ] | [ ] |
| **CG-05** | **Scenario 1 (Routine Transfer)** | `CALL-2026-1001` shows `LOW RISK` (Green badge) and `APPROVE`. | [ ] | [ ] | [ ] |
| **CG-06** | **Scenario 2 (Vishing Threat)** | `CALL-2026-1002` shows `CRITICAL RISK` (Purple badge) and `DENY`. | [ ] | [ ] | [ ] |
| **CG-07** | **Scenario 2 Public Indicators** | Displays `Credential Request`, `Coercion / Legal Threat`, etc. | [ ] | [ ] | [ ] |
| **CG-08** | **Scenario 3 (Hard Negative)** | `CALL-2026-1003` ("never share OTP") shows `LOW RISK` / `APPROVE`. | [ ] | [ ] | [ ] |
| **CG-09** | **Scenario 4 (Address Change)** | `CALL-2026-1004` shows `MEDIUM RISK` (Yellow badge) and `REVIEW`. | [ ] | [ ] | [ ] |
| **CG-10** | **Risk Badge Consistency** | Badge colors match consistently across Dashboard queue and active view. | [ ] | [ ] | [ ] |
| **CG-11** | **Escalation Interaction** | Agent note submitted; UI displays confirmed escalation status. | [ ] | [ ] | [ ] |
| **CG-12** | **Audit History Vault** | Table renders Request IDs, timestamps, public decisions (`APPROVE`, `DENY`). | [ ] | [ ] | [ ] |
| **CG-13** | **Zero Confidence Leakage** | Zero raw percentages, cosine similarities, or biometric scores visible. | [ ] | [ ] | [ ] |
| **CG-14** | **Audio Transit Boundary** | No raw customer audio captured or routed through CallGuard. | [ ] | [ ] | [ ] |
| **CG-15** | **Console Health & Errors** | 0 uncaught exceptions, 0 network failures, 0 runtime errors. | [ ] | [ ] | [ ] |

---

## 3. Defect & Observation Log (If Any)

*(If any test fails or behaves unexpectedly, record the defect details below. If zero defects are found, mark as "None".)*

| Defect ID | Associated Check ID | Description of Observed Anomaly | Severity (Low / Medium / High / Critical) | Recommendation |
|:---:|:---:|:---|:---:|:---|
| | | | | |
| | | | | |

---

## 4. Formal Independent Peer Sign-Off

*(To be completed and signed by Member 4 — Aditya upon conclusion of retest)*

### Reviewer Statement:
I, Aditya (Member 4), have independently executed the test procedures described in the Day 4 Peer Retest Guide against Member 5’s AAA-ASR phrase matcher and CallGuard application. I have recorded my actual observations in the tables above.

- **AAA-ASR Phrase Matcher Verdict:** [ ] ACCEPT & SIGN-OFF  /  [ ] REJECT (Defects Outstanding)
- **CallGuard Demonstration App Verdict:** [ ] ACCEPT & SIGN-OFF  /  [ ] REJECT (Defects Outstanding)
- **Overall Peer Review Recommendation:** [ ] APPROVED FOR DAY 4 FINAL RELEASE  /  [ ] CHANGES REQUESTED

**Reviewer Name:** Aditya (Member 4 — Deepfake Detection & Red-Team Lead)  
**Reviewer Signature / Hash:** [____________________________________]  
**Date of Sign-Off:** [____________________]  
