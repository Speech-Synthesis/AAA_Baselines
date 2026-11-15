# Changelog

All notable changes to AAA Engine are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-16

### Major Release - Production Ready

**Five-Outcome PolicyEngine**
- Centralized decision authority with APPROVE, DENY, STEP_UP, REVIEW, UNAVAILABLE outcomes
- Risk level classification (LOW, MEDIUM, HIGH, CRITICAL)
- Gate-blocked reporting for debugging
- requires_fresh_challenge and requires_human_review flags

**Parallel AD||ASR Execution**
- Deepfake detection and ASR phrase verification run concurrently
- ~30% faster authentication (1.1s vs 1.6s sequential)
- SV gating: speaker verification only runs after AD+ASR pass

**Vishing Risk Analysis (AAA-VR)**
- 10 risk indicators with severity classification
- Hard-negative detection for legitimate security advisories
- Negation pattern matching to avoid false positives
- Integration with PolicyEngine for REVIEW/STEP_UP decisions

**Security Hardening**
- AES-256-GCM voiceprint encryption with tenant-specific keys
- JWT authentication with RS256/HS256 support
- Row-Level Security (RLS) for multi-tenant isolation
- Automatic PII log redaction (23 test cases)
- Consent management with withdrawal support

**Host Application Integration**
- Banking Shield demo (port 3000)
- CallGuard demo (port 5174)
- AAA-controlled capture via iframe pattern
- LIVE mode with auto-fallback to mock

**Database**
- PostgreSQL (Supabase) with native UUID support
- GUID type with dialect-aware implementation
- Voiceprint history audit trail
- Model registry with quarantine support
- Consent records table

**Operations**
- Backup/restore procedures documented
- Model quarantine procedures documented
- Health check endpoints (/v1/health, /v1/ready)
- Model status monitoring

### Added

- `backend/app/core/policy_engine.py` - Centralized five-outcome decision engine
- `backend/app/adapters/vr.py` - Vishing risk transcript analysis
- `backend/app/security/voiceprint_crypto.py` - AES-256-GCM encryption
- `backend/app/core/logging.py` - PII log redaction
- `backend/app/api/v1/consent.py` - Consent management endpoints
- `backend/app/api/v1/health.py` - Health and readiness endpoints
- `backend/app/models.py` - ConsentRecord, VoiceprintHistory, ModelRegistry models
- `docs/operations/BACKUP_RESTORE.md` - Backup procedures
- `docs/operations/MODEL_QUARANTINE.md` - Quarantine procedures
- 437 tests (all passing)

### Changed

- `backend/app/api/v1/verify.py` - Parallel AD||ASR, PolicyEngine integration
- `backend/app/main.py` - CORS configuration via jwt_auth.configure_cors()
- `backend/app/models.py` - GUID type with PostgreSQL native UUID support
- `frontend/src/components/VerifyPage.jsx` - Five-outcome display
- `frontend/src/api.js` - Health check via /v1/health endpoint
- `apps/*/src/services/api.js` - LIVE mode with auto-fallback

### Security

- JWT secret validation (min 32 chars, no weak patterns)
- Challenge token HMAC with 90s TTL and single-use enforcement
- Voiceprint encryption with per-tenant key derivation
- Rate limiting: 10/min challenges, 5/min verify, 3/5min enroll
- CORS wildcard prohibition (blocked with CRITICAL log)

---

## [0.2.0] - 2026-11-14

### Added

- Host application demos (Banking Shield, CallGuard)
- Backend connectivity status indicator
- AAA-controlled capture pattern (iframe)
- Mock mode with auto-fallback

### Changed

- Default to LIVE mode (was MOCK)
- Improved error handling for backend unavailability

---

## [0.1.0] - 2024-10-25

### Initial Release

**Core Features**
- Four-layer authentication pipeline (L2 → ASR → L1 → L3)
- Deepfake detection using Wav2Vec2 model
- Phrase verification using Whisper ASR
- Speaker verification using ECAPA-TDNN
- Challenge-response tokens with HMAC-SHA256
- EMA-based voiceprint adaptation (alpha = 0.2)

**Backend**
- FastAPI REST API with automatic documentation
- SQLAlchemy ORM with PostgreSQL/SQLite support
- CORS middleware for cross-origin requests
- Comprehensive error handling

**Frontend**
- React 18 with Vite build system
- Audio recording with MediaRecorder API
- User registration, enrollment, and verification flows
- Authentication logs dashboard

**Infrastructure**
- Docker multi-stage build configuration
- Docker Compose orchestration
- Render deployment configuration
- Comprehensive documentation

### Changed
- L1 threshold adjusted from 0.70 to 0.50 for better acceptance rate
- Frontend API client auto-detects environment (localhost vs production)
- Database defaults to SQLite for easier development setup

### Fixed
- Audio resampling for non-16kHz input files
- CORS configuration for wildcard subdomains
- Token expiration validation logic

### Security
- HMAC-SHA256 signed challenge tokens
- Single-use token enforcement
- 90-second token TTL
- EMA prevents voiceprint poisoning

---

## Performance Metrics

### Version 1.0.0

| Metric | Value |
|--------|-------|
| Genuine User Acceptance | 99.2% |
| Deepfake Rejection | 95.8% |
| Phrase Verification Accuracy | 98.1% |
| False Rejection Rate (FRR) | 0.8% |
| False Acceptance Rate (FAR) | 0.6% |
| Equal Error Rate (EER) | 0.7% |
| End-to-End Latency (Parallel) | ~1.1s |
| Tests Passing | 437 |

---

## Known Issues

### Version 1.0.0

1. **Cold Start Latency:** First request takes 8-12 seconds due to model loading
2. **Modern TTS Detection:** L2 may not catch newest TTS systems (ElevenLabs, VALL-E)
3. **Language Support:** ASR phrase verification is English-only
4. **Noise Sensitivity:** Performance degrades in high-noise environments (SNR < 10dB)

---

## Upgrade Guide

### From 0.1.0 to 1.0.0

1. **Database Migration:**
   - New tables: consent_records, voiceprint_history, model_registry
   - GUID type now uses native PostgreSQL UUID
   - Run with SQLAlchemy create_all() or migrate manually

2. **Environment Variables:**
   - New required: `VOICEPRINT_ENCRYPTION_KEY`
   - Renamed: Check .env.example for complete list

3. **API Changes:**
   - Verify response now includes `decision` field (was `result`)
   - New fields: `risk_level`, `requires_fresh_challenge`, `requires_human_review`
   - Backward compatibility: `result` field still present

4. **Frontend:**
   - Update VerifyPage to use `decision` instead of `result`
   - Add support for STEP_UP and REVIEW outcomes

---

## Contributors

- Navadeep: Infrastructure and Backend Orchestration
- Surya: Speaker Verification, Policy Engine, Security
- Nandan: Deepfake Detection
- Aditya: Layer 3 and Frontend
- Karthik: Vishing Risk, Security Hardening

---

[unreleased]: https://github.com/Speech-Synthesis/AAA_Baselines/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Speech-Synthesis/AAA_Baselines/compare/v0.1.0...v1.0.0
[0.2.0]: https://github.com/Speech-Synthesis/AAA_Baselines/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Speech-Synthesis/AAA_Baselines/releases/tag/v0.1.0
