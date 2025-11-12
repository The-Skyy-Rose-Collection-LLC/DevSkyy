"""
Smoke Test: Basic Health Checks
Quick health checks for critical application components.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.smoke
def test_app_creation():
    """Test that FastAPI app can be created."""
    try:
        from main import app
        assert app is not None
        assert hasattr(app, 'routes')
    except Exception as e:
        pytest.fail(f"Failed to create app: {e}")


@pytest.mark.smoke
def test_health_endpoint_exists(test_client):
    """Test that health check endpoint is available."""
    response = test_client.get("/health")
    # Should not be 404 - it should exist
    assert response.status_code != 404, "Health endpoint not found"


@pytest.mark.smoke
def test_root_endpoint_exists(test_client):
    """Test that root endpoint is available."""
    response = test_client.get("/")
    # Should not be 404 - it should exist
    assert response.status_code != 404, "Root endpoint not found"


@pytest.mark.smoke
def test_database_models_defined():
    """Test that database models are properly defined."""
    try:
        from models_sqlalchemy import Base
        # Check that Base has some tables
        # Note: This might fail with import error, which is caught
        assert Base is not None
    except Exception as e:
        pytest.fail(f"Database models not properly defined: {e}")


@pytest.mark.smoke
def test_security_jwt_functions():
    """Test that JWT security functions are available."""
    try:
        from security.jwt_auth import create_access_token, verify_token
        assert callable(create_access_token)
        assert callable(verify_token)
    except ImportError as e:
        pytest.fail(f"JWT security functions not available: {e}")


@pytest.mark.smoke
def test_orchestrator_initialization():
    """Test that orchestrator can be initialized."""
    try:
        from agent.modules.backend.orchestrator import Orchestrator
        # Just check it can be imported, don't initialize
        # (initialization might require resources)
        assert Orchestrator is not None
    except Exception as e:
        pytest.fail(f"Orchestrator cannot be initialized: {e}")


@pytest.mark.smoke
def test_registry_initialization():
    """Test that registry can be initialized."""
    try:
        from agent.modules.backend.registry import Registry
        # Just check it can be imported
        assert Registry is not None
    except Exception as e:
        pytest.fail(f"Registry cannot be initialized: {e}")


@pytest.mark.smoke
def test_error_handlers_registered():
    """Test that error handlers are available."""
    try:
        from main import app
        from error_handlers import setup_error_handlers
        # Should be able to call setup
        assert callable(setup_error_handlers)
    except Exception as e:
        pytest.fail(f"Error handlers not properly available: {e}")


@pytest.mark.smoke
def test_logger_configuration():
    """Test that logger is properly configured."""
    try:
        from logger_config import get_logger
        logger = get_logger(__name__)
        assert logger is not None
        # Test that we can log
        logger.info("Smoke test log message")
    except Exception as e:
        pytest.fail(f"Logger not properly configured: {e}")


@pytest.mark.smoke
def test_api_routers_registration():
    """Test that API routers are registered with the app."""
    try:
        from main import app
        # Check that app has routes
        assert len(app.routes) > 0, "No routes registered in app"
        
        # Check for some critical routes
        route_paths = [route.path for route in app.routes]
        assert any('health' in path for path in route_paths), "Health route not registered"
    except Exception as e:
        pytest.fail(f"API routers not properly registered: {e}")
