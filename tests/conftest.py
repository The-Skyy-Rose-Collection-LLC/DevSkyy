"""
DevSkyy Enterprise - Test Fixtures and Configuration
Provides reusable fixtures for unit, integration, and API tests
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import main app
from main import app

# Import database models
from models_sqlalchemy import Base

# Import security modules
from security.jwt_auth import create_access_token, create_refresh_token

# ============================================================================
# Pytest Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Create FastAPI test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def async_test_client() -> AsyncGenerator:
    """Create async FastAPI test client"""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_user_data():
    """Sample test user data"""
    return {
        "user_id": "test_user_001",
        "email": "test@devskyy.com",
        "username": "testuser",
        "full_name": "Test User",
        "role": "admin",
        "permissions": ["read", "write", "admin"],
    }


@pytest.fixture(scope="function")
def test_access_token(test_user_data):
    """Generate test JWT access token"""
    return create_access_token(data=test_user_data)


@pytest.fixture(scope="function")
def test_refresh_token(test_user_data):
    """Generate test JWT refresh token"""
    return create_refresh_token(data=test_user_data)


@pytest.fixture(scope="function")
def auth_headers(test_access_token):
    """Generate authorization headers with test token"""
    return {"Authorization": f"Bearer {test_access_token}"}


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def mock_ai_response():
    """Mock AI API response"""
    return {
        "response": "This is a test AI response",
        "model": "claude-3-5-sonnet-20241022",
        "usage": {"input_tokens": 10, "output_tokens": 25},
    }


@pytest.fixture(scope="function")
def mock_project_data():
    """Sample project data"""
    return {
        "project_id": "proj_test_001",
        "name": "Test Project",
        "description": "A test project for unit testing",
        "status": "active",
        "owner": "test_user_001",
    }


@pytest.fixture(scope="function")
def mock_agent_data():
    """Sample agent data"""
    return {
        "agent_id": "agent_test_001",
        "name": "Test Agent",
        "type": "autonomous",
        "capabilities": ["code_generation", "testing"],
        "status": "active",
    }


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "test_encryption_key_32_bytes_!!")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add any cleanup logic here


# ============================================================================
# Performance Testing Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance tests"""
    import time

    start_time = time.time()
    yield lambda: time.time() - start_time


# ============================================================================
# Mocking Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def mock_external_api(monkeypatch):
    """Mock external API calls"""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    def mock_get(*args, **kwargs):
        return MockResponse({"message": "Mock response"}, 200)

    def mock_post(*args, **kwargs):
        return MockResponse({"message": "Mock created"}, 201)

    import requests

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)


# ============================================================================
# Test Data Generators
# ============================================================================


@pytest.fixture(scope="function")
def generate_test_users():
    """Generate multiple test users"""

    def _generate(count=5):
        return [
            {
                "user_id": f"user_{i:03d}",
                "email": f"user{i}@test.com",
                "username": f"testuser{i}",
                "role": "user" if i % 2 == 0 else "admin",
            }
            for i in range(count)
        ]

    return _generate


# ============================================================================
# Pytest Hooks for Custom Behavior
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "security: Security tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Auto-mark tests based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
