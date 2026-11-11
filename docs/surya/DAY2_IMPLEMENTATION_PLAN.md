# Surya — Day 2 Implementation Plan

**Date:** November 12, 2026
**Sprint Day:** 2 of 4
**Focus:** Critical security fixes and infrastructure

---

## Priority Order

| Priority | Task | Effort | Blocker |
|----------|------|--------|---------|
| P0 | Token persistence migration | 4h | None |
| P0 | Remove fallback secret | 30min | None |
| P1 | Rate limiting | 2h | None |
| P1 | CI/CD pipeline | 3h | None |
| P2 | Model adapter implementations | 4h | Team confirmations |
| P2 | Integration tests | 2h | Token persistence |

---

## Task 1: Token Persistence Migration (P0)

**Current:** `_token_store: dict[str, dict] = {}` in `layer3_adaptive.py:32`

**Target:** Use `challenges` table in PostgreSQL

### Implementation Steps

1. **Update `generate_challenge()`**
   - Store challenge in database instead of dict
   - Return challenge_id for reference

2. **Update `verify_token()`**
   - Query database for token
   - Use `SELECT ... FOR UPDATE` for row lock
   - Atomic update: `SET used = true WHERE used = false`

3. **Update `get_token_phrase()` and `get_token_user_id()`**
   - Query database instead of dict

4. **Add token cleanup**
   - Background task to purge expired challenges

### Code Changes

```python
# layer3_adaptive.py

async def validate_and_consume_token(token: str, db: Session) -> Challenge:
    """Atomically validate and consume a challenge token."""
    challenge = db.query(Challenge).filter(
        Challenge.token == token,
        Challenge.used == False,
        Challenge.expires_at > datetime.utcnow()
    ).with_for_update().first()

    if not challenge:
        raise InvalidTokenError()

    challenge.used = True
    db.commit()
    return challenge
```

### Testing

- Test concurrent token consumption
- Test expired token rejection
- Test replay prevention

---

## Task 2: Remove Fallback Secret (P0)

**Current:**
```python
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026").encode()
```

**Target:**
```python
_secret = os.environ.get("L3_HMAC_SECRET")
if not _secret:
    raise MissingSecretError("L3_HMAC_SECRET")
SECRET_KEY = _secret.encode()
```

### Implementation Steps

1. Import `MissingSecretError` from `core.exceptions`
2. Remove default fallback value
3. Fail at module import if secret missing
4. Update tests to set env var

---

## Task 3: Rate Limiting (P1)

**Package:** slowapi

### Implementation Steps

1. Add `slowapi` to requirements.txt
2. Create rate limiter instance
3. Apply to authentication endpoints

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/auth/challenge")
@limiter.limit("10/minute")
async def get_challenge(...):
    ...

@app.post("/auth/verify")
@limiter.limit("5/minute")
async def verify(...):
    ...
```

### Testing

- Test rate limit enforcement
- Test 429 response

---

## Task 4: CI/CD Pipeline (P1)

### Create `.github/workflows/test.yml`

```yaml
name: Test

on:
  push:
    branches: [main, feat/*]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        env:
          L3_HMAC_SECRET: test-secret-for-ci
          DEBUG: true
        run: |
          cd backend
          pytest tests/ -v

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install ruff
        run: pip install ruff

      - name: Run linter
        run: ruff check backend/
```

---

## Task 5: Model Adapter Implementations (P2)

**Blocked by:** Team confirmations

### After confirmations received:

1. Create `backend/app/adapters/` directory
2. Implement `base.py` with abstract interface
3. Implement `sv.py` wrapping `layer1_speaker.py`
4. Implement `ad.py` wrapping `layer2_deepfake.py`
5. Implement `asr.py` wrapping `layer3_asr.py`
6. Add mock adapters for testing

---

## Task 6: Integration Tests (P2)

**Blocked by:** Token persistence

### Tests to Add

1. Full enrollment flow
2. Full verification flow
3. Token expiration
4. Token replay prevention
5. Deepfake rejection
6. Phrase mismatch rejection
7. Speaker mismatch rejection

---

## Schedule

| Time | Task | Status |
|------|------|--------|
| 09:00-10:00 | Team sync, collect confirmations | |
| 10:00-12:00 | Token persistence (Part 1) | |
| 12:00-13:00 | Lunch | |
| 13:00-14:00 | Token persistence (Part 2) | |
| 14:00-14:30 | Remove fallback secret | |
| 14:30-16:30 | Rate limiting + CI/CD | |
| 16:30-18:00 | Model adapters (if confirmed) | |

---

## Dependencies to Collect

### Morning Sync Agenda

1. **Navadeep (SV)**
   - Confirm embedding dimension (192?)
   - Confirm score direction (higher = same speaker?)
   - Confirm threshold recommendation

2. **Aditya (AD)**
   - Confirm confidence semantics
   - Confirm spoof/bonafide output format

3. **Nandan (ASR)**
   - Confirm phrase matching approach
   - Confirm similarity threshold

4. **Karthik (Security)**
   - JWT public key location
   - Host app auth requirements

---

## Success Criteria for Day 2

- [ ] Token persistence working with tests
- [ ] No fallback secret in codebase
- [ ] Rate limiting active on auth endpoints
- [ ] CI/CD pipeline passing
- [ ] At least 2 model adapters implemented
- [ ] Integration test for full verification flow

---

**Document Version:** 1.0
