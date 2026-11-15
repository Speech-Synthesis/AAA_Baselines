"""
ORM Models - Navadeep
Database-agnostic models supporting both SQLite and PostgreSQL
"""

import json
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .db import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses String(36) for SQLite and native UUID for PostgreSQL.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        return value


class JSONEncodedList(TypeDecorator):
    """Stores a list as a JSON-encoded string.
    Works with both SQLite and PostgreSQL.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    email = Column(Text, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    voiceprints = relationship("Voiceprint", back_populates="user")
    challenges = relationship("Challenge", back_populates="user")
    auth_logs = relationship("AuthLog", back_populates="user")


class Voiceprint(Base):
    __tablename__ = "voiceprints"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    embedding = Column(JSONEncodedList)  # 192-dim float array stored as JSON
    sample_count = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="voiceprints")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    phrase = Column(Text)
    token = Column(Text, unique=True, index=True)  # Indexed for fast lookup
    signature = Column(Text)  # HMAC signature for verification
    payload = Column(Text)  # Raw signed payload
    expires_at = Column(DateTime, index=True)  # Indexed for cleanup queries
    used = Column(Boolean, default=False, index=True)  # Indexed for filtering
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="challenges")
    auth_logs = relationship("AuthLog", back_populates="challenge")


class AuthLog(Base):
    __tablename__ = "auth_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    challenge_id = Column(GUID(), ForeignKey("challenges.id"))
    l2_label = Column(Text)
    l2_confidence = Column(Float)
    l1_score = Column(Float)
    result = Column(Text)
    layer_blocked = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="auth_logs")
    challenge = relationship("Challenge", back_populates="auth_logs")


class ConsentRecord(Base):
    """
    Consent tracking per DATA_SECURITY.md §5.
    Records user consent for biometric data collection and processing.
    """

    __tablename__ = "consent_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    consent_type = Column(String(64), nullable=False)  # biometric_enrollment, data_processing
    consent_version = Column(String(32), nullable=False)  # Policy version consented to
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    withdrawn_at = Column(DateTime, nullable=True)
    ip_address_hash = Column(String(64), nullable=True)  # Hashed, not raw IP
    user_agent_hash = Column(String(64), nullable=True)

    user = relationship("User", backref="consent_records")


class VoiceprintHistory(Base):
    """
    Voiceprint change history per DATA_SECURITY.md §6.
    Tracks all voiceprint updates for audit and rollback capability.
    """

    __tablename__ = "voiceprint_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    voiceprint_id = Column(GUID(), ForeignKey("voiceprints.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # created, updated, revoked, restored
    sample_count_before = Column(Integer, nullable=True)
    sample_count_after = Column(Integer, nullable=True)
    embedding_hash = Column(String(64), nullable=True)  # SHA256 of embedding for integrity
    reason = Column(Text, nullable=True)  # Reason for change
    actor_id = Column(String(64), nullable=True)  # Who made the change (user, system, admin)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    voiceprint = relationship("Voiceprint", backref="history")
    user = relationship("User", backref="voiceprint_history")


class ModelRegistry(Base):
    """
    Model registry per DATA_SECURITY.md §7.
    Tracks deployed model versions, checksums, and status.
    """

    __tablename__ = "model_registry"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(128), nullable=False, index=True)  # aaa-sv, aaa-ad, aaa-asr, aaa-vr
    model_version = Column(String(64), nullable=False)
    checkpoint_path = Column(Text, nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="active")  # active, quarantined, deprecated
    deployed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deployed_by = Column(String(64), nullable=True)
    metrics_json = Column(Text, nullable=True)  # Evaluation metrics as JSON
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
