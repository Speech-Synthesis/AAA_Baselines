# CallGuard Risk Panel Integration Specification (AAA-VR)

**Module:** AAA-VR (Voice Risk / Transcript Risk Engine)  
**Author:** Karthik Mallareddy (mrkarthik1811@gmail.com)  
**Status:** FROZEN  

---

## 1. Overview
The CallGuard Risk Panel provides real-time fraud, coercion, and vishing protection for telephone agents and banking representatives. Downstream UI panels MUST display only approved public reason codes without leaking detection thresholds.

---

## 2. API Contract
- **Endpoint:** `POST /v1/risk/transcript`
- **Headers:**
  - `Authorization: Bearer <tenant_jwt>`
  - `X-Request-ID: <uuid>` (optional)

### Request Schema
```json
{
  "session_id": "call-session-987",
  "transcript": "I need an urgent transfer to an unlisted beneficiary right now.",
  "context": {
    "call_type": "inbound",
    "claimed_identity": "Jane Doe"
  }
}
```

### Response Schema (Safe Public Metadata)
```json
{
  "request_id": "c62b9a10-2e4a-4d2b-9861-558231920000",
  "session_id": "call-session-987",
  "risk_level": "HIGH",
  "risk_indicators": [
    "URGENT_TRANSFER_REQUEST",
    "UNVERIFIED_BENEFICIARY"
  ],
  "recommended_action": "STEP_UP",
  "confidence": 0.90,
  "model_version": "aaa-vr-transcript-risk-v1",
  "analyzed_at": "2026-11-13T17:00:00Z"
}
```

---

## 3. Frozen Public Reason-Code List
1. `URGENT_TRANSFER_REQUEST` — Immediate wire/funds transfer demand.
2. `PRESSURE_TACTICS_DETECTED` — Coercive threats, legal action, or fabricated emergencies.
3. `ACCOUNT_NUMBER_MENTIONED` — Raw account or routing details disclosed.
4. `CREDENTIAL_HARVESTING_ATTEMPT` — Demands for PIN, OTP, passwords, or SSN.
5. `UNVERIFIED_BENEFICIARY` — Redirection to third-party accounts, crypto, or gift cards.
6. `IMPERSONATION_ATTEMPT` — Claiming false authority (fraud desk, law enforcement).
7. `VOICE_STRESS_ANOMALY` — Inconsistent acoustic pattern under challenge.
