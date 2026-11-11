"""
Pytest Configuration and Fixtures
"""

import os
import sys
import pytest

# Add backend/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test environment
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_aaa_engine.db")


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
    from app.db import SessionLocal, engine, Base

    # Create all tables
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def reset_token_store():
    """Reset in-memory token store between tests."""
    from app.layer3_adaptive import _token_store
    _token_store.clear()
    yield
    _token_store.clear()
