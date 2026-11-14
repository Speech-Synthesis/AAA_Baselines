# AAA Engine — Docker Manifest

**Date:** November 14, 2026
**Version:** 1.0

---

## 1. Container Images

### 1.1 AAA Engine API

| Attribute | Value |
|-----------|-------|
| Image Name | `aaa-engine-api` |
| Base Image | `python:3.14-slim` |
| Exposed Port | 8000 |
| Health Check | `/health` |

### 1.2 Dockerfile

```dockerfile
# AAA Engine API Dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 2. Docker Compose

### 2.1 Development Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/aaa_engine
      - JWT_SECRET=${JWT_SECRET}
      - VOICEPRINT_ENCRYPTION_KEY=${VOICEPRINT_ENCRYPTION_KEY}
      - CORS_ORIGINS=http://localhost:3000
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=aaa_engine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 2.2 Production Configuration

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  api:
    image: aaa-engine-api:1.0.0
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - VOICEPRINT_ENCRYPTION_KEY=${VOICEPRINT_ENCRYPTION_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

## 3. Environment Variables

### 3.1 Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | `<random-32-char-string>` |
| `VOICEPRINT_ENCRYPTION_KEY` | AES-256 key (base64) | `<base64-encoded-32-bytes>` |

### 3.2 Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `[]` | Comma-separated allowed origins |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Default rate limit |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 4. Build Commands

### 4.1 Build Image

```bash
# Build API image
docker build -t aaa-engine-api:1.0.0 ./backend

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.14 \
  -t aaa-engine-api:1.0.0 \
  ./backend
```

### 4.2 Run Container

```bash
# Run with environment file
docker run -d \
  --name aaa-api \
  --env-file .env \
  -p 8000:8000 \
  aaa-engine-api:1.0.0

# Run with inline env vars
docker run -d \
  --name aaa-api \
  -e DATABASE_URL=postgresql://localhost:5432/aaa \
  -e JWT_SECRET=your-secret-here \
  -e VOICEPRINT_ENCRYPTION_KEY=your-key-here \
  -p 8000:8000 \
  aaa-engine-api:1.0.0
```

### 4.3 Docker Compose

```bash
# Start development stack
docker-compose up -d

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f api

# Stop stack
docker-compose down
```

---

## 5. Image Layers

| Layer | Size (est.) | Description |
|-------|-------------|-------------|
| Base (python:3.14-slim) | ~150MB | Python runtime |
| Dependencies | ~200MB | pip packages |
| Application | ~5MB | Source code |
| **Total** | ~355MB | Compressed |

---

## 6. Security Considerations

### 6.1 Image Security

- [x] Non-root user for container process
- [x] No secrets in image layers
- [x] Minimal base image (slim variant)
- [x] Security updates applied

### 6.2 Runtime Security

- [x] Read-only root filesystem (when possible)
- [x] No privileged mode required
- [x] Resource limits enforced
- [x] Health checks configured

### 6.3 Secret Management

```yaml
# Using Docker secrets (Swarm mode)
secrets:
  jwt_secret:
    external: true
  encryption_key:
    external: true

services:
  api:
    secrets:
      - jwt_secret
      - encryption_key
    environment:
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
      - VOICEPRINT_ENCRYPTION_KEY_FILE=/run/secrets/encryption_key
```

---

## 7. Registry

### 7.1 Image Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `1.0.0` | Version 1.0.0 release |
| `1.0` | Latest 1.0.x patch |
| `main` | Latest main branch build |

### 7.2 Push to Registry

```bash
# Tag image
docker tag aaa-engine-api:1.0.0 registry.example.com/aaa-engine-api:1.0.0

# Push to registry
docker push registry.example.com/aaa-engine-api:1.0.0
```

---

**Document Version:** 1.0
**Author:** Surya
**Timestamp:** November 14, 2026
