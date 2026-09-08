"""
ORM Models - Navadeep
Matches docs/DB_SCHEMA.sql exactly
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    email = Column(Text, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    voiceprints = relationship("Voiceprint", back_populates="user")
    challenges = relationship("Challenge", back_populates="user")
    auth_logs = relationship("AuthLog", back_populates="user")


class Voiceprint(Base):
    __tablename__ = "voiceprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    embedding = Column(ARRAY(Float))  # 192-dim float array
    sample_count = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="voiceprints")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    phrase = Column(Text)
    token = Column(Text)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="challenges")
    auth_logs = relationship("AuthLog", back_populates="challenge")


class AuthLog(Base):
    __tablename__ = "auth_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id"))
    l2_label = Column(Text)
    l2_confidence = Column(Float)
    l1_score = Column(Float)
    result = Column(Text)
    layer_blocked = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="auth_logs")
    challenge = relationship("Challenge", back_populates="auth_logs")
