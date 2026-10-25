# AAA Engine — Shared Contract (Phase 0 Checkpoint)

Read by all 4 people before writing any code. Nobody starts their module until this file is merged to `main`. Any change to this file after Phase 0 requires all 4 people to agree — it's the single source of truth everyone's code is built against.

---

## 1. Team / Track / Tool Map

| Person | Track | AI Tool | Branch |
|---|---|---|---|
| Navadeep | Infra + Backend orchestration | Claude Pro | `infra-backend` |
| Surya | Layer 1 — Speaker Verification | Claude Pro | `layer1-speaker` |
| Nandan | Layer 2 — Deepfake Detection | Antigravity | `layer2-deepfake` |
| Aditya | Layer 3 (Challenge-Response + EMA) + Frontend | Antigravity | `layer3-frontend` |

Repo: one shared GitHub repo, `main` protected, each person works only on their own branch and only touches their own files (see Repo Structure below) to avoid merge conflicts. PRs open at each checkpoint.

---

## 2. Repo Structure (each person owns their own files only)

```
/backend
  /app
    main.py              # Navadeep — orchestrates L2 → L1 → L3, wires everything
    db.py                # Navadeep — SQLAlchemy engine, session
    models.py             # Navadeep — ORM models (matches schema below)
    layer1_speaker.py     # Surya — implements verify_speaker() / enroll_speaker()
    layer2_deepfake.py    # Nandan — implements detect_spoof()
    layer3_adaptive.py    # Aditya — implements generate_challenge(), verify_token(), update_voiceprint()
  requirements.txt
/frontend                 # Aditya — React (Vite)
/docs
  00_SHARED_CONTRACT.md   # this file
  DB_SCHEMA.sql
docker-compose.yml         # Navadeep
.env.example               # Navadeep
```

Rule: only `main.py` imports from the other three `layerX_*.py` files. Nobody edits someone else's `layerX_*.py`. This is what keeps merge conflicts near-zero.

---

## 3. Audio Spec (fixed for everyone)

- Format: WAV, 16kHz, mono
- Enrollment clip: min 3s (Phase 1) → 10s (Phase 2, per FR1)
- Challenge/verify clip: min 2–3s
- All audio hits the API as multipart file upload

---

## 4. Database — Postgres (hosted, shared)

Navadeep provisions a free-tier hosted Postgres (Neon or Supabase) in Phase 0 and shares the connection string via `.env` (never committed — `.env.example` only, real `.env` shared over Slack/WhatsApp).

```sql
-- DB_SCHEMA.sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT UNIQUE,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE voiceprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  embedding FLOAT8[192],
  sample_count INT DEFAULT 1,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  phrase TEXT,
  token TEXT,
  expires_at TIMESTAMP,
  used BOOLEAN DEFAULT FALSE
);

CREATE TABLE auth_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  challenge_id UUID REFERENCES challenges(id),
  l2_label TEXT,
  l2_confidence FLOAT,
  l1_score FLOAT,
  result TEXT,
  layer_blocked INT,
  created_at TIMESTAMP DEFAULT now()
);
```

---

## 5. API Contract (frozen — Navadeep implements the routes, calls into the other 3 modules)

| Endpoint | Method | Body / Query | Response |
|---|---|---|---|
| `/auth/register` | POST | `{name, email}` | `{user_id}` |
| `/auth/enroll` | POST | `user_id` + audio file | `{status, sample_count}` |
| `/auth/challenge` | GET | `?user_id=` | `{phrase, token, expires_at}` |
| `/auth/verify` | POST | `user_id, token` + audio file | see below |
| `/users/{id}/voiceprint-history` | GET | — | `[{updated_at, sample_count}, ...]` |

`/auth/verify` response shape (matches PPT demo JSON exactly):
```json
{
  "result": "ACCEPT" | "REJECT",
  "confidence": 0.0,
  "layer_blocked": null | 1 | 2,
  "session_id": "uuid",
  "reason": "string",
  "l2_label": "bonafide" | "spoof",
  "l2_confidence": 0.0,
  "l1_score": 0.0
}
```

---

## 6. Module Interfaces (function signatures each person's file must expose — this is what makes independent work possible)

**`layer1_speaker.py` (Surya):**
```python
def enroll_speaker(audio_bytes: bytes) -> dict:
    # returns {"embedding": list[float]}  # 192-dim

def verify_speaker(audio_bytes: bytes, stored_embedding: list[float]) -> dict:
    # returns {"score": float, "embedding": list[float]}  # cosine similarity 0-1
```

**`layer2_deepfake.py` (Nandan):**
```python
def detect_spoof(audio_bytes: bytes) -> dict:
    # returns {"label": "bonafide" | "spoof", "confidence": float}
```

**`layer3_adaptive.py` (Aditya):**
```python
def generate_challenge(user_id: str) -> dict:
    # returns {"phrase": str, "token": str, "expires_at": datetime}

def verify_token(token: str) -> bool:
    # single-use + TTL check

def update_voiceprint(old_embedding: list[float], new_embedding: list[float], alpha: float = 0.2) -> list[float]:
    # returns 0.8*old + 0.2*current, elementwise
```

Everyone stubs/mocks the others' functions with fake return values during Phase 1 so nobody blocks on anybody else. Real wiring happens at the Phase 2 integration checkpoint.

---

## 7. Models (Phase 1 — pretrained, zero training)

- **Layer 1**: `speechbrain/spkrec-ecapa-voxceleb` (HF/SpeechBrain) — pretrained ECAPA-TDNN, 192-dim embedding, CPU-fine for demo.
- **Layer 2**: `HyperMoon/wav2vec2-base-960h-finetuned-deepfake` (trained on ASVspoof2019). Fallback: `abhishtagatya/wav2vec2-base-960h-asv19-deepfake`.

Phase 2 (later, on Amrita HPC): fine-tune Wav2Vec2BERT on ASVspoof2019 LA / eval on 2021 DF; benchmark ECAPA-TDNN threshold on VoxCeleb1.

---

## 8. Phase Timeline (all 4 people)

| Phase | What | Exit criteria |
|---|---|---|
| **0 — Sync** | This doc agreed + merged, hosted DB live, repo/branches created | Everyone can reach the DB, `main` has this file + schema |
| **1 — Independent build** | Each person builds their module against mocked interfaces | Each branch's module passes its own local test with mocked I/O |
| **2 — Integration** | Merge all 4 branches, Navadeep wires real calls in `main.py`, run enroll→challenge→verify end-to-end (1 ACCEPT + 1 REJECT) | Live demo works against the shared DB |
| **3 — Phase 2 upgrades** | Fine-tune Wav2Vec2BERT on HPC, benchmark ECAPA-TDNN on VoxCeleb1, EMA α tuning, security hardening, load test | Matches "Plans for Upcoming Semesters" slide targets |

No one starts Phase 1 code before Phase 0's exit criteria are met.
