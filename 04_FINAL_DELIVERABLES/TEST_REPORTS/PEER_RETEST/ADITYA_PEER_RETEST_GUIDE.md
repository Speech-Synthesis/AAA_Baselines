# Member 4 (Aditya) Independent Peer Retest Guide

**Component Under Test:** AAA-ASR Exact Phrase Matcher & CallGuard Demonstration Host Application  
**Author / Lead:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Assigned Independent Reviewer:** Aditya (Member 4 — Deepfake Detection & Red-Team Lead)  
**Target Repository:** `E:\AAA_PROJECT\AAA_Baselines`  
**Base Branch:** `feat/nandan-asr-callguard-day2`  
**Current HEAD Commit:** `f7bc9cd9e80b5ea8420078394d65be5fc6f8417f`  
**Review Type:** Independent Peer Verification & Retest Sign-Off (Day 4)  

---

## 1. Objective for the Independent Reviewer

Aditya (Member 4) is assigned as the independent quality gate for Member 5’s deliverables:
1. **AAA-ASR Phrase Verifier:** Verify that challenge phrases are evaluated with strict exact-match security invariants without fuzzy or broad semantic acceptance fallbacks.
2. **CallGuard Call-Centre Application:** Verify the complete call-centre security workflow in mock mode across all four seeded scenarios, ensuring proper risk badge styling, genuine hard-negative handling, threat escalation, and zero raw biometric score leakage.

This guide provides the exact commands, execution steps, expected results, and verification criteria to support your independent testing and formal sign-off.

---

## 2. Part A — AAA-ASR Phrase Matcher Retest

### 2.1 Test Environment & Execution Command
Execute the comprehensive test suite using the isolated Python 3.11 environment on the `E:` drive:

```powershell
Set-Location "E:\AAA_PROJECT\AAA_Baselines"

# Verify Python 3.11 environment
.\.venv311\Scripts\python.exe --version
.\.venv311\Scripts\python.exe -m pytest --version

# Run the official test suite
.\.venv311\Scripts\python.exe -m pytest backend/tests/test_phrase_matcher.py -v
```

### 2.2 Expected Test Results
- **Collected Test Cases:** Exactly **160 tests**
- **Expected Result:** **160 PASSED in < 2.0s (100% pass rate, 0 failures, 0 errors, 0 skips)**

### 2.3 Verification Criteria & Security Invariants
Inspect that the test execution validates the following non-negotiable security requirements:
- **Exact Match:** Phrases with identical normalized words return code `OK` and `match=True`.
- **Case Normalization:** Case-insensitive comparisons (`SEVEN RED CHAIR` == `seven red chair`).
- **Punctuation Stripping:** Commas, periods, question marks, and exclamation marks are stripped cleanly.
- **Whitespace Collapsing:** Leading, trailing, multiple spaces, tabs (`\t`), and newlines (`\n`, `\r\n`) are normalized.
- **Approved Fillers:** Natural hesitations (`um`, `uh`, `er`, `hmm`, `erm`, `ah`) are safely omitted from transcript.
- **Digit / Word Conversion:** Controlled challenge vocabulary numbers (`7` $\leftrightarrow$ `seven`, `20` $\leftrightarrow$ `twenty`) map correctly.
- **Missing Words:** Any omitted word triggers immediate rejection (`MISMATCH`).
- **Extra Words:** Any inserted token or preamble triggers immediate rejection (`MISMATCH`).
- **Reordered Words:** Any word transposition triggers immediate rejection (`MISMATCH`).
- **Substituted / Mutated Words:** Near-miss phrases (e.g. `chair` $\to$ `couch`) trigger immediate rejection (`MISMATCH`).
- **Empty / No-Speech:** Empty string or high `no_speech_prob` returns `NO_SPEECH` (`match=False`).
- **Expired Challenge:** Expired nonce token returns `EXPIRED_CHALLENGE` (`match=False`).
- **Low Confidence Gate:** Transcript matching text but having `confidence < 0.50` returns `LOW_CONF` (`match=False`).
- **Zero-Fuzzy Policy:** High confidence or high string similarity scores **cannot** override a textual mismatch.

---

## 3. Part B — CallGuard Demonstration App Retest

### 3.1 Starting the Application in Mock Mode
Start CallGuard using the existing dependencies on `E:`:

```powershell
Set-Location "E:\AAA_PROJECT\AAA_Baselines\apps\callguard"

# Ensure mock mode is active (default) and launch Vite dev server
$env:VITE_USE_MOCK_API = "true"
npm run dev
```

Open a web browser and navigate to:  
👉 **`http://localhost:5174/`**

### 3.2 Four-Scenario Verification Matrix
Verify the four seeded call records in the Priority Call Queue and their respective Active Call consoles:

| Call ID | Scenario Name | Seeded Customer | Expected Risk Level | Expected Action | Key Verification Criteria |
|:---|:---|:---:|:---:|:---:|:---|
| **CALL-2026-1001** | Routine Transfer Verification | `customer_001` | **LOW RISK** (Green) | **APPROVE** | Routine IVR transfer; dual-channel transcript; clean conversational flow. |
| **CALL-2026-1002** | Suspected Urgent Credential Solicit | `customer_002` | **CRITICAL RISK** (Purple / Red) | **DENY** | Coercive wire demand; displays public reason codes: `Credential Request`, `Coercion / Legal Threat`, `False Authority Claim`. |
| **CALL-2026-1003** | Genuine Security Advisory (Hard Negative) | `customer_003` | **LOW RISK** (Green) | **APPROVE** | Bank agent advises customer *"never share your password or OTP"*. Must **NOT** trigger scam alert. Clean flow. |
| **CALL-2026-1004** | Address Change Request | `customer_002` | **MEDIUM RISK** (Yellow) | **REVIEW** | Unverified third-party beneficiary; prompts agent caution. |

### 3.3 Visual & Boundary Verification Checks
During the UI walkthrough, verify the following compliance items:
1. **Simulated Call Warning:** The header banner `⚠️ SIMULATED CALL — DEMO DATA ONLY · SYNTHETIC BIOMETRICS & PROMPTS · TENANT: callcentre_demo` must be permanently visible across all views.
2. **Risk Badge Styling:**
   - `LOW` $\to$ Green badge (`#10b981` / `badge-low`)
   - `MEDIUM` $\to$ Yellow badge (`#f59e0b` / `badge-medium`)
   - `CRITICAL` $\to$ Purple / Red glowing border (`#ef4444` / `rgba(239, 68, 68, 0.35)`)
3. **Escalation Interaction:** On `CALL-2026-1002`, enter a short operator note in the Escalation Panel and submit. Verify that the UI reflects the confirmed state (`ESCALATED - Escalated to Fraud Supervisor Tier 2`).
4. **Audit History Vault:** Inspect the audit table at the bottom of the active console or dashboard. Verify that it displays Request IDs (`req_...`), timestamps, and public decisions (`APPROVE`, `DENY`).
5. **Zero Numerical Confidence Leakage:** Confirm that **zero floating-point numbers, cosine similarities, or deepfake probability percentages** are exposed to the agent.
6. **No Raw Audio Transit:** Verify that CallGuard does not capture, buffer, or record customer audio directly.
7. **Console Health:** Open Developer Tools (F12) and confirm 0 uncaught exceptions or React runtime errors.

---

## 4. Reference Evidence Catalog

For visual comparison during testing, reference Member 5’s Day 4 evidence screenshots located at:  
`E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\INTEGRATION_EVIDENCE\CALLGUARD\DAY4\`

- `01_day4_agent_login.png`: Agent portal login screen with demo operator selector.
- `02_day4_dashboard.png`: Dashboard overview with active call counters and status.
- `03_day4_call_queue.png`: Priority Call Queue table showing all 4 seeded calls.
- `03_day4_call_queue_dedicated.png`: Focused crop of the Priority Call Queue.
- `04_day4_scenario1_low.png`: Scenario 1 Active Call console (`LOW` / `APPROVE`).
- `05_day4_scenario2_critical.png`: Scenario 2 Active Call console (`CRITICAL` / `DENY`).
- `06_day4_scenario3_hard_negative.png`: Scenario 3 Active Call console (`LOW` / `APPROVE`).
- `07_day4_scenario4_medium.png`: Scenario 4 Active Call console (`MEDIUM` / `REVIEW`).
- `08_day4_risk_panel.png`: Focused close-up of AAA-VR Risk Panel on Scenario 2.
- `09_day4_escalation.png`: Confirmed threat escalation state.
- `10_day4_audit_history.png`: Protected Biometric Vault audit log table.

---

## 5. Next Steps for Aditya

1. Run the test suite and verify all 160 phrase matcher tests pass.
2. Launch CallGuard and execute the 4-scenario browser walkthrough.
3. Open `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\TEST_REPORTS\PEER_RETEST\ADITYA_PEER_SIGNOFF_TEMPLATE.md`.
4. Record your actual findings, observations, and timestamps.
5. Provide your formal independent sign-off verdict (`ACCEPT` / `REJECT`).
