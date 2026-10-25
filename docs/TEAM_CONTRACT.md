# Team Development Contract

Internal documentation defining module ownership, interface contracts, and development workflow.

---

## Table of Contents

- [Team Structure](#team-structure)
- [Module Ownership](#module-ownership)
- [Interface Contracts](#interface-contracts)
- [Audio Specification](#audio-specification)
- [Database Schema](#database-schema)
- [API Contract](#api-contract)
- [ML Models](#ml-models)
- [Development Phases](#development-phases)

---

## Team Structure

| Member | Role | Responsibility |
|--------|------|----------------|
| Navadeep | Lead Developer | Infrastructure, Backend orchestration, API routing |
| Surya | ML Engineer | Layer 1 - Speaker Verification (ECAPA-TDNN) |
| Nandan | ML Engineer | Layer 2 - Deepfake Detection (Wav2Vec2) |
| Aditya | Full Stack | Layer 3 - Challenge-Response, EMA, Frontend |

---

## Module Ownership

### Backend Files

| File | Owner | Purpose |
|------|-------|---------|
| `main.py` | Navadeep | API routes, pipeline orchestration |
| `db.py` | Navadeep | Database engine configuration |
| `models.py` | Navadeep | SQLAlchemy ORM models |
| `layer1_speaker.py` | Surya | Speaker embedding extraction and verification |
| `layer2_deepfake.py` | Nandan | Deepfake/spoof detection |
| `layer3_adaptive.py` | Aditya | Challenge generation, token validation, EMA |
| `layer3_asr.py` | Aditya | ASR phrase verification |

### Frontend Files

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `frontend/src/components/` | Aditya | React page components |
| `frontend/src/api.js` | Aditya | Backend API client |

### Integration Rule

Only `main.py` imports from the layer modules. Direct cross-module imports are prohibited to prevent merge conflicts and maintain clear interfaces.

---

## Interface Contracts

### Layer 1: Speaker Verification

**File:** `backend/app/layer1_speaker.py`
**Owner:** Surya

```python
def enroll_speaker(audio_bytes: bytes) -> dict:
    """
    Extract speaker embedding from audio.

    Args:
        audio_bytes: Raw WAV audio data (16kHz mono)

    Returns:
        {"embedding": list[float]}  # 192-dimensional vector
    """

def verify_speaker(audio_bytes: bytes, stored_embedding: list[float]) -> dict:
    """
    Compare audio against stored voiceprint.

    Args:
        audio_bytes: Raw WAV audio data
        stored_embedding: 192-dim embedding from enrollment

    Returns:
        {
            "score": float,      # Cosine similarity [0, 1]
            "embedding": list    # Current embedding for EMA update
        }
    """
```

### Layer 2: Deepfake Detection

**File:** `backend/app/layer2_deepfake.py`
**Owner:** Nandan

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

### Layer 3: Challenge-Response

**File:** `backend/app/layer3_adaptive.py`
**Owner:** Aditya

```python
def generate_challenge(user_id: str) -> dict:
    """
    Generate random challenge phrase with signed token.

    Args:
        user_id: UUID of the user

    Returns:
        {
            "phrase": str,       # Random 4-word phrase
            "token": str,        # HMAC-SHA256 signed token
            "expires_at": datetime  # 90 seconds from now
        }
    """

def verify_token(token: str) -> bool:
    """
    Validate challenge token.

    Checks:
        - Token exists in database
        - Token not expired (90s TTL)
        - Token not already used

    Returns:
        True if valid, False otherwise
    """

def update_voiceprint(
    old_embedding: list[float],
    new_embedding: list[float],
    alpha: float = 0.2
) -> list[float]:
    """
    Update voiceprint using Exponential Moving Average.

    Formula: new = (1-alpha) * old + alpha * current
           = 0.8 * old + 0.2 * current

    Returns:
        Updated 192-dimensional embedding
    """
```

---

## Audio Specification

| Property | Requirement |
|----------|-------------|
| Format | WAV |
| Sample Rate | 16kHz |
| Channels | Mono |
| Bit Depth | 16-bit PCM |
| Enrollment Duration | Minimum 3 seconds |
| Verification Duration | Minimum 2 seconds |
| Upload Method | multipart/form-data |

Audio is automatically resampled and converted to mono if necessary.

---

## Database Schema

Reference: [DB_SCHEMA.sql](DB_SCHEMA.sql)

### Tables

**users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

**voiceprints**
```sql
CREATE TABLE voiceprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    embedding FLOAT8[192] NOT NULL,
    sample_count INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id)
);
```

**challenges**
```sql
CREATE TABLE challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);
```

**auth_logs**
```sql
CREATE TABLE auth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID REFERENCES challenges(id) ON DELETE SET NULL,
    l2_label TEXT,
    l2_confidence FLOAT,
    l1_score FLOAT,
    result TEXT NOT NULL,
    layer_blocked INT,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## API Contract

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/auth/register` | POST | `{name, email}` | `{user_id}` |
| `/auth/enroll` | POST | `user_id` + audio | `{status, sample_count}` |
| `/auth/challenge` | GET | `?user_id=<uuid>` | `{phrase, token, expires_at}` |
| `/auth/verify` | POST | `user_id, token` + audio | See below |
| `/users/{id}/voiceprint-history` | GET | - | `[{updated_at, sample_count}]` |
| `/users/{id}/auth-logs` | GET | - | `[{id, result, ...}]` |

### Verify Response Schema

```json
{
    "result": "ACCEPT | REJECT",
    "confidence": 0.0,
    "layer_blocked": null | 1 | 2 | 3 | 4,
    "session_id": "uuid",
    "reason": "string",
    "l2_label": "bonafide | spoof",
    "l2_confidence": 0.0,
    "l1_score": 0.0,
    "asr_transcript": "string",
    "asr_similarity": 0.0
}
```

---

## ML Models

### Layer 1: Speaker Verification

| Property | Value |
|----------|-------|
| Model | `speechbrain/spkrec-ecapa-voxceleb` |
| Architecture | ECAPA-TDNN |
| Embedding Dimension | 192 |
| Training Data | VoxCeleb |

### Layer 2: Deepfake Detection

| Property | Value |
|----------|-------|
| Model | `garystafford/wav2vec2-deepfake-voice-detector` |
| Architecture | Wav2Vec2 + Classification Head |
| Training Data | ASVspoof 2019 LA |
| Output Classes | bonafide, spoof |

### ASR: Phrase Verification

| Property | Value |
|----------|-------|
| Model | OpenAI Whisper (base) |
| Parameters | 74M |
| Languages | English (primary) |

---

## Development Phases

### Phase 0: Setup
- Contract agreement
- Repository structure
- Database provisioning
- Environment configuration

### Phase 1: Independent Development
- Build modules against mocked interfaces
- Unit testing with synthetic data
- No cross-team dependencies

### Phase 2: Integration
- Merge all modules
- Wire real function calls
- End-to-end testing
- Bug resolution

### Phase 3: Enhancement
- Performance optimization
- Threshold tuning
- Documentation
- Production deployment

---

**Contract Version:** 1.0
**Effective Date:** October 2024
