# AAA Engine — System Architecture

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)

---

## 1. Overview

AAA Engine (Adaptive Audio Authentication) is a voice biometric authentication middleware with integrated deepfake detection. It provides a secure, privacy-preserving voice authentication service that can be integrated into host applications like Banking Shield and CallGuard.

### Core Principles

1. **Fail-Closed** — Required model failures result in DENY, never APPROVE
2. **Privacy by Default** — No raw audio retention, local inference preferred
3. **Defense in Depth** — Multiple verification layers, any can reject
4. **Tenant Isolation** — Complete separation between tenants
5. **Adaptive Security** — Voiceprints evolve with legitimate use

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HOST APPLICATIONS                                   │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │   Banking Shield    │              │     CallGuard       │               │
│  │   (Karthik)         │              │     (Nandan)        │               │
│  └──────────┬──────────┘              └──────────┬──────────┘               │
└─────────────┼────────────────────────────────────┼──────────────────────────┘
              │ Authenticated Request               │
              └─────────────────┬───────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AAA ENGINE CORE                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        API GATEWAY (v1)                               │   │
│  │  /v1/enroll │ /v1/challenges │ /v1/verify │ /v1/risk/transcript      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     TENANT RESOLUTION                                 │   │
│  │              (JWT validation, tenant context extraction)              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    SESSION & CHALLENGE SERVICE                        │   │
│  │       (Challenge generation, capture grants, token lifecycle)         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATOR                                     │   │
│  │                                                                       │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │   │    Gate 1   │  │    Gate 2   │  │    Gate 3   │                  │   │
│  │   │   AAA-AD    │  │   AAA-ASR   │  │   AAA-SV    │                  │   │
│  │   │  (Aditya)   │  │  (Nandan)   │  │ (Navadeep)  │                  │   │
│  │   │  Deepfake   │  │   Phrase    │  │  Speaker    │                  │   │
│  │   │  Detection  │  │ Validation  │  │Verification │                  │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      POLICY ENGINE                                    │   │
│  │      (Final decision: APPROVE / DENY / STEP_UP / REVIEW)              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      PERSISTENCE LAYER                                │   │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │   │   Users    │  │ Voiceprints│  │ Challenges │  │ Audit Logs │    │   │
│  │   └────────────┘  └────────────┘  └────────────┘  └────────────┘    │   │
│  │                      PostgreSQL                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌───────────────────────┐
                        │       AAA-VR          │
                        │     (Karthik)         │
                        │  Transcript Risk      │
                        │     Analysis          │
                        └───────────────────────┘
```

---

## 3. Component Responsibilities

### 3.1 API Gateway

**Purpose:** HTTP interface for host applications

**Responsibilities:**
- Route requests to appropriate services
- Validate request format and headers
- Apply rate limiting
- Handle CORS
- Generate correlation IDs
- Format responses

**Key Endpoints:**
| Endpoint | Purpose |
|----------|---------|
| POST /v1/enroll | Voice enrollment |
| POST /v1/challenges | Generate challenge |
| POST /v1/verify | Submit verification |
| GET /v1/health | Liveness check |
| GET /v1/ready | Readiness check |

### 3.2 Tenant Resolution

**Purpose:** Extract and validate tenant context

**Responsibilities:**
- Validate JWT authentication
- Extract tenant identifier from token
- Establish tenant context for request
- Enforce tenant isolation

### 3.3 Session & Challenge Service

**Purpose:** Manage authentication sessions and challenges

**Responsibilities:**
- Generate cryptographically random challenge phrases
- Create HMAC-signed, time-limited tokens
- Issue capture authorization grants
- Enforce single-use token consumption
- Track session state

**Token Lifecycle:**
```
CREATED → AUTHORIZED → CAPTURE_RECEIVED → CONSUMED → COMPLETED
                 │
                 └→ EXPIRED (TTL exceeded)
```

### 3.4 Orchestrator

**Purpose:** Coordinate model execution pipeline

**Responsibilities:**
- Execute gates in defined order
- Handle gate failures (fail-fast)
- Support parallel execution where safe
- Aggregate gate results
- Apply timeout policies

**Gate Execution Order:**
1. **Gate 1 (AAA-AD):** Deepfake detection
2. **Gate 2 (AAA-ASR):** Phrase validation
3. **Gate 3 (AAA-SV):** Speaker verification

**Parallel Execution:**
Gates 1 and 2 MAY execute in parallel when resource constraints permit, as they are independent. Gate 3 (SV) MUST wait until Gates 1 and 2 pass.

### 3.5 Policy Engine

**Purpose:** Make final authentication decision

**Responsibilities:**
- Evaluate gate results against thresholds
- Apply business rules
- Determine decision outcome
- Trigger voiceprint updates on success
- Generate audit events

**Decision Matrix:**
| AD Result | ASR Result | SV Result | Decision |
|-----------|------------|-----------|----------|
| Pass | Pass | Pass | APPROVE |
| Fail | - | - | DENY |
| Pass | Fail | - | DENY |
| Pass | Pass | Fail | DENY |
| Pass | Pass | Marginal | STEP_UP |
| Error | - | - | UNAVAILABLE |

### 3.6 Model Adapters

**Purpose:** Abstract model implementation details

**Common Interface:**
```python
class ModelAdapter:
    async def health(self) -> bool
    async def predict(self, request: ModelRequest) -> ModelResponse
    def version(self) -> str
```

**Adapter Types:**
| Adapter | Owner | Model |
|---------|-------|-------|
| SpeakerVerificationAdapter | Navadeep | ECAPA-TDNN |
| DeepfakeDetectionAdapter | Aditya | Wav2Vec2 |
| ASRAdapter | Nandan | Whisper |
| TranscriptRiskAdapter | Karthik | TBD |

---

## 4. Data Flow

### 4.1 Enrollment Flow

```
1. Host App → POST /v1/enroll
2. Validate JWT, extract tenant
3. Validate consent token
4. Validate audio format
5. Extract speaker embedding (AAA-SV)
6. Encrypt embedding (AES-256-GCM)
7. Store voiceprint
8. Return enrollment confirmation
```

### 4.2 Challenge Flow

```
1. Host App → POST /v1/challenges
2. Validate JWT, extract tenant
3. Verify user has enrolled voiceprint
4. Generate random phrase
5. Create HMAC-signed token (90s TTL)
6. Issue capture grant
7. Store challenge record
8. Return challenge + capture grant
```

### 4.3 Verification Flow

```
1. Host App → POST /v1/verify
2. Validate JWT + capture grant
3. Validate challenge not expired/used
4. Mark challenge as CONSUMED
5. Execute Gate 1: Deepfake detection
   └── If spoof → DENY
6. Execute Gate 2: Phrase validation
   └── If mismatch → DENY
7. Execute Gate 3: Speaker verification
   └── If below threshold → DENY
8. Policy engine makes final decision
9. If APPROVE:
   └── EMA update voiceprint
10. Log audit event
11. Return decision (no internal scores)
```

---

## 5. Security Architecture

### 5.1 Authentication

| Layer | Mechanism |
|-------|-----------|
| Host App → AAA | JWT (RS256) |
| Challenge Token | HMAC-SHA256 |
| Capture Grant | JWT (short-lived) |

### 5.2 Data Protection

| Data | Protection |
|------|------------|
| Voiceprints | AES-256-GCM encryption |
| Raw Audio | Not retained (processed in memory) |
| Challenge Tokens | Single-use, 90s TTL |
| API Keys | Environment variables |

### 5.3 Tenant Isolation

- Tenant ID embedded in all database queries
- Cross-tenant access prevented at repository level
- Separate encryption keys per tenant (future)

### 5.4 Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| /v1/challenges | 10 | 1 min |
| /v1/verify | 5 | 1 min |
| /v1/enroll | 3 | 5 min |

---

## 6. Deployment Architecture

### 6.1 Local Development

```yaml
services:
  aaa-backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://...
      - L3_HMAC_SECRET=${L3_HMAC_SECRET}

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### 6.2 Production (Render)

```yaml
services:
  - type: web
    name: aaa-backend
    runtime: python
    healthCheckPath: /v1/health
    envVars:
      - key: DATABASE_URL
        fromDatabase: ...
```

---

## 7. Module Organization

```
backend/app/
├── api/
│   └── v1/
│       ├── enroll.py
│       ├── challenges.py
│       ├── verify.py
│       ├── requests.py
│       ├── transcript.py
│       ├── voiceprints.py
│       └── health.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── exceptions.py
├── orchestration/
│   ├── pipeline.py
│   ├── model_router.py
│   └── policy_engine.py
├── services/
│   ├── challenge_service.py
│   ├── enrollment_service.py
│   ├── capture_service.py
│   └── audit_service.py
├── adapters/
│   ├── base.py
│   ├── sv.py
│   ├── ad.py
│   ├── asr.py
│   └── vr.py
├── db/
│   ├── models.py
│   ├── session.py
│   └── repositories.py
└── schemas/
    ├── common.py
    ├── enrollment.py
    ├── challenge.py
    ├── verification.py
    └── transcript.py
```

---

## 8. Integration Points

### 8.1 Banking Shield

- Uses /v1/enroll for customer enrollment
- Uses /v1/verify for transaction authorization
- Receives APPROVE/DENY/STEP_UP decisions

### 8.2 CallGuard

- Uses /v1/verify for caller authentication
- Uses /v1/risk/transcript for vishing detection
- Real-time processing requirements

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Target |
|--------|--------|
| Verification latency | < 2s |
| Challenge generation | < 100ms |
| Model inference (total) | < 1.5s |

### 9.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Health check interval | 10s |
| Graceful shutdown | 30s |

### 9.3 Scalability

| Aspect | Approach |
|--------|----------|
| Horizontal scaling | Stateless API, shared PostgreSQL |
| Session state | Database-backed (not in-memory) |
| Model loading | Lazy initialization |

---

**Document Version:** 1.0
**Classification:** Architecture Documentation
