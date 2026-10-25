# Installation Guide

Complete setup instructions for AAA Engine development and deployment.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher
- **PostgreSQL**: 15.x or higher (or Supabase account)
- **Git**: For version control
- **OS**: Windows, macOS, or Linux

### Hardware Requirements
- **RAM**: Minimum 4GB (8GB recommended for model loading)
- **Storage**: 2GB free space (for models and dependencies)
- **Microphone**: For voice enrollment and authentication

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Speech-Synthesis/AAA_Baselines.git
cd AAA_Baselines
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration

Create `.env` file in `backend/` directory:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=your-secret-key-change-in-production
L3_HMAC_SECRET=your-hmac-secret-for-tokens
DEBUG=true
```

**Using Supabase** (recommended for quick start):
1. Create free account at [supabase.com](https://supabase.com)
2. Create new project
3. Get connection string from Settings → Database → Connection string (URI)
4. Tables will be auto-created on first run

### 4. Frontend Setup

```bash
cd ../frontend
npm install
```

### 5. Run Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Open browser at: **http://localhost:5173**

---

## Development Setup

### Backend Development

#### Install Development Dependencies

```bash
pip install pytest pytest-cov black flake8 mypy
```

#### Run Tests

```bash
cd backend
pytest
```

#### Code Formatting

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

#### Database Migrations

If you need to modify database schema:

```bash
# Auto-generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### Frontend Development

#### Development Server

```bash
npm run dev  # Hot reload enabled
```

#### Build for Production

```bash
npm run build  # Output to dist/
npm run preview  # Preview production build
```

#### Linting

```bash
npm run lint
```

---

## Production Deployment

### Option 1: Fly.io (Recommended)

**Prerequisites**: Install [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)

```bash
# Login
fly auth login

# Deploy backend
fly launch --config fly.toml
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SECRET_KEY="your-secret"
fly secrets set L3_HMAC_SECRET="your-hmac-secret"
fly deploy

# Deploy frontend (static site)
cd frontend
npm run build
fly launch --name aaa-frontend
```

### Option 2: Docker Compose

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 3: Manual VPS Deployment

```bash
# Backend (with systemd)
sudo nano /etc/systemd/system/aaa-backend.service
sudo systemctl enable aaa-backend
sudo systemctl start aaa-backend

# Frontend (with nginx)
npm run build
sudo cp -r dist/* /var/www/html/
```

### Environment Variables (Production)

**Backend (.env)**:
```env
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=<generate-strong-random-key>
L3_HMAC_SECRET=<generate-strong-random-key>
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
```

**Frontend (auto-detection in api.js)**:
```javascript
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://your-backend-url.com';
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
- Check DATABASE_URL format: `postgresql://user:password@host:5432/database`
- Verify PostgreSQL is running: `pg_isready`
- Check firewall allows port 5432
- For Supabase: Ensure IP whitelist includes your server

#### 2. ModuleNotFoundError: No module named 'app'

**Solution**:
```bash
# Ensure you're in backend/ directory
cd backend
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### 3. Model Download Timeout

**Error**: `HfHubHTTPError: 504 Server Error`

**Solution**:
```bash
# Pre-download models
python -c "
from transformers import AutoModelForAudioClassification, Wav2Vec2Processor
from speechbrain.pretrained import EncoderClassifier

# Download L2 model
AutoModelForAudioClassification.from_pretrained('garystafford/wav2vec2-deepfake-voice-detector')
Wav2Vec2Processor.from_pretrained('garystafford/wav2vec2-deepfake-voice-detector')

# Download L1 model
EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb')
"
```

#### 4. CORS Error in Browser

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
Edit `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend-domain.com"  # Add your domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5. Audio Recording Not Working

**Error**: `DOMException: Permission denied`

**Solution**:
- Use HTTPS (required for microphone access in production)
- Allow microphone permissions in browser
- For development: Use `localhost` (exempted from HTTPS requirement)

#### 6. Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Performance Optimization

#### Model Caching
Models are cached after first load. First request may take 10-30 seconds.

#### Database Connection Pooling
Already configured in `backend/app/db.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

#### Audio Processing
Audio is auto-resampled to 16kHz mono. Upload WAV files for best performance.

---

## Verification

### Test Installation

```bash
# Backend health check
curl http://localhost:8000/
# Expected: {"message": "AAA Engine API", "status": "running"}

# Database check
curl http://localhost:8000/users
# Expected: [] or list of users

# Frontend check
# Open http://localhost:5173 - should see registration page
```

### Test Authentication Flow

1. **Register**: Create user with name + email
2. **Enroll**: Record 3 voice samples (5+ seconds each)
3. **Challenge**: Request authentication challenge
4. **Verify**: Record response to challenge phrase

All steps should complete without errors.

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (FastAPI auto-generated)
- **Database Schema**: See `backend/app/models.py`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Contributing**: See `CONTRIBUTING.md`

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/Speech-Synthesis/AAA_Baselines/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Speech-Synthesis/AAA_Baselines/discussions)
- **Email**: [Contact maintainers]

---

**Installation Status**: ✅ Complete
**Next Steps**: See [README.md](README.md) for usage guide
