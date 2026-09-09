# AAA Engine — Adaptive Audio Authentication

A three-layer voice authentication system with deepfake detection and adaptive voiceprint updates.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION PIPELINE                       │
│                                                                       │
│   Audio ──► [L2: Deepfake] ──► [L1: Speaker] ──► [L3: Challenge]     │
│              Detection         Verification       + EMA Update       │
│                                                                       │
│   Reject if:  spoof > 0.5    similarity < 0.7   token invalid/expired │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Layer 1 — Speaker Verification**: ECAPA-TDNN embeddings (192-dim) with cosine similarity matching
- **Layer 2 — Deepfake Detection**: Wav2Vec2-based spoof detection for replay/TTS attacks
- **Layer 3 — Challenge-Response**: HMAC-SHA256 signed tokens (90s TTL, single-use) + EMA voiceprint adaptation
- **Adaptive Voiceprints**: Embeddings evolve over time: `0.8 × old + 0.2 × new`

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLAlchemy |
| Frontend | React + Vite |
| Database | PostgreSQL (Supabase) |
| L1 Model | `speechbrain/spkrec-ecapa-voxceleb` |
| L2 Model | `garystafford/wav2vec2-deepfake-voice-detector` |
| Audio | WAV 16kHz mono (soundfile, no FFmpeg) |

## Project Structure

```
AAA_Baselines/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI orchestration (L2→L1→L3 pipeline)
│   │   ├── db.py                # SQLAlchemy engine + session
│   │   ├── models.py            # ORM models (User, Voiceprint, Challenge, AuthLog)
│   │   ├── layer1_speaker.py    # Speaker verification (ECAPA-TDNN)
│   │   ├── layer2_deepfake.py   # Deepfake detection (Wav2Vec2)
│   │   └── layer3_adaptive.py   # Challenge-response + EMA updates
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React pages (Register, Enroll, Verify, Dashboard)
│   │   ├── api.js               # API client
│   │   └── App.jsx              # Router
│   └── package.json
└── docs/
    └── 00_SHARED_CONTRACT.md    # Team contract + API specs
```

## Quick Start

### 1. Clone & Setup Environment

```bash
git clone https://github.com/Speech-Synthesis/AAA_Baselines.git
cd AAA_Baselines
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your Supabase/PostgreSQL connection string:
# DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run

```bash
# Terminal 1: Backend (port 8000)
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend (port 5173)
cd frontend
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /auth/register` | Register user | `{name, email}` → `{user_id}` |
| `POST /auth/enroll` | Enroll voice | `user_id` + audio file → `{status, sample_count}` |
| `GET /auth/challenge` | Get challenge | `?user_id=` → `{phrase, token, expires_at}` |
| `POST /auth/verify` | Verify voice | `user_id, token` + audio → See response below |
| `GET /users/{id}/voiceprint-history` | Get history | `[{updated_at, sample_count}]` |

### Verify Response

```json
{
  "result": "ACCEPT",
  "confidence": 0.85,
  "layer_blocked": null,
  "session_id": "uuid",
  "reason": "Authentication successful",
  "l2_label": "bonafide",
  "l2_confidence": 0.92,
  "l1_score": 0.85
}
```

## Authentication Flow

```
1. REGISTER    →  User provides name + email
2. ENROLL      →  Record 3+ seconds of speech → creates 192-dim embedding
3. CHALLENGE   →  Request challenge phrase + token (90s TTL)
4. VERIFY      →  Submit audio + token:
                   └─► L2: Check for deepfake/spoof (reject if confidence > 0.5)
                   └─► L1: Compare speaker embedding (reject if similarity < 0.7)
                   └─► L3: Validate token + update voiceprint with EMA
```

## EMA Voiceprint Adaptation

On each successful authentication, the stored voiceprint is updated:

```python
new_embedding = 0.8 * old_embedding + 0.2 * current_embedding
```

This allows the system to adapt to gradual voice changes over time while maintaining stability.

**Implementation**: `backend/app/layer3_adaptive.py:134-164`

```python
def update_voiceprint(old_embedding, new_embedding, alpha=0.2):
    return [(1.0 - alpha) * old + alpha * new
            for old, new in zip(old_embedding, new_embedding)]
```

**Called in**:
- `main.py:129` — During enrollment (updates existing voiceprint)
- `main.py:289` — After successful verification

## Thresholds

| Layer | Threshold | Action |
|-------|-----------|--------|
| L2 Spoof | > 0.5 | Reject (deepfake detected) |
| L1 Similarity | < 0.7 | Reject (speaker mismatch) |
| L3 Token | expired/used/invalid | Reject (token failed) |

## Database Schema

```sql
users (id, name, email, created_at)
voiceprints (id, user_id, embedding[192], sample_count, updated_at)
challenges (id, user_id, phrase, token, expires_at, used)
auth_logs (id, user_id, challenge_id, l2_label, l2_confidence, l1_score, result, layer_blocked, created_at)
```

## Models

### Layer 1: Speaker Verification
- **Model**: `speechbrain/spkrec-ecapa-voxceleb`
- **Output**: 192-dimensional embedding
- **Metric**: Cosine similarity (normalized to 0-1)

### Layer 2: Deepfake Detection
- **Model**: `garystafford/wav2vec2-deepfake-voice-detector`
- **Labels**: `{0: 'real', 1: 'fake'}` → mapped to `bonafide/spoof`
- **Note**: Modern high-quality TTS (ElevenLabs, etc.) may evade detection — this is a known limitation of current deepfake detection models

## Audio Requirements

- **Format**: WAV
- **Sample Rate**: 16kHz (auto-resampled if different)
- **Channels**: Mono (auto-converted if stereo)
- **Duration**:
  - Enrollment: minimum 3 seconds
  - Verification: minimum 2-3 seconds

## Team

| Person | Track | Branch |
|--------|-------|--------|
| Navadeep | Infra + Backend orchestration | `infra-backend` |
| Surya | Layer 1 — Speaker Verification | `layer1-speaker` |
| Nandan | Layer 2 — Deepfake Detection | `layer2-deepfake` |
| Aditya | Layer 3 + Frontend | `layer3-frontend` |

## License

MIT
