# Installation Guide

Complete setup instructions for development and production deployment of AAA Engine.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 4 GB | 8 GB |
| Storage | 2 GB | 5 GB |
| CPU | 2 cores | 4 cores |

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend build |
| PostgreSQL | 15+ | Production database |
| Git | Any | Version control |
| Docker | 24+ | Container deployment (optional) |

### Verifying Prerequisites

```bash
# Check Python version
python --version
# Expected: Python 3.11.x or higher

# Check Node.js version
node --version
# Expected: v20.x.x or higher

# Check npm version
npm --version
# Expected: 10.x.x or higher

# Check PostgreSQL (if using)
psql --version
# Expected: psql (PostgreSQL) 15.x or higher
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
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note:** First-time installation downloads ML models (~2 GB). This may take several minutes depending on your connection.

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install
```

### Step 4: Database Setup

**Option A: SQLite (Development)**

No additional setup required. SQLite database file is created automatically.

**Option B: PostgreSQL (Production)**

```bash
# Create database
createdb aaa_engine

# Or using psql
psql -U postgres -c "CREATE DATABASE aaa_engine;"
```

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
# SQLite (Development):
DATABASE_URL=sqlite:///./aaa_engine.db

# PostgreSQL (Production):
# DATABASE_URL=postgresql://user:password@localhost:5432/aaa_engine

# Security Keys (REQUIRED - generate unique values)
SECRET_KEY=your-secret-key-minimum-32-characters-long
L3_HMAC_SECRET=your-hmac-secret-minimum-32-characters-long

# Application Settings
DEBUG=true
```

### Generating Secure Keys

```bash
# Python method
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL method
openssl rand -hex 32
```

### Frontend Configuration

The frontend automatically detects the environment:

```javascript
// frontend/src/api.js
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://your-backend-url.com';
```

For production, update the production URL or use environment variables in your build process.

---

## Running the Application

### Development Mode

Open two terminal windows:

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
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**

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

### Accessing the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Alternative Docs | http://localhost:8000/redoc | ReDoc UI |

---

## Production Deployment

### Option 1: Render (Recommended)

The repository includes `render.yaml` for automated deployment.

1. Create account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Click "New Blueprint Instance"
4. Select the repository
5. Configure environment variables in dashboard:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `L3_HMAC_SECRET`
6. Deploy

### Option 2: Manual VPS Deployment

**Backend with Gunicorn:**

```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**Systemd Service:**

Create `/etc/systemd/system/aaa-backend.service`:

```ini
[Unit]
Description=AAA Engine Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/aaa-engine/backend
Environment="PATH=/opt/aaa-engine/backend/venv/bin"
EnvironmentFile=/opt/aaa-engine/backend/.env
ExecStart=/opt/aaa-engine/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable aaa-backend
sudo systemctl start aaa-backend
```

**Frontend with Nginx:**

Build frontend:

```bash
cd frontend
npm run build
```

Nginx configuration (`/etc/nginx/sites-available/aaa-frontend`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/aaa-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Configuration

The included `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./aaa_engine.db
      - SECRET_KEY=${SECRET_KEY}
      - L3_HMAC_SECRET=${L3_HMAC_SECRET}
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Building Individual Images

**Backend:**

```bash
docker build -t aaa-backend -f backend/Dockerfile ./backend
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./aaa_engine.db \
  -e SECRET_KEY=your-secret \
  -e L3_HMAC_SECRET=your-hmac-secret \
  aaa-backend
```

**Full Stack:**

```bash
docker build -t aaa-engine .
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./aaa_engine.db \
  -e SECRET_KEY=your-secret \
  -e L3_HMAC_SECRET=your-hmac-secret \
  aaa-engine
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions:**
1. Verify DATABASE_URL format is correct
2. Ensure PostgreSQL service is running: `sudo systemctl status postgresql`
3. Check if database exists: `psql -l`
4. Verify network/firewall allows connection

#### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**
1. Ensure you're in the `backend/` directory
2. Verify virtual environment is activated
3. Reinstall dependencies: `pip install -r requirements.txt`

#### Model Download Timeout

**Error:** `requests.exceptions.ReadTimeout` or `HfHubHTTPError: 504`

**Solutions:**
1. Check internet connection
2. Pre-download models:
   ```python
   from transformers import AutoModelForAudioClassification
   from speechbrain.pretrained import EncoderClassifier

   # Download L2 model
   AutoModelForAudioClassification.from_pretrained(
       'garystafford/wav2vec2-deepfake-voice-detector'
   )

   # Download L1 model
   EncoderClassifier.from_hparams(
       source='speechbrain/spkrec-ecapa-voxceleb'
   )
   ```
3. Set longer timeout in environment

#### CORS Error

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solutions:**
1. Verify frontend origin is in CORS allowed list
2. Edit `backend/app/main.py` to add your domain:
   ```python
   allow_origins=[
       "http://localhost:5173",
       "https://your-domain.com"
   ]
   ```

#### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solutions:**

```bash
# Find process using port
# Linux/macOS:
lsof -i :8000

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
1. Use HTTPS in production (required for microphone access)
2. Allow microphone permission in browser settings
3. Use localhost for development (exempt from HTTPS requirement)

---

## Verification

### Backend Health Check

```bash
curl http://localhost:8000/
```

Expected response:
```json
{"message": "AAA Engine API", "status": "running"}
```

### Database Check

```bash
curl http://localhost:8000/users
```

Expected response:
```json
[]
```

### Frontend Check

Open http://localhost:5173 in browser. You should see the registration page.

### Full Pipeline Test

1. **Register:** Create user with name and email
2. **Enroll:** Record 3 voice samples (5+ seconds each)
3. **Challenge:** Request authentication challenge
4. **Verify:** Speak the challenge phrase and submit

All steps should complete without errors.

---

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [DEMO.md](DEMO.md) for usage walkthrough
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

---

**Installation Guide Version:** 1.0
