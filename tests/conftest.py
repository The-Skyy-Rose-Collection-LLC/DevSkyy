"""
Global pytest configuration and fixtures for DevSkyy test suite.

This conftest provides:
- Test environment setup
- Common fixtures (db, client, auth)
- Mock configurations for external services
- Test utilities
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables BEFORE any imports
os.environ["ENVIRONMENT"] = "testing"  # UnifiedConfig expects "testing" not "test"
os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-long!!"
os.environ["SECRET_KEY"] = "test-secret-key-32-characters-long!!"
os.environ["DATABASE_URL"] = "sqlite:///./test_devskyy.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Test DB
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["DISABLE_AUTH"] = "false"  # Test auth in tests

# Prevent actual API calls during tests
os.environ["MOCK_EXTERNAL_APIS"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///./test_devskyy.db",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create fresh database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create FastAPI test client."""
    # Import main app
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API calls."""
    with patch("anthropic.Anthropic") as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mocked Claude response")]
        mock_client.messages.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mocked GPT response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis connections."""
    with patch("redis.Redis") as mock:
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = True
        mock_client.ping.return_value = True
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch connections."""
    with patch("elasticsearch.Elasticsearch") as mock:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.index.return_value = {"result": "created"}
        mock_client.search.return_value = {"hits": {"hits": []}}
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate valid JWT auth headers for testing."""
    from security.jwt_auth import create_access_token

    token = create_access_token(
        data={"sub": "test-user", "role": "Admin"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user():
    """Mock admin user for testing."""
    return {
        "username": "admin@test.com",
        "email": "admin@test.com",
        "role": "Admin",
        "user_id": "test-admin-123",
    }


@pytest.fixture
def test_agent_config():
    """Standard agent configuration for tests."""
    return {
        "name": "test_agent",
        "type": "backend",
        "enabled": True,
        "config": {
            "max_iterations": 5,
            "timeout": 30,
        },
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test."""
    yield
    # Cleanup after test
    if os.path.exists("./test_devskyy.db"):
        try:
            os.remove("./test_devskyy.db")
        except Exception:
            pass


@pytest.fixture
def mock_all_external_services(
    mock_anthropic,
    mock_openai,
    mock_redis,
    mock_elasticsearch,
):
    """Convenience fixture to mock all external services at once."""
    return {
        "anthropic": mock_anthropic,
        "openai": mock_openai,
        "redis": mock_redis,
        "elasticsearch": mock_elasticsearch,
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
