# AAA Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://postgresql.org)
[![Tests](https://img.shields.io/badge/Tests-437%20passing-brightgreen.svg)](#testing)

**Adaptive Audio Authentication with Deepfake Detection**

A production-ready voice authentication system combining multiple security layers: deepfake detection (AD), phrase verification (ASR), speaker recognition (SV), vishing risk analysis (VR), and a centralized five-outcome PolicyEngine.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Five-Outcome Policy](#five-outcome-policy)
- [Security Layers](#security-layers)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Host Applications](#host-applications)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

AAA Engine implements a multi-layered voice authentication pipeline designed to protect against modern attack vectors including AI-generated deepfakes, voice cloning, replay attacks, and social engineering (vishing).

### Key Differentiators

- **Parallel Execution:** AD||ASR run concurrently for ~30% faster authentication
- **SV Gating:** Speaker verification only runs after AD+ASR pass (security + cost)
- **Five-Outcome Policy:** Not just accept/reject - includes STEP_UP, REVIEW, UNAVAILABLE
- **Vishing Detection:** 10 risk indicators with hard-negative support
- **Adaptive Voiceprints:** EMA-based evolution (0.8 old + 0.2 new)
- **Tenant Isolation:** Row-Level Security for multi-tenant deployments
- **AES-256-GCM:** Voiceprint encryption at rest

### Authentication Pipeline

```
                           Audio Input
                               |
               +---------------+---------------+
               |                               |
               v                               v
    +-------------------+           +-------------------+
    |   AAA-AD (L2)     |           |   AAA-ASR         |
    |   Deepfake        |  PARALLEL |   Phrase          |
    |   Detection       |           |   Verification    |
    |   (Wav2Vec2)      |           |   (Whisper)       |
    +-------------------+           +-------------------+
               |                               |
               +---------------+---------------+
                               |
                         Both Pass?
                               |
                               v
                    +-------------------+
                    |   AAA-SV (L1)     |
                    |   Speaker         |
                    |   Verification    |
                    |   (ECAPA-TDNN)    |
                    +-------------------+
                               |
                               v
                    +-------------------+
                    |   POLICY ENGINE   |
                    |                   |
                    |   APPROVE         |
                    |   DENY            |
                    |   STEP_UP         |
                    |   REVIEW          |
                    |   UNAVAILABLE     |
                    +-------------------+
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | FastAPI 0.104+ | Async REST API |
| Frontend | React 18 + Vite 5 | User interface |
| Database | PostgreSQL 15 (Supabase) | Data persistence with RLS |
| L1 Model | ECAPA-TDNN (SpeechBrain) | 192-dim speaker embeddings |
| L2 Model | Wav2Vec2 (HuggingFace) | Deepfake detection |
| ASR Model | Whisper (OpenAI) | Speech-to-text |
| VR Engine | Rule-based + Pattern | Vishing risk analysis |
| Encryption | AES-256-GCM | Voiceprint security |

---

## Key Features

### Security

- **Multi-Layer Defense:** AD (deepfake) → ASR (phrase) → SV (speaker) → Policy
- **Fail-Closed Design:** System never fails open
- **Token Security:** HMAC-SHA256 signed, 90s TTL, single-use
- **Voiceprint Protection:** AES-256-GCM encryption with tenant-specific keys
- **Log Redaction:** Automatic PII removal from all logs
- **Tenant Isolation:** PostgreSQL Row-Level Security

### Performance

- **Parallel Execution:** AD||ASR concurrent processing (~1.1s total vs 1.6s sequential)
- **Lazy Model Loading:** Models load on first use, not startup
- **Connection Pooling:** SQLAlchemy pool for database efficiency
- **Rate Limiting:** Built-in protection against abuse

### Operations

- **Health Checks:** `/v1/health` (liveness) and `/v1/ready` (readiness)
- **Model Registry:** Version control and quarantine support
- **Audit Trail:** Complete authentication logging
- **Consent Management:** GDPR-compliant consent tracking

---

## Five-Outcome Policy

The centralized PolicyEngine returns one of five decisions:

| Decision | Description | Frontend Action |
|----------|-------------|-----------------|
| **APPROVE** | All gates passed | Grant access |
| **DENY** | Authentication failed | Block access, show reason |
| **STEP_UP** | Marginal confidence | Request fresh challenge |
| **REVIEW** | Anomaly detected | Queue for human review |
| **UNAVAILABLE** | Service degraded | Show retry message |

### Risk Levels

| Level | Description |
|-------|-------------|
| LOW | Normal authentication |
| MEDIUM | Minor anomalies detected |
| HIGH | Significant concern |
| CRITICAL | Immediate threat (credential harvesting, impersonation) |

---

## Security Layers

### Layer 2: Deepfake Detection (AAA-AD)

| Specification | Value |
|--------------|-------|
| Model | `garystafford/wav2vec2-deepfake-voice-detector` |
| Output | bonafide / spoof with confidence |
| Threshold | 0.5 (configurable) |
| Latency | ~420ms (CPU) |

### ASR: Phrase Verification (AAA-ASR)

| Specification | Value |
|--------------|-------|
| Model | OpenAI Whisper (base) |
| Matcher | Deterministic phrase matching |
| Threshold | 0.6 Levenshtein similarity |
| Latency | ~800ms (CPU) |

### Layer 1: Speaker Verification (AAA-SV)

| Specification | Value |
|--------------|-------|
| Model | `speechbrain/spkrec-ecapa-voxceleb` |
| Output | 192-dim embedding + cosine similarity |
| Threshold | 0.5 (configurable) |
| Latency | ~300ms (CPU) |

### Vishing Risk Analysis (AAA-VR)

10 risk indicators with hard-negative detection:

- OTP_SOLICITATION (CRITICAL)
- CREDENTIAL_HARVESTING_ATTEMPT (CRITICAL)
- PRESSURE_TACTICS_DETECTED (HIGH)
- IMPERSONATION_ATTEMPT (HIGH)
- REMOTE_ACCESS_REQUEST (HIGH)
- EMOTIONAL_MANIPULATION (HIGH)
- FINANCIAL_COERCION (HIGH)
- BYPASS_REQUEST (HIGH)
- URGENT_TRANSFER_REQUEST (MEDIUM)
- ACCOUNT_NUMBER_MENTIONED (MEDIUM)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Speech-Synthesis/AAA_Baselines.git
cd AAA_Baselines

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create config
cp ../.env.example .env
# Edit .env: set DEBUG=true

# Start backend
uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Access

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend UI |
| http://localhost:8000/docs | API Documentation |
| http://localhost:8000/v1/health | Health Check |

---

## Project Structure

```
AAA_Baselines/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # REST endpoints
│   │   │   ├── health.py        # /v1/health, /v1/ready
│   │   │   ├── challenges.py    # /v1/challenges
│   │   │   ├── verify.py        # /v1/verify
│   │   │   ├── enroll.py        # /v1/enroll
│   │   │   ├── risk.py          # /v1/risk/transcript
│   │   │   └── consent.py       # /v1/consent
│   │   ├── core/
│   │   │   ├── config.py        # Settings management
│   │   │   ├── policy_engine.py # Five-outcome decisions
│   │   │   ├── ratelimit.py     # Rate limiting
│   │   │   └── logging.py       # Log redaction
│   │   ├── security/
│   │   │   ├── jwt_auth.py      # JWT + CORS
│   │   │   ├── voiceprint_crypto.py  # AES-256-GCM
│   │   │   └── host_auth.py     # Host app policy
│   │   ├── adapters/
│   │   │   └── vr.py            # Vishing risk analysis
│   │   ├── aaa_asr/
│   │   │   └── phrase_matcher.py  # Deterministic matching
│   │   ├── layer1_speaker.py    # ECAPA-TDNN
│   │   ├── layer2_deepfake.py   # Wav2Vec2
│   │   ├── layer3_asr.py        # Whisper
│   │   ├── layer3_adaptive.py   # Challenge + EMA
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── db.py                # Database config
│   │   └── main.py              # FastAPI app
│   ├── tests/                   # 437 tests
│   └── requirements.txt
├── frontend/                    # Main React frontend
├── apps/
│   ├── banking_shield/          # Banking host app demo
│   └── callguard/               # Call center host app demo
├── docs/                        # Documentation
├── .env.example                 # Configuration template
├── docker-compose.yml           # Docker deployment
├── ARCHITECTURE.md              # Technical architecture
├── SECURITY.md                  # Security documentation
├── INSTALLATION.md              # Setup guide
└── README.md                    # This file
```

---

## API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Liveness check |
| `/v1/ready` | GET | Readiness check (models, DB) |
| `/v1/challenges` | POST | Generate challenge phrase |
| `/v1/verify` | POST | Verify voice authentication |
| `/v1/enroll` | POST | Enroll voiceprint |
| `/v1/risk/transcript` | POST | Analyze transcript for vishing |

### Response Format

```json
{
  "request_id": "uuid",
  "decision": "APPROVE | DENY | STEP_UP | REVIEW | UNAVAILABLE",
  "session_id": "uuid",
  "reason": "Human-readable reason",
  "reason_public": "Safe public reason code",
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "requires_fresh_challenge": false,
  "requires_human_review": false
}
```

### Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/v1/challenges` | 10/minute |
| `/v1/verify` | 5/minute |
| `/v1/enroll` | 3/5minutes |

---

## Host Applications

### Banking Shield (Port 3000)

Banking sector demo with high-security policy tier:
- Voice authentication for high-value transactions
- Vishing detection integration
- Audit logging

### CallGuard (Port 5174)

Call center demo with real-time protection:
- Live transcript analysis
- Risk indicator display
- STEP_UP workflow support

### AAA-Controlled Capture

Both host apps use the iframe pattern - audio is captured and uploaded directly to AAA, never passing through the host application.

---

## Configuration

### Environment Variables

See [.env.example](.env.example) for complete reference.

**Required:**
```bash
DATABASE_URL=postgresql://...
AAA_JWT_SECRET=<32+ chars>
L3_HMAC_SECRET=<32+ chars>
ALLOWED_ORIGINS=http://localhost:5173,...
```

**Optional:**
```bash
L2_SPOOF_THRESHOLD=0.5
L1_SIMILARITY_THRESHOLD=0.5
ASR_PHRASE_THRESHOLD=0.6
WHISPER_MODEL=base
DEBUG=false
```

---

## Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# With coverage
pytest --cov=app

# Verbose
pytest -v

# Specific test
pytest tests/test_api_v1.py -v
```

**Current Status:** 437 tests passing

Test categories:
- `test_api_v1.py` - API endpoint tests
- `test_policy_engine.py` - Five-outcome decision tests
- `test_tenant_isolation.py` - RLS security tests
- `test_log_redaction.py` - PII redaction tests
- `test_vr_hard_negatives.py` - Vishing detection tests
- `test_voiceprint_crypto.py` - Encryption tests

---

## Deployment

### Development

```bash
# Backend
uvicorn app.main:app --reload --port 8000

# Frontend
npm run dev
```

### Production

See [INSTALLATION.md](INSTALLATION.md) for detailed deployment guides:
- Render (recommended)
- Railway
- Docker
- Manual VPS

### Docker

```bash
docker-compose up -d
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture and data flow |
| [SECURITY.md](SECURITY.md) | Security model and threat analysis |
| [INSTALLATION.md](INSTALLATION.md) | Complete setup guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guidelines |
| [docs/operations/](docs/operations/) | Backup, restore, quarantine procedures |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**AAA Engine v1.0.0**  
**Last Updated:** November 2026
