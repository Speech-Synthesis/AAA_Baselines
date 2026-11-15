# Installation Guide

Complete setup instructions for development, testing, and production deployment of AAA Engine.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Configuration Reference](#configuration-reference)
- [Running the Applications](#running-the-applications)
- [Database Setup](#database-setup)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended | Notes |
|-------------|---------|-------------|-------|
| RAM | 4 GB | 8 GB | Model loading requires ~3GB |
| Storage | 5 GB | 10 GB | ML models ~2GB each |
| CPU | 2 cores | 4+ cores | Parallel AD\|\|ASR benefits from more cores |
| GPU | Optional | NVIDIA CUDA | 5-10x inference speedup |

### Software Requirements

| Software | Version | Required | Purpose |
|----------|---------|----------|---------|
| Python | 3.11+ | Yes | Backend runtime |
| Node.js | 20+ | Yes | Frontend build |
| PostgreSQL | 15+ | Production | Database (Supabase recommended) |
| Git | Any | Yes | Version control |
| Docker | 24+ | Optional | Container deployment |

### Verify Prerequisites

```bash
# Python
python --version
# Expected: Python 3.11.x or higher

# Node.js
node --version
# Expected: v20.x.x or higher

# npm
npm --version
# Expected: 10.x.x or higher

# Git
git --version
# Expected: git version 2.x.x

# PostgreSQL (optional for dev)
psql --version
# Expected: psql (PostgreSQL) 15.x or higher
```

---

## Quick Start

**5-minute setup for development:**

```bash
# 1. Clone repository
git clone https://github.com/Speech-Synthesis/AAA_Baselines.git
cd AAA_Baselines

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Create .env file
cp ../.env.example .env
# Edit .env: set DEBUG=true, optionally set DATABASE_URL

# 4. Start backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# 5. Frontend setup (Terminal 2)
cd ../frontend
npm install
npm run dev

# 6. Open browser
# http://localhost:5173
```

---

## Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/Speech-Synthesis/AAA_Baselines.git
cd AAA_Baselines
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note:** First-time installation downloads ML models (~2-3 GB total):
- ECAPA-TDNN (Speaker Verification): ~200 MB
- Wav2Vec2 (Deepfake Detection): ~380 MB
- Whisper base (ASR): ~150 MB

### Step 3: Frontend Setup

```bash
# From project root
cd frontend
npm install
```

### Step 4: Host Applications (Optional)

```bash
# Banking Shield
cd apps/banking_shield
npm install

# CallGuard
cd ../callguard
npm install
```

### Step 5: Environment Configuration

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# See Configuration Reference below
```

---

## Configuration Reference

### Required Environment Variables

```bash
# =============================================================================
# DATABASE [REQUIRED]
# =============================================================================
# Development (SQLite - auto-created)
DATABASE_URL=sqlite:///./aaa_engine.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# =============================================================================
# SECURITY SECRETS [REQUIRED for production]
# =============================================================================
# JWT Authentication (min 32 chars)
AAA_JWT_SECRET=your_jwt_secret_here

# Challenge Token Signing (min 32 chars)
L3_HMAC_SECRET=your_hmac_secret_here

# Voiceprint Encryption (min 32 chars)
VOICEPRINT_ENCRYPTION_KEY=your_encryption_key_here

# =============================================================================
# CORS [REQUIRED]
# =============================================================================
# Comma-separated origins (NO wildcards)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:5174

# =============================================================================
# APPLICATION MODE
# =============================================================================
DEBUG=true  # Set to false in production
```

### Optional Configuration

```bash
# Model Thresholds (defaults shown)
L2_SPOOF_THRESHOLD=0.5      # Deepfake detection
L1_SIMILARITY_THRESHOLD=0.5  # Speaker verification
ASR_PHRASE_THRESHOLD=0.6     # Phrase matching

# Model Configuration
WHISPER_MODEL=base           # tiny, base, small, medium, large

# Rate Limiting
RATE_LIMIT_CHALLENGES=10/minute
RATE_LIMIT_VERIFY=5/minute
RATE_LIMIT_ENROLL=3/5minutes

# Challenge TTL
CHALLENGE_TTL_SECONDS=90
```

### Generating Secure Keys

```bash
# Python method (recommended)
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL method
openssl rand -hex 32

# Example output (64 hex characters = 256 bits):
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

---

## Running the Applications

### Development Mode

Open multiple terminals:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
Loading model: garystafford/wav2vec2-deepfake-voice-detector
Successfully loaded: garystafford/wav2vec2-deepfake-voice-detector
INFO:     Application startup complete.
```

**Terminal 2 - Main Frontend:**
```bash
cd frontend
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

**Terminal 3 - Banking Shield (optional):**
```bash
cd apps/banking_shield
npm run dev
# Runs on port 3000
```

**Terminal 4 - CallGuard (optional):**
```bash
cd apps/callguard
npm run dev
# Runs on port 5174
```

### Application URLs

| Application | URL | Description |
|-------------|-----|-------------|
| Main Frontend | http://localhost:5173 | Demo/testing interface |
| Banking Shield | http://localhost:3000 | Banking host app demo |
| CallGuard | http://localhost:5174 | Call center host app demo |
| Backend API | http://localhost:8000 | REST API |
| Swagger Docs | http://localhost:8000/docs | Interactive API docs |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

---

## Database Setup

### Development (SQLite)

No setup required. SQLite database is created automatically at `backend/aaa_engine.db`.

### Production (PostgreSQL)

#### Option 1: Supabase (Recommended)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → Database → Connection string
4. Copy the URI and set in `.env`:

```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres
```

#### Option 2: Neon

1. Create account at [neon.tech](https://neon.tech)
2. Create database
3. Copy connection string:

```bash
DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech/[db]?sslmode=require
```

#### Option 3: Local PostgreSQL

```bash
# Create database
createdb aaa_engine

# Set connection string
DATABASE_URL=postgresql://postgres:password@localhost:5432/aaa_engine
```

#### Schema Migration

Tables are created automatically on first run via SQLAlchemy `create_all()`.

For production, consider using Alembic for migrations:
```bash
# Future: alembic upgrade head
```

---

## Production Deployment

### Option 1: Render (Recommended)

1. Create account at [render.com](https://render.com)
2. Connect GitHub repository
3. Create "New Blueprint Instance"
4. Configure environment variables:
   - `DATABASE_URL` (Supabase connection string)
   - `AAA_JWT_SECRET`
   - `L3_HMAC_SECRET`
   - `VOICEPRINT_ENCRYPTION_KEY`
   - `ALLOWED_ORIGINS`
5. Deploy

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Add PostgreSQL plugin
4. Set environment variables
5. Deploy

### Option 3: Manual VPS

**Backend with Gunicorn:**

```bash
# Install production server
pip install gunicorn

# Run with workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**Systemd Service:**

Create `/etc/systemd/system/aaa-engine.service`:

```ini
[Unit]
Description=AAA Engine Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/aaa-engine/backend
Environment="PATH=/opt/aaa-engine/backend/venv/bin"
EnvironmentFile=/opt/aaa-engine/.env
ExecStart=/opt/aaa-engine/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable aaa-engine
sudo systemctl start aaa-engine
sudo systemctl status aaa-engine
```

**Nginx Reverse Proxy:**

```nginx
server {
    listen 80;
    server_name api.yoursite.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yoursite.com;

    ssl_certificate /etc/letsencrypt/live/api.yoursite.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yoursite.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout for model loading
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

---

## Docker Deployment

### Using Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - AAA_JWT_SECRET=${AAA_JWT_SECRET}
      - L3_HMAC_SECRET=${L3_HMAC_SECRET}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    command: npm run dev -- --host
    depends_on:
      - backend
```

### Building Images

```bash
# Backend
docker build -t aaa-backend -f backend/Dockerfile ./backend

# Run backend
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./aaa_engine.db \
  -e AAA_JWT_SECRET=your-secret \
  -e L3_HMAC_SECRET=your-hmac-secret \
  -e DEBUG=true \
  aaa-backend
```

---

## Troubleshooting

### Common Issues

#### Model Download Timeout

**Error:** `requests.exceptions.ReadTimeout` or `HfHubHTTPError: 504`

**Solution:**
```bash
# Pre-download models manually
python -c "
from transformers import AutoModelForAudioClassification
from speechbrain.inference.speaker import EncoderClassifier
import whisper

# Download deepfake model
AutoModelForAudioClassification.from_pretrained('garystafford/wav2vec2-deepfake-voice-detector')

# Download speaker model
EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb')

# Download Whisper
whisper.load_model('base')
"
```

#### Database Connection Failed

**Error:** `sqlalchemy.exc.OperationalError`

**Solutions:**
1. Check DATABASE_URL format
2. Verify PostgreSQL service is running
3. Check network/firewall allows connection
4. Verify credentials

#### CORS Error

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
Add your frontend origin to ALLOWED_ORIGINS:
```bash
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.com
```

#### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process
# Linux/macOS:
lsof -i :8000 | grep LISTEN
# Windows:
netstat -ano | findstr :8000

# Kill process
# Linux/macOS:
kill -9 <PID>
# Windows:
taskkill /PID <PID> /F
```

#### Audio Recording Not Working

**Error:** `DOMException: Permission denied`

**Solutions:**
1. Use HTTPS in production
2. Allow microphone permission in browser
3. Use localhost for development (exempt from HTTPS)

#### L3_HMAC_SECRET Not Set

**Error:** `MissingSecretError: L3_HMAC_SECRET environment variable must be set`

**Solution:**
Set L3_HMAC_SECRET in .env or set DEBUG=true for development.

---

## Verification

### Backend Health Check

```bash
# Health (liveness)
curl http://localhost:8000/v1/health
# Expected: {"status":"healthy","timestamp":"..."}

# Ready (all dependencies)
curl http://localhost:8000/v1/ready
# Expected: {"status":"ready","checks":{...}}
```

### API Documentation

Open http://localhost:8000/docs in browser to see interactive Swagger UI.

### End-to-End Test

1. **Register:** Create user with name and email
2. **Enroll:** Record 3 voice samples (5+ seconds each)
3. **Challenge:** Request authentication challenge
4. **Verify:** Speak the challenge phrase and submit
5. **Dashboard:** View authentication logs

### Run Test Suite

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# With coverage
pytest --cov=app

# Verbose
pytest -v

# Specific test file
pytest tests/test_api_v1.py
```

Expected: 437 tests passing.

---

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Read [SECURITY.md](SECURITY.md) for security guidelines
- See [DEMO.md](DEMO.md) for usage walkthrough
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

---

**Installation Guide Version:** 2.0  
**Last Updated:** November 2026
