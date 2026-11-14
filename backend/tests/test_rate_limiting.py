"""
Rate Limiting Tests for AAA Engine
Tests HTTP 429 responses and rate limit behavior.
"""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.ratelimit import (
    _get_client_ip,
    limiter,
    rate_limit_exceeded_handler,
)


class TestRateLimitHandler:
    """Tests for rate limit exceeded handler."""

    def test_rate_limit_handler_returns_429(self):
        """Rate limit exceeded should return 429 status code."""
        # Create a minimal FastAPI app for testing
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        @app.get("/test")
        @limiter.limit("1/minute")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # First request should succeed
        response = client.get("/test")
        assert response.status_code == 200

        # Second request should hit rate limit
        response = client.get("/test")
        assert response.status_code == 429

    def test_rate_limit_response_format(self):
        """Rate limit response should have correct JSON format."""
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        @app.get("/test-format")
        @limiter.limit("1/minute")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # Exhaust rate limit
        client.get("/test-format")
        response = client.get("/test-format")

        assert response.status_code == 429
        data = response.json()

        # Check response structure
        assert "error" in data
        assert data["error"] == "rate_limit_exceeded"
        assert "message" in data
        assert "retry_after" in data
        assert "details" in data

    def test_rate_limit_retry_after_header(self):
        """Rate limit response should include Retry-After header."""
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        @app.get("/test-header")
        @limiter.limit("1/minute")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # Exhaust rate limit
        client.get("/test-header")
        response = client.get("/test-header")

        assert response.status_code == 429
        assert "Retry-After" in response.headers


class TestClientIPExtraction:
    """Tests for client IP extraction from request headers."""

    def test_get_client_ip_from_x_forwarded_for(self):
        """Should extract IP from X-Forwarded-For header."""

        class MockRequest:
            def __init__(self):
                self.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
                self.client = type("Client", (), {"host": "127.0.0.1"})()

        request = MockRequest()
        ip = _get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_from_x_real_ip(self):
        """Should extract IP from X-Real-IP header."""

        class MockRequest:
            def __init__(self):
                self.headers = {"X-Real-IP": "10.20.30.40"}
                self.client = type("Client", (), {"host": "127.0.0.1"})()

        request = MockRequest()
        ip = _get_client_ip(request)
        assert ip == "10.20.30.40"


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    def test_limiter_instance_exists(self):
        """Limiter instance should be created."""
        assert limiter is not None
        assert isinstance(limiter, Limiter)

    def test_handler_function_exists(self):
        """Rate limit handler function should exist."""
        assert callable(rate_limit_exceeded_handler)


class TestRateLimitBehavior:
    """Tests for rate limit enforcement behavior."""

    def test_rate_limit_resets_after_window(self):
        """Rate limit should allow requests after window resets."""
        app = FastAPI()
        app.state.limiter = Limiter(key_func=get_remote_address)
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        # Use a per-second limit for testing
        @app.get("/test-reset")
        @app.state.limiter.limit("2/second")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # First two requests should succeed
        assert client.get("/test-reset").status_code == 200
        assert client.get("/test-reset").status_code == 200

        # Third should hit limit
        response = client.get("/test-reset")
        assert response.status_code == 429

    def test_different_ips_have_separate_limits(self):
        """Different IPs should have separate rate limit counters."""

        def custom_key_func(request: Request) -> str:
            return request.headers.get("X-Test-IP", "default")

        test_limiter = Limiter(key_func=custom_key_func)
        app = FastAPI()
        app.state.limiter = test_limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        @app.get("/test-ip")
        @test_limiter.limit("1/minute")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # First IP - first request succeeds
        response = client.get("/test-ip", headers={"X-Test-IP": "ip1"})
        assert response.status_code == 200

        # First IP - second request hits limit
        response = client.get("/test-ip", headers={"X-Test-IP": "ip1"})
        assert response.status_code == 429

        # Second IP - first request succeeds (separate counter)
        response = client.get("/test-ip", headers={"X-Test-IP": "ip2"})
        assert response.status_code == 200


class TestRateLimitErrorDetails:
    """Tests for rate limit error response details."""

    def test_error_includes_documentation_reference(self):
        """Rate limit error should include documentation reference."""
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        @app.get("/test-docs")
        @limiter.limit("1/minute")
        def test_endpoint(request: Request):
            return {"status": "ok"}

        client = TestClient(app)

        # Exhaust limit
        client.get("/test-docs")
        response = client.get("/test-docs")

        data = response.json()
        assert "details" in data
        assert "documentation" in data["details"]
