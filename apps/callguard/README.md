# CallGuard — Simulated Call-Centre Security Console

**Host Application:** CallGuard (Demonstration Host App 2)  
**Assigned Owner:** Nandan (Member 5)  
**Independent Peer Reviewer:** Aditya  
**Target Architecture:** AAA Engine Public REST API v1.0  
**Tenant ID:** `callcentre_demo`  
**Status:** DAY 1 IMPLEMENTATION & INTEGRATION PREPARATION  

---

## 1. Project Overview & Purpose

CallGuard is a simulated call-centre voice authentication and vishing (voice phishing) defense console. It demonstrates how modern enterprise customer service operations integrate the **AAA Engine** (Adaptive Acoustic Authentication with Deepfake Detection) to:

1. **Verify Customer Voice & Phrase Deterministically:** Prompt callers with single-use dynamic challenge phrases and verify them with zero-tolerance for near-miss or altered text.
2. **Defend Against Vishing & Social Engineering:** Continually analyze live transcript segments for coercion, urgency, and credential solicitations using **AAA-VR**.
3. **Trigger Tier 2 Human Review:** Allow operators to step-up or escalate suspicious calls without exposing raw biometric scores or accusing callers prematurely.
4. **Maintain Auditable Compliance:** Record immutable verification request IDs and safe public reason codes.

> **CRITICAL COMPLIANCE NOTICE:**  
> **SIMULATED CALL — DEMO DATA ONLY.** CallGuard operates purely on synthetic customer identifiers, simulated call sessions, and mocked/consented challenge phrases. No live telephony interception, recording of real customers, or storage of actual PII is permitted.

---

## 2. Technology Stack

- **Framework:** React 18.2 (Functional Components + Hooks)
- **Build Tool:** Vite 5.0
- **Language:** JavaScript (ES Modules)
- **Styling:** Custom Enterprise Dark CSS Design System (no heavy external UI bloat)
- **Runtime:** Node.js v22.22.1 / npm 10.8.1
- **API Target:** AAA Engine REST API `/v1/*`

---

## 3. Directory Structure

```text
apps/callguard/
├── README.md                 # Technical documentation & demo runbook
├── package.json              # Local npm dependencies
├── vite.config.js            # Vite configuration (port 5174)
├── index.html                # Entry HTML shell
├── src/
│   ├── main.jsx              # React DOM mounting
│   ├── App.jsx               # Top-level router & global state
│   ├── data/
│   │   └── mockData.js       # Seeded agents, calls, customers, audit logs
│   ├── services/
│   │   └── api.js            # AAA Engine API client & mock adapter
│   ├── pages/
│   │   ├── AgentLogin.jsx    # Seeded agent authentication
│   │   ├── Dashboard.jsx     # Call queue & priority overview
│   │   └── ActiveCall.jsx    # Active call console with voice verifier
│   ├── components/
│   │   ├── RiskPanel.jsx     # AAA-VR vishing risk indicator
│   │   ├── EscalationPanel.jsx # Human review & fraud escalation
│   │   └── AuditHistory.jsx  # Security audit trail (no raw scores)
│   └── styles/
│       └── style.css         # Enterprise dark theme design system
```

---

## 4. Installation & Local Development

All dependencies must be installed on the **E: drive** in compliance with project policy:

```powershell
# Navigate to the CallGuard directory
cd E:\AAA_Project\AAA_Baselines\apps\callguard

# Install dependencies using local E: drive cache
npm install --cache E:\AAA_Project\AAA_Baselines\.cache\npm

# Start the Vite development server
npm run dev
```

The application will be accessible at:  
👉 **`http://localhost:5174`**

To produce a production build:
```powershell
npm run build
```

---

## 5. Seeded Demo Accounts & Scenarios

### 5.1 Demo Operators
- **Sarah Jenkins** (`agent.sarah`): Senior Security Specialist (High-Value Verification Queue). Password: `demo123`
- **David Chen** (`agent.david`): Tier 2 Fraud Investigator (Escalated Vishing Review). Password: `demo123`

### 5.2 Seeded Call Scenarios
1. **CALL-2026-1001 (`customer_001`): Routine High-Value Wire Transfer**
   - **Vishing Risk:** `LOW` (`ROUTINE_TRANSACTION`)
   - **Voice Verification:** Pending challenge. Clicking "Caller Speaks Exact Phrase" simulates biometric approval (`APPROVE` / `REQUIRED_CHECKS_PASSED`).
2. **CALL-2026-1002 (`customer_002`): Urgent Executive Credential Solicitation (Vishing Attack)**
   - **Vishing Risk:** `HIGH` (`URGENT_CREDENTIAL_SOLICITATION`)
   - **Recommended Action:** `ESCALATE_HUMAN_REVIEW`
   - **Voice Verification:** Caller attempts near-miss or wrong phrase (`DENY` / `CHALLENGE_MISMATCH`).
3. **CALL-2026-1003 (`customer_003`): Genuine Security Advisory (Hard Negative Test)**
   - **Transcript:** Agent states *"Remember we will never ask you to share your OTP"*.
   - **Vishing Risk:** `LOW` (`SECURITY_AWARENESS_WARNING`).
   - **Verification:** Proves AAA-VR does not trigger naive false positives on fraud advisory text.

---

## 6. AAA Integration Architecture & Security Guardrails

### 6.1 Strict Audio Handling Rule
- **Direct Upload Only:** The AAA-controlled web capture component records directly on the client device and uploads straight to AAA (`POST /v1/verify`).
- **Zero Transit:** CallGuard host frontend and backend **NEVER** receive, buffer, proxy, or store customer audio.

### 6.2 Biometric Privacy & Public Reasons
- CallGuard consumes only high-level safe policy decisions (`APPROVE`, `DENY`, `STEP_UP`, `REVIEW`, `UNAVAILABLE`) and public reason categories.
- Raw ECAPA-TDNN embeddings, cosine similarity scores, and Wav2Vec2 confidence floats are strictly protected inside AAA Engine and are **NEVER** rendered in CallGuard.

### 6.3 No Client Secrets in Frontend
- All tenant credentials reside on the host backend. The frontend utilizes single-use, scoped capture grants issued by `/v1/challenges`.

---

## 7. Known Day 1 Limitations

1. **Mock API Adapter Active:** By default, CallGuard connects to `api.js` mock responses matching Surya's approved API specification. Full live integration with the unified AAA middleware occurs on Day 3.
2. **Simulated Microphone Trigger:** Challenge voice submission is simulated via deterministic UI triggers until the unified capture web component is embedded.
3. **Local Telephony Out of Scope:** The app models a call-centre desktop workflow; live SIP/PSTN trunking is explicitly excluded from sprint requirements.
