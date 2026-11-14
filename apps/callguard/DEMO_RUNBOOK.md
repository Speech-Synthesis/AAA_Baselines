# CallGuard Demonstration Runbook

**Application:** CallGuard — Call-Centre Voice Security Console (Host Application 2)  
**Project:** AAA Engine (Adaptive Acoustic Authentication with Deepfake Detection)  
**Author / Engineering Lead:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Target Repository:** `Speech-Synthesis/AAA_Baselines` (`E:\AAA_PROJECT\AAA_Baselines`)  
**Host Application Path:** `apps/callguard`  
**Tenant ID:** `callcentre_demo`  
**Sprint Milestone:** Day 4 Final Deliverable (14 November 2026)  
**Target Audience:** Evaluators, Teammates, Project Supervisors, and Demonstrators  

---

## 1. Project Overview & Architecture

### 1.1 What CallGuard Does
CallGuard is an enterprise call-centre security console designed to protect customer support agents and financial institutions from social engineering, voice phishing (vishing), and deepfake identity fraud. It demonstrates how modern enterprise customer service operations integrate the independent **AAA Engine middleware** without compromising caller privacy.

### 1.2 Role in the AAA Engine Ecosystem
AAA Engine serves as an independent acoustic authentication and deepfake defense layer. CallGuard acts as **Host Application 2** (alongside Banking Shield as Host Application 1). CallGuard showcases two core security capabilities:
1. **Challenge-Phrase Acoustic Verification (AAA-ASR):** Verifying caller voice and phrase deterministically using single-use challenge nonces with zero-tolerance for near-miss or altered text.
2. **Real-Time Vishing Defense (AAA-VR):** Continuously scanning caller and agent conversational turns for coercion, urgency, and credential harvesting signals using frozen public risk categories.

### 1.3 Intended Operator Workflow
1. The call-centre agent logs into the CallGuard console under a seeded operator profile.
2. The agent monitors the **Priority Call Queue**, where inbound calls are prioritized by preliminary risk tier.
3. Upon opening an active call, the agent views dual-channel conversational transcripts and real-time **AAA-VR Risk Panel** indicators.
4. If a sensitive transaction requires step-up identity verification, the agent initiates an AAA voice challenge.
5. In severe vishing scenarios, the agent triggers the **Tier 2 Escalation Workflow**, placing an immediate administrative hold on the session.
6. All security decisions, correlation request IDs, and timestamps are recorded in the immutable **Protected Biometric Vault (Audit History)**.

### 1.4 Mock Demonstration Mode vs. Live Backend Mode
- **Mock Demonstration Mode (Default / Tested):** Governed by `VITE_USE_MOCK_API=true` in `src/services/api.js`. Operates self-contained with zero network dependencies, executing four deterministic scenarios directly in the browser. Perfect for offline presentations, automated testing, and peer reviews.
- **Live Backend Mode:** Configured by setting `VITE_USE_MOCK_API=false` and pointing `VITE_AAA_API_BASE_URL` to `http://localhost:8000`. Connects to Surya's live FastAPI backend (`/v1/challenges`, `/v1/verify`, `/v1/risk/transcript`).

---

## 2. Environment Prerequisites

All files, caches, and runtime artifacts must remain strictly on the **E: drive** in compliance with team workspace policy.

### 2.1 Software & Tooling Versions
- **Operating System:** Windows 10 / 11 (64-bit)
- **Node.js:** `v20.x` or `v22.x` (Tested on `v22.22.1`)
- **npm:** `v10.x` (Tested on `npm 10.8.1`)
- **Python (for AAA-ASR tests):** Python 3.11.9 (`.venv311` on `E:` drive)
- **Browser:** Any modern Chromium-based browser (Google Chrome, Microsoft Edge, Brave)

### 2.2 Directory Structure Check
Confirm you are in the correct repository location:
```powershell
Set-Location "E:\AAA_PROJECT\AAA_Baselines\apps\callguard"
```

### 2.3 Environment Variables
No external `.env` file is required for mock demonstration. The service layer defaults to mock execution automatically:
- `VITE_USE_MOCK_API`: Defaults to `"true"`
- `VITE_AAA_API_BASE_URL`: Defaults to `"http://localhost:8000"`

---

## 3. Application Startup Instructions

### 3.1 Step 1: Open PowerShell and Navigate to CallGuard
```powershell
Set-Location "E:\AAA_PROJECT\AAA_Baselines\apps\callguard"
```

### 3.2 Step 2: Install Dependencies (One-Time Setup Only)
*Note: If `node_modules` is already present on `E:`, skip this step.*
```powershell
# Only run if node_modules is missing:
npm install --cache E:\AAA_PROJECT\AAA_Baselines\.cache\npm
```

### 3.3 Step 3: Start the Vite Development Server in Mock Mode
```powershell
$env:VITE_USE_MOCK_API = "true"
npm run dev
```

Expected startup terminal output:
```text
  VITE v5.4.21  ready in 329 ms

  ➜  Local:   http://localhost:5174/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### 3.4 Step 4: Open CallGuard in Your Browser
Open your browser and navigate to:  
👉 **`http://localhost:5174/`**

### 3.5 Step 5: Stopping the Server
When your demonstration is complete, return to PowerShell and press:  
`Ctrl + C` (followed by `Y` and `Enter`).

---

## 4. Login & Dashboard Demonstration

### 4.1 Operator Authentication & Role Selection
Upon navigating to `http://localhost:5174/`, you will be greeted by the **Agent Portal Login Screen**.
- **Demonstration Action:** Select an operator from the dropdown:
  - **Sarah Jenkins** (`agent.sarah`): Senior Security Specialist (High-Value Verification Queue).
  - **David Chen** (`agent.david`): Tier 2 Fraud Investigator (Escalated Vishing Review).
- **Credentials:** Pre-filled with demo credentials (`demo123`). Click **"Sign In to Console"**.
- **Supporting Evidence:** `01_day4_agent_login.png`

### 4.2 Permanent Compliance Warning Banner
Observe the yellow/amber warning banner permanently anchored to the top of every screen:  
`⚠️ SIMULATED CALL — DEMO DATA ONLY · SYNTHETIC BIOMETRICS & PROMPTS · TENANT: callcentre_demo`  
*Explanation Point for Audience:* Highlights regulatory compliance: CallGuard strictly uses synthetic caller identities, consented voice prompts, and zero live telephony interception.

### 4.3 Main Dashboard Counters
The dashboard displays real-time high-level operational telemetry cards:
- **Active Calls in Queue:** `4` (All four seeded evaluation scenarios).
- **High Risk Threats:** `1` (Immediate visual warning for pending critical attack).
- **Pending Biometric Challenges:** `2`
- **System Health:** `99.8%` (AAA Engine middleware status).
- **Supporting Evidence:** `02_day4_dashboard.png`

### 4.4 Priority Call Queue Table
The queue automatically ranks incoming calls based on conversational risk markers:
- Displays columns: `CALL ID`, `CUSTOMER REF`, `SCENARIO / PURPOSE`, `CHANNEL`, `STATUS`, `VISHING RISK PREVIEW`, and `ACTION`.
- Color-coded risk badges:
  - `LOW RISK`: Green badge
  - `MEDIUM RISK`: Yellow badge
  - `CRITICAL RISK`: Glowing purple / red border
- Click **"Open Call Console"** on any row to open the full interactive console.
- **Supporting Evidence:** `03_day4_call_queue_dedicated.png`

---

## 5. Four Scenario Demonstrations

CallGuard features four distinct seeded scenarios engineered to evaluate the full breadth of AAA Engine and AAA-VR capabilities.

```
+----------------------------------------------------------------------------------------------------+
|                                    CALLGUARD DEMO SCENARIOS                                        |
+-------------------+-------------------+--------------------+------------------+--------------------+
| Call ID           | Scenario Name     | Customer Ref       | Expected Risk    | Protocol Action    |
+-------------------+-------------------+--------------------+------------------+--------------------+
| CALL-2026-1001    | Routine Transfer  | customer_001       | LOW RISK (Green) | APPROVE            |
| CALL-2026-1002    | Credential Solicit| customer_002       | CRITICAL (Purple)| DENY               |
| CALL-2026-1003    | Hard Negative Adv.| customer_003       | LOW RISK (Green) | APPROVE            |
| CALL-2026-1004    | Address Change    | customer_002       | MEDIUM (Yellow)  | REVIEW             |
+-------------------+-------------------+--------------------+------------------+--------------------+
```

---

### 5.1 Scenario 1: Routine Wire Transfer (`CALL-2026-1001`)

- **What the Operator Sees:** Click `CALL-2026-1001` from the dashboard. The Active Call Console opens with dual-channel speech bubbles (Agent in blue, Caller in dark gray) and relative timestamps (`00:05` to `00:50`).
- **Transcript Context:** Customer requests status on a pending corporate wire transfer. Natural, professional dialogue with zero coercive phrasing.
- **Risk Panel Display:** Renders `LOW RISK` (Green badge). Recommended protocol action: `APPROVE`. Public indicators state: *"Routine verification pattern; no social engineering anomalies detected."*
- **Operator Action:** Explain that for standard routine operations, normal call flow proceeds without friction.
- **Biometric Challenge Demo:** Click **"Initiate Voice Challenge"** $\to$ AAA Engine generates fresh phrase *"Seven Red Chair Twenty"*. Click **"Caller Speaks Exact Phrase"** $\to$ Decision: `APPROVE` (`REQUIRED_CHECKS_PASSED`).
- **Supporting Evidence:** `04_day4_scenario1_low.png`

---

### 5.2 Scenario 2: Coercive Vishing & Credential Theft (`CALL-2026-1002`)

- **What the Operator Sees:** Open `CALL-2026-1002`. The console immediately flashes a red/purple alert state with a prominent threat border.
- **Transcript Context:** The caller impersonates an executive authority, claims an urgent crisis, demands an immediate wire transfer to an unlisted third party, and aggressively demands the operator bypass OTP verification under threat of legal action and termination.
- **Risk Panel Display:** Renders `CRITICAL RISK` (Purple / Red). Recommended action: `DENY` *(Threat markers detected. Do not release sensitive credentials or funds. Escalate immediately).*
- **Flagged Reason Indicators:**
  - `Credential Request`
  - `Coercion / Legal Threat`
  - `False Authority Claim`
- **Operator Action:** Demonstrate that the system safely protects frontline agents from high-pressure coercion. Proceed immediately to the Escalation Panel.
- **Biometric Challenge Demo:** Click **"Simulate Near-Miss / Wrong Phrase"** $\to$ Exact phrase matcher deterministically triggers `DENY` (`CHALLENGE_MISMATCH`).
- **Supporting Evidence:** `05_day4_scenario2_critical.png` and `08_day4_risk_panel.png`

---

### 5.3 Scenario 3: Genuine Security Advisory — Hard Negative (`CALL-2026-1003`)

- **What the Operator Sees:** Open `CALL-2026-1003`.
- **Transcript Context:** An outbound fraud callback where the genuine bank representative reminds the customer: *"Remember, Secure Trust will never ask you for your full password or OTP over the phone."*
- **The Hard Negative Challenge:** Naive keyword-spotting models frequently misclassify security advisories as scams because words like `"OTP"` and `"password"` appear in the transcript.
- **Risk Panel Display:** AAA-VR correctly understands conversational syntax and context:
  - Risk Level: **`LOW RISK`** (Green badge)
  - Protocol Action: **`APPROVE`**
  - Public Indicators: **`None detected (Clean conversational flow)`**
- **Operator Action:** Emphasize that AAA-VR prevents false alarms on legitimate compliance warnings, ensuring seamless customer service.
- **Supporting Evidence:** `06_day4_scenario3_hard_negative.png`

---

### 5.4 Scenario 4: Address Change Request — Step-Up (`CALL-2026-1004`)

- **What the Operator Sees:** Open `CALL-2026-1004`.
- **Transcript Context:** Customer calls to change registered mailing address and add an unverified account beneficiary.
- **Risk Panel Display:**
  - Risk Level: **`MEDIUM RISK`** (Yellow caution badge)
  - Recommended Protocol Action: **`REVIEW`** *(Single risk marker present. Prompt agent to exercise standard verification caution).*
  - Public Indicators: **`Unverified Beneficiary`**
- **Operator Action:** Demonstrate how CallGuard handles borderline or single-indicator cases: rather than denying the customer, it recommends a secondary step-up or supervisor review.
- **Supporting Evidence:** `07_day4_scenario4_medium.png`

---

## 6. Threat Escalation Workflow

In Scenario 2 (`CALL-2026-1002`), show how CallGuard empowers agents to escalate threats directly to Fraud Operations:

1. Scroll to the **Human Review & Escalation Panel** on the right sidebar of the Active Call Console.
2. In the text field, type a short operational note (strictly non-sensitive, no PII):  
   `"Severe vishing attempt: Caller pressured bypass of standard voice challenge and demanded unauthorized wire."`
3. Click the red button: **"Escalate for Human Review"**.
4. **Immediate UI Feedback:** The component updates in real time to display the confirmed escalation state:
   - Header badge changes to: `ESCALATED` (Red badge)
   - Status banner: `Escalated to Fraud Supervisor Tier 2`
   - Operational directive: `Supervisor dispatched to monitor call session. Transaction hold applied.`
   - Immutable Agent Note appended to session.
- **Supporting Evidence:** `09_day4_escalation.png`

---

## 7. Audit History Vault & Privacy Verification

Scroll to the bottom of the Active Call Console or return to the Dashboard to inspect the **Security & Verification Audit Log**:

### 7.1 What the Audit Table Displays
- **Request ID:** Globally unique cryptographic correlation token (e.g. `req_4c1e87d0-c002`).
- **Customer Ref:** Pseudonymous customer identifier (`customer_001`, `customer_002`).
- **Tenant ID:** `callcentre_demo` (enforcing strict tenant isolation).
- **Decision:** Safe public categorization (`APPROVE`, `DENY`, `STEP_UP`, `REVIEW`).
- **Risk Level:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Public Reason Code:** Standardized RFC-compliant identifier (e.g. `CHALLENGE_MISMATCH`, `REQUIRED_CHECKS_PASSED`).
- **Timestamp:** Precise wall-clock execution time.
- **Action Taken:** Operational audit record.

### 7.2 Why Sensitive Biometric Scores Are Hidden
*Crucial Demonstration Point:* Point out to your evaluators that **nowhere in CallGuard** are raw floating-point numbers displayed:
- ❌ No raw speaker cosine similarity scores (e.g. `0.7842`).
- ❌ No deepfake probability percentages (e.g. `94.2% fake`).
- ❌ No Wav2Vec2 confidence floats.
- **Why?** Exposing raw thresholds to frontline agents creates security vulnerabilities (social engineering, threshold gaming) and violates enterprise biometric privacy standards (GDPR / CCPA / BIPA). CallGuard receives only **safe categorical decisions** from AAA Core.
- **Supporting Evidence:** `10_day4_audit_history.png`

---

## 8. AAA-ASR: Transcription vs. Strict Phrase Verification

When asked how speech recognition works under the hood, explain the two-stage separation built into `backend/app/aaa_asr/`:

```
+-----------------------------------------------------------------------------------+
|                            TWO-STAGE ASR ARCHITECTURE                             |
+-----------------------------------------------------------------------------------+
|  [Stage 1: Speech-to-Text]                                                        |
|  Audio WAV (16kHz) ---> Local OpenAI Whisper Base (74M) ---> Raw Text Hypothesis |
|                                                                                   |
|  [Stage 2: Deterministic Phrase Verifier]                                         |
|  Raw Hypothesis + Expected Challenge Nonce                                        |
|      │                                                                            |
|      ├──> Normalization: Case, Punctuation, Whitespace, Approved Fillers          |
|      │                                                                            |
|      └──> Exact Equality Comparison (Ref == Hyp)                                  |
|               ├── Exact Match  ---> Code: "OK" (match=True)                       |
|               ├── 1 Word Diff  ---> Code: "MISMATCH" (match=False)                |
|               ├── Expired Nonce---> Code: "EXPIRED_CHALLENGE" (match=False)       |
|               └── Low Conf     ---> Code: "LOW_CONF" (match=False)                |
+-----------------------------------------------------------------------------------+
```

### 8.1 Key Engineering Distinctions
1. **Local Whisper Transcription (`transcriber.py`):** Loads weights locally from `.models/whisper/base.pt`. Transcribes raw audio into text with zero external cloud calls.
2. **Deterministic Phrase Matcher (`phrase_matcher.py`):** Operates independently of Whisper. Normalizes only approved variances (stripping punctuation, case differences, and natural fillers like `"um"`, `"uh"`).
3. **Zero Fuzzy Matching:** Unlike legacy prototypes that allowed fuzzy similarity ($\ge 0.6$), AAA-ASR enforces strict string equality. One omitted, extra, or substituted word triggers an instant `MISMATCH`.
4. **Fail-Closed Security Gates:** High confidence cannot turn a wrong word into a pass. Expired challenge tokens (>90s) fail closed.

---

## 9. Security & Privacy Guardrails

Highlight the following non-negotiable boundaries implemented by Member 5:

1. **Zero Raw Audio Transit:** CallGuard never captures, buffers, records, or proxies raw caller audio. In the live architecture, audio uploads directly from the client device to AAA Engine via short-lived capture grants.
2. **Local Model Execution:** Whisper Base runs 100% locally on the `E:` drive. No audio is ever uploaded to OpenAI, Azure, or any cloud API.
3. **No Secrets in Frontend:** The CallGuard client contains zero administrative credentials, API keys, or Supabase service-role secrets.
4. **Synthetic Data Exclusively:** All customer names, phone numbers, and account records are synthetic demo data.

---

## 10. Troubleshooting Guide

| Issue Encountered | Root Cause | Practical Resolution |
|:---|:---|:---|
| **Port 5174 in use** | A previous Vite process is running in the background. | Run `Get-NetTCPConnection -LocalPort 5174` and terminate the PID using `Stop-Process -Id <PID> -Force`. Or start Vite on port 5175: `npm run dev -- --port 5175`. |
| **Vite fails to start** | Node or PowerShell execution policy issue. | Ensure you are running 64-bit PowerShell and that Node is available: `node -v`. |
| **Missing `node_modules`** | Dependencies not yet installed on new machine. | Run `npm install --cache E:\AAA_PROJECT\AAA_Baselines\.cache\npm` from `apps/callguard/`. |
| **Blank browser screen** | Browser console error or cached build. | Open Chrome DevTools (`F12`), check Console tab, and perform a hard refresh (`Ctrl + Shift + R`). |
| **Backend connection refused** | Live mode accidentally enabled without AAA backend running. | In PowerShell run `$env:VITE_USE_MOCK_API="true"` and restart Vite. |
| **Calls queue empty** | Mock data array modified or uninitialized. | Verify `src/data/mockData.js` has not been altered (`git checkout apps/callguard/src/data/mockData.js`). |

---

## 11. Recommended 5–7 Minute Presentation Sequence

```
[0:00 - 1:00]  Introduction & Architecture Overview
               - Show slide or README. Explain AAA Engine middleware & CallGuard's role.
               - Emphasize zero raw audio transit & synthetic data compliance.

[1:00 - 2:00]  Login & Dashboard Overview
               - Open http://localhost:5174/ (Show 01_day4_agent_login.png).
               - Sign in as Sarah Jenkins.
               - Highlight permanent compliance banner and 4-call Priority Queue (Show 03_day4_call_queue_dedicated.png).

[2:00 - 3:15]  Scenario 1 vs Scenario 2 (The Contrast Demo)
               - Open Scenario 1 (CALL-2026-1001): Show LOW RISK and successful voice verification.
               - Open Scenario 2 (CALL-2026-1002): Show CRITICAL RISK alert, vishing triggers, and failed voice challenge.

[3:15 - 4:15]  Escalation & Hard Negative Verification
               - On Scenario 2: Enter note and click "Escalate for Human Review" (Show 09_day4_escalation.png).
               - Open Scenario 3 (CALL-2026-1003): Explain hard negative logic (advisory "never share OTP" does NOT trigger scam).

[4:15 - 5:00]  Audit History Vault & Privacy Verification
               - Scroll to Audit Vault (Show 10_day4_audit_history.png).
               - Prove zero raw confidence leakage (only safe public metadata).

[5:00 - 6:00]  Q&A & Offline Whisper Proof
               - Mention 160/160 unit tests passing on AAA-ASR.
               - Reference NANDAN_DAY4_OFFLINE_WHISPER_VERIFICATION.md.
```

---

## 12. Known Limitations & Scope Disclosures

To maintain absolute academic and engineering honesty, disclose the following operational boundaries:
1. **Simulated Telephony:** CallGuard simulates call-centre workflows using pre-recorded and conversational transcripts. Live PSTN/SIP trunking and direct telephone wire interception are out of sprint scope.
2. **Mock Mode Presentation:** This demonstration executes against verified client-side mock adapters matching the frozen API v1 contract. Live end-to-end integration requires Surya's backend server running simultaneously on port 8000.
3. **Acoustic Environment Sensitivity:** While Whisper Base handles general speech accurately, extreme ambient noise or thick non-native accents may require speech volume normalization.
4. **Demonstration Biometrics:** Biometric challenge clicks in the UI simulate the safe policy outcomes of AAA Core; actual voice recording takes place through the independent AAA capture component.
