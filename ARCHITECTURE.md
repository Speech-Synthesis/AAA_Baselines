# AAA Engine Architecture

Technical deep dive into AAA Engine's system architecture, data flow, security model, and implementation details.

---

## Table of Contents

- [System Overview](#system-overview)
- [Five-Outcome Policy Engine](#five-outcome-policy-engine)
- [Authentication Pipeline](#authentication-pipeline)
- [Layer Implementations](#layer-implementations)
- [Security Architecture](#security-architecture)
- [Database Design](#database-design)
- [API Architecture](#api-architecture)
- [Host Application Integration](#host-application-integration)
- [Performance & Scalability](#performance--scalability)

---

## System Overview

### Design Principles

1. **Defense in Depth:** Multiple independent security layers, each capable of rejecting malicious attempts
2. **Fail-Closed:** Any gate failure results in denial - system never fails open
3. **Parallel Execution:** AD (deepfake) and ASR (phrase) run concurrently for performance
4. **SV Gating:** Speaker verification only runs after AD and ASR pass (security + cost optimization)
5. **Adaptability:** Voiceprints evolve via EMA to accommodate natural voice changes
6. **Tenant Isolation:** Row-Level Security (RLS) for multi-tenant deployments
7. **Audit Trail:** Complete logging with PII redaction for compliance

### High-Level Architecture

```
+===========================================================================+
|                           CLIENT LAYER                                     |
|                                                                            |
|   +---------------------+    +---------------------+    +--------------+   |
|   | Main Frontend       |    | Banking Shield      |    | CallGuard    |   |
|   | (Port 5173)         |    | (Port 3000)         |    | (Port 5174)  |   |
|   +---------------------+    +---------------------+    +--------------+   |
|              |                        |                        |           |
|              +------------------------+------------------------+           |
|                                       |                                    |
|                          AAA-Controlled Capture                            |
|                          (Iframe Pattern)                                  |
+===========================================================================+
                                        |
                                        | HTTPS REST API
                                        | multipart/form-data (audio)
                                        | application/json (metadata)
                                        |
+===========================================================================+
|                           API LAYER (Port 8000)                            |
|                              FastAPI + Uvicorn                             |
|                                                                            |
|   +-------------+  +-------------+  +-------------+  +-------------+       |
|   | /v1/health  |  | /v1/        |  | /v1/verify  |  | /v1/risk/   |       |
|   | /v1/ready   |  | challenges  |  | /v1/enroll  |  | transcript  |       |
|   +-------------+  +-------------+  +-------------+  +-------------+       |
|                                                                            |
|   +--------------------------------------------------------------------+   |
|   |                    MIDDLEWARE STACK                                 |   |
|   |  CORS → Rate Limiting → JWT Auth → Tenant Isolation → Log Redaction|   |
|   +--------------------------------------------------------------------+   |
+===========================================================================+
                                        |
                                        v
+===========================================================================+
|                        PROCESSING LAYER                                    |
|                                                                            |
|   +====================================================================+   |
|   |              PARALLEL EXECUTION: AD || ASR                          |   |
|   |   +------------------------+    +------------------------+          |   |
|   |   | AAA-AD (Layer 2)       |    | AAA-ASR (Whisper)      |          |   |
|   |   | Wav2Vec2 Deepfake      |    | Phrase Verification    |          |   |
|   |   | Detection              |    | Deterministic Matcher  |          |   |
|   |   +------------------------+    +------------------------+          |   |
|   +====================================================================+   |
|                          | Both Pass                                       |
|                          v                                                 |
|   +--------------------------------------------------------------------+   |
|   | AAA-SV (Layer 1) - Speaker Verification                             |   |
|   | ECAPA-TDNN 192-dim Embeddings                                       |   |
|   | Cosine Similarity with EMA Update                                   |   |
|   +--------------------------------------------------------------------+   |
|                          |                                                 |
|                          v                                                 |
|   +--------------------------------------------------------------------+   |
|   | AAA-VR - Vishing Risk Analysis (Optional)                           |   |
|   | 10 Risk Indicators + Hard-Negative Detection                        |   |
|   +--------------------------------------------------------------------+   |
|                          |                                                 |
|                          v                                                 |
|   +--------------------------------------------------------------------+   |
|   | POLICY ENGINE - Five-Outcome Decision                               |   |
|   | APPROVE | DENY | STEP_UP | REVIEW | UNAVAILABLE                     |   |
|   +--------------------------------------------------------------------+   |
+===========================================================================+
                                        |
                                        v
+===========================================================================+
|                        PERSISTENCE LAYER                                   |
|                    PostgreSQL (Supabase) with RLS                          |
|                                                                            |
|  +----------+ +-------------+ +------------+ +-----------+ +------------+  |
|  | users    | | voiceprints | | challenges | | auth_logs | | consent_   |  |
|  |          | |             | |            | |           | | records    |  |
|  | id (UUID)| | id (UUID)   | | id (UUID)  | | id (UUID) | | id (UUID)  |  |
|  | name     | | user_id     | | user_id    | | user_id   | | user_id    |  |
|  | email    | | embedding   | | phrase     | | decision  | | consent_   |  |
|  | tenant_id| | (encrypted) | | token      | | risk_level| | type       |  |
|  +----------+ +-------------+ +------------+ +-----------+ +------------+  |
|                                                                            |
|  +------------------+  +------------------+                                 |
|  | voiceprint_      |  | model_registry   |                                 |
|  | history          |  |                  |                                 |
|  | (audit trail)    |  | (version control)|                                 |
|  +------------------+  +------------------+                                 |
+===========================================================================+
```

---

## Five-Outcome Policy Engine

The PolicyEngine is the centralized decision authority. **All authentication decisions flow through it.**

### Decision Outcomes

| Decision | Description | Action Required |
|----------|-------------|-----------------|
| **APPROVE** | All gates pass, authentication successful | Grant access |
| **DENY** | Authentication failed (spoof, wrong voice, invalid token) | Block access |
| **STEP_UP** | Marginal confidence, need additional verification | Request fresh challenge |
| **REVIEW** | Anomaly detected, requires human review | Queue for manual review |
| **UNAVAILABLE** | Service degraded, cannot process | Retry later |

### Policy Decision Flow

```
                     PolicyInput
                         |
        +----------------+----------------+
        |                |                |
   AD Result        ASR Result        SV Result
   (L2)             (Phrase)          (L1)
        |                |                |
        v                v                v
+--------------------------------------------------+
|              POLICY ENGINE                        |
|                                                   |
|  1. Check service availability                    |
|     - All required models loaded?                 |
|     - Database accessible?                        |
|     → UNAVAILABLE if any critical service down    |
|                                                   |
|  2. Check challenge validity                      |
|     - Token expired? → DENY (TOKEN_EXPIRED)       |
|     - Token consumed? → DENY (TOKEN_REUSED)       |
|     - Invalid signature? → DENY (TOKEN_INVALID)   |
|                                                   |
|  3. Evaluate AD gate (Layer 2)                    |
|     - spoof_confidence > 0.5 → DENY (SPOOF)       |
|     - AD timeout → UNAVAILABLE                    |
|                                                   |
|  4. Evaluate ASR gate                             |
|     - phrase_similarity < 0.6 → DENY (PHRASE)     |
|     - ASR timeout → UNAVAILABLE                   |
|                                                   |
|  5. Evaluate SV gate (Layer 1)                    |
|     - score < 0.4 → DENY (SPEAKER_MISMATCH)       |
|     - 0.4 <= score < 0.5 → STEP_UP                |
|     - score >= 0.5 → Continue                     |
|                                                   |
|  6. Apply risk modifiers                          |
|     - VR CRITICAL indicators → REVIEW             |
|     - VR HIGH indicators → STEP_UP                |
|                                                   |
|  7. Final decision                                |
|     - All gates pass → APPROVE                    |
+--------------------------------------------------+
                         |
                         v
                  PolicyOutput
                  {
                    decision: Decision,
                    reason_public: str,
                    reason_internal: str,
                    risk_level: RiskLevel,
                    gate_blocked: str | None,
                    requires_fresh_challenge: bool,
                    requires_human_review: bool
                  }
```

### Risk Levels

| Level | Description | Typical Triggers |
|-------|-------------|------------------|
| **LOW** | Normal operation | Clean authentication |
| **MEDIUM** | Minor anomalies | Address change requests |
| **HIGH** | Significant concern | Urgent transfer requests, pressure tactics |
| **CRITICAL** | Immediate threat | Credential harvesting, impersonation |

---

## Authentication Pipeline

### Enrollment Flow

```
User Registration
       |
       v
+------------------+
| POST /auth/      |
| register         |
| {name, email}    |
+--------+---------+
         |
         v
   Create User Record
   (UUID primary key)
         |
         v
+------------------+
| POST /v1/enroll  |
| user_id + audio  |
+--------+---------+
         |
         v
+------------------+
| AAA-SV:          |
| Extract ECAPA    |
| 192-dim Embedding|
+--------+---------+
         |
         +---> First sample? ---> Create voiceprint
         |                        Encrypt with AES-256-GCM
         |
         +---> Existing? ---> EMA Update:
                              new = 0.8 * old + 0.2 * current
                              Re-encrypt
         |
         v
   Log to voiceprint_history
   Return {status, sample_count}
```

### Verification Flow (Parallel AD||ASR)

```
+---------------------------+
| GET /v1/challenges        |
| ?user_id=<uuid>           |
+-------------+-------------+
              |
              v
    +-------------------+
    | Generate 4-word   |
    | Random Phrase     |
    | (50^4 combinations)|
    +-------------------+
              |
              v
    +-------------------+
    | HMAC-SHA256 Token |
    | payload: user_id  |
    |   + phrase        |
    |   + expires_at    |
    +-------------------+
              |
              v
    Store in challenges table
    Return {phrase, token, expires_at, ttl_seconds: 90}
              |
              v
+---------------------------+
| POST /v1/verify           |
| user_id + token + audio   |
+-------------+-------------+
              |
              v
+===========================================================+
|           PARALLEL EXECUTION (asyncio.gather)              |
|                                                            |
|   +-----------------------+    +-----------------------+   |
|   | AD (Layer 2)          |    | ASR (Whisper)         |   |
|   | Wav2Vec2 Deepfake     |    | Transcribe → Match    |   |
|   | ~420ms                |    | ~800ms                |   |
|   +-----------------------+    +-----------------------+   |
|              |                           |                 |
|              v                           v                 |
|         l2_result                  asr_result              |
|   {label, confidence}         {match, similarity,          |
|                                transcript}                 |
+===========================================================+
              |
              | Both results ready
              v
    +-------------------+     +---------------------------+
    | AD Gate Check     | --> | If spoof > 0.5            |
    |                   |     | → DENY (SPOOF_DETECTED)   |
    +-------------------+     +---------------------------+
              |
              | Pass
              v
    +-------------------+     +---------------------------+
    | ASR Gate Check    | --> | If similarity < 0.6       |
    |                   |     | → DENY (PHRASE_MISMATCH)  |
    +-------------------+     +---------------------------+
              |
              | Pass (AD and ASR both passed)
              v
+=============================================================+
|                 SV GATE (Layer 1)                            |
|   Only runs after AD+ASR pass (security + cost saving)       |
|                                                              |
|   +-----------------------------------------------------+    |
|   | 1. Decrypt stored voiceprint (AES-256-GCM)          |    |
|   | 2. Extract embedding from new audio                  |    |
|   | 3. Compute cosine similarity                         |    |
|   | 4. Apply threshold logic                             |    |
|   +-----------------------------------------------------+    |
+=============================================================+
              |
              v
    +-------------------+     +---------------------------+
    | SV Score < 0.4    | --> | DENY (SPEAKER_MISMATCH)   |
    +-------------------+     +---------------------------+
              |
    +-------------------+     +---------------------------+
    | 0.4 <= Score < 0.5| --> | STEP_UP (marginal match)  |
    +-------------------+     +---------------------------+
              |
              | Score >= 0.5
              v
    +-------------------+
    | Token Validation  |
    | - Check expiry    |
    | - Check single-use|
    | - Verify HMAC     |
    +-------------------+
              |
              v
    +-------------------+
    | APPROVE           |
    | - Consume token   |
    | - EMA update VP   |
    | - Log success     |
    +-------------------+
```

---

## Layer Implementations

### Layer 2: Deepfake Detection (AAA-AD)

**File:** `backend/app/layer2_deepfake.py`

**Model:** `garystafford/wav2vec2-deepfake-voice-detector`

| Specification | Value |
|--------------|-------|
| Architecture | Wav2Vec2 + Classification Head |
| Parameters | ~95M |
| Input | 16kHz mono WAV |
| Output | {label: bonafide|spoof, confidence: 0.0-1.0} |
| Threshold | 0.5 (configurable via L2_SPOOF_THRESHOLD) |
| Latency | ~420ms (CPU) |

**Lazy Loading Pattern:**
```python
_MODEL = None  # Module-level, loaded on first use

def _load_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
        _MODEL.eval()
```

### ASR Layer: Phrase Verification (AAA-ASR)

**File:** `backend/app/layer3_asr.py`

**Model:** OpenAI Whisper (base, 74M parameters)

| Specification | Value |
|--------------|-------|
| Model Size | base (74M params) |
| Input | 16kHz mono WAV |
| Output | (match: bool, similarity: float, transcript: str) |
| Threshold | 0.6 (configurable via ASR_PHRASE_THRESHOLD) |
| Latency | ~800ms (CPU) |

**Deterministic Phrase Matcher:**
```python
# backend/app/aaa_asr/phrase_matcher.py
def verify_phrase(transcript: str, expected: str, threshold: float) -> tuple[bool, float]:
    """
    Deterministic phrase matching with normalization.
    
    Normalization:
    - Lowercase
    - Remove punctuation
    - Collapse whitespace
    - Number word substitution (1 → one)
    
    Similarity: Levenshtein ratio
    """
```

### Layer 1: Speaker Verification (AAA-SV)

**File:** `backend/app/layer1_speaker.py`

**Model:** `speechbrain/spkrec-ecapa-voxceleb`

| Specification | Value |
|--------------|-------|
| Architecture | ECAPA-TDNN |
| Embedding Size | 192 dimensions |
| Input | 16kHz mono WAV |
| Output | {score: 0.0-1.0, embedding: float[192]} |
| Threshold | 0.5 (configurable via L1_SIMILARITY_THRESHOLD) |
| Latency | ~300ms (CPU) |

**EMA Voiceprint Adaptation:**
```python
def update_voiceprint(old: list[float], new: list[float], alpha: float = 0.2) -> list[float]:
    """
    Exponential Moving Average update.
    
    Formula: updated = (1 - alpha) * old + alpha * new
           = 0.8 * old + 0.2 * new
    
    Security rationale:
    - alpha = 0.2 requires ~10 successful auths for 50% shift
    - Prevents single-sample poisoning attacks
    - Allows gradual adaptation to natural voice changes
    """
    return [(1.0 - alpha) * o + alpha * n for o, n in zip(old, new)]
```

### Vishing Risk Analysis (AAA-VR)

**File:** `backend/app/adapters/vr.py`

**10 Risk Indicators:**

| Indicator | Severity | Example Trigger |
|-----------|----------|-----------------|
| OTP_SOLICITATION | CRITICAL | "read back your OTP" |
| CREDENTIAL_HARVESTING_ATTEMPT | CRITICAL | "give me your password" |
| PRESSURE_TACTICS_DETECTED | HIGH | "do it now or you'll be fired" |
| IMPERSONATION_ATTEMPT | HIGH | "I'm calling from the fraud desk" |
| REMOTE_ACCESS_REQUEST | HIGH | "install TeamViewer" |
| EMOTIONAL_MANIPULATION | HIGH | "your account will be closed" |
| FINANCIAL_COERCION | HIGH | "urgent wire transfer needed" |
| BYPASS_REQUEST | HIGH | "skip the verification" |
| URGENT_TRANSFER_REQUEST | MEDIUM | "immediately transfer funds" |
| ACCOUNT_NUMBER_MENTIONED | MEDIUM | "account ending in 1234" |

**Hard-Negative Detection:**
```python
NEGATION_PATTERNS = [
    r"never\s+share\s+your\s+(otp|pin|password)",
    r"we\s+will\s+never\s+ask",
    r"fraud\s+prevention\s+unit",
    r"keep\s+your\s+(?:otp|pin|password).*(?:private|secret)",
]
# Genuine bank security advisories are NOT flagged as threats
```

---

## Security Architecture

### Cryptographic Primitives

| Component | Algorithm | Key Size | Purpose |
|-----------|-----------|----------|---------|
| Challenge Tokens | HMAC-SHA256 | 256-bit | Token signing |
| JWT Auth | RS256 / HS256 | 256-bit+ | Tenant authentication |
| Voiceprint Storage | AES-256-GCM | 256-bit | At-rest encryption |
| Password Hashing | Argon2id | N/A | Host app secrets |

### Token Security

```
Challenge Token Structure:
+------------------------------------------------------------------+
| HMAC-SHA256(                                                      |
|   secret = L3_HMAC_SECRET,                                        |
|   message = f"{user_id}:{phrase}:{expires_at.isoformat()}"        |
| )                                                                 |
+------------------------------------------------------------------+
| Output: 64-character hex string                                   |
| TTL: 90 seconds                                                   |
| Single-use: Marked as consumed after successful verification      |
+------------------------------------------------------------------+
```

### Voiceprint Encryption

```python
def encrypt_embedding(embedding: list[float], tenant_id: str, user_id: str) -> str:
    """
    AES-256-GCM encryption with tenant-specific key derivation.
    
    Key derivation: HKDF(master_key, salt=tenant_id + user_id)
    Ciphertext format: base64(nonce || ciphertext || tag)
    """
```

### Threat Matrix

| Attack Vector | Mitigation | Layer |
|--------------|------------|-------|
| AI Voice Cloning | Wav2Vec2 deepfake detector | L2 (AD) |
| TTS Synthesis | Wav2Vec2 deepfake detector | L2 (AD) |
| Voice Conversion | Wav2Vec2 deepfake detector | L2 (AD) |
| Replay Attack (recording) | Single-use HMAC tokens | L3 |
| Replay Attack (wrong phrase) | ASR phrase verification | ASR |
| Impersonation | Speaker embedding comparison | L1 (SV) |
| Token Forgery | HMAC-SHA256 signature | L3 |
| Brute Force | 90s token expiration + rate limiting | L3 |
| Voiceprint Poisoning | EMA with low alpha (0.2) | L3 |
| Social Engineering | VR transcript analysis | VR |
| Data Breach | AES-256-GCM encryption | Storage |
| Cross-tenant Access | Row-Level Security (RLS) | DB |

### Log Redaction

All logs are automatically redacted to remove PII:

```python
REDACTION_PATTERNS = [
    (r"email[\"']?\s*[:=]\s*[^,\s]+@[^,\s]+", "email: [REDACTED]"),
    (r"password[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+", "password: [REDACTED]"),
    (r"token[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9._-]{20,}", "token: [REDACTED]"),
    (r"Bearer\s+[a-zA-Z0-9._-]+", "Bearer [REDACTED]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
]
```

---

## Database Design

### Entity Relationship Diagram

```
+-------------+       +---------------+       +--------------+
|   users     |       |  voiceprints  |       |  challenges  |
+-------------+       +---------------+       +--------------+
| id (PK,UUID)|<----->| id (PK,UUID)  |       | id (PK,UUID) |
| name        |   1:1 | user_id (FK)  |<------| user_id (FK) |
| email       |       | embedding     |   1:N | phrase       |
| tenant_id   |       | (encrypted)   |       | token        |
| created_at  |       | sample_count  |       | signature    |
+-------------+       | updated_at    |       | expires_at   |
      ^               +---------------+       | used         |
      |                      |                +--------------+
      |                      v                       |
      |         +------------------+                 |
      |         | voiceprint_      |                 |
      |         | history          |                 |
      |         +------------------+                 |
      |         | id (PK,UUID)     |                 |
      |         | voiceprint_id    |                 |
      |         | action           |                 |
      |         | embedding_hash   |                 |
      |         +------------------+                 |
      |                                              |
      |       +---------------+                      |
      +------>|  auth_logs    |<---------------------+
          1:N +---------------+
              | id (PK,UUID)  |
              | user_id (FK)  |
              | challenge_id  |
              | decision      |
              | risk_level    |
              | gate_blocked  |
              | created_at    |
              +---------------+

+------------------+       +------------------+
| consent_records  |       | model_registry   |
+------------------+       +------------------+
| id (PK,UUID)     |       | id (PK,UUID)     |
| user_id (FK)     |       | model_name       |
| tenant_id        |       | model_version    |
| consent_type     |       | checkpoint_sha256|
| consent_version  |       | status           |
| granted_at       |       | deployed_at      |
| withdrawn_at     |       | metrics_json     |
+------------------+       +------------------+
```

### GUID Type (PostgreSQL Native UUID)

```python
class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses native UUID for PostgreSQL, VARCHAR(36) for SQLite.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))
```

---

## API Architecture

### Endpoint Summary

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/v1/health` | GET | None | None | Liveness check |
| `/v1/ready` | GET | None | None | Readiness check (models, DB) |
| `/v1/challenges` | POST | Optional | 10/min | Generate challenge |
| `/v1/verify` | POST | Optional | 5/min | Verify authentication |
| `/v1/enroll` | POST | Optional | 3/5min | Enroll voiceprint |
| `/v1/risk/transcript` | POST | JWT | 10/min | VR analysis |
| `/v1/consent` | POST | JWT | None | Record consent |
| `/v1/capture/grants` | POST | JWT | 10/min | AAA-controlled capture |
| `/v1/voiceprints/{id}` | DELETE | JWT | None | Revoke voiceprint |

### Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | All 5 decisions (APPROVE, DENY, etc.) |
| 400 | Bad Request | Missing audio, invalid user |
| 401 | Unauthorized | Invalid/expired JWT |
| 403 | Forbidden | Tenant isolation violation |
| 404 | Not Found | User/voiceprint not found |
| 413 | Payload Too Large | Audio > 10MB |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Model failure |
| 503 | Service Unavailable | Models not loaded |

---

## Host Application Integration

### AAA-Controlled Capture Pattern

```
+-------------------------------------------------------------+
|                    HOST APPLICATION                          |
|                                                              |
|   +---------------------+                                    |
|   | User Interface      |                                    |
|   +----------+----------+                                    |
|              |                                               |
|              | 1. Request challenge                          |
|              v                                               |
|   +---------------------+                                    |
|   | POST /v1/challenges |                                    |
|   +----------+----------+                                    |
|              |                                               |
|              | 2. Receive {phrase, token, capture_url}       |
|              v                                               |
|   +---------------------+                                    |
|   | Render AAA Capture  |                                    |
|   | Component (iframe)  | <-- Audio NEVER passes through    |
|   +----------+----------+     host application               |
|              |                                               |
+-------------------------------------------------------------+
               |
               | 3. Audio uploaded directly to AAA
               v
+-------------------------------------------------------------+
|                    AAA ENGINE                                |
|                                                              |
|   +-----------------------+                                  |
|   | POST /v1/verify       |                                  |
|   | (receives audio       |                                  |
|   |  directly from iframe)|                                  |
|   +-----------+-----------+                                  |
|               |                                              |
|               v                                              |
|   +-----------------------+                                  |
|   | Five-Outcome Decision |                                  |
|   +-----------+-----------+                                  |
|               |                                              |
+-------------------------------------------------------------+
               |
               | 4. Decision callback to host
               v
+-------------------------------------------------------------+
|                    HOST APPLICATION                          |
|                                                              |
|   Receives: {decision, reason_public, risk_level}            |
|   (No raw audio, no internal scores)                         |
+-------------------------------------------------------------+
```

### Port Configuration (Development)

| Application | Port | Purpose |
|-------------|------|---------|
| AAA Backend | 8000 | REST API |
| Main Frontend | 5173 | Demo/testing |
| Banking Shield | 3000 | Host app demo |
| CallGuard | 5174 | Host app demo |

---

## Performance & Scalability

### Latency Breakdown (CPU)

| Stage | Latency | Notes |
|-------|---------|-------|
| Audio Preprocessing | ~50ms | Resample to 16kHz |
| AD (Deepfake) | ~420ms | Wav2Vec2 inference |
| ASR (Whisper) | ~800ms | Transcription |
| SV (Speaker) | ~300ms | ECAPA embedding |
| Policy Evaluation | <10ms | Pure logic |
| **Total (Sequential)** | **~1580ms** | Old approach |
| **Total (Parallel AD\|\|ASR)** | **~1100ms** | Current approach |

### Scaling Strategies

1. **Vertical (GPU):** 5-10x inference speedup
2. **Horizontal:** Load balancer with stateless backends
3. **Model Optimization:** INT8 quantization, ONNX runtime
4. **Caching:** Redis for challenge tokens

---

## References

- [ECAPA-TDNN Paper](https://arxiv.org/abs/2005.07143)
- [Wav2Vec 2.0 Paper](https://arxiv.org/abs/2006.11477)
- [Whisper Paper](https://arxiv.org/abs/2212.04356)
- [ASVspoof Challenge](https://www.asvspoof.org/)

---

**Document Version:** 2.0  
**Last Updated:** November 2026
