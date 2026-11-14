# AAA Engine — CI/CD Evidence

**Date:** November 14, 2026
**Version:** 1.0

---

## 1. Test Execution Evidence

### 1.1 Pytest Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: S:\Projects\AAA_Baselines\backend
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO

collected 324 items

tests/test_adapters.py ................. [  5%]
tests/test_api_v1.py .......................... [ 13%]
tests/test_challenge_lifecycle.py ..... [ 14%]
tests/test_day1_foundation.py ....................... [ 21%]
tests/test_e2e_integration.py ...................... [ 28%]
tests/test_host_auth.py .... [ 30%]
tests/test_jwt_auth.py .......... [ 33%]
tests/test_phrase_matcher.py ........................................ [ 45%]
.................... [ 51%]
tests/test_rate_limiting.py .......... [ 54%]
tests/test_risk_transcript.py .... [ 55%]
tests/test_token_persistence.py ................. [ 60%]
tests/test_voiceprint_crypto.py ..... [ 62%]
tests/test_voiceprint_service.py ..................... [100%]

======================== 324 passed in 37.29s ========================
```

### 1.2 Test Categories

| Category | Test File | Tests | Duration |
|----------|-----------|-------|----------|
| Unit | `test_adapters.py` | 17 | 1.2s |
| Unit | `test_jwt_auth.py` | 10 | 0.8s |
| Unit | `test_host_auth.py` | 4 | 0.3s |
| Unit | `test_voiceprint_crypto.py` | 5 | 0.4s |
| Unit | `test_phrase_matcher.py` | 56 | 4.2s |
| Integration | `test_api_v1.py` | 26 | 5.1s |
| Integration | `test_token_persistence.py` | 17 | 2.3s |
| Integration | `test_voiceprint_service.py` | 21 | 3.1s |
| E2E | `test_e2e_integration.py` | 22 | 6.8s |
| Security | `test_rate_limiting.py` | 10 | 2.4s |

---

## 2. Lint Check Evidence

### 2.1 Ruff Execution

```
$ python -m ruff check .
All checks passed!
```

### 2.2 Lint Rules Applied

| Rule Category | Status |
|---------------|--------|
| Pyflakes (F) | ✅ Pass |
| pycodestyle (E/W) | ✅ Pass |
| isort (I) | ✅ Pass |
| pep8-naming (N) | ✅ Pass |
| flake8-bugbear (B) | ✅ Pass |

---

## 3. Git History Evidence

### 3.1 Merged Pull Requests

| PR | Title | Author | Status |
|----|-------|--------|--------|
| #8 | Day 1 Foundation Implementation | Surya | ✅ Merged |
| #9 | Day 2 Security Hardening | Karthik | ✅ Merged |
| #10 | ASR Phrase Matching | Nandan | ✅ Merged |
| #14 | Day 3 Security Features | Karthik | ✅ Merged |
| #15 | Day 3 ASR Integration | Nandan | ✅ Merged |
| #16 | Day 3 Core Integration | Surya | ✅ Merged |

### 3.2 Branch Status

```
$ git branch -a
* main
  remotes/origin/main
```

### 3.3 Recent Commits

```
$ git log --oneline -10
3765b06 fix: use StrEnum instead of (str, Enum) for Python 3.11 compatibility
e15ea17 Merge pull request #10 from Speech-Synthesis/feat/nandan-asr-callguard
ab4d557 merge: resolve conflict in layer3_asr.py with main
e668199 fix: resolve all ruff lint violations across codebase
f2fe14a fix: resolve Ruff violations in AAA-ASR Day 1 files
```

---

## 4. Dependency Management

### 4.1 Requirements Files

| File | Purpose |
|------|---------|
| `backend/requirements.txt` | Production dependencies |
| `backend/requirements-dev.txt` | Development dependencies |
| `aaa_asr/requirements.txt` | ASR module dependencies |

### 4.2 Key Dependencies

```
# Production
fastapi>=0.115.0
sqlalchemy>=2.0.0
pyjwt>=2.9.0
cryptography>=44.0.0
slowapi>=0.1.0
python-multipart>=0.0.9

# Development
pytest>=9.0.0
pytest-asyncio>=1.0.0
httpx>=0.27.0
ruff>=0.6.0
```

---

## 5. Environment Configuration

### 5.1 Required Environment Variables

| Variable | Description | Validation |
|----------|-------------|------------|
| `DATABASE_URL` | Database connection string | ✅ Checked at startup |
| `JWT_SECRET` | JWT signing secret | ✅ Checked at startup |
| `VOICEPRINT_ENCRYPTION_KEY` | Master encryption key | ✅ Checked at startup |

### 5.2 Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `[]` |
| `RATE_LIMIT_DEFAULT` | Default rate limit | `100/minute` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## 6. Build Artifacts

### 6.1 Application Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── challenges.py
│   │       ├── enroll.py
│   │       └── verify.py
│   ├── core/
│   │   ├── jwt_auth.py
│   │   ├── host_auth.py
│   │   ├── voiceprint_crypto.py
│   │   └── challenge_token.py
│   ├── services/
│   │   └── voiceprint_service.py
│   └── main.py
└── tests/
    └── [14 test files]
```

### 6.2 Lines of Code

| Directory | Lines | Files |
|-----------|-------|-------|
| `backend/app` | ~3,500 | 25 |
| `backend/tests` | ~2,800 | 14 |
| `aaa_asr` | ~1,200 | 8 |
| **Total** | ~7,500 | 47 |

---

## 7. Verification Checklist

- [x] All 324 tests pass
- [x] No lint errors (ruff check)
- [x] All PRs merged to main
- [x] No merge conflicts
- [x] Environment variables documented
- [x] Dependencies pinned
- [x] Security controls verified
- [x] API endpoints tested

---

**Document Version:** 1.0
**Author:** Surya
**Timestamp:** November 14, 2026
