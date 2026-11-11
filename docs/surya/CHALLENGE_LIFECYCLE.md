# AAA Engine — Challenge Lifecycle

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)

---

## Overview

This document defines the lifecycle management for authentication challenges in AAA Engine. Challenges are time-limited, single-use tokens that bind a user session to a specific verification attempt.

---

## Challenge Properties

| Property | Requirement |
|----------|-------------|
| **Freshness** | Generated on-demand, not reusable |
| **Single-Use** | Consumed atomically, prevents replay |
| **Time-Limited** | 90-second TTL (strict) |
| **Unpredictable** | Cryptographically random phrase + nonce |
| **Session-Bound** | Tied to authenticated tenant + user |
| **Auditable** | Full lifecycle logged |

---

## State Machine

```
                           ┌──────────────────────────────────────────────────┐
                           │                                                  │
                           ▼                                                  │
┌─────────┐  generate()  ┌──────────┐  issue_grant()  ┌────────────┐         │
│  START  │────────────►│  CREATED  │───────────────►│ AUTHORIZED │         │
└─────────┘              └──────────┘                 └────────────┘         │
                               │                            │                 │
                               │ TTL expired                │ receive_audio() │
                               │                            ▼                 │
                               │                   ┌────────────────┐        │
                               │                   │CAPTURE_RECEIVED│        │
                               │                   └────────────────┘        │
                               │                            │                 │
                               │                            │ validate_token()│
                               ▼                            ▼                 │
                        ┌──────────┐              ┌──────────────┐            │
                        │ EXPIRED  │              │   CONSUMED   │            │
                        └──────────┘              └──────────────┘            │
                               │                            │                 │
                               │                            │ finish()        │
                               ▼                            ▼                 │
                        ┌──────────┐              ┌──────────────┐            │
                        │TERMINATED│              │  COMPLETED   │────────────┘
                        └──────────┘              └──────────────┘
```

---

## State Definitions

| State | Description | Transitions |
|-------|-------------|-------------|
| **CREATED** | Challenge generated, token issued | → AUTHORIZED, → EXPIRED |
| **AUTHORIZED** | Capture grant issued to client | → CAPTURE_RECEIVED, → EXPIRED |
| **CAPTURE_RECEIVED** | Audio received, pending validation | → CONSUMED |
| **CONSUMED** | Token validated and marked used | → COMPLETED |
| **COMPLETED** | Verification finished (success or failure) | Terminal |
| **EXPIRED** | TTL exceeded before consumption | → TERMINATED |
| **TERMINATED** | Challenge invalid, cannot proceed | Terminal |

---

## Challenge Token Structure

```
Token Format: {nonce}.{expires_timestamp}.{signature}

Where:
  nonce            = 32 hex characters (16 bytes random)
  expires_timestamp = Unix timestamp (seconds)
  signature        = HMAC-SHA256(payload, secret_key)
  payload          = "{user_id}:{expires_timestamp}:{phrase}:{nonce}"
```

### Example Token

```
a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4.1731319890.f8a9b7c6d5e4f3a2b1c0d9e8f7a6b5c4
```

---

## Database Schema

### challenges Table

```sql
CREATE TABLE challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    session_id VARCHAR(255),
    phrase TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    capture_grant TEXT,
    state VARCHAR(20) NOT NULL DEFAULT 'CREATED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    authorized_at TIMESTAMP,
    captured_at TIMESTAMP,
    consumed_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,

    -- Indexes for efficient queries
    INDEX idx_challenges_token (token),
    INDEX idx_challenges_user_state (user_id, state),
    INDEX idx_challenges_expires (expires_at)
);
```

---

## Operations

### 1. Generate Challenge

```python
async def generate_challenge(
    tenant_id: UUID,
    user_id: UUID,
    session_id: Optional[str] = None
) -> ChallengeResponse:
    """
    Generate a new authentication challenge.

    Steps:
    1. Verify user has enrolled voiceprint
    2. Generate random phrase
    3. Create HMAC-signed token with 90s TTL
    4. Store challenge in database
    5. Return challenge details
    """
    # Generate phrase
    phrase = _generate_dynamic_phrase()

    # Create token with 90s TTL
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=90)
    nonce = secrets.token_hex(16)

    payload = f"{user_id}:{int(expires_at.timestamp())}:{phrase}:{nonce}"
    signature = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    token = f"{nonce}.{int(expires_at.timestamp())}.{signature}"

    # Store in database
    challenge = Challenge(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        phrase=phrase,
        token=token,
        state="CREATED",
        expires_at=expires_at
    )
    db.add(challenge)
    db.commit()

    return ChallengeResponse(
        challenge_id=challenge.id,
        phrase=phrase,
        expires_at=expires_at,
        ttl_seconds=90
    )
```

### 2. Issue Capture Grant

```python
async def issue_capture_grant(challenge_id: UUID) -> str:
    """
    Issue a capture authorization grant for audio upload.

    The grant is a short-lived JWT that authorizes:
    - Single audio upload
    - To specific challenge
    - Within TTL window
    """
    challenge = await db.get(Challenge, challenge_id)

    if challenge.state != "CREATED":
        raise InvalidChallengeStateError()

    if datetime.utcnow() > challenge.expires_at:
        challenge.state = "EXPIRED"
        db.commit()
        raise ChallengeExpiredError()

    # Generate capture grant JWT
    grant = jwt.encode({
        "sub": str(challenge_id),
        "aud": "aaa-capture",
        "exp": challenge.expires_at,
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(8)
    }, CAPTURE_GRANT_SECRET)

    challenge.capture_grant = grant
    challenge.state = "AUTHORIZED"
    challenge.authorized_at = datetime.utcnow()
    db.commit()

    return grant
```

### 3. Validate and Consume Token

```python
async def validate_and_consume(token: str) -> Challenge:
    """
    Atomically validate and consume a challenge token.

    Uses database transaction with row-level locking to ensure
    single-use semantics in distributed environment.
    """
    async with db.transaction():
        # Lock the row for update
        challenge = await db.execute(
            select(Challenge)
            .where(Challenge.token == token)
            .with_for_update()
        ).scalar_one_or_none()

        if not challenge:
            raise TokenNotFoundError()

        if challenge.state == "CONSUMED":
            raise TokenAlreadyUsedError()

        if challenge.state == "EXPIRED":
            raise TokenExpiredError()

        if datetime.utcnow() > challenge.expires_at:
            challenge.state = "EXPIRED"
            raise TokenExpiredError()

        # Verify HMAC signature
        nonce, expires_ts, signature = token.split(".")
        payload = f"{challenge.user_id}:{expires_ts}:{challenge.phrase}:{nonce}"
        expected_sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise InvalidSignatureError()

        # Atomically mark as consumed
        challenge.state = "CONSUMED"
        challenge.consumed_at = datetime.utcnow()

        return challenge
```

---

## Atomic Consumption in PostgreSQL

To ensure single-use semantics under concurrent requests:

```sql
-- Atomic consume with row-level lock
UPDATE challenges
SET state = 'CONSUMED',
    consumed_at = NOW()
WHERE token = $1
  AND state IN ('CREATED', 'AUTHORIZED', 'CAPTURE_RECEIVED')
  AND expires_at > NOW()
RETURNING *;
```

If 0 rows affected, the token was:
- Not found
- Already consumed
- Expired
- In invalid state

---

## Phrase Generation

**Status:** IMPLEMENTED (November 11, 2026)

### Extensive Word Pools

All phrases are dynamically generated from extensive word pools:

| Category | Count | Examples |
|----------|-------|----------|
| Numbers | 29 | zero, one, twelve, forty, hundred |
| Colors | 50 | crimson, jade, turquoise, lavender, cobalt |
| Animals | 57 | falcon, phoenix, dolphin, panther, hedgehog |
| Objects | 53 | shield, crystal, lighthouse, rainbow, fortress |
| Concepts | 49 | nexus, harmony, courage, destiny, legacy |
| Adjectives | 53 | swift, noble, radiant, eternal, majestic |
| Verbs | 53 | soar, guard, discover, pioneer, navigate |
| Places | 35 | summit, harbor, gateway, boulevard, terminal |
| Time Words | 20 | dawn, twilight, solstice, epoch, midnight |

**Total unique words:** 399

### 12 Phrase Templates

```python
# Template 1: "Say: NUMBER COLOR ANIMAL NUMBER"
"Say: eleven mint eagle three"

# Template 2: "Say: COLOR ADJECTIVE OBJECT"
"Say: yellow premier window"

# Template 3: "Say: ADJECTIVE COLOR ANIMAL VERB"
"Say: swift crimson falcon soar"

# Template 4: "Say: NUMBER CONCEPT COLOR PLACE"
"Say: twelve harmony jade summit"

# Template 5: "Say: COLOR ANIMAL PLACE NUMBER"
"Say: cobalt phoenix harbor five"

# Template 6: "Say: ADJECTIVE CONCEPT VERB OBJECT"
"Say: noble courage guard shield"

# Template 7: "Say: NUMBER ADJECTIVE ANIMAL TIME"
"Say: seven brave wolf dawn"

# Template 8: "The ADJECTIVE COLOR ANIMAL VERB"
"The grand violet cougar climb"

# Template 9: "VERB the ADJECTIVE OBJECT at TIME"
"Roam the noble tower at noon"

# Template 10: "A COLOR ANIMAL guards the CONCEPT"
"A cobalt phoenix guards the legacy"

# Template 11: "The CONCEPT of NUMBER ADJECTIVE OBJECTS"
"The dream of twelve brave moonlight"

# Template 12: "From PLACE to PLACE the ANIMAL travels"
"From boulevard to clearing the pelican travels"
```

### Entropy Calculation

| Template | Combinations |
|----------|-------------|
| Template 1 (num-color-animal-num) | 2,396,850 |
| Template 2 (color-adj-object) | 140,450 |
| Template 3 (adj-color-animal-verb) | 8,005,650 |
| Templates 4-12 | Millions more |

**Total unique phrases:** Tens of millions

### No Static Phrases

All phrases are dynamically generated. No fixed phrase list exists.

---

## Capture Grant Structure

```json
{
  "sub": "challenge-uuid",
  "aud": "aaa-capture",
  "exp": 1731319890,
  "iat": 1731319800,
  "jti": "unique-grant-id"
}
```

### Validation Rules

1. Verify JWT signature
2. Check `aud` claim is "aaa-capture"
3. Check `exp` not exceeded
4. Check `jti` not already used (optional replay protection)
5. Check `sub` matches challenge being verified

---

## Cleanup Jobs

### Expired Challenge Cleanup

```python
async def cleanup_expired_challenges():
    """
    Mark expired challenges as TERMINATED.
    Run every 5 minutes.
    """
    await db.execute(
        update(Challenge)
        .where(Challenge.state.in_(["CREATED", "AUTHORIZED"]))
        .where(Challenge.expires_at < datetime.utcnow())
        .values(state="EXPIRED")
    )
```

### Old Challenge Purge

```python
async def purge_old_challenges():
    """
    Delete challenges older than 24 hours.
    Run daily.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    await db.execute(
        delete(Challenge)
        .where(Challenge.created_at < cutoff)
    )
```

---

## Security Considerations

### Token Entropy

- 16-byte nonce = 128 bits of entropy
- Brute force infeasible within 90s TTL

### Replay Prevention

- Single-use enforcement via database state
- Row-level locking prevents race conditions
- HMAC signature prevents tampering

### Time Synchronization

- Server time is authoritative
- Client clocks not trusted
- TTL enforced server-side only

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Token generation | IMPLEMENTED (in-memory) |
| HMAC signing | IMPLEMENTED |
| Single-use enforcement | IMPLEMENTED (in-memory) |
| Database persistence | **NOT IMPLEMENTED** |
| Atomic consumption | **NOT IMPLEMENTED** |
| Capture grants | **NOT IMPLEMENTED** |
| Cleanup jobs | **NOT IMPLEMENTED** |

**Day-2 Priority:** Migrate token store from in-memory dict to PostgreSQL with atomic operations.

---

**Document Version:** 1.0
**Classification:** Architecture Documentation
