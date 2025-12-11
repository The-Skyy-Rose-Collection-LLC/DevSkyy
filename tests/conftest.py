"""
Test Configuration
==================

Pytest fixtures and configuration for DevSkyy test suite.

Dependencies:
- pytest==7.4.3 (PyPI verified)
- pytest-asyncio==0.21.1 (PyPI verified)
- httpx==0.25.2 (PyPI verified)
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests")


# =============================================================================
# Event Loop
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Application Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create test application"""
    from main_enterprise import app

    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def test_user_data() -> dict:
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecureP@ssw0rd123!",
        "role": "developer",
    }


@pytest.fixture
def admin_user_data() -> dict:
    """Admin user data"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminP@ssw0rd123!",
        "role": "admin",
    }


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, test_user_data: dict) -> str:
    """Get authentication token"""
    from security.jwt_oauth2_auth import auth_manager

    # Create token directly for testing
    token = auth_manager.create_access_token(
        user_id="test_user_001",
        username=test_user_data["username"],
        role=test_user_data["role"],
    )
    return token.access_token


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user_data: dict) -> str:
    """Get admin authentication token"""
    from security.jwt_oauth2_auth import auth_manager

    token = auth_manager.create_access_token(
        user_id="admin_001", username=admin_user_data["username"], role="admin"
    )
    return token.access_token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Get admin auth headers"""
    return {"Authorization": f"Bearer {admin_token}"}


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    from database import DatabaseConfig, db_manager

    # Use in-memory SQLite for tests
    config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:")
    await db_manager.initialize(config)

    async with db_manager.session() as session:
        yield session

    await db_manager.close()


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_product() -> dict:
    """Sample product data"""
    return {
        "sku": "SR-TEST-001",
        "name": "Test Rose Gold Hoodie",
        "description": "Premium test product",
        "price": 189.99,
        "quantity": 50,
        "category": "hoodies",
        "collection": "BLACK ROSE",
    }


@pytest.fixture
def sample_order() -> dict:
    """Sample order data"""
    return {
        "order_number": "ORD-TEST-001",
        "user_id": "test_user_001",
        "status": "pending",
        "subtotal": 189.99,
        "tax": 15.20,
        "shipping": 10.00,
        "total": 215.19,
        "currency": "USD",
    }


# =============================================================================
# Encryption Fixtures
# =============================================================================


@pytest.fixture
def encryption_key() -> str:
    """Test encryption key"""
    return "test_encryption_key_32bytes!!"


@pytest.fixture
def sample_pii_data() -> dict:
    """Sample PII data for encryption tests"""
    return {
        "email": "customer@example.com",
        "ssn": "123-45-6789",
        "credit_card": "4111111111111111",
        "phone": "555-123-4567",
        "address": "123 Test St, Oakland, CA 94610",
    }


# =============================================================================
# Webhook Fixtures
# =============================================================================


@pytest.fixture
def webhook_endpoint() -> dict:
    """Test webhook endpoint"""
    return {
        "url": "https://webhook.test/callback",
        "events": ["order.created", "order.updated"],
        "secret": "whsec_test_secret_key",
    }


# =============================================================================
# Agent Fixtures
# =============================================================================


@pytest.fixture
def agent_task() -> dict:
    """Sample agent task"""
    return {
        "agent_name": "instagram_agent",
        "action": "post",
        "parameters": {"content": "Test post content", "hashtags": ["test", "devskyy"]},
        "priority": "normal",
    }


# =============================================================================
# Utility Functions
# =============================================================================


def assert_valid_uuid(value: str) -> None:
    """Assert value is valid UUID format"""
    import re

    uuid_pattern = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$",
        re.IGNORECASE,
    )
    assert uuid_pattern.match(value), f"Invalid UUID: {value}"


def assert_valid_timestamp(value: str) -> None:
    """Assert value is valid ISO timestamp"""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Invalid timestamp: {value}")
