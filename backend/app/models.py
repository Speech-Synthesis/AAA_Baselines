"""
ORM Models - Navadeep
Database-agnostic models supporting both SQLite and PostgreSQL
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, TypeDecorator
from sqlalchemy.orm import relationship

from .db import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses String(36) for SQLite and native UUID for PostgreSQL.
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
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
    token = Column(Text)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

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
