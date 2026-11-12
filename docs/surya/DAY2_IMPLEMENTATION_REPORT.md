# Surya — Day 2 Implementation Report

**Date:** November 12, 2026
**Sprint Day:** 2 of 4
**Branch:** `feat/surya-day2-security`

---

## 1. Executive Summary

Day 2 addressed critical security issues and established infrastructure for reliable production deployment. All planned tasks were completed:

- ✅ PostgreSQL token persistence (replacing in-memory storage)
- ✅ Fallback secret removal (fail-fast configuration)
- ✅ Rate limiting on authentication endpoints
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Mock model adapters for testing
- ✅ Integration tests for token lifecycle

**Tests:** 57 tests passing

---

## 2. Critical Fixes

### 2.1 Token Persistence (SEC-001 - RESOLVED)

**Before:**
```python
_token_store: dict[str, dict] = {}  # In-memory, lost on restart
```

**After:**
- Challenges persisted to PostgreSQL/SQLite `challenges` table
- Added `signature`, `payload`, `created_at` columns to Challenge model
- Atomic token consumption using `UPDATE ... WHERE used = 0`
- Race condition prevention for concurrent verification attempts
- Cleanup function for expired tokens

**New Functions:**
- `generate_challenge(user_id, db)` - Creates and persists challenge
- `verify_token(token, db)` - Atomically validates and consumes
- `validate_and_consume_token(token, db)` - Returns full challenge data
- `cleanup_expired_tokens(db)` - Purges expired challenges

### 2.2 Fallback Secret Removal (SEC-002 - RESOLVED)

**Before:**
```python
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026")
```

**After:**
```python
if not _hmac_secret:
    if DEBUG:
        warnings.warn("Using insecure default for DEBUG mode only")
        _hmac_secret = "INSECURE_DEBUG_SECRET_DO_NOT_USE_IN_PRODUCTION"
    else:
        raise MissingSecretError("L3_HMAC_SECRET")
```

**Behavior:**
- Production: Fails immediately if `L3_HMAC_SECRET` not set
- Development: Warns but allows startup with insecure default
- Test: Uses dedicated test secret via environment variable

---

## 3. Infrastructure

### 3.1 Rate Limiting

**Implementation:** SlowAPI middleware with custom error handler

**Configuration (via environment):**
```python
RATE_LIMIT_CHALLENGES: str = "10/minute"
RATE_LIMIT_VERIFY: str = "5/minute"
RATE_LIMIT_ENROLL: str = "3/5minutes"
```

**Protected Endpoints:**
- `GET /auth/challenge` - 10 requests/minute
- `POST /auth/verify` - 5 requests/minute
- `POST /auth/enroll` - 3 requests/5 minutes

**Error Response (HTTP 429):**
```json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded: 10 per 1 minute",
    "retry_after": 60
}
```

### 3.2 CI/CD Pipeline

**File:** `.github/workflows/test.yml`

**Jobs:**
1. **test** - Runs pytest against SQLite and PostgreSQL
2. **lint** - Runs ruff linter
3. **security** - Runs bandit security scanner
4. **docker** - Validates Docker build

**Triggers:**
- Push to `main` or `feat/*` branches
- Pull requests to `main`

### 3.3 Configuration Improvements

**File:** `backend/app/core/config.py`

**Changes:**
- Added `extra = "ignore"` to Settings to allow unknown env vars
- Fixed pydantic-settings compatibility

**File:** `backend/pyproject.toml`

**Added:**
- ruff configuration for linting
- pytest configuration

---

## 4. Model Adapters

### 4.1 Architecture

```
backend/app/adapters/
├── __init__.py       # Exports
├── base.py           # Abstract interfaces
├── sv.py             # ECAPA-TDNN speaker verification
├── ad.py             # Wav2Vec2 deepfake detection
├── asr.py            # Whisper ASR
└── mock.py           # Mock implementations for testing
```

### 4.2 Base Interfaces

```python
class SpeakerVerificationAdapter(ModelAdapter):
    def extract_embedding(self, audio_bytes) -> SpeakerResult
    def compare_embeddings(self, e1, e2) -> float
    def verify_speaker(self, audio, enrolled, threshold) -> SpeakerResult

class DeepfakeDetectionAdapter(ModelAdapter):
    def detect(self, audio_bytes) -> DeepfakeResult
    def is_spoof(self, audio_bytes, threshold) -> bool

class ASRAdapter(ModelAdapter):
    def transcribe(self, audio_bytes) -> ASRResult
    def compare_phrases(self, transcript, expected) -> float
    def verify_phrase(self, audio, expected, threshold) -> ASRResult
```

### 4.3 Mock Adapters

**MockSpeakerAdapter:**
- Configurable default score
- Deterministic embeddings based on input
- `set_score(score)` for test control

**MockDeepfakeAdapter:**
- Configurable label and confidence
- `set_result(label, confidence)` for test control

**MockASRAdapter:**
- Configurable transcript and similarity
- `set_transcript(text)` and `set_similarity(score)` for test control

---

## 5. Test Coverage

### 5.1 Tests Added

| File | Tests | Purpose |
|------|-------|---------|
| `test_token_persistence.py` | 17 | Challenge lifecycle, replay prevention |
| `test_adapters.py` | 17 | Mock adapter functionality |
| `test_day1_foundation.py` | 23 | Updated for db-backed tokens |

### 5.2 Test Categories

**Token Persistence:**
- Challenge generation with/without DB
- Unique phrase generation
- 90-second TTL verification
- Token single-use enforcement
- Replay prevention
- Expired token rejection
- Cleanup functionality

**Secret Configuration:**
- Production mode fails without secret
- Debug mode warns but continues

**Mock Adapters:**
- Interface compliance
- Configurable behavior
- Deterministic output

### 5.3 Test Execution

```bash
cd backend
pytest tests/ -v

# Result: 57 passed
```

---

## 6. Files Changed

### New Files

```
backend/app/adapters/
├── __init__.py
├── base.py
├── sv.py
├── ad.py
├── asr.py
└── mock.py

backend/app/core/
└── ratelimit.py

backend/tests/
├── test_token_persistence.py
└── test_adapters.py

.github/workflows/
└── test.yml

backend/
└── pyproject.toml
```

### Modified Files

```
backend/app/layer3_adaptive.py    # Database persistence, secret validation
backend/app/models.py             # Challenge table columns
backend/app/main.py               # Rate limiting integration
backend/app/core/config.py        # Settings extra=ignore
backend/tests/conftest.py         # Test fixtures
backend/tests/test_day1_foundation.py  # Updated for db tokens
backend/requirements.txt          # Added slowapi
```

---

## 7. Migration Notes

### 7.1 Database Migration Required

The `challenges` table has new columns:
- `signature` (TEXT)
- `payload` (TEXT)
- `created_at` (DATETIME)
- `expires_at` now indexed
- `used` now indexed
- `token` now unique and indexed

**For existing databases, run:**
```sql
ALTER TABLE challenges ADD COLUMN signature TEXT;
ALTER TABLE challenges ADD COLUMN payload TEXT;
ALTER TABLE challenges ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
CREATE UNIQUE INDEX ix_challenges_token ON challenges(token);
CREATE INDEX ix_challenges_expires_at ON challenges(expires_at);
CREATE INDEX ix_challenges_used ON challenges(used);
```

### 7.2 Environment Variables Required

**Production:**
```bash
L3_HMAC_SECRET=<strong-secret-key>  # REQUIRED
DEBUG=false                         # Recommended
DATABASE_URL=postgresql://...       # Recommended
```

**Development:**
```bash
DEBUG=true                          # Allows insecure defaults
```

---

## 8. Day 3 Preview

### Planned Tasks

1. **Voiceprint Encryption** - AES-256-GCM for stored embeddings
2. **CORS Restriction** - Remove wildcard patterns
3. **JWT Host App Authentication** - Validate calling application
4. **Structured Logging** - Replace print statements
5. **API v1 Endpoint Implementation** - Complete `/v1/enroll`, `/v1/verify`

### Pending Team Confirmations

- Navadeep: SV embedding dimension, score semantics
- Aditya: AD confidence interpretation
- Nandan: ASR phrase matching algorithm
- Karthik: JWT public key format

---

## 9. Commands for Verification

```bash
# Run all tests
cd backend
pytest tests/ -v

# Start server
uvicorn app.main:app --reload --port 8000

# Test health
curl http://localhost:8000/v1/health

# Test rate limiting (11th request should fail)
for i in {1..11}; do curl -s http://localhost:8000/auth/challenge?user_id=test; done
```

---

**Document Version:** 1.0
**Completion Time:** November 12, 2026
