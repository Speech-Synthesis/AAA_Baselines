# Architecture Documentation

Technical deep dive into AAA Engine's system architecture, data flow, and implementation details.

---

## Table of Contents

- [System Overview](#system-overview)
- [Authentication Pipeline](#authentication-pipeline)
- [Layer Implementations](#layer-implementations)
- [Database Design](#database-design)
- [API Architecture](#api-architecture)
- [Security Model](#security-model)
- [Performance Considerations](#performance-considerations)
- [Scalability](#scalability)

---

## System Overview

### Design Principles

1. **Defense in Depth:** Multiple independent security layers, each capable of rejecting malicious attempts
2. **Fail-Fast:** Early rejection at cheaper layers reduces computational cost
3. **Adaptability:** Voiceprints evolve over time to accommodate natural voice changes
4. **Modularity:** Each layer is independently testable and replaceable

### High-Level Architecture

```
+------------------------------------------------------------------------+
|                              CLIENT LAYER                               |
|                                                                         |
|   +---------------------+                  +---------------------+      |
|   |   React Frontend    | <--------------> |   Audio Recording   |      |
|   |   (Vite, Port 5173) |                  |   (MediaRecorder)   |      |
|   +---------------------+                  +---------------------+      |
|              |                                                          |
+------------------------------------------------------------------------+
               |
               | HTTP/HTTPS REST API
               | Content-Type: multipart/form-data
               |
+------------------------------------------------------------------------+
|                              API LAYER                                  |
|                           FastAPI (Port 8000)                           |
|                                                                         |
|   +------------+   +------------+   +-------------+   +------------+   |
|   | POST       |   | POST       |   | GET         |   | POST       |   |
|   | /auth/     |   | /auth/     |   | /auth/      |   | /auth/     |   |
|   | register   |   | enroll     |   | challenge   |   | verify     |   |
|   +------------+   +-----+------+   +------+------+   +-----+------+   |
|                          |                 |               |            |
+------------------------------------------------------------------------+
                           |                 |               |
                           v                 v               v
+------------------------------------------------------------------------+
|                          PROCESSING LAYER                               |
|                                                                         |
|   +------------------+   +------------------+   +------------------+    |
|   | layer2_deepfake  |   | layer3_asr       |   | layer1_speaker   |    |
|   | .py              |   | .py              |   | .py              |    |
|   |                  |   |                  |   |                  |    |
|   | Wav2Vec2         |   | Whisper ASR      |   | ECAPA-TDNN       |    |
|   | Deepfake         |   | Phrase           |   | Speaker          |    |
|   | Detection        |   | Verification     |   | Embeddings       |    |
|   +------------------+   +------------------+   +------------------+    |
|                                                                         |
|   +------------------------------------------------------------------+ |
|   | layer3_adaptive.py                                                | |
|   |                                                                    | |
|   | - generate_challenge(): Create HMAC-signed challenge tokens        | |
|   | - verify_token(): Validate token expiry and single-use             | |
|   | - update_voiceprint(): EMA-based voiceprint adaptation             | |
|   +------------------------------------------------------------------+ |
|                                                                         |
+------------------------------------------------------------------------+
               |
               v
+------------------------------------------------------------------------+
|                         PERSISTENCE LAYER                               |
|                                                                         |
|   +-------------+   +---------------+   +--------------+   +----------+ |
|   | users       |   | voiceprints   |   | challenges   |   | auth_logs| |
|   |             |   |               |   |              |   |          | |
|   | id (PK)     |   | id (PK)       |   | id (PK)      |   | id (PK)  | |
|   | name        |   | user_id (FK)  |   | user_id (FK) |   | user_id  | |
|   | email       |   | embedding[192]|   | phrase       |   | result   | |
|   | created_at  |   | sample_count  |   | token        |   | l2_label | |
|   |             |   | updated_at    |   | expires_at   |   | l1_score | |
|   +-------------+   +---------------+   +--------------+   +----------+ |
|                                                                         |
|                    PostgreSQL / SQLite (SQLAlchemy ORM)                 |
+------------------------------------------------------------------------+
```

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
   Return user_id
         |
         v
+------------------+
| POST /auth/      |
| enroll           |
| user_id + audio  |
+--------+---------+
         |
         v
+------------------+
| Layer 1:         |
| Extract ECAPA    |
| Embedding        |
| (192-dim vector) |
+--------+---------+
         |
         +---> First sample? ---> Create voiceprint record
         |
         +---> Existing voiceprint? ---> EMA update:
                                         new = 0.8 * old + 0.2 * current
         |
         v
   Increment sample_count
   Return {status, sample_count}
```

### Verification Flow

```
+---------------------------+
| GET /auth/challenge       |
| ?user_id=<uuid>           |
+-------------+-------------+
              |
              v
    +-------------------+
    | Generate Random   |
    | 4-Word Phrase     |
    | from word list    |
    +-------------------+
              |
              v
    +-------------------+
    | Create HMAC Token |
    | Message: user_id  |
    |   + phrase        |
    |   + expires_at    |
    | Secret: L3_HMAC   |
    +-------------------+
              |
              v
    Store in challenges table
    Return {phrase, token, expires_at}
              |
              v
+---------------------------+
| POST /auth/verify         |
| user_id + token + audio   |
+-------------+-------------+
              |
              v
+---------------------------+     +---------------------------+
| LAYER 2: Deepfake Check   |     | If spoof confidence > 0.5 |
| Wav2Vec2 Classification   | --> | REJECT                    |
| Output: bonafide/spoof    |     | layer_blocked = 2         |
+-------------+-------------+     +---------------------------+
              |
              | Pass
              v
+---------------------------+     +---------------------------+
| ASR: Phrase Verification  |     | If similarity < 0.6       |
| Whisper Transcription     | --> | REJECT                    |
| Levenshtein Similarity    |     | layer_blocked = 4         |
+-------------+-------------+     +---------------------------+
              |
              | Pass
              v
+---------------------------+     +---------------------------+
| LAYER 1: Speaker Verify   |     | If score < 0.5            |
| ECAPA Embedding Extract   | --> | REJECT                    |
| Cosine Similarity         |     | layer_blocked = 1         |
+-------------+-------------+     +---------------------------+
              |
              | Pass
              v
+---------------------------+     +---------------------------+
| LAYER 3: Token Validation |     | If invalid/expired/used   |
| Check expiry (90s TTL)    | --> | REJECT                    |
| Check single-use          |     | layer_blocked = 3         |
+-------------+-------------+     +---------------------------+
              |
              | Pass
              v
    +-------------------+
    | ACCEPT            |
    | - Mark token used |
    | - EMA update      |
    |   voiceprint      |
    | - Log success     |
    +-------------------+
```

### Sequential Execution Rationale

Layers execute sequentially, not in parallel, for these reasons:

1. **Cost Optimization:** Cheapest checks run first (L2 ~420ms is faster to run before L1 extraction)
2. **Security:** Avoid revealing speaker information if deepfake is detected
3. **Early Termination:** Stop processing immediately on rejection

---

## Layer Implementations

### Layer 2: Deepfake Detection

**File:** `backend/app/layer2_deepfake.py`

**Model:** `garystafford/wav2vec2-deepfake-voice-detector`

**Architecture:**
```
Audio Input (16kHz mono)
       |
       v
+------------------+
| Wav2Vec2         |
| Feature          |
| Extractor        |
+--------+---------+
         |
         v
+------------------+
| Transformer      |
| Encoder          |
| (12 layers)      |
+--------+---------+
         |
         v
+------------------+
| Classification   |
| Head             |
| (2 classes)      |
+--------+---------+
         |
         v
   Softmax --> bonafide (0) / spoof (1)
```

**Function Signature:**
```python
def detect_spoof(audio_bytes: bytes) -> dict:
    """
    Classify audio as genuine or synthetic.

    Args:
        audio_bytes: Raw WAV audio data

    Returns:
        {
            "label": "bonafide" | "spoof",
            "confidence": float  # 0.0 to 1.0
        }
    """
```

**Limitations:**
- Trained on ASVspoof 2019 data (pre-modern TTS systems)
- May not detect latest generation TTS (ElevenLabs, VALL-E, XTTS)
- Adversarial examples remain a concern

---

### ASR Layer: Phrase Verification

**File:** `backend/app/layer3_asr.py`

**Model:** OpenAI Whisper (base, 74M parameters)

**Process:**
```
Audio Input
       |
       v
+------------------+
| Whisper ASR      |
| Transcription    |
+--------+---------+
         |
         v
+------------------+
| Text Cleanup     |
| - Lowercase      |
| - Strip spaces   |
+--------+---------+
         |
         v
+------------------+
| Levenshtein      |
| Similarity       |
| Ratio            |
+--------+---------+
         |
         v
   Compare to expected phrase
   Return (match, similarity, transcript)
```

**Function Signature:**
```python
def verify_phrase(
    audio_bytes: bytes,
    expected_phrase: str,
    threshold: float
) -> tuple[bool, float, str]:
    """
    Verify spoken phrase matches expected phrase.

    Returns:
        (match: bool, similarity: float, transcript: str)
    """
```

---

### Layer 1: Speaker Verification

**File:** `backend/app/layer1_speaker.py`

**Model:** `speechbrain/spkrec-ecapa-voxceleb` (ECAPA-TDNN)

**Architecture:**
```
Audio Input (16kHz mono)
       |
       v
+----------------------+
| Mel Spectrogram      |
| Extraction           |
+----------+-----------+
           |
           v
+----------------------+
| ECAPA-TDNN Encoder   |
| - SE-Res2Net blocks  |
| - Channel attention  |
| - Temporal attention |
+----------+-----------+
           |
           v
+----------------------+
| Statistics Pooling   |
| (mean + std)         |
+----------+-----------+
           |
           v
   192-dimensional embedding
```

**Function Signatures:**
```python
def enroll_speaker(audio_bytes: bytes) -> dict:
    """
    Extract speaker embedding from audio.

    Returns:
        {"embedding": list[float]}  # 192-dimensional
    """

def verify_speaker(
    audio_bytes: bytes,
    stored_embedding: list[float]
) -> dict:
    """
    Compare audio to stored voiceprint.

    Returns:
        {
            "score": float,      # Cosine similarity [0, 1]
            "embedding": list    # For EMA update
        }
    """
```

**Similarity Calculation:**
```python
# Cosine similarity ranges from -1 to 1
# Normalize to 0-1 range for threshold comparison
raw_similarity = cosine_similarity(enrolled, current)
score = (raw_similarity + 1) / 2
```

---

### Layer 3: Challenge-Response and Adaptation

**File:** `backend/app/layer3_adaptive.py`

**Challenge Generation:**
```python
WORD_LIST = [
    "apple", "blue", "cloud", "delta", "eagle", "forest",
    "guitar", "house", "island", "jungle", "king", "lion",
    # ... 50 words total
]

def generate_challenge(user_id: str) -> dict:
    # Select 4 random words
    phrase = " ".join(random.sample(WORD_LIST, 4))

    # Set expiration (90 seconds)
    expires_at = datetime.utcnow() + timedelta(seconds=90)

    # Generate HMAC token
    message = f"{user_id}:{phrase}:{expires_at.isoformat()}"
    token = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return {
        "phrase": phrase,
        "token": token,
        "expires_at": expires_at
    }
```

**Token Security:**
- 50^4 = 6,250,000 possible phrase combinations
- HMAC-SHA256 prevents token forgery
- 90-second window limits attack time
- Single-use enforcement prevents replay

**EMA Voiceprint Adaptation:**
```python
def update_voiceprint(
    old_embedding: list[float],
    new_embedding: list[float],
    alpha: float = 0.2
) -> list[float]:
    """
    Exponential Moving Average update.

    Formula: new = (1 - alpha) * old + alpha * current
           = 0.8 * old + 0.2 * current

    Rationale:
    - alpha = 0.2 balances stability with adaptability
    - Requires ~10 successful authentications to shift 50%
    - Prevents single-sample poisoning attacks
    """
    return [
        (1.0 - alpha) * old + alpha * new
        for old, new in zip(old_embedding, new_embedding)
    ]
```

---

## Database Design

### Entity Relationship Diagram

```
+-------------+       +---------------+       +--------------+
|   users     |       |  voiceprints  |       |  challenges  |
+-------------+       +---------------+       +--------------+
| id (PK)     |<----->| id (PK)       |       | id (PK)      |
| name        |   1:1 | user_id (FK)  |<------| user_id (FK) |
| email       |       | embedding[]   |   1:N | phrase       |
| created_at  |       | sample_count  |       | token        |
+-------------+       | updated_at    |       | expires_at   |
      ^               +---------------+       | used         |
      |                                       +--------------+
      |                                              |
      |       +---------------+                      |
      +------>|  auth_logs    |<---------------------+
          1:N +---------------+
              | id (PK)       |
              | user_id (FK)  |
              | challenge_id  |
              | l2_label      |
              | l2_confidence |
              | l1_score      |
              | result        |
              | layer_blocked |
              | created_at    |
              +---------------+
```

### Schema Definition

See [docs/DB_SCHEMA.sql](docs/DB_SCHEMA.sql) for complete schema.

**Key Design Decisions:**

1. **UUID Primary Keys:** Prevent enumeration attacks
2. **One-to-One Voiceprint:** Each user has exactly one voiceprint record
3. **Embedding Storage:** PostgreSQL FLOAT8[] array (192 elements)
4. **Audit Trail:** All authentication attempts logged with layer details

---

## API Architecture

### Request/Response Flow

```
Client Request
       |
       v
+------------------+
| CORS Middleware  |
| (origin check)   |
+--------+---------+
         |
         v
+------------------+
| FastAPI Router   |
| (path matching)  |
+--------+---------+
         |
         v
+------------------+
| Pydantic         |
| Validation       |
+--------+---------+
         |
         v
+------------------+
| Route Handler    |
| (business logic) |
+--------+---------+
         |
         v
+------------------+
| Database Session |
| (SQLAlchemy)     |
+--------+---------+
         |
         v
   JSON Response
```

### Error Handling

| HTTP Code | Meaning | Example |
|-----------|---------|---------|
| 200 | Success | Authentication result (ACCEPT or REJECT) |
| 400 | Bad Request | Email already registered |
| 404 | Not Found | User not found |
| 422 | Validation Error | Missing required field |
| 500 | Server Error | Model loading failure |

---

## Security Model

### Threat Matrix

| Attack Vector | Mitigation | Layer |
|--------------|------------|-------|
| AI Voice Cloning | Wav2Vec2 deepfake detector | L2 |
| Voice Conversion | Wav2Vec2 deepfake detector | L2 |
| Replay Attack (recording) | Single-use HMAC tokens | L3 |
| Replay Attack (wrong phrase) | ASR phrase verification | ASR |
| Impersonation | Speaker embedding comparison | L1 |
| Token Forgery | HMAC-SHA256 signature | L3 |
| Brute Force | 90-second token expiration | L3 |
| Voiceprint Poisoning | EMA with low alpha (0.2) | L3 |

### Cryptographic Primitives

- **Token Signing:** HMAC-SHA256
- **Token Format:** Hex-encoded 64-character string
- **Secret Management:** Environment variables (never committed)

---

## Performance Considerations

### Model Loading

```python
# Lazy loading pattern to avoid startup delay
_DEEPFAKE_MODEL = None

def get_deepfake_model():
    global _DEEPFAKE_MODEL
    if _DEEPFAKE_MODEL is None:
        _DEEPFAKE_MODEL = load_model()
    return _DEEPFAKE_MODEL
```

### Database Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

### Audio Processing Optimization

- Resample to 16kHz once at entry point
- Reuse normalized audio across all layers
- Process in memory (no temp files for main path)

---

## Scalability

### Current Capacity

- Single server: ~100 concurrent users
- Database: PostgreSQL handles thousands of RPS
- Bottleneck: Model inference (CPU-bound)

### Scaling Strategies

1. **Vertical:** GPU acceleration for model inference (5-10x speedup)
2. **Horizontal:** Load balancer with multiple backend instances
3. **Caching:** Redis for challenge tokens (faster than PostgreSQL)
4. **Model Optimization:** INT8 quantization (4x memory reduction)

### Future Architecture

```
                    +------------------+
                    | Load Balancer    |
                    | (nginx/HAProxy)  |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
+----------------+  +----------------+  +----------------+
| Backend Pod 1  |  | Backend Pod 2  |  | Backend Pod N  |
| (Gunicorn)     |  | (Gunicorn)     |  | (Gunicorn)     |
+-------+--------+  +-------+--------+  +-------+--------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                 +----------+-----------+
                 |                      |
                 v                      v
        +----------------+     +----------------+
        | PostgreSQL     |     | Redis          |
        | (Primary)      |     | (Cache)        |
        +----------------+     +----------------+
```

---

## References

- [ECAPA-TDNN Paper](https://arxiv.org/abs/2005.07143)
- [Wav2Vec 2.0 Paper](https://arxiv.org/abs/2006.11477)
- [Whisper Paper](https://arxiv.org/abs/2212.04356)
- [ASVspoof Challenge](https://www.asvspoof.org/)

---

**Document Version:** 1.1
**Last Updated:** October 2026
