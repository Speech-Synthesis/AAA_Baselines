# Security Policy

Comprehensive security documentation for AAA Engine including vulnerability reporting, security architecture, threat model, and compliance requirements.

---

## Table of Contents

- [Reporting Vulnerabilities](#reporting-vulnerabilities)
- [Security Architecture](#security-architecture)
- [Authentication Security](#authentication-security)
- [Data Protection](#data-protection)
- [API Security](#api-security)
- [Threat Model](#threat-model)
- [Compliance & Audit](#compliance--audit)
- [Deployment Security](#deployment-security)
- [Incident Response](#incident-response)

---

## Reporting Vulnerabilities

### How to Report

**DO NOT** open public GitHub issues for security vulnerabilities.

1. **Email:** Report directly to maintainers with encrypted email if possible
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)
   - Your contact information

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Initial Acknowledgment | Within 24 hours |
| Severity Assessment | Within 48 hours |
| Status Update | Within 7 days |
| Fix Release (Critical) | Within 14 days |
| Fix Release (High) | Within 30 days |
| Fix Release (Medium/Low) | Within 90 days |

### Severity Classification

| Severity | Description | Examples |
|----------|-------------|----------|
| **Critical** | Remote code execution, auth bypass | Token forgery, SQL injection |
| **High** | Significant data exposure, privilege escalation | Cross-tenant access, voiceprint theft |
| **Medium** | Limited impact, requires authentication | Rate limit bypass, log injection |
| **Low** | Minimal impact | Information disclosure, DoS |

### Bug Bounty

We appreciate responsible disclosure and will credit reporters in security advisories (unless anonymity is requested).

---

## Security Architecture

### Defense in Depth

```
+===========================================================================+
|                         PERIMETER SECURITY                                 |
|  +---------------------------------------------------------------------+   |
|  | CORS (strict origins) | Rate Limiting | HTTPS/TLS 1.3             |   |
|  +---------------------------------------------------------------------+   |
+===========================================================================+
                                    |
                                    v
+===========================================================================+
|                         AUTHENTICATION LAYER                               |
|  +---------------------------------------------------------------------+   |
|  | JWT Auth (RS256/HS256) | Tenant Isolation (RLS) | API Keys         |   |
|  +---------------------------------------------------------------------+   |
+===========================================================================+
                                    |
                                    v
+===========================================================================+
|                         VOICE AUTHENTICATION                               |
|                                                                            |
|  +-------------------+    +-------------------+    +-------------------+   |
|  | Layer 2 (AD)      |    | ASR Layer         |    | Layer 1 (SV)      |   |
|  | Deepfake          |    | Phrase            |    | Speaker           |   |
|  | Detection         |    | Verification      |    | Verification      |   |
|  | Wav2Vec2          |    | Whisper + Match   |    | ECAPA-TDNN        |   |
|  +-------------------+    +-------------------+    +-------------------+   |
|           |                       |                       |                |
|           v                       v                       v                |
|  +---------------------------------------------------------------------+   |
|  |                      POLICY ENGINE                                   |   |
|  |  Five Outcomes: APPROVE | DENY | STEP_UP | REVIEW | UNAVAILABLE     |   |
|  +---------------------------------------------------------------------+   |
+===========================================================================+
                                    |
                                    v
+===========================================================================+
|                         DATA SECURITY                                      |
|  +---------------------------------------------------------------------+   |
|  | AES-256-GCM Encryption | PII Log Redaction | Audit Logging         |   |
|  +---------------------------------------------------------------------+   |
+===========================================================================+
```

### Cryptographic Standards

| Component | Algorithm | Key Size | Standard |
|-----------|-----------|----------|----------|
| Challenge Tokens | HMAC-SHA256 | 256-bit | RFC 2104 |
| JWT Signing | RS256 / HS256 | 256-bit+ | RFC 7519 |
| Voiceprint Encryption | AES-256-GCM | 256-bit | NIST SP 800-38D |
| Key Derivation | HKDF-SHA256 | 256-bit | RFC 5869 |
| Password Hashing | Argon2id | N/A | RFC 9106 |

---

## Authentication Security

### Challenge-Response Protocol

```
+------------------------------------------------------------------+
|                    CHALLENGE TOKEN SECURITY                       |
+------------------------------------------------------------------+

Generation:
  1. Generate 4 random words from 50+ word vocabulary
     → 50^4 = 6,250,000 possible combinations
  
  2. Create HMAC-SHA256 signature
     message = f"{user_id}:{phrase}:{expires_at.isoformat()}"
     token = HMAC-SHA256(L3_HMAC_SECRET, message)
  
  3. Store challenge in database
     - id: UUID
     - user_id: FK
     - phrase: text
     - token: unique index
     - expires_at: timestamp (90s from now)
     - used: boolean (default false)

Verification:
  1. Check token exists in database
  2. Verify expiration (90s TTL)
  3. Verify not already used (single-use)
  4. Recompute HMAC and compare (constant-time)
  5. Mark as used on successful authentication

Security Properties:
  - Unpredictable: 256-bit random signature
  - Time-limited: 90 second TTL
  - Single-use: Prevents replay attacks
  - Tamper-evident: HMAC signature verification
+------------------------------------------------------------------+
```

### Five-Outcome Policy

| Decision | Security Implication |
|----------|---------------------|
| **APPROVE** | All gates passed, safe to grant access |
| **DENY** | Authentication failed, block access |
| **STEP_UP** | Marginal confidence, require fresh challenge |
| **REVIEW** | Anomaly detected, queue for human review |
| **UNAVAILABLE** | Service degraded, fail closed |

### Rate Limiting

| Endpoint | Limit | Window | Rationale |
|----------|-------|--------|-----------|
| `/v1/challenges` | 10 | 1 minute | Prevent challenge flooding |
| `/v1/verify` | 5 | 1 minute | Prevent brute force |
| `/v1/enroll` | 3 | 5 minutes | Prevent voiceprint poisoning |
| `/v1/risk/transcript` | 10 | 1 minute | Prevent abuse |

---

## Data Protection

### Voiceprint Encryption

```python
# At-rest encryption for voiceprint embeddings
# backend/app/security/voiceprint_crypto.py

class VoiceprintEncryptor:
    """
    AES-256-GCM encryption with tenant-specific key derivation.
    
    Key derivation:
      key = HKDF(
          master_key=VOICEPRINT_ENCRYPTION_KEY,
          salt=SHA256(tenant_id + user_id),
          info=b"aaa-voiceprint-v1"
      )
    
    Ciphertext format:
      base64(nonce[12] || ciphertext || tag[16])
    
    Security properties:
      - 256-bit AES key per tenant+user
      - Unique nonce per encryption
      - Authenticated encryption (GCM)
      - Key isolation between tenants
    """
```

### Data Classification

| Data Type | Classification | Storage | Retention |
|-----------|---------------|---------|-----------|
| Voiceprint Embeddings | Biometric | Encrypted | User-controlled |
| Audio Files | Biometric | NOT stored | Transient only |
| Challenge Phrases | Internal | Plaintext | 90 seconds |
| Auth Logs | Audit | Redacted | 90 days |
| User PII (name, email) | Personal | Database | User-controlled |
| JWT Tokens | Credential | Not stored | Token expiry |

### Log Redaction

All logs automatically redact sensitive data:

```python
REDACTED_PATTERNS = [
    # Credentials
    ("password", "[REDACTED]"),
    ("secret", "[REDACTED]"),
    ("token", "[REDACTED]"),
    ("api_key", "[REDACTED]"),
    
    # PII
    ("email", "[EMAIL_REDACTED]"),
    ("phone", "[PHONE_REDACTED]"),
    ("ssn", "[SSN_REDACTED]"),
    
    # Biometric
    ("embedding", "[EMBEDDING_REDACTED]"),
    ("voiceprint", "[VOICEPRINT_REDACTED]"),
]
```

### Consent Management

```
+------------------------------------------------------------------+
|                    CONSENT RECORD                                 |
+------------------------------------------------------------------+
| id: UUID                                                          |
| user_id: FK                                                       |
| tenant_id: string                                                 |
| consent_type: "biometric_enrollment" | "data_processing"          |
| consent_version: "1.0"                                            |
| granted_at: timestamp                                             |
| withdrawn_at: timestamp | null                                    |
| ip_address_hash: SHA256 (not raw IP)                              |
| user_agent_hash: SHA256 (not raw UA)                              |
+------------------------------------------------------------------+

Consent Required For:
  - Voice enrollment (biometric data collection)
  - Voiceprint storage and processing
  - Cross-session authentication
  
Withdrawal Rights:
  - User can withdraw consent at any time
  - Voiceprint is deleted on withdrawal
  - Auth logs retained for audit (redacted)
+------------------------------------------------------------------+
```

---

## API Security

### CORS Configuration

```python
# Strict CORS - NO wildcards allowed

ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Main frontend
    "http://localhost:3000",    # Banking Shield
    "http://localhost:5174",    # CallGuard
    "https://your-frontend.com" # Production
]

# Wildcard '*' is BLOCKED and logs a CRITICAL alert
if "*" in allowed_origins:
    logger.critical("SECURITY ALERT: Wildcard CORS blocked")
    allowed_origins = []  # Fail closed
```

### Request Validation

| Validation | Implementation |
|------------|---------------|
| Input Schema | Pydantic models with strict types |
| Audio Size | Max 10MB per request |
| Audio Duration | Min 50ms, Max 30s |
| Content-Type | multipart/form-data for audio |
| UUID Format | Validated before database query |
| SQL Injection | SQLAlchemy parameterized queries |

### Tenant Isolation

```sql
-- Row-Level Security (PostgreSQL)
CREATE POLICY tenant_isolation ON voiceprints
    USING (tenant_id = current_setting('app.tenant_id'));

-- Every query automatically filtered by tenant
SELECT * FROM voiceprints;
-- Becomes: SELECT * FROM voiceprints WHERE tenant_id = 'current_tenant';
```

---

## Threat Model

### Attack Vectors & Mitigations

| Attack | Risk | Mitigation | Residual Risk |
|--------|------|------------|---------------|
| **AI Voice Cloning** | HIGH | Wav2Vec2 deepfake detector | Modern TTS may evade |
| **Replay Attack** | HIGH | Single-use tokens, phrase verification | None (mitigated) |
| **Voice Recording** | HIGH | Dynamic challenge phrases | None (mitigated) |
| **Impersonation** | HIGH | Speaker embedding comparison | Twin/family voices |
| **Brute Force** | MEDIUM | Rate limiting, token expiry | Distributed attacks |
| **Token Forgery** | HIGH | HMAC-SHA256 signature | None (mitigated) |
| **Voiceprint Theft** | HIGH | AES-256-GCM encryption | Key compromise |
| **Cross-Tenant Access** | HIGH | Row-Level Security | RLS bypass bugs |
| **Social Engineering** | MEDIUM | VR transcript analysis | Novel techniques |
| **Vishing** | MEDIUM | 10 risk indicators + hard negatives | Sophisticated scripts |

### Known Limitations

| Limitation | Risk Level | Mitigation Plan |
|------------|------------|-----------------|
| Modern TTS (ElevenLabs, VALL-E) | MEDIUM | Model fine-tuning roadmap |
| Twin/family voice similarity | LOW | Step-up authentication |
| Noise sensitivity | LOW | Recording guidelines |
| Adversarial audio | MEDIUM | Research ongoing |

---

## Compliance & Audit

### Audit Trail

```
+------------------------------------------------------------------+
|                    AUTH LOG RECORD                                |
+------------------------------------------------------------------+
| id: UUID                                                          |
| user_id: FK                                                       |
| challenge_id: FK                                                  |
| decision: APPROVE | DENY | STEP_UP | REVIEW | UNAVAILABLE         |
| risk_level: LOW | MEDIUM | HIGH | CRITICAL                        |
| gate_blocked: AD | ASR | SV | null                                |
| created_at: timestamp                                             |
| request_id: correlation ID                                        |
+------------------------------------------------------------------+

Note: Raw scores (l2_confidence, l1_score) NOT in public response
      Stored in logs for forensic analysis only
+------------------------------------------------------------------+
```

### Model Registry

```
+------------------------------------------------------------------+
|                    MODEL REGISTRY RECORD                          |
+------------------------------------------------------------------+
| id: UUID                                                          |
| model_name: aaa-sv | aaa-ad | aaa-asr | aaa-vr                    |
| model_version: semantic version                                   |
| checkpoint_path: local path                                       |
| checkpoint_sha256: integrity hash                                 |
| status: active | quarantined | deprecated                         |
| deployed_at: timestamp                                            |
| deployed_by: admin ID                                             |
| metrics_json: evaluation metrics                                  |
+------------------------------------------------------------------+

Quarantine Process:
  1. Mark model as "quarantined" in registry
  2. System falls back to previous active version
  3. Decision: UNAVAILABLE if no fallback
  4. Audit log generated
+------------------------------------------------------------------+
```

### Voiceprint History

```
+------------------------------------------------------------------+
|                    VOICEPRINT HISTORY RECORD                      |
+------------------------------------------------------------------+
| id: UUID                                                          |
| voiceprint_id: FK                                                 |
| user_id: FK                                                       |
| tenant_id: string                                                 |
| action: created | updated | revoked | restored                    |
| sample_count_before: int                                          |
| sample_count_after: int                                           |
| embedding_hash: SHA256 (for integrity, not the actual embedding)  |
| reason: text                                                      |
| actor_id: who made the change                                     |
| created_at: timestamp                                             |
+------------------------------------------------------------------+
```

---

## Deployment Security

### Required Configuration

```bash
# These MUST be set in production

# Strong secrets (64+ hex characters recommended)
AAA_JWT_SECRET=<cryptographically secure, 32+ chars>
L3_HMAC_SECRET=<cryptographically secure, 32+ chars>
VOICEPRINT_ENCRYPTION_KEY=<cryptographically secure, 32+ chars>

# Strict CORS
ALLOWED_ORIGINS=https://your-frontend.com

# Production database (NOT SQLite)
DATABASE_URL=postgresql://...

# Disable debug
DEBUG=false
```

### Security Checklist

- [ ] HTTPS enforced (TLS 1.3)
- [ ] Strong secrets generated and set
- [ ] CORS origins explicitly listed (no wildcards)
- [ ] PostgreSQL with connection encryption
- [ ] Rate limiting configured
- [ ] Log redaction enabled
- [ ] Audit logging enabled
- [ ] Model checksums verified
- [ ] Backup/restore tested
- [ ] Incident response plan documented

### Reverse Proxy Configuration

```nginx
# Example Nginx configuration

server {
    listen 443 ssl http2;
    server_name api.yoursite.com;

    # TLS 1.3 only
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /v1/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8000;
    }
}
```

---

## Incident Response

### Response Procedure

1. **Detection:** Monitor for anomalies
   - Unusual rate of DENY decisions
   - Spike in STEP_UP/REVIEW outcomes
   - Failed token validations
   - Cross-tenant access attempts

2. **Containment:**
   - Quarantine affected models
   - Revoke compromised tokens
   - Block suspicious IPs

3. **Investigation:**
   - Review auth logs
   - Check voiceprint history
   - Analyze VR indicators

4. **Recovery:**
   - Restore from backup if needed
   - Re-enroll affected users
   - Update security measures

5. **Post-Incident:**
   - Document incident
   - Update threat model
   - Implement improvements

### Emergency Contacts

Document your security team contacts here.

---

**Security Policy Version:** 2.0  
**Last Updated:** November 2026
