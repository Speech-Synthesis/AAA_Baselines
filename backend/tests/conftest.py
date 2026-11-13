"""
Pytest Configuration and Fixtures
"""

import os
import sys

import pytest

# Add backend/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test environment BEFORE any imports
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_aaa_engine.db"
os.environ["L3_HMAC_SECRET"] = "test-hmac-secret-for-testing-only"


@pytest.fixture(scope="session")
def app():
    """Create FastAPI application for testing."""
    from app.main import app
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Import models to ensure they're registered with Base
    from app import models  # noqa: F401
    from app.db import Base, SessionLocal, engine

    # Drop and recreate all tables for fresh schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def reset_token_store():
    """Reset in-memory token store between tests."""
    from app.layer3_adaptive import _token_store
    _token_store.clear()
    yield
    _token_store.clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache to pick up test environment variables."""
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
