# Surya — Day 1 Repository Audit

**Audit Date:** November 11, 2026
**Repository:** AAA_Baselines
**Branch:** `feat/surya-aaa-core` (created from `main` @ `568370b`)
**Auditor:** Surya (Project Lead — AAA Core)

---

## 1. Repository Structure

```
AAA_Baselines/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application (490 lines)
│   │   ├── db.py                # Database configuration (35 lines)
│   │   ├── models.py            # SQLAlchemy ORM models (105 lines)
│   │   ├── layer1_speaker.py    # Speaker verification - ECAPA-TDNN (124 lines)
│   │   ├── layer2_deepfake.py   # Deepfake detection - Wav2Vec2 (105 lines)
│   │   ├── layer3_adaptive.py   # Challenge-response + EMA (172 lines)
│   │   ├── layer3_asr.py        # ASR phrase verification - Whisper (168 lines)
│   │   └── test_layer3.py       # Layer 3 unit tests
│   ├── pretrained_models/       # Local model cache
│   ├── test_audio/              # Test audio samples
│   ├── requirements.txt         # Python dependencies (17 packages)
│   ├── test_layer1.py           # Layer 1 test script
│   ├── test_layer2.py           # Layer 2 test script
│   ├── Dockerfile
│   ├── .env                     # Local environment (not committed)
│   └── .env.example             # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/          # React pages
│   │   ├── utils/               # Audio encoder utility
│   │   ├── App.jsx              # Main React app
│   │   ├── api.js               # Backend API client (120 lines)
│   │   └── index.css            # Styles
│   ├── package.json             # Node dependencies
│   └── index.html
├── docs/
│   ├── DB_SCHEMA.sql            # Database schema definition
│   └── TEAM_CONTRACT.md         # Team working agreement
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── docker-compose.yml           # Multi-service configuration
├── Dockerfile                   # Root Dockerfile
├── render.yaml                  # Render deployment config
├── README.md                    # Project documentation (510 lines)
├── ARCHITECTURE.md              # Architecture documentation (686 lines)
├── INSTALLATION.md              # Installation guide (530 lines)
├── CONTRIBUTING.md              # Contribution guidelines (480 lines)
├── SECURITY.md                  # Security policy (155 lines)
├── CHANGELOG.md                 # Version history (120 lines)
├── DEMO.md                      # Demo instructions (480 lines)
└── LICENSE                      # MIT License
```

---

## 2. Existing Architecture

### Application Entry Point

**File:** `backend/app/main.py`

- FastAPI application with CORS middleware
- Direct model imports at module level
- Database tables auto-created on startup via `Base.metadata.create_all()`
- Serves both API and static frontend files

### Existing API Routes

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/` | GET | Basic health check | Working |
| `/users` | GET | List all registered users | Working |
| `/auth/register` | POST | Register new user | Working |
| `/auth/enroll` | POST | Enroll voice sample | Working |
| `/auth/challenge` | GET | Generate challenge | Working |
| `/auth/verify` | POST | Verify authentication | Working |
| `/users/{id}/voiceprint-history` | GET | Get voiceprint history | Working |
| `/users/{id}/auth-logs` | GET | Get auth logs | Working |
| `/{full_path:path}` | GET | Frontend catch-all | Working |

**Note:** All routes are under legacy paths (`/auth/*`), not versioned (`/v1/*`).

### Processing Pipeline

```
1. L2: Deepfake Detection (Wav2Vec2)
   └── Reject if spoof confidence > 0.5
         │
2. L3A: ASR Phrase Verification (Whisper)
   └── Reject if similarity < 0.6
         │
3. L1: Speaker Verification (ECAPA-TDNN)
   └── Reject if score < 0.5
         │
4. L3B: Token Verification
   └── Reject if invalid/expired/used
         │
5. Success: EMA Voiceprint Update
```

---

## 3. Database Implementation

### ORM Configuration

**File:** `backend/app/db.py`

- SQLAlchemy 2.0 with sessionmaker
- Supports both SQLite (development) and PostgreSQL (production)
- Connection URL from `DATABASE_URL` environment variable
- Default: `sqlite:///./aaa_engine.db`

### Tables (from `models.py`)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User accounts | id, name, email, created_at |
| `voiceprints` | Voice embeddings | id, user_id, embedding (JSON), sample_count |
| `challenges` | Auth challenges | id, user_id, phrase, token, expires_at, used |
| `auth_logs` | Audit trail | id, user_id, l2_*, l1_*, result, layer_blocked |

### Cross-Database Compatibility

- `GUID` type decorator handles UUID across SQLite/PostgreSQL
- `JSONEncodedList` stores embeddings as JSON text

---

## 4. Security Implementation

### Current Security Controls

| Control | Implementation | Status |
|---------|----------------|--------|
| Token Signing | HMAC-SHA256 | ✅ Implemented |
| Token TTL | 90 seconds | ✅ Implemented |
| Single-Use Tokens | In-memory tracking | ⚠️ Not persistent |
| EMA Protection | α=0.2 | ✅ Implemented |
| CORS | Whitelist with wildcards | ⚠️ Too permissive |

### Confirmed Security Issues

#### CRITICAL: In-Memory Token Store

**File:** `backend/app/layer3_adaptive.py:32`

```python
_token_store: dict[str, dict] = {}
```

**Impact:**
- Tokens lost on server restart
- Cannot scale horizontally
- Memory leak without cleanup

#### CRITICAL: Fallback Secret Key

**File:** `backend/app/layer3_adaptive.py:16`

```python
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026").encode()
```

**Impact:**
- Hardcoded fallback secret is predictable
- Production deployments may accidentally use insecure default

#### HIGH: Wildcard CORS Origins

**File:** `backend/app/main.py:43-44`

```python
"https://*.onrender.com",
"https://*.hf.space"
```

**Impact:**
- Any subdomain on these hosts can access the API
- Cross-tenant attacks possible

#### HIGH: Hardcoded Thresholds

**File:** `backend/app/main.py:57-59`

```python
L2_SPOOF_THRESHOLD = 0.5
L1_SIMILARITY_THRESHOLD = 0.50
ASR_PHRASE_THRESHOLD = 0.6
```

**Impact:**
- Cannot tune security without code deployment
- No environment-based configuration

#### MEDIUM: Raw Score Exposure

**File:** `backend/app/main.py:84-95`

```python
class VerifyResponse(BaseModel):
    l2_label: str
    l2_confidence: float
    l1_score: float
```

**Impact:**
- Internal model scores exposed to clients
- Could aid adversarial attacks

---

## 5. Model Adapters

### Current Implementation

Models are **directly imported** at module level, not abstracted through interfaces.

| Component | File | Model | Loading |
|-----------|------|-------|---------|
| Speaker Verification | `layer1_speaker.py` | ECAPA-TDNN | Module-level |
| Deepfake Detection | `layer2_deepfake.py` | Wav2Vec2 | Lazy (function) |
| ASR | `layer3_asr.py` | Whisper | Lazy (function) |

### No Provider Abstraction

- Models are hardcoded, not interchangeable
- No health/version reporting
- No timeout configuration
- No mock/stub support

---

## 6. Docker Configuration

### docker-compose.yml

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
```

### Dockerfile (backend)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Issues:**
- No health checks
- No multi-stage build
- No non-root user

---

## 7. Test Infrastructure

### Existing Tests

| File | Type | Status |
|------|------|--------|
| `backend/app/test_layer3.py` | Unit tests | Present |
| `backend/test_layer1.py` | Manual test | Requires audio |
| `backend/test_layer2.py` | Manual test | Generates synthetic audio |

### Missing

- pytest configuration
- CI integration
- Integration tests
- API contract tests

---

## 8. Confirmed Problems

| ID | Severity | Description | Location |
|----|----------|-------------|----------|
| SEC-001 | CRITICAL | In-memory token storage | `layer3_adaptive.py:32` |
| SEC-002 | CRITICAL | Fallback secret key | `layer3_adaptive.py:16` |
| SEC-003 | HIGH | Wildcard CORS patterns | `main.py:43-44` |
| SEC-004 | HIGH | Hardcoded thresholds | `main.py:57-59` |
| SEC-005 | MEDIUM | Raw model scores exposed | `main.py:84-95` |
| ARCH-001 | HIGH | No API versioning | `main.py` |
| ARCH-002 | HIGH | No health/readiness endpoints | `main.py` |
| ARCH-003 | MEDIUM | No rate limiting | `main.py` |
| ARCH-004 | MEDIUM | No structured logging | Throughout |
| ARCH-005 | MEDIUM | No model adapter abstraction | `layer*.py` |
| TEST-001 | HIGH | No automated test suite | - |
| TEST-002 | HIGH | No CI/CD pipeline | `.github/` |

---

## 9. Reusable Existing Components

### REUSE AS-IS

| Component | File | Quality | Notes |
|-----------|------|---------|-------|
| Speaker Verification | `layer1_speaker.py` | Excellent | Clean ECAPA-TDNN implementation |
| Deepfake Detection | `layer2_deepfake.py` | Good | Working Wav2Vec2 with known limitations |
| ASR Verification | `layer3_asr.py` | Excellent | Robust Whisper with normalization |
| ORM Models | `models.py` | Excellent | Cross-database compatible |
| Database Config | `db.py` | Good | Simple, effective |
| Frontend API Client | `api.js` | Good | Complete endpoint coverage |
| EMA Algorithm | `layer3_adaptive.py:141-171` | Excellent | Mathematically correct |

### REPAIR

| Component | File | Issue | Effort |
|-----------|------|-------|--------|
| Token Service | `layer3_adaptive.py` | Persistence + secret | 6h |
| Main API | `main.py` | Config + security | 4h |
| CORS Config | `main.py` | Restrict origins | 15min |

---

## 10. Files Requiring Modification

| File | Modification Type | Priority |
|------|-------------------|----------|
| `main.py` | Add versioned routes, health, rate limiting | HIGH |
| `layer3_adaptive.py` | Remove fallback secret, add persistence | CRITICAL |
| `db.py` | Add connection pooling | MEDIUM |
| `models.py` | Add indexes, cascade rules | MEDIUM |

---

## 11. Files That Must Remain Untouched

| File | Owner | Reason |
|------|-------|--------|
| `layer1_speaker.py` | Navadeep (SV) | Model-specific implementation |
| `layer2_deepfake.py` | Aditya (AD) | Model-specific implementation |
| `layer3_asr.py` | Nandan (ASR) | Model-specific implementation |

**Note:** These files may be wrapped by adapters but should not be directly modified by AAA Core work.

---

## 12. Day-2 Implementation Dependencies

| Dependency | Owner | Required For | Blocking |
|------------|-------|--------------|----------|
| SV inference interface | Navadeep | Adapter implementation | Yes |
| AD output contract | Aditya | Adapter implementation | Yes |
| ASR response schema | Nandan | Adapter implementation | Yes |
| Tenant auth contract | Karthik | Security implementation | Yes |
| PostgreSQL credentials | Infrastructure | Persistence testing | No |

---

## Appendix: Git Status

```
Branch: feat/surya-aaa-core
Base: main @ 568370b
Working tree: Clean
Upstream: Not yet pushed
```

---

**Document Version:** 1.0
**Classification:** Internal Technical Documentation
