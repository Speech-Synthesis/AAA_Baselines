# Architecture Documentation

Technical deep dive into AAA Engine's system architecture, data flow, and implementation details.

## Table of Contents
- [System Overview](#system-overview)
- [Authentication Pipeline](#authentication-pipeline)
- [Layer Details](#layer-details)
- [Database Design](#database-design)
- [API Architecture](#api-architecture)
- [Security Model](#security-model)
- [Performance Optimization](#performance-optimization)

---

## System Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                          │
│                                                               │
│  ┌────────────────┐         ┌────────────────┐              │
│  │  React Frontend │◄──────►│  Microphone    │              │
│  │  (Port 5173)    │         │  Input         │              │
│  └────────┬───────┘         └────────────────┘              │
│           │ HTTP/HTTPS                                        │
└───────────┼──────────────────────────────────────────────────┘
            │
            │ REST API (FormData multipart/form-data)
            │
┌───────────▼──────────────────────────────────────────────────┐
│                       API LAYER (FastAPI)                     │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Register │  │  Enroll  │  │ Challenge│  │  Verify  │    │
│  │  /auth/  │  │  /auth/  │  │  /auth/  │  │  /auth/  │    │
│  │ register │  │ enroll   │  │ challenge│  │  verify  │    │
│  └──────────┘  └────┬─────┘  └─────┬────┘  └────┬─────┘    │
│                      │              │             │           │
└──────────────────────┼──────────────┼─────────────┼──────────┘
                       │              │             │
                       ▼              ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                           │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Layer 2   │  │   Layer ASR │  │   Layer 1   │          │
│  │  Deepfake   │  │   Phrase    │  │   Speaker   │          │
│  │  Detection  │  │   Verify    │  │  Embeddings │          │
│  │  (Wav2Vec2) │  │  (Whisper)  │  │  (ECAPA)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│  ┌─────────────┐                                             │
│  │   Layer 3   │                                             │
│  │  Challenge  │                                             │
│  │  + EMA      │                                             │
│  │  (HMAC)     │                                             │
│  └─────────────┘                                             │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                          │
│                                                               │
│  ┌─────────┐  ┌─────────────┐  ┌───────────┐  ┌──────────┐ │
│  │  Users  │  │ Voiceprints │  │ Challenges│  │ AuthLogs │ │
│  └─────────┘  └─────────────┘  └───────────┘  └──────────┘ │
│                                                               │
│            PostgreSQL Database (Supabase)                     │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | React | 18.x | User interface |
| Build Tool | Vite | 5.x | Frontend bundling |
| HTTP Client | Axios | 1.x | API communication |
| Backend | FastAPI | 0.104.x | REST API framework |
| ORM | SQLAlchemy | 2.x | Database abstraction |
| Database | PostgreSQL | 15.x | Data persistence |
| L1 Model | ECAPA-TDNN | speechbrain | Speaker embeddings |
| L2 Model | Wav2Vec2 | transformers | Deepfake detection |
| ASR Model | Whisper | openai-whisper | Speech-to-text |
| Audio | soundfile | 0.12.x | Audio I/O |
| Deployment | Fly.io | - | Container hosting |

---

## Authentication Pipeline

### Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  ENROLLMENT PHASE                             │
│                                                               │
│  User ──► Record Voice (3+ samples)                          │
│              │                                                │
│              ▼                                                │
│         L1: Extract ECAPA Embedding (192-dim)                │
│              │                                                │
│              ▼                                                │
│         Store/Update Voiceprint (EMA if existing)            │
│              │                                                │
│              ▼                                                │
│         Sample Count += 1                                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│               VERIFICATION PHASE                              │
│                                                               │
│  Step 1: GET /auth/challenge?user_id=<uuid>                  │
│          ├─► Generate random phrase                          │
│          ├─► Create HMAC token (90s TTL)                     │
│          └─► Store in challenges table                       │
│                                                               │
│  Step 2: User records audio speaking phrase                  │
│                                                               │
│  Step 3: POST /auth/verify                                   │
│          user_id + token + audio.wav                         │
│              │                                                │
│              ▼                                                │
│         ┌─────────────────┐                                  │
│         │  L2: Deepfake   │  Wav2Vec2 inference              │
│         │  Detection      │  ➜ bonafide/spoof                │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ├─► if spoof confidence > 0.5:              │
│                  │   REJECT (layer_blocked=2)                │
│                  │                                            │
│                  ▼                                            │
│         ┌─────────────────┐                                  │
│         │  ASR: Phrase    │  Whisper transcription           │
│         │  Verification   │  ➜ compare vs expected          │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ├─► if similarity < 0.6:                    │
│                  │   REJECT (layer_blocked=4)                │
│                  │                                            │
│                  ▼                                            │
│         ┌─────────────────┐                                  │
│         │  L1: Speaker    │  ECAPA embedding extraction      │
│         │  Verification   │  ➜ cosine similarity            │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ├─► if similarity < 0.50:                   │
│                  │   REJECT (layer_blocked=1)                │
│                  │                                            │
│                  ▼                                            │
│         ┌─────────────────┐                                  │
│         │  L3: Token      │  HMAC validation                 │
│         │  Validation     │  ➜ check expiry, usage          │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ├─► if invalid/expired:                     │
│                  │   REJECT (layer_blocked=3)                │
│                  │                                            │
│                  ▼                                            │
│         ✅ ACCEPT                                             │
│         ├─► Update voiceprint (EMA: 0.8*old + 0.2*new)      │
│         ├─► Mark token as used                               │
│         ├─► Log success in auth_logs                         │
│         └─► Return session_id + metrics                      │
└──────────────────────────────────────────────────────────────┘
```

### Sequential Layer Execution

**Key Design Decision**: Layers execute sequentially, not in parallel.

**Rationale**:
1. **Early Rejection**: Stop processing if deepfake detected (saves compute)
2. **Attack Surface**: Don't leak speaker info if deepfake suspected
3. **Cost Optimization**: L2 (420ms) cheaper than L1 (290ms) + L2 combined

**Execution Order**:
```python
# backend/app/main.py:227-405

# 1. L2: Deepfake Detection (cheapest to run first)
l2_result = detect_spoof(audio_bytes)
if l2_result["label"] == "spoof" and l2_result["confidence"] > 0.5:
    return REJECT(layer_blocked=2)

# 2. ASR: Phrase Verification (before revealing speaker identity)
asr_match, similarity, transcript = verify_phrase(audio_bytes, expected_phrase)
if not asr_match:
    return REJECT(layer_blocked=4)

# 3. L1: Speaker Verification (most expensive, run if L2 passes)
l1_result = verify_speaker(audio_bytes, voiceprint.embedding)
if l1_result["score"] < 0.50:
    return REJECT(layer_blocked=1)

# 4. L3: Token Validation (final check)
if not verify_token(token):
    return REJECT(layer_blocked=3)

# All layers passed → ACCEPT
```

---

## Layer Details

### Layer 2: Deepfake Detection

**File**: `backend/app/layer2_deepfake.py:1-52`

**Model**: `garystafford/wav2vec2-deepfake-voice-detector`

**Implementation**:
```python
from transformers import AutoModelForAudioClassification, Wav2Vec2Processor
import torch

# Load model (cached after first run)
model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)

def detect_spoof(audio_bytes: bytes) -> dict:
    """
    Classify audio as bonafide (real) or spoof (fake).

    Returns:
        {
            "label": "bonafide" | "spoof",
            "confidence": float  # Probability of predicted label
        }
    """
    # Load audio (auto-resample to 16kHz)
    audio, sr = sf.read(io.BytesIO(audio_bytes))
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

    # Preprocess
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")

    # Inference
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]

    # Map output (0: real, 1: fake)
    predicted_id = probs.argmax().item()
    label_map = {0: "bonafide", 1: "spoof"}

    return {
        "label": label_map[predicted_id],
        "confidence": probs[predicted_id].item()
    }
```

**Training Data**: ASVspoof 2019 LA (Logical Access) dataset
- **Bonafide**: Real human speech
- **Spoof**: TTS-generated, voice-converted, replay attacks

**Limitations**:
- Trained on 2019 TTS systems (pre-GPT era)
- May not detect modern systems (ElevenLabs, Vall-E, XTTS)
- Adversarial examples possible

**Threshold**: 0.5 (chosen via ROC curve on validation set)

---

### Layer ASR: Phrase Verification

**File**: `backend/app/layer3_asr.py:1-65`

**Model**: OpenAI Whisper (base)

**Implementation**:
```python
import whisper
from difflib import SequenceMatcher

# Load Whisper model
model = whisper.load_model("base")

def verify_phrase(audio_bytes: bytes, expected_phrase: str, threshold: float) -> tuple:
    """
    Transcribe audio and compare to expected phrase.

    Returns:
        (match: bool, similarity: float, transcript: str)
    """
    # Save audio temporarily (Whisper needs file path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # Transcribe
    result = model.transcribe(tmp_path)
    transcript = result["text"].strip().lower()

    # Cleanup
    os.unlink(tmp_path)

    # Compare using Levenshtein similarity
    expected_clean = expected_phrase.strip().lower()
    similarity = SequenceMatcher(None, expected_clean, transcript).ratio()

    return (similarity >= threshold, similarity, transcript)
```

**Threshold**: 0.6 (allows minor transcription errors like "the" vs "a")

**Purpose**: Prevents replay attacks where attacker uses recorded audio of different phrase

---

### Layer 1: Speaker Verification

**File**: `backend/app/layer1_speaker.py:1-78`

**Model**: `speechbrain/spkrec-ecapa-voxceleb`

**Implementation**:
```python
from speechbrain.pretrained import EncoderClassifier
import torch

# Load ECAPA-TDNN model
classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

def enroll_speaker(audio_bytes: bytes) -> dict:
    """
    Extract speaker embedding from audio.

    Returns:
        {"embedding": list[float]}  # 192-dimensional
    """
    # Load audio
    audio, sr = sf.read(io.BytesIO(audio_bytes))
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

    # Extract embedding
    signal = torch.tensor(audio).unsqueeze(0)
    with torch.no_grad():
        embedding = classifier.encode_batch(signal)

    return {"embedding": embedding.squeeze(0).tolist()}


def verify_speaker(audio_bytes: bytes, enrolled_embedding: list[float]) -> dict:
    """
    Compare current audio to enrolled voiceprint.

    Returns:
        {
            "score": float,  # Cosine similarity [0, 1]
            "embedding": list[float]  # For EMA update
        }
    """
    # Extract embedding from current audio
    result = enroll_speaker(audio_bytes)
    current_embedding = result["embedding"]

    # Compute cosine similarity
    enrolled_tensor = torch.tensor(enrolled_embedding)
    current_tensor = torch.tensor(current_embedding)

    similarity = torch.nn.functional.cosine_similarity(
        enrolled_tensor.unsqueeze(0),
        current_tensor.unsqueeze(0)
    ).item()

    # Normalize to [0, 1] (cosine similarity is [-1, 1])
    score = (similarity + 1) / 2

    return {"score": score, "embedding": current_embedding}
```

**Embedding Dimension**: 192 (fixed by ECAPA-TDNN architecture)

**Threshold History**:
- Initial: 0.7 (high security, some false rejections)
- Current: 0.50 (balanced based on testing)

---

### Layer 3: Challenge-Response + EMA

**File**: `backend/app/layer3_adaptive.py:1-164`

**Challenge Generation**:
```python
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta

# Word list for phrase generation
WORD_LIST = [
    "apple", "blue", "cloud", "delta", "eagle", "forest",
    "guitar", "house", "island", "jungle", "king", "lion",
    # ... (50 words total)
]

def generate_challenge(user_id: str) -> dict:
    """
    Generate random challenge phrase with HMAC token.

    Returns:
        {
            "phrase": str,  # Random 4-word phrase
            "token": str,   # HMAC-SHA256 signature
            "expires_at": datetime  # Current time + 90s
        }
    """
    # Generate random phrase (4 words)
    phrase_words = secrets.SystemRandom().sample(WORD_LIST, 4)
    phrase = " ".join(phrase_words)

    # Create expiry timestamp
    expires_at = datetime.utcnow() + timedelta(seconds=90)

    # Generate HMAC token
    message = f"{user_id}:{phrase}:{expires_at.isoformat()}"
    secret_key = os.getenv("L3_HMAC_SECRET").encode()
    token = hmac.new(secret_key, message.encode(), hashlib.sha256).hexdigest()

    return {
        "phrase": phrase,
        "token": token,
        "expires_at": expires_at
    }


def verify_token(token: str) -> bool:
    """
    Validate HMAC token (check expiry, single-use).

    Returns:
        bool: True if valid, False otherwise
    """
    # Lookup in database
    challenge = db.query(Challenge).filter(Challenge.token == token).first()

    if not challenge:
        return False  # Token not found

    if challenge.used:
        return False  # Already used (replay attack)

    if datetime.utcnow() > challenge.expires_at:
        return False  # Expired

    return True
```

**EMA Voiceprint Adaptation**:
```python
def update_voiceprint(old_embedding: list[float],
                      new_embedding: list[float],
                      alpha: float = 0.2) -> list[float]:
    """
    Update voiceprint using Exponential Moving Average.

    Args:
        old_embedding: Current stored voiceprint
        new_embedding: New embedding from successful auth
        alpha: Learning rate (0.2 = 20% weight to new sample)

    Returns:
        Updated embedding (192-dim)

    Formula:
        voiceprint_new = (1 - α) * voiceprint_old + α * embedding_new
        voiceprint_new = 0.8 * voiceprint_old + 0.2 * embedding_new

    Rationale:
        - α=0.2 balances adaptability and stability
        - Requires ~10 successful attacks to shift voiceprint 50%
        - Prevents one-shot poisoning attacks
    """
    return [
        (1.0 - alpha) * old + alpha * new
        for old, new in zip(old_embedding, new_embedding)
    ]
```

**Security Properties**:
- **Replay Prevention**: Single-use tokens stored in database
- **Time Constraint**: 90-second window prevents offline attacks
- **Phrase Randomness**: 50^4 = 6.25M possible phrases
- **HMAC Integrity**: SHA-256 prevents token forgery

---

## Database Design

### Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Voiceprints table (one per user)
CREATE TABLE voiceprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    embedding FLOAT8[192] NOT NULL,  -- ECAPA-TDNN output
    sample_count INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)  -- One voiceprint per user
);

-- Challenges table (ephemeral, 90s TTL)
CREATE TABLE challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Auth logs (audit trail)
CREATE TABLE auth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID REFERENCES challenges(id) ON DELETE SET NULL,
    l2_label VARCHAR(20),  -- "bonafide" | "spoof"
    l2_confidence FLOAT,
    l1_score FLOAT,
    result VARCHAR(20),  -- "ACCEPT" | "REJECT"
    layer_blocked INTEGER,  -- 1, 2, 3, 4, or NULL
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_voiceprints_user ON voiceprints(user_id);
CREATE INDEX idx_challenges_token ON challenges(token);
CREATE INDEX idx_challenges_expires ON challenges(expires_at);
CREATE INDEX idx_auth_logs_user ON auth_logs(user_id);
CREATE INDEX idx_auth_logs_created ON auth_logs(created_at DESC);
```

### Data Flow

**Registration**:
```sql
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com')
RETURNING id;
```

**Enrollment** (first sample):
```sql
INSERT INTO voiceprints (user_id, embedding, sample_count)
VALUES ('uuid', [0.1, 0.2, ..., 0.192], 1);
```

**Enrollment** (subsequent samples):
```sql
UPDATE voiceprints
SET embedding = [0.08, 0.16, ..., 0.1536],  -- EMA updated
    sample_count = sample_count + 1,
    updated_at = NOW()
WHERE user_id = 'uuid';
```

**Challenge Generation**:
```sql
INSERT INTO challenges (user_id, phrase, token, expires_at)
VALUES ('uuid', 'blue sky mountain river', 'abc123...', NOW() + INTERVAL '90 seconds');
```

**Verification Success**:
```sql
-- Mark token as used
UPDATE challenges SET used = TRUE WHERE token = 'abc123...';

-- Update voiceprint
UPDATE voiceprints
SET embedding = [EMA updated],
    sample_count = sample_count + 1,
    updated_at = NOW()
WHERE user_id = 'uuid';

-- Log success
INSERT INTO auth_logs (user_id, challenge_id, l2_label, l2_confidence, l1_score, result)
VALUES ('uuid', 'challenge-uuid', 'bonafide', 0.94, 0.87, 'ACCEPT');
```

---

## API Architecture

### Endpoint Documentation

**Base URL**: `http://localhost:8000` (dev), `https://your-domain.com` (prod)

**Auto-Generated Docs**: `http://localhost:8000/docs` (Swagger UI)

### 1. POST /auth/register

**Request**:
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Response** (201 Created):
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Errors**:
- 400: Email already registered

---

### 2. POST /auth/enroll

**Request** (FormData):
```
user_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
audio: <binary WAV file>
```

**Response** (200 OK):
```json
{
  "status": "enrolled",
  "sample_count": 3
}
```

**Errors**:
- 404: User not found
- 400: Invalid audio format

---

### 3. GET /auth/challenge

**Request**:
```
GET /auth/challenge?user_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response** (200 OK):
```json
{
  "phrase": "blue sky mountain river",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2026-10-25T14:32:45Z"
}
```

**Errors**:
- 404: User not found
- 400: No enrolled voiceprint

---

### 4. POST /auth/verify

**Request** (FormData):
```
user_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
token: "eyJ0eXAiOiJKV1QiLCJhbGc..."
audio: <binary WAV file>
```

**Response** (200 OK - Success):
```json
{
  "result": "ACCEPT",
  "confidence": 0.87,
  "layer_blocked": null,
  "session_id": "c9d8e7f6-a5b4-3210-9876-543210fedcba",
  "reason": "Authentication successful",
  "l2_label": "bonafide",
  "l2_confidence": 0.94,
  "l1_score": 0.87,
  "asr_transcript": "blue sky mountain river",
  "asr_similarity": 0.98
}
```

**Response** (200 OK - Rejection):
```json
{
  "result": "REJECT",
  "confidence": 0.78,
  "layer_blocked": 2,
  "session_id": "b7e1d9f3-...",
  "reason": "Deepfake/spoof detected",
  "l2_label": "spoof",
  "l2_confidence": 0.78,
  "l1_score": 0.0
}
```

**Errors**:
- 404: User not found
- 400: No enrolled voiceprint

---

## Security Model

### Threat Mitigation

| Attack | Mitigation | Layer |
|--------|-----------|-------|
| TTS Deepfake | Wav2Vec2 classifier | L2 |
| Voice Conversion | Wav2Vec2 classifier | L2 |
| Replay Attack | Single-use HMAC tokens (90s TTL) | L3 |
| Wrong Phrase | ASR transcription + Levenshtein | ASR |
| Impersonation | ECAPA speaker embeddings | L1 |
| Token Forgery | HMAC-SHA256 with secret key | L3 |
| Voiceprint Poisoning | EMA α=0.2 (requires ~10 attacks) | L3 |

### Cryptographic Security

**HMAC Token**:
```python
# Generation
secret = os.getenv("L3_HMAC_SECRET")  # 64-char random string
message = f"{user_id}:{phrase}:{expires_at}"
token = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

# Verification
expected_token = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
if not hmac.compare_digest(token, expected_token):
    raise InvalidTokenError
```

**Database Encryption**:
- PostgreSQL TDE (Transparent Data Encryption)
- SSL/TLS for connections (Supabase default)

**Transport Security**:
- HTTPS/TLS 1.3 in production
- CORS restricted to allowed origins

---

## Performance Optimization

### Model Caching

**Problem**: First request loads models from disk (8-12s cold start)

**Solution**: In-memory caching after first load

```python
# Lazy loading pattern
_DEEPFAKE_MODEL = None
_SPEAKER_MODEL = None
_WHISPER_MODEL = None

def get_deepfake_model():
    global _DEEPFAKE_MODEL
    if _DEEPFAKE_MODEL is None:
        _DEEPFAKE_MODEL = AutoModelForAudioClassification.from_pretrained(...)
    return _DEEPFAKE_MODEL
```

### Database Connection Pooling

```python
# backend/app/db.py
engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # Maintain 5 connections
    max_overflow=10,    # Allow 10 additional connections under load
    pool_pre_ping=True  # Check connection health before use
)
```

### Audio Processing

**Optimization**: Auto-resample to 16kHz once, reuse for all layers

```python
# Resample once at entry point
audio, sr = sf.read(io.BytesIO(audio_bytes))
if sr != 16000:
    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

# Reuse for L2, ASR, L1
l2_result = detect_spoof(audio)  # Uses 16kHz audio
l1_result = verify_speaker(audio)  # Reuses same audio
```

---

## Scalability Considerations

### Current Limits
- **Single Server**: 100 concurrent users (tested)
- **Database**: PostgreSQL handles 1000s RPS
- **Bottleneck**: Model inference (GPU would help)

### Future Improvements
- **GPU Inference**: 5-10x speedup for Wav2Vec2, ECAPA
- **Model Quantization**: INT8 reduces memory 4x
- **Load Balancer**: Horizontal scaling with multiple backend instances
- **Redis Cache**: Store challenge tokens in-memory (faster than PostgreSQL)
- **CDN**: Serve frontend from edge (Cloudflare, Fastly)

---

**Architecture Version**: 1.0.0
**Last Updated**: October 2026
**Maintainers**: See [README.md](README.md#team)
