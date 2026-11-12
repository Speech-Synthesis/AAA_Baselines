# AAA Engine — Sequence Flows

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)

---

## 1. Enrollment Flow

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Auth as Tenant Resolution
    participant Enroll as Enrollment Service
    participant SV as AAA-SV Adapter
    participant DB as PostgreSQL

    Client->>API: POST /v1/enroll<br/>(JWT, user_id, audio, consent_token)
    API->>Auth: Validate JWT
    Auth-->>API: Tenant Context

    API->>Enroll: Process Enrollment
    Enroll->>Enroll: Validate consent token
    Enroll->>Enroll: Validate audio format

    Enroll->>SV: Extract embedding(audio)
    SV-->>Enroll: Embedding (192-dim)

    Enroll->>Enroll: Encrypt embedding (AES-256-GCM)
    Enroll->>DB: Store voiceprint

    DB-->>Enroll: Success
    Enroll-->>API: Enrollment Result
    API-->>Client: 201 Created<br/>{status: "enrolled", sample_count: 1}
```

---

## 2. Challenge Generation Flow

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Auth as Tenant Resolution
    participant Challenge as Challenge Service
    participant DB as PostgreSQL

    Client->>API: POST /v1/challenges<br/>(JWT, user_id)
    API->>Auth: Validate JWT
    Auth-->>API: Tenant Context

    API->>Challenge: Generate Challenge
    Challenge->>DB: Verify user has voiceprint
    DB-->>Challenge: Voiceprint exists

    Challenge->>Challenge: Generate random phrase<br/>"Say: seven crimson falcon four"
    Challenge->>Challenge: Generate HMAC token (90s TTL)
    Challenge->>Challenge: Generate capture grant

    Challenge->>DB: Store challenge record
    DB-->>Challenge: Challenge ID

    Challenge-->>API: Challenge Response
    API-->>Client: 201 Created<br/>{phrase, capture_grant, expires_at}
```

---

## 3. Verification Flow (Success)

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Auth as Tenant Resolution
    participant Verify as Verification Service
    participant Orch as Orchestrator
    participant AD as AAA-AD
    participant ASR as AAA-ASR
    participant SV as AAA-SV
    participant Policy as Policy Engine
    participant DB as PostgreSQL

    Client->>API: POST /v1/verify<br/>(JWT, capture_grant, challenge_id, audio)
    API->>Auth: Validate JWT + capture grant
    Auth-->>API: Tenant Context

    API->>Verify: Process Verification
    Verify->>DB: Get & consume challenge
    DB-->>Verify: Challenge (now consumed)

    Verify->>Orch: Execute Pipeline(audio, phrase)

    par Gate 1 & 2 (Parallel)
        Orch->>AD: detect_spoof(audio)
        AD-->>Orch: {label: "bonafide", confidence: 0.95}

        Orch->>ASR: verify_phrase(audio, phrase)
        ASR-->>Orch: {match: true, similarity: 0.92}
    end

    Note over Orch: Gates 1 & 2 passed

    Orch->>SV: verify_speaker(audio, voiceprint)
    SV-->>Orch: {score: 0.87, embedding: [...]}

    Note over Orch: Gate 3 passed

    Orch->>Policy: Evaluate Results
    Policy-->>Orch: APPROVE

    Orch->>DB: EMA update voiceprint
    Orch->>DB: Log audit event

    Orch-->>Verify: Decision: APPROVE
    Verify-->>API: Verification Result
    API-->>Client: 200 OK<br/>{decision: "APPROVE", reason: "..."}
```

---

## 4. Verification Flow (Denial - Deepfake Detected)

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Verify as Verification Service
    participant Orch as Orchestrator
    participant AD as AAA-AD
    participant Policy as Policy Engine
    participant DB as PostgreSQL

    Client->>API: POST /v1/verify<br/>(audio)
    API->>Verify: Process Verification

    Verify->>Orch: Execute Pipeline(audio)

    Orch->>AD: detect_spoof(audio)
    AD-->>Orch: {label: "spoof", confidence: 0.89}

    Note over Orch: Gate 1 FAILED<br/>Deepfake detected

    Orch->>Policy: Evaluate (AD failed)
    Policy-->>Orch: DENY

    Orch->>DB: Log audit event (layer_blocked: 2)

    Orch-->>Verify: Decision: DENY
    Verify-->>API: Verification Result
    API-->>Client: 422<br/>{decision: "DENY", reason: "Verification failed"}
```

---

## 5. Verification Flow (Denial - Phrase Mismatch)

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant Orch as Orchestrator
    participant AD as AAA-AD
    participant ASR as AAA-ASR
    participant Policy as Policy Engine
    participant DB as PostgreSQL

    Note over Orch: Audio received

    par Gate 1 & 2
        Orch->>AD: detect_spoof(audio)
        AD-->>Orch: {label: "bonafide"}

        Orch->>ASR: verify_phrase(audio, expected)
        ASR-->>Orch: {match: false, similarity: 0.35}
    end

    Note over Orch: Gate 2 FAILED<br/>Phrase mismatch

    Orch->>Policy: Evaluate (ASR failed)
    Policy-->>Orch: DENY

    Orch->>DB: Log audit event (layer_blocked: 4)

    Orch-->>Client: {decision: "DENY", reason: "Phrase mismatch"}
```

---

## 6. Verification Flow (Denial - Speaker Mismatch)

```mermaid
sequenceDiagram
    participant Orch as Orchestrator
    participant AD as AAA-AD
    participant ASR as AAA-ASR
    participant SV as AAA-SV
    participant Policy as Policy Engine
    participant DB as PostgreSQL

    par Gate 1 & 2
        Orch->>AD: detect_spoof(audio)
        AD-->>Orch: {label: "bonafide"}

        Orch->>ASR: verify_phrase(audio, expected)
        ASR-->>Orch: {match: true, similarity: 0.88}
    end

    Note over Orch: Gates 1 & 2 passed

    Orch->>SV: verify_speaker(audio, voiceprint)
    SV-->>Orch: {score: 0.32, embedding: [...]}

    Note over Orch: Gate 3 FAILED<br/>Speaker score below threshold

    Orch->>Policy: Evaluate (SV failed)
    Policy-->>Orch: DENY

    Orch->>DB: Log audit event (layer_blocked: 1)

    Orch-->>Client: {decision: "DENY", reason: "Verification failed"}
```

---

## 7. Token Validation Flow

```mermaid
sequenceDiagram
    participant Verify as Verification Service
    participant Challenge as Challenge Service
    participant DB as PostgreSQL

    Verify->>Challenge: Validate & consume token

    Challenge->>DB: SELECT challenge WHERE token = ?
    DB-->>Challenge: Challenge record

    alt Token not found
        Challenge-->>Verify: INVALID (not found)
    else Token already used
        Challenge-->>Verify: INVALID (already used)
    else Token expired
        Challenge-->>Verify: INVALID (expired)
    else Token valid
        Challenge->>DB: UPDATE challenge SET used = true
        DB-->>Challenge: Updated
        Challenge-->>Verify: VALID (consumed)
    end
```

---

## 8. Voiceprint Revocation Flow

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Auth as Tenant Resolution
    participant Revoke as Revocation Service
    participant DB as PostgreSQL

    Client->>API: POST /v1/voiceprints/{id}/revoke<br/>(JWT, reason, confirmation)
    API->>Auth: Validate JWT
    Auth-->>API: Tenant Context

    API->>Revoke: Process Revocation
    Revoke->>Revoke: Validate confirmation token

    Revoke->>DB: Get voiceprint
    DB-->>Revoke: Voiceprint

    Revoke->>Revoke: Verify tenant ownership

    Revoke->>DB: DELETE voiceprint
    Revoke->>DB: Log revocation audit event

    DB-->>Revoke: Success
    Revoke-->>API: Revocation Complete
    API-->>Client: 200 OK<br/>{status: "revoked"}
```

---

## 9. Health Check Flow

```mermaid
sequenceDiagram
    participant Client as Health Monitor
    participant API as AAA API Gateway

    Client->>API: GET /v1/health
    API-->>Client: 200 OK<br/>{status: "healthy"}
```

---

## 10. Readiness Check Flow

```mermaid
sequenceDiagram
    participant Client as Health Monitor
    participant API as AAA API Gateway
    participant DB as PostgreSQL
    participant AD as AAA-AD
    participant ASR as AAA-ASR
    participant SV as AAA-SV

    Client->>API: GET /v1/ready

    par Check all dependencies
        API->>DB: Ping
        DB-->>API: OK

        API->>AD: health()
        AD-->>API: OK

        API->>ASR: health()
        ASR-->>API: OK

        API->>SV: health()
        SV-->>API: OK
    end

    alt All checks pass
        API-->>Client: 200 OK<br/>{status: "ready"}
    else Any check fails
        API-->>Client: 503 Service Unavailable<br/>{status: "not_ready"}
    end
```

---

## 11. EMA Voiceprint Update Flow

```mermaid
sequenceDiagram
    participant Policy as Policy Engine
    participant DB as PostgreSQL

    Note over Policy: Authentication APPROVED

    Policy->>DB: Get current voiceprint
    DB-->>Policy: old_embedding (192-dim)

    Policy->>Policy: EMA calculation<br/>new = 0.8 * old + 0.2 * current

    Policy->>Policy: Encrypt updated embedding

    Policy->>DB: UPDATE voiceprint<br/>SET embedding = new,<br/>sample_count = sample_count + 1

    DB-->>Policy: Updated
```

---

## 12. Error Handling Flow

```mermaid
sequenceDiagram
    participant Client as Host Application
    participant API as AAA API Gateway
    participant Orch as Orchestrator
    participant Model as Model Adapter
    participant Policy as Policy Engine

    Client->>API: POST /v1/verify

    API->>Orch: Execute Pipeline

    Orch->>Model: predict(audio)

    alt Model timeout
        Model--xOrch: Timeout (10s)
        Orch->>Policy: Model unavailable
        Policy-->>Orch: UNAVAILABLE
    else Model error
        Model--xOrch: Exception
        Orch->>Policy: Model error
        Policy-->>Orch: UNAVAILABLE
    end

    Orch-->>API: Decision: UNAVAILABLE
    API-->>Client: 503<br/>{decision: "UNAVAILABLE"}
```

---

## State Diagrams

### Challenge State Machine

```mermaid
stateDiagram-v2
    [*] --> CREATED: generate_challenge()
    CREATED --> AUTHORIZED: issue_capture_grant()
    AUTHORIZED --> CAPTURE_RECEIVED: receive_audio()
    CAPTURE_RECEIVED --> CONSUMED: validate_token()
    CONSUMED --> COMPLETED: finish_verification()

    CREATED --> EXPIRED: TTL exceeded (90s)
    AUTHORIZED --> EXPIRED: TTL exceeded

    EXPIRED --> [*]
    COMPLETED --> [*]
```

### Verification Request State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: receive_request()
    PENDING --> PROCESSING: start_pipeline()
    PROCESSING --> COMPLETED: decision_made()
    PROCESSING --> FAILED: error_occurred()

    COMPLETED --> [*]
    FAILED --> [*]
```

---

**Document Version:** 1.0
**Classification:** Architecture Documentation
