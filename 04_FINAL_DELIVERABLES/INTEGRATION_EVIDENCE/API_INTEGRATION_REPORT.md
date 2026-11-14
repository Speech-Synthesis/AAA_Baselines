# AAA Engine — API Integration Evidence

**Date:** November 14, 2026
**Version:** 1.0
**Project Lead:** Surya

---

## 1. API Endpoints Summary

### 1.1 V1 API Endpoints (Production)

| Endpoint | Method | Auth | Rate Limit | Status |
|----------|--------|------|------------|--------|
| `/v1/challenges` | POST | Optional JWT | 10/min | ✅ Active |
| `/v1/enroll` | POST | Optional JWT | 5/min | ✅ Active |
| `/v1/verify` | POST | Optional JWT | 20/min | ✅ Active |
| `/health` | GET | None | None | ✅ Active |

### 1.2 Legacy Auth Endpoints

| Endpoint | Method | Status |
|----------|--------|--------|
| `/auth/challenge` | POST | ⚠️ Deprecated |
| `/auth/enroll` | POST | ⚠️ Deprecated |
| `/auth/verify` | POST | ⚠️ Deprecated |

---

## 2. Request/Response Examples

### 2.1 Challenge Generation

**Request:**
```http
POST /v1/challenges HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Optional

{
    "user_id": "user-123"
}
```

**Response (201 Created):**
```json
{
    "challenge_id": "chg_abc123def456",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "phrase": "The quick brown fox jumps over the lazy dog",
    "expires_at": "2026-11-14T12:05:00Z"
}
```

### 2.2 Voice Enrollment

**Request:**
```http
POST /v1/enroll HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Optional

{
    "user_id": "user-123",
    "audio_base64": "<base64_encoded_audio>",
    "sample_rate": 16000
}
```

**Response (201 Created):**
```json
{
    "user_id": "user-123",
    "enrolled": true,
    "voiceprint_id": "vp_xyz789",
    "created_at": "2026-11-14T12:00:00Z"
}
```

### 2.3 Voice Verification

**Request:**
```http
POST /v1/verify HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Optional

{
    "user_id": "user-123",
    "challenge_token": "<challenge_token>",
    "audio_base64": "<base64_encoded_audio>",
    "sample_rate": 16000
}
```

**Response (200 OK):**
```json
{
    "decision": "APPROVE",
    "request_id": "req_abc123",
    "verified_at": "2026-11-14T12:01:00Z"
}
```

**Response (200 OK - Rejected):**
```json
{
    "decision": "REJECT",
    "reason": "speaker_mismatch",
    "request_id": "req_def456"
}
```

---

## 3. Verification Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        /v1/verify Endpoint                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: Token Validation                                            │
│ - Validate challenge token signature (HMAC-SHA256)                  │
│ - Check token not expired                                           │
│ - Consume token (single-use enforcement)                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: L2 — Deepfake Detection                                     │
│ - Adapter: MockSpoofAdapter / ProductionSpoofAdapter                │
│ - Output: bonafide | spoof                                          │
│ - Threshold: configurable                                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: ASR — Phrase Verification                                   │
│ - Adapter: MockASRAdapter / WhisperAdapter                          │
│ - Phrase matching with fuzzy logic                                  │
│ - WER threshold: 0.3                                                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: L1 — Speaker Verification                                   │
│ - Retrieve encrypted voiceprint                                     │
│ - Decrypt with tenant key (AES-256-GCM)                             │
│ - Compare embeddings (cosine similarity)                            │
│ - Threshold: 0.7                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: L3 — Risk Assessment                                        │
│ - Aggregate layer decisions                                         │
│ - Apply business rules                                              │
│ - Generate final decision: APPROVE | REJECT | REVIEW                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Authentication Integration

### 4.1 JWT Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│ AAA API  │────▶│ JWT Auth │
└──────────┘     └──────────┘     └──────────┘
      │                                 │
      │ Authorization: Bearer <token>   │
      │                                 ▼
      │                          ┌──────────┐
      │                          │ Validate │
      │                          │  Token   │
      │                          └──────────┘
      │                                 │
      │                                 ▼
      │                          ┌──────────┐
      │                          │ Extract  │
      │                          │tenant_id │
      │                          └──────────┘
```

### 4.2 Host App Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Host App │────▶│ AAA API  │────▶│Host Auth │
└──────────┘     └──────────┘     └──────────┘
      │                                 │
      │ X-Host-App-ID: app-123          │
      │ X-Host-Signature: <hmac>        ▼
      │ X-Host-Timestamp: <unix>   ┌──────────┐
      │                            │ Validate │
      │                            │   HMAC   │
      │                            └──────────┘
```

---

## 5. Error Responses

### 5.1 Standard Error Format

```json
{
    "error": "error_code",
    "message": "Human-readable description",
    "request_id": "req_abc123"
}
```

### 5.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_token` | 401 | Challenge token invalid or expired |
| `token_consumed` | 400 | Token already used (replay attempt) |
| `user_not_found` | 404 | User not enrolled |
| `rate_limit_exceeded` | 429 | Too many requests |
| `validation_error` | 422 | Invalid request body |
| `internal_error` | 500 | Server error |

---

## 6. Integration Test Results

### 6.1 End-to-End Tests

| Test Scenario | Result |
|---------------|--------|
| Full enrollment flow | ✅ Pass |
| Full verification flow | ✅ Pass |
| Challenge generation | ✅ Pass |
| Token single-use | ✅ Pass |
| JWT tenant isolation | ✅ Pass |
| Encrypted voiceprint storage | ✅ Pass |
| Decryption for verification | ✅ Pass |

### 6.2 API Contract Tests

| Endpoint | Request Validation | Response Format | Status |
|----------|-------------------|-----------------|--------|
| `/v1/challenges` | ✅ | ✅ | Pass |
| `/v1/enroll` | ✅ | ✅ | Pass |
| `/v1/verify` | ✅ | ✅ | Pass |
| `/health` | ✅ | ✅ | Pass |

---

## 7. Performance Metrics

| Endpoint | Avg Latency | P95 Latency | Throughput |
|----------|-------------|-------------|------------|
| `/v1/challenges` | 12ms | 25ms | 100 req/s |
| `/v1/enroll` | 150ms | 300ms | 20 req/s |
| `/v1/verify` | 200ms | 400ms | 50 req/s |

*Note: Metrics from mock adapters. Production latency depends on ML model inference.*

---

## 8. SDK Integration Examples

### 8.1 Python Client

```python
import httpx

class AAAClient:
    def __init__(self, base_url: str, jwt_token: str = None):
        self.base_url = base_url
        self.headers = {}
        if jwt_token:
            self.headers["Authorization"] = f"Bearer {jwt_token}"

    def create_challenge(self, user_id: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/v1/challenges",
            json={"user_id": user_id},
            headers=self.headers
        )
        return response.json()

    def verify(self, user_id: str, token: str, audio_b64: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/v1/verify",
            json={
                "user_id": user_id,
                "challenge_token": token,
                "audio_base64": audio_b64,
                "sample_rate": 16000
            },
            headers=self.headers
        )
        return response.json()
```

### 8.2 cURL Examples

```bash
# Create challenge
curl -X POST http://localhost:8000/v1/challenges \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'

# Verify with audio
curl -X POST http://localhost:8000/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "challenge_token": "<token>",
    "audio_base64": "<base64_audio>",
    "sample_rate": 16000
  }'
```

---

**Document Version:** 1.0
**Author:** Surya
**Timestamp:** November 14, 2026
