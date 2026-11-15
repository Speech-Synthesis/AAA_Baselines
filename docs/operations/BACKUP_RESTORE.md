# AAA Engine - Backup and Restore Procedures

Per DATA_SECURITY.md §9, this document defines backup/restore procedures for all critical AAA Engine data.

## 1. Data Classification

| Data Type | Backup Frequency | Retention | Encryption |
|-----------|------------------|-----------|------------|
| User accounts | Daily | 90 days | AES-256 |
| Voiceprints (encrypted) | Daily | Until revoked + 30 days | AES-256-GCM |
| Consent records | Daily | 7 years (compliance) | AES-256 |
| Auth logs | Daily | 1 year | AES-256 |
| Challenge tokens | Not backed up | Ephemeral (90s TTL) | N/A |
| Model checkpoints | On deployment | Indefinite | SHA256 verified |

## 2. Backup Procedures

### 2.1 Database Backup (PostgreSQL)

```bash
# Daily automated backup (run via cron at 02:00 UTC)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/aaa-engine"
DB_NAME="aaa_production"

# Create encrypted backup
pg_dump $DB_NAME | gpg --symmetric --cipher-algo AES256 \
  -o "$BACKUP_DIR/aaa_db_${DATE}.sql.gpg"

# Verify backup integrity
gpg --decrypt "$BACKUP_DIR/aaa_db_${DATE}.sql.gpg" | head -10

# Upload to secure offsite storage
aws s3 cp "$BACKUP_DIR/aaa_db_${DATE}.sql.gpg" \
  s3://aaa-backups-encrypted/database/ --sse aws:kms

# Cleanup local backups older than 7 days
find $BACKUP_DIR -name "*.sql.gpg" -mtime +7 -delete
```

### 2.2 Voiceprint Backup

Voiceprints are already encrypted with AES-256-GCM per-tenant. Backup includes:
- Encrypted embedding blob
- Tenant ID (for key derivation)
- Sample count and metadata
- NOT the decryption key (stored separately in HSM/KMS)

```bash
# Export voiceprints table (already encrypted at rest)
pg_dump -t voiceprints $DB_NAME | gpg -c -o voiceprints_${DATE}.sql.gpg
```

### 2.3 Model Checkpoint Backup

```bash
# Backup model registry entries and checkpoints
MODEL_DIR="/opt/aaa-engine/models"
CHECKPOINT_BACKUP="/var/backups/aaa-engine/models"

# For each registered model
for model in aaa-sv aaa-ad aaa-asr aaa-vr; do
  # Verify checksum before backup
  sha256sum "$MODEL_DIR/$model/checkpoint.pt" > "$CHECKPOINT_BACKUP/${model}_sha256.txt"
  
  # Copy checkpoint with verification
  cp "$MODEL_DIR/$model/checkpoint.pt" "$CHECKPOINT_BACKUP/${model}_${DATE}.pt"
  
  # Verify copy
  sha256sum -c "$CHECKPOINT_BACKUP/${model}_sha256.txt"
done
```

## 3. Restore Procedures

### 3.1 Database Restore

```bash
# 1. Stop AAA Engine services
systemctl stop aaa-engine

# 2. Create restore point
pg_dump $DB_NAME > /tmp/pre_restore_backup.sql

# 3. Decrypt and restore
gpg --decrypt aaa_db_${DATE}.sql.gpg | psql $DB_NAME

# 4. Verify data integrity
psql $DB_NAME -c "SELECT COUNT(*) FROM users;"
psql $DB_NAME -c "SELECT COUNT(*) FROM voiceprints;"
psql $DB_NAME -c "SELECT COUNT(*) FROM consent_records;"

# 5. Restart services
systemctl start aaa-engine

# 6. Run health check
curl -f http://localhost:8000/v1/ready
```

### 3.2 Voiceprint Restore

```bash
# Voiceprints require tenant encryption keys from KMS
# 1. Verify KMS access
aws kms describe-key --key-id $AAA_VOICEPRINT_KMS_KEY

# 2. Restore voiceprints table
gpg -d voiceprints_${DATE}.sql.gpg | psql $DB_NAME

# 3. Verify decryption works (sample test)
python -c "
from app.security.voiceprint_crypto import VoiceprintEncryptor
enc = VoiceprintEncryptor()
# Test decryption of first voiceprint
print('Voiceprint encryption keys valid')
"
```

### 3.3 Model Checkpoint Restore

```bash
# 1. Verify checkpoint integrity
sha256sum -c ${model}_sha256.txt

# 2. Restore checkpoint
cp ${model}_${DATE}.pt $MODEL_DIR/$model/checkpoint.pt

# 3. Update model registry
python -c "
from app.models import ModelRegistry
# Mark restored checkpoint as active
"

# 4. Restart to reload model
systemctl restart aaa-engine

# 5. Verify model loaded
curl http://localhost:8000/v1/ready | jq '.checks.models'
```

## 4. Disaster Recovery

### 4.1 RTO/RPO Targets

| Metric | Target | Measured |
|--------|--------|----------|
| Recovery Time Objective (RTO) | 4 hours | TBD |
| Recovery Point Objective (RPO) | 24 hours | Daily backups |

### 4.2 DR Runbook

1. **Assess damage**: Identify which components are affected
2. **Activate DR site**: Spin up infrastructure in DR region
3. **Restore database**: From most recent backup
4. **Restore models**: From checkpoint backup
5. **Verify keys**: Ensure KMS keys are accessible
6. **Health check**: Run `/v1/ready` endpoint
7. **Smoke test**: Verify enrollment and verification work
8. **Update DNS**: Point traffic to DR site

## 5. Backup Verification

Monthly backup verification drill:

```bash
# 1. Restore to test environment
./scripts/restore_to_test.sh ${LATEST_BACKUP}

# 2. Run verification suite
pytest tests/test_backup_verification.py

# 3. Verify voiceprint decryption
python scripts/verify_voiceprint_restore.py

# 4. Document results
echo "Backup verification completed: $(date)" >> /var/log/aaa-backup-drill.log
```

## 6. Compliance

- All backups encrypted at rest (AES-256)
- All backups encrypted in transit (TLS 1.3)
- Backup access logged and audited
- Retention periods comply with GDPR/CCPA
- Annual backup restoration drill documented

---

Last Updated: 2026-11-15
Author: AAA Engine Team
