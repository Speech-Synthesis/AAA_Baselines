# AAA-VR CallGuard Risk Panel Integration Report

**Target Service:** AAA-VR (Adaptive Acoustic Authentication — Voice Risk Engine)  
**Author / Security Owner:** Karthik Mallareddy (`mrkarthik1811@gmail.com`)  
**Target Integration:** CallGuard Day 2 Risk Panel  
**Date:** November 13, 2026  
**Status:** **FROZEN & PRODUCTION READY**  
**Branch:** `feat/karthik-security-banking`  

---

## 1. Executive Summary

This integration report provides the official, frozen contract between the **AAA-VR Transcript Risk Engine** and the **CallGuard Risk Panel**. 

All reason codes, risk levels, and recommended actions specified herein are strictly scoped to **safe public metadata**. They are mathematically safe for rendering in agent-facing UIs and host application dashboards without leaking detection thresholds, internal confidence weights, or acoustic feature metrics to potential adversaries.

---

## 2. API Endpoint Specification

### `POST /v1/risk/transcript`

Processes conversational transcripts from active telephone sessions, analyzes linguistic and acoustic-adjacent threat markers (coercion, social engineering, credential harvesting), and returns structured risk mitigation guidance.

#### HTTP Headers
| Header | Type | Required | Description |
|---|---|---|---|
| `Authorization` | `string` | **Yes** | Bearer JWT obtained from `/v1/auth/token` binding the `tenant_id` |
| `Content-Type` | `string` | **Yes** | Must be `application/json` |
| `X-Request-ID` | `string` (UUID) | Optional | Distributed tracing UUID. If omitted, AAA-VR generates one |

#### Request Payload
```json
{
  "session_id": "call-session-98742",
  "transcript": "Hello, I am calling from the fraud department. I need you to transfer funds immediately to account ending in 4567, or your profile will be suspended.",
  "context": {
    "call_type": "inbound",
    "claimed_identity": "Agent Smith",
    "customer_id": "cust-8812"
  }
}
```

#### Request Schema Attributes
- `session_id` (`string`, required): Unique identifier for the telecom/call session.
- `transcript` (`string`, required): Transcribed conversational segment (min 1 character).
- `context` (`object`, optional): Key-value contextual metadata (e.g., `call_type`, `claimed_identity`).

---

## 3. Expected Response Structure (Safe Metadata Only)

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "call-session-98742",
  "risk_level": "HIGH",
  "risk_indicators": [
    "URGENT_TRANSFER_REQUEST",
    "PRESSURE_TACTICS_DETECTED",
    "ACCOUNT_NUMBER_MENTIONED",
    "IMPERSONATION_ATTEMPT"
  ],
  "recommended_action": "STEP_UP",
  "confidence": 0.90,
  "model_version": "aaa-vr-transcript-risk-v1",
  "analyzed_at": "2026-11-13T17:15:00.000000Z"
}
```

### Response Field Definitions
| Field | Type | Description |
|---|---|---|
| `request_id` | `string` (UUID) | Unique correlation ID for audit and logging. |
| `session_id` | `string` | The corresponding call session identifier. |
| `risk_level` | `enum` | Overall risk assessment tier: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. |
| `risk_indicators` | `string[]` | Array of triggered public reason codes. |
| `recommended_action`| `enum` | Mitigation action: `APPROVE`, `REVIEW`, `STEP_UP`, `DENY`. |
| `confidence` | `float` | Assessment confidence score between `0.0` and `1.0`. |
| `model_version` | `string` | Version of the AAA-VR model engine (`aaa-vr-transcript-risk-v1`). |
| `analyzed_at` | `string` (ISO 8601) | UTC timestamp of completion. |

---

## 4. Frozen Public Reason-Code List (`risk_indicators`)

The CallGuard UI panel must **only** render reason codes from this approved frozen list:

| Reason Code | Display Label | Risk Weight | Threat Description |
|---|---|:---:|---|
| `URGENT_TRANSFER_REQUEST` | **Urgent Wire Demand** | Medium | Caller demands immediate wire or funds movement with manufactured urgency. |
| `PRESSURE_TACTICS_DETECTED` | **Coercion / Legal Threat** | High | Coercive pressure, threats of arrest, police, legal action, or account termination. |
| `ACCOUNT_NUMBER_MENTIONED` | **Sensitive Account Disclosure** | Low/Med | Raw account numbers, routing numbers, IBAN, or SWIFT details spoken aloud. |
| `CREDENTIAL_HARVESTING_ATTEMPT`| **Credential Request** | Critical | Demanding passwords, PINs, OTP codes, CVV, or Social Security numbers. |
| `UNVERIFIED_BENEFICIARY` | **Unverified Beneficiary** | High | Redirection of funds to unlisted accounts, cryptocurrency, or gift cards. |
| `IMPERSONATION_ATTEMPT` | **False Authority Claim** | Critical | False claims of representing bank security, fraud desks, IRS, or federal agents. |
| `VOICE_STRESS_ANOMALY` | **Acoustic Cadence Anomaly** | Med | Inconsistent vocal stress or cadence detected under challenge conditions. |

---

## 5. Decision Matrix & Action Guidance

| Risk Level | Recommended Action | Risk Panel UI Badge | Action for Agent / System |
|:---:|:---:|:---:|---|
| `LOW` | `APPROVE` |  **Green (Safe)** | Normal call flow; no abnormal vishing signals detected. |
| `MEDIUM` | `REVIEW` |  **Yellow (Caution)** | Single isolated flag; prompt agent to exercise standard verification caution. |
| `HIGH` | `STEP_UP` |  **Orange (Step-Up)** | Multiple risk markers present. Trigger AAA voice biometric challenge (`/v1/challenges`). |
| `CRITICAL` | `DENY` |  **Red (Escalate)** | Coercion or credential harvesting detected. Escalate immediately to Fraud Operations desk. |

---

## 6. Integration Example for CallGuard Frontend (React / TypeScript)

```typescript
// CallGuard Risk Client Integration
interface RiskAnalysisResponse {
  request_id: string;
  session_id: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_indicators: string[];
  recommended_action: 'APPROVE' | 'REVIEW' | 'STEP_UP' | 'DENY';
  confidence: number;
  model_version: string;
  analyzed_at: string;
}

export async function submitTranscriptForRisk(
  sessionId: string,
  transcript: string,
  token: string
): Promise<RiskAnalysisResponse> {
  const response = await fetch('/v1/risk/transcript', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Request-ID': crypto.randomUUID(),
    },
    body: JSON.stringify({
      session_id: sessionId,
      transcript: transcript,
    }),
  });

  if (!response.ok) {
    if (response.status === 429) throw new Error('RATE_LIMITED');
    if (response.status === 401) throw new Error('UNAUTHORIZED');
    throw new Error('RISK_EVALUATION_FAILED');
  }

  return response.json();
}
```

---

## 7. Security Guarantees

1. **Multi-Tenant Scoping**: All calls are authenticated via JWT Bearer tokens. Database and memory isolation guarantees tenant data segregation.
2. **Zero Attacker Threshold Leakage**: Error codes (e.g., `429 RATE_LIMITED`, `401 INVALID_CREDENTIALS`) and indicators never expose remaining limits, heuristic margins, or internal detection thresholds.
3. **Auditability**: Every analysis is tagged with an immutable `request_id` and timestamp.
