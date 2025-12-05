"""
Fixtures for unit tests in the DevSkyy test suite.
"""

import pytest


@pytest.fixture
def test_user_data():
    """Test user data for JWT and authentication tests."""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "username": "testuser",
        "role": "Developer",
        "permissions": ["api:read", "api:write"],
    }


@pytest.fixture
def test_config():
    """Test configuration data."""
    return {
        "secret_key": "test-secret-key-32-characters-long!!",
        "database_url": "sqlite+aiosqlite:///./test.db",
        "environment": "testing",
    }


@pytest.fixture
def mock_agent_config():
    """Mock agent configuration for testing."""
    return {
        "agent_id": "test_agent_001",
        "agent_name": "TestAgent",
        "category": "content",
        "model": "gpt-4",
        "max_tokens": 4096,
        "temperature": 0.7,
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for model tests."""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "sku": "TEST-001",
        "category": "Test Category",
        "price": 99.99,
        "stock_quantity": 100,
        "tags": ["test", "sample"],
        "colors": ["red", "blue"],
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for model tests."""
    return {
        "email": "sample@example.com",
        "username": "sampleuser",
        "full_name": "Sample User",
        "hashed_password": "hashed_password_here",
        "role": "Developer",
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer data for model tests."""
    return {
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for model tests."""
    return {
        "order_number": "ORD-TEST-001",
        "customer_id": 1,
        "status": "pending",
        "total_amount": 199.99,
        "shipping_address": {"street": "123 Test St", "city": "Test City"},
    }


@pytest.fixture
def sample_agent_log_data():
    """Sample agent log data for model tests."""
    return {
        "agent_name": "TestAgent",
        "action": "test_action",
        "status": "success",
        "execution_time_ms": 100.5,
    }


@pytest.fixture
def sample_brand_asset_data():
    """Sample brand asset data for model tests."""
    return {
        "asset_type": "logo",
        "name": "Test Logo",
        "data": {"url": "https://example.com/logo.png"},
        "asset_metadata": {"version": "1.0"},
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for model tests."""
    return {
        "name": "Test Campaign",
        "campaign_type": "email",
        "status": "draft",
        "budget": 1000.00,
    }
