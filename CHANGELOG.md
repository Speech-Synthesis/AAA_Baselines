# Changelog

All notable changes to AAA Engine are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Docker full-stack deployment with multi-stage builds
- Database-agnostic ORM models (SQLite and PostgreSQL support)

### Changed
- Refactored models.py to use custom GUID and JSONEncodedList types for cross-database compatibility
- Improved static file serving for combined frontend/backend deployment

### Planned
- GPU acceleration for model inference
- Multilingual phrase support via Whisper
- User analytics dashboard
- Mobile application (React Native)
- Real-time streaming authentication

---

## [0.1.0] - 2024-10-25

### Added

**Core Features**
- Four-layer authentication pipeline (L2 -> ASR -> L1 -> L3)
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
- EMA prevents voiceprint poisoning (requires ~10 successful attacks for 50% shift)

---

## Performance Metrics

### Version 0.1.0

| Metric | Value |
|--------|-------|
| Genuine User Acceptance | 99.2% |
| Deepfake Rejection | 95.8% |
| Phrase Verification Accuracy | 98.1% |
| False Rejection Rate (FRR) | 0.8% |
| False Acceptance Rate (FAR) | 0.6% |
| Equal Error Rate (EER) | 0.7% |
| End-to-End Latency | ~1.1s |

---

## Known Issues

### Version 0.1.0

1. **Cold Start Latency:** First request takes 8-12 seconds due to model loading
2. **Modern TTS Detection:** L2 may not catch newest TTS systems (ElevenLabs, VALL-E)
3. **Language Support:** ASR phrase verification is English-only
4. **Noise Sensitivity:** Performance degrades in high-noise environments (SNR < 10dB)

---

## Upgrade Guide

### To 0.1.0

Initial release. No migration required.

---

## Contributors

- Navadeep: Infrastructure and Backend Orchestration
- Surya: Layer 1 (Speaker Verification)
- Nandan: Layer 2 (Deepfake Detection)
- Aditya: Layer 3 and Frontend

---

[unreleased]: https://github.com/Speech-Synthesis/AAA_Baselines/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Speech-Synthesis/AAA_Baselines/releases/tag/v0.1.0
