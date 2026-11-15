"""
Database configuration - Navadeep
SQLAlchemy engine and session management with production-ready pooling.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

logger = logging.getLogger("aaa_engine.db")

# Load .env from project root (parent of backend/)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aaa_engine.db")

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"


def create_db_engine() -> Engine:
    """
    Create database engine with appropriate configuration.

    SQLite: Uses StaticPool for thread safety
    PostgreSQL: Uses QueuePool with connection pooling
    """
    is_sqlite = DATABASE_URL.startswith("sqlite")

    if is_sqlite:
        # SQLite configuration
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Single connection for SQLite
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
        logger.info("Created SQLite engine (StaticPool)")
    else:
        # PostgreSQL configuration with connection pooling
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=POOL_PRE_PING,  # Verify connections before use
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
        logger.info(
            f"Created PostgreSQL engine (pool_size={POOL_SIZE}, "
            f"max_overflow={MAX_OVERFLOW}, pre_ping={POOL_PRE_PING})"
        )

    return engine


# Create engine with fallback
try:
    engine = create_db_engine()
except Exception as e:
    logger.warning(f"Failed to create engine with {DATABASE_URL}: {e}")
    logger.warning("Falling back to SQLite")
    DATABASE_URL = "sqlite:///./aaa_engine.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get DB session.

    Yields:
        SQLAlchemy Session instance
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_pool_status() -> dict:
    """
    Get current connection pool status for health checks.

    Returns:
        dict with pool statistics (PostgreSQL only)
    """
    if DATABASE_URL.startswith("sqlite"):
        return {"type": "sqlite", "pooled": False}

    pool = engine.pool
    return {
        "type": "postgresql",
        "pooled": True,
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, "invalidatedcount") else 0,
    }
