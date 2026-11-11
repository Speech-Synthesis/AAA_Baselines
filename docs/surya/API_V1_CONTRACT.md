# AAA Engine — API v1 Contract

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)
**Status:** APPROVED FOR IMPLEMENTATION

---

## Overview

This document defines the public API contract for AAA Engine v1. All endpoints are prefixed with `/v1/` and follow RESTful conventions.

### Design Principles

1. **Versioned API** — All endpoints under `/v1/` for backward compatibility
2. **Tenant Isolation** — All requests scoped to authenticated tenant
3. **Fail-Closed** — Required model failures result in DENY, not APPROVE
4. **Privacy by Default** — No raw audio retention, no internal score exposure
5. **Idempotency** — Safe operations where possible

### Public Decision Enum

| Value | Description |
|-------|-------------|
| `APPROVE` | Authentication successful |
| `DENY` | Authentication failed |
| `STEP_UP` | Additional verification required |
| `REVIEW` | Manual review required |
| `UNAVAILABLE` | Service temporarily unavailable |

---

## Authentication

### Host Application Authentication

All API requests require authentication via Bearer token.

```http
Authorization: Bearer <host_application_jwt>
```

The JWT must contain:
- `sub`: Tenant identifier
- `aud`: `aaa-engine`
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp

### AAA Capture Authorization

Capture grants are short-lived, single-use tokens for audio upload authorization.

---

## Endpoints

### POST /v1/enroll

Consent-based voice enrollment.

#### Request

```http
POST /v1/enroll
Content-Type: multipart/form-data
Authorization: Bearer <jwt>
X-Request-ID: <uuid>
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string (UUID) | Yes | User identifier |
| `audio` | file (WAV) | Yes | Enrollment audio (16kHz, mono, 3-10s) |
| `consent_token` | string | Yes | User consent verification token |

#### Response

**201 Created**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "enrolled",
  "sample_count": 3,
  "enrolled_at": "2026-11-11T10:30:00Z"
}
```

**400 Bad Request**

```json
{
  "error": "invalid_request",
  "message": "Audio duration must be between 3 and 10 seconds",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**409 Conflict**

```json
{
  "error": "already_enrolled",
  "message": "User already has an active voiceprint",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /v1/challenges

Generate a fresh, session-bound authentication challenge.

#### Request

```http
POST /v1/challenges
Content-Type: application/json
Authorization: Bearer <jwt>
X-Request-ID: <uuid>
```

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "optional-session-identifier"
}
```

#### Response

**201 Created**

```json
{
  "challenge_id": "789e0123-e89b-12d3-a456-426614174000",
  "phrase": "Say: seven crimson falcon four",
  "capture_grant": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-11-11T10:31:30Z",
  "ttl_seconds": 90
}
```

**404 Not Found**

```json
{
  "error": "user_not_found",
  "message": "User does not exist or has no enrolled voiceprint",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /v1/verify

Submit audio capture for verification.

#### Request

```http
POST /v1/verify
Content-Type: multipart/form-data
Authorization: Bearer <jwt>
X-Request-ID: <uuid>
X-Capture-Grant: <capture_grant_token>
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `challenge_id` | string (UUID) | Yes | Challenge identifier |
| `audio` | file (WAV) | Yes | Verification audio (16kHz, mono) |

#### Response

**200 OK**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "verification_id": "abc12345-e89b-12d3-a456-426614174000",
  "decision": "APPROVE",
  "reason": "Authentication successful",
  "completed_at": "2026-11-11T10:30:45Z"
}
```

**Note:** Internal model scores (l1_score, l2_confidence) are NOT exposed in the public response. These are logged internally for audit purposes.

#### Decision Outcomes

| Decision | Description |
|----------|-------------|
| `APPROVE` | All gates passed |
| `DENY` | One or more gates failed |
| `STEP_UP` | Marginal result, additional factor required |
| `REVIEW` | Anomaly detected, manual review flagged |
| `UNAVAILABLE` | Required model unavailable |

**422 Unprocessable Entity**

```json
{
  "error": "verification_failed",
  "decision": "DENY",
  "reason": "Challenge phrase mismatch",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### GET /v1/verification-requests/{request_id}

Retrieve verification request status.

#### Request

```http
GET /v1/verification-requests/abc12345-e89b-12d3-a456-426614174000
Authorization: Bearer <jwt>
```

#### Response

**200 OK**

```json
{
  "request_id": "abc12345-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "decision": "APPROVE",
  "created_at": "2026-11-11T10:30:00Z",
  "completed_at": "2026-11-11T10:30:45Z"
}
```

---

### POST /v1/risk/transcript

Submit transcript for risk analysis (AAA-VR).

#### Request

```http
POST /v1/risk/transcript
Content-Type: application/json
Authorization: Bearer <jwt>
X-Request-ID: <uuid>
```

```json
{
  "session_id": "call-session-123",
  "transcript": "I need to transfer money to account ending in 4567...",
  "context": {
    "call_type": "inbound",
    "claimed_identity": "John Smith"
  }
}
```

#### Response

**200 OK**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_level": "HIGH",
  "risk_indicators": [
    "urgent_transfer_request",
    "account_number_mentioned",
    "pressure_tactics_detected"
  ],
  "recommended_action": "STEP_UP",
  "analyzed_at": "2026-11-11T10:30:00Z"
}
```

---

### POST /v1/voiceprints/{voiceprint_id}/revoke

Revoke an enrolled voiceprint.

#### Request

```http
POST /v1/voiceprints/123e4567-e89b-12d3-a456-426614174000/revoke
Content-Type: application/json
Authorization: Bearer <jwt>
X-Request-ID: <uuid>
```

```json
{
  "reason": "user_requested",
  "confirmation_token": "revoke-confirmation-xyz"
}
```

#### Response

**200 OK**

```json
{
  "voiceprint_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "revoked",
  "revoked_at": "2026-11-11T10:30:00Z"
}
```

---

### GET /v1/health

Liveness check.

#### Request

```http
GET /v1/health
```

#### Response

**200 OK**

```json
{
  "status": "healthy",
  "timestamp": "2026-11-11T10:30:00Z"
}
```

---

### GET /v1/ready

Readiness check.

#### Request

```http
GET /v1/ready
```

#### Response

**200 OK** (when ready)

```json
{
  "status": "ready",
  "timestamp": "2026-11-11T10:30:00Z",
  "checks": {
    "database": "ok",
    "models": {
      "speaker_verification": "ok",
      "deepfake_detection": "ok",
      "asr": "ok"
    },
    "configuration": "ok"
  }
}
```

**503 Service Unavailable** (when not ready)

```json
{
  "status": "not_ready",
  "timestamp": "2026-11-11T10:30:00Z",
  "checks": {
    "database": "ok",
    "models": {
      "speaker_verification": "ok",
      "deepfake_detection": "loading",
      "asr": "ok"
    },
    "configuration": "ok"
  }
}
```

---

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes* | Bearer token for authenticated endpoints |
| `X-Request-ID` | Recommended | Client-generated request ID for tracing |
| `X-Capture-Grant` | Conditional | Required for audio upload |
| `Content-Type` | Yes | `application/json` or `multipart/form-data` |

*Not required for `/v1/health` and `/v1/ready`

### Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Echo of client request ID |
| `X-Correlation-ID` | Server-generated correlation ID |

---

## Error Responses

### Standard Error Format

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {}
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `unauthorized` | 401 | Missing or invalid authentication |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `conflict` | 409 | Resource conflict |
| `validation_error` | 422 | Request validation failed |
| `rate_limited` | 429 | Too many requests |
| `internal_error` | 500 | Internal server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

---

## Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/v1/challenges` | 10 requests | 1 minute |
| `/v1/verify` | 5 requests | 1 minute |
| `/v1/enroll` | 3 requests | 5 minutes |
| Other endpoints | 100 requests | 1 minute |

---

## Validation Rules

### Audio Requirements

| Property | Requirement |
|----------|-------------|
| Format | WAV (PCM) |
| Sample Rate | 16000 Hz |
| Channels | Mono (1 channel) |
| Bit Depth | 16-bit |
| Duration (enrollment) | 3-10 seconds |
| Duration (verification) | 2-10 seconds |
| Max File Size | 5 MB |

### UUID Format

All identifiers follow RFC 4122 UUID v4 format:
```
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
```

---

## Idempotency

The following endpoints support idempotency:

| Endpoint | Idempotency Key |
|----------|-----------------|
| POST /v1/enroll | `X-Idempotency-Key` header |
| POST /v1/verify | `challenge_id` (inherently single-use) |

---

**Document Version:** 1.0
**Classification:** API Contract
