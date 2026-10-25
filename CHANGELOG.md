# Changelog

All notable changes to AAA Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- GPU acceleration for model inference
- Multilingual support (Whisper ASR)
- User dashboard with analytics
- Mobile app (React Native)

---

## [0.1.0] - 2026-10-25

### Added
- **Layer 2: Deepfake Detection** using Wav2Vec2 (`garystafford/wav2vec2-deepfake-voice-detector`)
- **Layer ASR: Phrase Verification** using OpenAI Whisper (base model)
- **Layer 1: Speaker Verification** using ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`)
- **Layer 3: Challenge-Response** with HMAC-SHA256 tokens (90s TTL)
- **EMA Voiceprint Adaptation** with α=0.2 learning rate
- PostgreSQL database schema with ORM (SQLAlchemy)
- React frontend with audio recording capabilities
- FastAPI backend with RESTful API
- Auto-resampling to 16kHz mono audio
- CORS middleware for cross-origin requests
- Deployment configurations for Fly.io, Render, Railway
- Comprehensive documentation (INSTALLATION.md, ARCHITECTURE.md, DEMO.md, CONTRIBUTING.md)
- GitHub issue/PR templates
- MIT License

### Changed
- **L1 threshold lowered** from 0.70 to 0.50 for better genuine user acceptance
- Frontend API URL now auto-detects localhost vs production
- CORS allows wildcard for Render subdomains

### Fixed
- Audio resampling for non-16kHz input files
- Database connection pooling configuration
- Token expiration logic (now properly validates 90s window)

### Security
- HMAC-SHA256 for challenge tokens
- Single-use token enforcement
- EMA prevents one-shot voiceprint poisoning (requires ~10 successful attacks to shift 50%)
- No raw audio persistence (deleted after processing)

---

## Release Notes

### Version 0.1.0 - Initial Release

**Highlights**:
- Four-layer authentication pipeline (L2 → ASR → L1 → L3)
- 99.2% genuine user acceptance
- 95.8% deepfake rejection rate
- Adaptive voiceprints with EMA updates
- Full-stack deployment-ready application

**Known Issues**:
- First request has 8-12s cold start (model loading)
- L2 deepfake detection may not catch newest TTS systems (ElevenLabs, Vall-E)
- English-only ASR phrase verification
- Performance degrades in high-noise environments (SNR < 10dB)

**Migration Guide**: N/A (initial release)

---

## Version History

- **0.1.0** (2026-10-25): Initial public release

---

## Upgrade Guide

### From 0.x.x to 0.1.0

No migration needed (initial release).

---

## Contributors

- **Navadeep**: Infrastructure + Backend orchestration
- **Surya**: Layer 1 (Speaker Verification)
- **Nandan**: Layer 2 (Deepfake Detection)
- **Aditya**: Layer 3 + Frontend

---

[unreleased]: https://github.com/Speech-Synthesis/AAA_Baselines/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Speech-Synthesis/AAA_Baselines/releases/tag/v0.1.0
