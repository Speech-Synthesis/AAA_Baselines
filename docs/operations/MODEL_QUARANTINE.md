# AAA Engine - Model Quarantine Procedure

Per DATA_SECURITY.md §7, this document defines the model quarantine procedure for compromised, degraded, or untrusted model checkpoints.

## 1. Overview

Model quarantine is triggered when:
- Evaluation metrics fall below acceptance thresholds
- Checkpoint integrity verification fails (SHA256 mismatch)
- Anomalous behavior detected in production
- Security vulnerability identified in model weights
- Audit reveals training data contamination

## 2. Quarantine States

| State | Description | API Behavior |
|-------|-------------|--------------|
| `active` | Model is in production use | Normal operation |
| `quarantined` | Model isolated, not serving | Returns UNAVAILABLE |
| `deprecated` | Scheduled for removal | Warning in logs |
| `archived` | Removed from production | Not loadable |

## 3. Quarantine Triggers

### 3.1 Automatic Triggers

```python
# In app/core/model_monitor.py

QUARANTINE_THRESHOLDS = {
    "aaa-sv": {
        "min_eer": 0.05,      # EER > 5% triggers quarantine
        "min_tar_at_1pct_far": 0.95,  # TAR@1%FAR < 95% triggers
    },
    "aaa-ad": {
        "min_auc": 0.95,      # AUC < 95% triggers quarantine
        "max_eer": 0.02,      # EER > 2% triggers quarantine
    },
    "aaa-asr": {
        "min_accuracy": 0.98, # Exact match < 98% triggers
    },
    "aaa-vr": {
        "min_precision": 0.90,  # Precision < 90% triggers
        "min_recall": 0.85,     # Recall < 85% triggers
    },
}

def check_model_health(model_name: str, metrics: dict) -> bool:
    """Returns False if model should be quarantined."""
    thresholds = QUARANTINE_THRESHOLDS.get(model_name, {})
    for metric, threshold in thresholds.items():
        if metric.startswith("min_") and metrics.get(metric[4:], 1.0) < threshold:
            return False
        if metric.startswith("max_") and metrics.get(metric[4:], 0.0) > threshold:
            return False
    return True
```

### 3.2 Manual Triggers

```bash
# Quarantine a model immediately
python -m app.cli quarantine-model --model aaa-sv --reason "EER degradation detected"

# Or via API (admin only)
curl -X POST http://localhost:8000/admin/models/aaa-sv/quarantine \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Security audit finding #123"}'
```

## 4. Quarantine Procedure

### Step 1: Detection and Alert

```python
# app/core/model_monitor.py
import logging
from app.models import ModelRegistry

logger = logging.getLogger("aaa_engine.model_monitor")

def quarantine_model(model_name: str, reason: str, db_session) -> None:
    """Quarantine a model and update registry."""
    
    # Update model status in registry
    model = db_session.query(ModelRegistry).filter(
        ModelRegistry.model_name == model_name,
        ModelRegistry.status == "active"
    ).first()
    
    if not model:
        raise ValueError(f"No active model found: {model_name}")
    
    model.status = "quarantined"
    model.notes = f"Quarantined: {reason}"
    model.updated_at = datetime.utcnow()
    
    db_session.commit()
    
    # Log security event
    logger.critical(
        f"MODEL_QUARANTINED: {model_name} - {reason}",
        extra={
            "model_name": model_name,
            "model_version": model.model_version,
            "reason": reason,
            "event_type": "security",
        }
    )
    
    # Send alerts
    send_pagerduty_alert(f"AAA Model Quarantined: {model_name}")
    send_slack_notification(f"⚠️ Model {model_name} quarantined: {reason}")
```

### Step 2: Isolate Model

```bash
#!/bin/bash
# scripts/quarantine_model.sh

MODEL_NAME=$1
REASON=$2
DATE=$(date +%Y%m%d_%H%M%S)

# 1. Move checkpoint to quarantine directory
mkdir -p /opt/aaa-engine/quarantine/${MODEL_NAME}
mv /opt/aaa-engine/models/${MODEL_NAME}/checkpoint.pt \
   /opt/aaa-engine/quarantine/${MODEL_NAME}/checkpoint_${DATE}.pt

# 2. Create quarantine manifest
cat > /opt/aaa-engine/quarantine/${MODEL_NAME}/manifest_${DATE}.json <<EOF
{
  "model_name": "${MODEL_NAME}",
  "quarantine_date": "$(date -Iseconds)",
  "reason": "${REASON}",
  "original_path": "/opt/aaa-engine/models/${MODEL_NAME}/checkpoint.pt",
  "quarantine_by": "$(whoami)"
}
EOF

# 3. Update model registry
python -c "
from app.db import SessionLocal
from app.models import ModelRegistry
db = SessionLocal()
model = db.query(ModelRegistry).filter(
    ModelRegistry.model_name == '${MODEL_NAME}',
    ModelRegistry.status == 'active'
).first()
if model:
    model.status = 'quarantined'
    db.commit()
    print(f'Model {model.model_name} quarantined')
"

# 4. Restart AAA Engine to unload model
systemctl restart aaa-engine

# 5. Verify model is not loaded
sleep 5
curl -s http://localhost:8000/v1/ready | jq ".checks.models.${MODEL_NAME//-/_}"
```

### Step 3: Activate Fallback

```python
# app/core/model_fallback.py

FALLBACK_MODELS = {
    "aaa-sv": "aaa-sv-baseline-v0",  # Conservative baseline
    "aaa-ad": "aaa-ad-baseline-v0",
    "aaa-asr": None,  # No fallback - return UNAVAILABLE
    "aaa-vr": "aaa-vr-rules-only",   # Pattern-based fallback
}

def get_active_model(model_name: str, db_session) -> str | None:
    """Get active model, falling back if primary is quarantined."""
    
    primary = db_session.query(ModelRegistry).filter(
        ModelRegistry.model_name == model_name,
        ModelRegistry.status == "active"
    ).first()
    
    if primary:
        return primary.checkpoint_path
    
    # Check for fallback
    fallback_name = FALLBACK_MODELS.get(model_name)
    if fallback_name:
        fallback = db_session.query(ModelRegistry).filter(
            ModelRegistry.model_name == fallback_name,
            ModelRegistry.status == "active"
        ).first()
        if fallback:
            logger.warning(f"Using fallback model: {fallback_name}")
            return fallback.checkpoint_path
    
    return None  # Model unavailable
```

### Step 4: Investigation

Document investigation in quarantine folder:

```markdown
# /opt/aaa-engine/quarantine/aaa-sv/investigation_20261115.md

## Investigation Summary

**Model**: aaa-sv-b1-v1.0
**Quarantine Date**: 2026-11-15
**Reason**: EER increased from 2.1% to 5.8%

## Root Cause Analysis

1. **Data**: Training data contamination from batch #42
2. **Training**: Early stopping triggered too late
3. **Evaluation**: Test set overlap with training

## Remediation

1. Remove contaminated data batch
2. Retrain from clean checkpoint
3. Update evaluation pipeline

## Resolution

- [ ] Root cause identified
- [ ] Remediation plan approved
- [ ] New model trained
- [ ] New model evaluated
- [ ] New model deployed
- [ ] Quarantine lifted
```

## 5. Restore from Quarantine

```bash
#!/bin/bash
# scripts/restore_quarantined_model.sh

MODEL_NAME=$1
QUARANTINE_DATE=$2

# 1. Verify model integrity
QUARANTINE_PATH="/opt/aaa-engine/quarantine/${MODEL_NAME}/checkpoint_${QUARANTINE_DATE}.pt"
sha256sum -c "${QUARANTINE_PATH}.sha256"

# 2. Run evaluation
python -m app.cli evaluate-model \
  --checkpoint $QUARANTINE_PATH \
  --output /tmp/eval_${MODEL_NAME}_${QUARANTINE_DATE}.json

# 3. Verify metrics pass thresholds
python -c "
import json
with open('/tmp/eval_${MODEL_NAME}_${QUARANTINE_DATE}.json') as f:
    metrics = json.load(f)
# Check against thresholds
print('Metrics:', metrics)
"

# 4. Restore to active (requires approval)
read -p "Approve restoration? (yes/no): " approval
if [ "$approval" == "yes" ]; then
    cp $QUARANTINE_PATH /opt/aaa-engine/models/${MODEL_NAME}/checkpoint.pt
    
    python -c "
from app.db import SessionLocal
from app.models import ModelRegistry
db = SessionLocal()
model = db.query(ModelRegistry).filter(
    ModelRegistry.model_name == '${MODEL_NAME}'
).order_by(ModelRegistry.updated_at.desc()).first()
model.status = 'active'
model.notes = 'Restored from quarantine after remediation'
db.commit()
"
    
    systemctl restart aaa-engine
    echo "Model restored"
fi
```

## 6. API Behavior During Quarantine

When a model is quarantined:

```python
# In policy engine
if not model_available("aaa-sv"):
    return PolicyOutput(
        decision=Decision.UNAVAILABLE,
        reason_public="SERVICE_UNAVAILABLE",
        reason_internal="Model aaa-sv is quarantined",
    )
```

The `/v1/ready` endpoint will show:

```json
{
  "status": "not_ready",
  "checks": {
    "models": {
      "speaker_verification": "unavailable",
      "deepfake_detection": "ok",
      "asr": "ok",
      "vishing_risk": "ok"
    }
  }
}
```

## 7. Audit Trail

All quarantine events are logged:

```json
{
  "timestamp": "2026-11-15T10:00:00Z",
  "event": "MODEL_QUARANTINE",
  "model_name": "aaa-sv",
  "model_version": "b1-v1.0",
  "reason": "EER degradation",
  "action": "quarantined",
  "actor": "model_monitor_daemon"
}
```

---

Last Updated: 2026-11-15
Author: AAA Engine Team
