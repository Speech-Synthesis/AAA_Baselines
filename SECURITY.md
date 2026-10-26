# Security Policy

Guidelines for reporting security vulnerabilities and our security practices.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |

---

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly with details
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Initial Response | Within 48 hours |
| Status Update | Within 7 days |
| Fix Release | Within 30 days (critical) |

### After Reporting

- We will acknowledge receipt of your report
- We will investigate and validate the issue
- We will work on a fix and coordinate disclosure
- We will credit reporters in the security advisory (unless anonymity is requested)

---

## Security Measures

### Authentication Security

| Measure | Implementation |
|---------|----------------|
| Token Signing | HMAC-SHA256 |
| Token Expiration | 90 seconds TTL |
| Token Reuse | Single-use enforcement |
| Voiceprint Protection | EMA prevents poisoning |

### Data Protection

| Data | Protection |
|------|------------|
| Voice Embeddings | 192-dim vectors (not reversible to audio) |
| Tokens | HMAC-signed, time-limited |
| Passwords | Not stored (voice-only authentication) |
| Database | Parameterized queries (SQL injection prevention) |

### API Security

| Measure | Implementation |
|---------|----------------|
| CORS | Configured allowed origins |
| Input Validation | Pydantic models |
| Rate Limiting | Recommended via reverse proxy |
| HTTPS | Required in production |

---

## Security Architecture

```
+------------------------------------------------------------------+
|                    SECURITY LAYERS                                |
|                                                                   |
|  +-------------------+                                            |
|  | Layer 2           | Deepfake Detection                        |
|  | (Wav2Vec2)        | Blocks AI-generated audio                 |
|  +-------------------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | ASR Layer         | Phrase Verification                       |
|  | (Whisper)         | Blocks replay attacks                     |
|  +-------------------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | Layer 1           | Speaker Verification                      |
|  | (ECAPA-TDNN)      | Blocks impersonation                      |
|  +-------------------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | Layer 3           | Token Validation                          |
|  | (HMAC-SHA256)     | Blocks token reuse/forgery                |
|  +-------------------+                                            |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Known Limitations

| Limitation | Risk Level | Mitigation |
|------------|------------|------------|
| Modern TTS Detection | Medium | Model fine-tuning planned |
| Noise Sensitivity | Low | Recording guidelines |
| Cold Start Latency | Low | Pre-warming in production |

---

## Best Practices for Deployment

### Required

- Use HTTPS in production
- Set strong SECRET_KEY and L3_HMAC_SECRET
- Configure proper CORS origins
- Enable database connection encryption

### Recommended

- Deploy behind rate-limiting reverse proxy
- Monitor authentication logs for anomalies
- Regular security updates for dependencies
- Periodic voiceprint re-enrollment for high-security users

---

## Dependency Security

We monitor dependencies for known vulnerabilities. Run security audits:

```bash
# Backend
pip install safety
safety check -r backend/requirements.txt

# Frontend
cd frontend
npm audit
```

---

**Security Policy Version:** 1.0
**Last Updated:** October 2024
