# AAA Engine — CallGuard Visual Evidence Report (Day 4)

**Document ID:** `NANDAN_DAY4_CALLGUARD_VISUAL_EVIDENCE_REPORT`  
**Execution Timestamp:** 2026-11-15T00:43:55+05:30  
**Verification Lead:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Role:** Member 5  
**Target Repository:** `E:\AAA_PROJECT\AAA_Baselines`  
**Active Branch:** `feat/nandan-asr-callguard-day2`  
**Commit HEAD:** `f7bc9cd9e80b5ea8420078394d65be5fc6f8417f`  
**Mode:** STRICT READ-ONLY AUDIT & VISUAL EVIDENCE CAPTURE  

---

## 1. Executive Summary & Verification Verdict

A complete, fresh visual evidence pack of 10 high-resolution screenshots was captured for the CallGuard application operating in strict mock mode on `http://localhost:5174/`. Every view was independently inspected, verified in the browser DOM, and saved to the official deliverables directory.

| Check / Requirement | Specification | Observed Result | Status |
|:---|:---|:---|:---:|
| **Mock Mode Enforcement** | `VITE_USE_MOCK_API=true` | Zero live backend or cloud requests made | **PASS** |
| **Simulated Call Warning** | `⚠️ SIMULATED CALL — DEMO DATA ONLY` | Visible at top banner of every page | **PASS** |
| **Risk Badge Color Consistency** | `LOW`=Green, `MEDIUM`=Yellow, `CRITICAL`=Purple/Red | Consistent across Dashboard queue and Active Call views | **PASS** |
| **Zero Confidence Leakage** | No raw cosine similarities or deepfake % scores | Only safe public categorical decisions displayed | **PASS** |
| **Scenario 2 Consistency** | `CALL-2026-1002` vishing threat | Queue: `CRITICAL`; Risk Panel: `CRITICAL RISK` / `DENY` | **PASS** |
| **Scenario 3 Hard Negative** | Genuine bank advisor warning | `CALL-2026-1003`: `LOW RISK` / `APPROVE` (no scam flag) | **PASS** |
| **Scenario 4 Consistency** | Address change request | `CALL-2026-1004`: `MEDIUM RISK` / `REVIEW` | **PASS** |
| **Escalation Interaction** | Threat escalation protocol | Active note entered; confirmed `ESCALATED TO FRAUD OPS` | **PASS** |
| **Audit History Vault** | Request IDs, timestamps, public outcomes | Structured correlation log with zero raw biometric scores | **PASS** |
| **Console Errors** | Browser console runtime audit | 0 uncaught exceptions, 0 runtime errors | **PASS** |
| **Blocked Items** | Any missing views | None (10/10 screenshots verified and captured) | **NONE** |

---

## 2. Screenshot Evidence Catalog

All captured screenshots are stored in:
`E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\INTEGRATION_EVIDENCE\CALLGUARD\DAY4\`

| Screenshot File | Dimensions / Size | What It Depicts | Acceptance Requirement Verified |
|:---|:---:|:---|:---|
| **`01_day4_agent_login.png`** | 55,824 B | Agent Login screen with operator identity dropdown (`Sarah Jenkins`, `David Chen`), shift ID (`SHF-2026-N5`), tenant (`callcentre_demo`), and demo credentials. | Operator authentication & session initiation. |
| **`02_day4_dashboard.png`** | 165,510 B | Main Operator Dashboard showing overview counters (4 Active Calls, 1 High Risk Threat, 2 Pending Challenges, 99.8% System Health) and persistent demo banner. | System health & high-level monitoring. |
| **`03_day4_call_queue.png`** | 165,510 B | Priority Call Queue table showing all four seeded calls sorted with correct risk badge styling (`LOW`=Green, `CRITICAL`=Purple, `MEDIUM`=Yellow). | Multi-scenario call queue management. |
| **`04_day4_scenario1_low.png`** | 89,433 B | Active Call Console for `CALL-2026-1001` (Routine Transfer Verification), showing customer `customer_001`, dual-channel transcript, and `LOW RISK` / `APPROVE`. | Scenario 1: Normal customer interaction. |
| **`05_day4_scenario2_critical.png`** | 97,684 B | Active Call Console for `CALL-2026-1002` (Suspected Urgent Credential Solicit), showing customer `customer_002`, transcript, and `CRITICAL RISK` / `DENY`. | Scenario 2: Social engineering & vishing defense. |
| **`06_day4_scenario3_hard_negative.png`** | 60,192 B | Active Call Console for `CALL-2026-1003` (Genuine Security Advisory), customer `customer_003`, `LOW RISK` / `APPROVE`. Transcript contains "never share your OTP". | Scenario 3: Hard negative (no false scam trigger). |
| **`07_day4_scenario4_medium.png`** | 61,573 B | Active Call Console for `CALL-2026-1004` (Address Change Request), customer `customer_002`, `MEDIUM RISK` / `REVIEW`. | Scenario 4: Step-up / manual review threshold. |
| **`08_day4_risk_panel.png`** | 65,584 B | Focused view of `RiskPanel` under Scenario 2 displaying risk level, indicators (`Credential Request`, `Coercion / Legal Threat`, `False Authority Claim`), and recommended action. | Layer 3 Voice Risk (AAA-VR) integration. |
| **`09_day4_escalation.png`** | 47,539 B | Escalation modal / status banner after operator enters note and clicks "Escalate for Human Review", displaying confirmed state `ESCALATED - Escalated to Fraud Supervisor Tier 2`. | Human-in-the-loop escalation workflow. |
| **`10_day4_audit_history.png`** | 32,289 B | Audit History vault table (`Security & Verification Audit Log · Protected Biometric Vault`) showing correlation IDs (`req_4c1e87d0-c002`), timestamps, operator actions, and public decisions with zero numerical score leakage. | Regulatory audit trail & privacy enforcement. |

---

## 3. Four-Scenario Verification Matrix

| Scenario ID | Scenario Name & Type | Customer Ref | Displayed Risk Level | Protocol Action | Public Reason Indicators | Hard Negative Check | Final Verdict |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---:|
| **CALL-2026-1001** | Routine Transfer (Inbound IVR) | `customer_001` | **LOW RISK** (Green) | **APPROVE** | Routine verification pattern; no anomalies detected. | N/A | **PASS** |
| **CALL-2026-1002** | Urgent Credential Solicit (Vishing) | `customer_002` | **CRITICAL RISK** (Purple) | **DENY** | `Credential Request`, `Coercion / Legal Threat`, `False Authority Claim`. | N/A | **PASS** |
| **CALL-2026-1003** | Genuine Security Advisory (Callback) | `customer_003` | **LOW RISK** (Green) | **APPROVE** | None detected (Clean conversational flow). | **PASS** ("never share OTP" does not trigger scam alert) | **PASS** |
| **CALL-2026-1004** | Address Change Request (Inbound Support) | `customer_002` | **MEDIUM RISK** (Yellow) | **REVIEW** | `Unverified Beneficiary`. | N/A | **PASS** |

---

## 4. Privacy, Security, and Non-Negotiable Boundaries Audit

1. **No Audio Transit:** CallGuard does not capture or route customer audio through the application.
2. **Zero Numerical Confidence Leakage:** All UI elements display qualitative categories (`APPROVE`, `DENY`, `REVIEW`, `LOW`, `MEDIUM`, `CRITICAL`). Zero raw floating-point numbers or percentages are rendered in the DOM.
3. **Synthetic Data Only:** All customer identifiers, account numbers, and phone records are synthetic.
4. **Mock Mode Preserved:** The frontend was tested strictly with `VITE_USE_MOCK_API=true`, ensuring zero outbound network leaks.

---

## 5. File Integrity Statement

No application source files, styles, mock data, or build configurations were altered. All temporary processes (Vite development server) were cleanly terminated. Only the 10 screenshots and this report were generated.
