"""
Pytest Configuration
====================

Shared fixtures and configuration.
"""

import pytest

# =============================================================================
# Async HTTP Client Fixtures (for GDPR and API tests)
# =============================================================================


@pytest.fixture
async def client():
    """
    Async HTTP client for testing FastAPI endpoints.

    Uses httpx.AsyncClient with ASGITransport for the main FastAPI app.
    """
    import httpx

    from main_enterprise import app

    # Use ASGITransport for httpx >= 0.27
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(jwt_manager):
    """
    Authorization headers with a valid JWT token for a regular user.

    Returns headers dict with Bearer token for user "test-user-123".
    """
    tokens = jwt_manager.create_token_pair(
        user_id="test-user-123",
        roles=["api_user"],
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def admin_headers(jwt_manager):
    """
    Authorization headers with a valid JWT token for an admin user.

    Returns headers dict with Bearer token for user "admin-user-456"
    with admin privileges.
    """
    tokens = jwt_manager.create_token_pair(
        user_id="admin-user-456",
        roles=["admin", "api_user"],
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def tool_registry():
    """Fresh tool registry for each test."""
    from runtime.tools import ToolRegistry

    return ToolRegistry()


@pytest.fixture
def tool_context():
    """Default tool call context."""
    from runtime.tools import ToolCallContext

    return ToolCallContext(
        request_id="test-request",
        user_id="test-user",
    )


@pytest.fixture
def encryption():
    """AES-256-GCM encryption instance."""
    from security.aes256_gcm_encryption import AESGCMEncryption

    return AESGCMEncryption()


@pytest.fixture
def jwt_manager():
    """JWT manager instance - uses the same instance as the app."""
    from security.jwt_oauth2_auth import jwt_manager as _jwt_manager

    return _jwt_manager


@pytest.fixture
def brand_kit():
    """Default SkyyRose brand kit."""
    from wordpress.elementor import SKYYROSE_BRAND_KIT

    return SKYYROSE_BRAND_KIT


@pytest.fixture
def elementor_builder():
    """Elementor builder instance."""
    from wordpress.elementor import ElementorBuilder

    return ElementorBuilder()


# Markers
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require external services)"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
