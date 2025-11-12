"""
Smoke Test: Import Verification
Tests that all critical modules can be imported without errors.
This catches import-time failures early in the CI/CD pipeline.
"""

import pytest


@pytest.mark.smoke
def test_import_main():
    """Test that main application module imports successfully."""
    try:
        import main
        assert hasattr(main, 'app')
    except ImportError as e:
        pytest.fail(f"Failed to import main: {e}")


@pytest.mark.smoke
def test_import_database():
    """Test that database module imports successfully."""
    try:
        import database
    except ImportError as e:
        pytest.fail(f"Failed to import database: {e}")


@pytest.mark.smoke
def test_import_security():
    """Test that security modules import successfully."""
    try:
        from security import jwt_auth
        assert hasattr(jwt_auth, 'create_access_token')
    except ImportError as e:
        pytest.fail(f"Failed to import security.jwt_auth: {e}")


@pytest.mark.smoke
def test_import_models():
    """Test that SQLAlchemy models import successfully."""
    try:
        import models_sqlalchemy
    except ImportError as e:
        pytest.fail(f"Failed to import models_sqlalchemy: {e}")


@pytest.mark.smoke
def test_import_api_routes():
    """Test that API routes can be imported."""
    try:
        from api import agents, dashboard
    except ImportError as e:
        pytest.fail(f"Failed to import API routes: {e}")


@pytest.mark.smoke
def test_import_logger():
    """Test that logging configuration imports successfully."""
    try:
        import logger_config
    except ImportError as e:
        pytest.fail(f"Failed to import logger_config: {e}")


@pytest.mark.smoke
def test_import_error_handlers():
    """Test that error handlers import successfully."""
    try:
        import error_handlers
    except ImportError as e:
        pytest.fail(f"Failed to import error_handlers: {e}")


@pytest.mark.smoke
def test_critical_dependencies():
    """Test that critical third-party dependencies are available."""
    critical_modules = [
        'fastapi',
        'pydantic',
        'sqlalchemy',
        'pytest',
    ]
    
    missing_modules = []
    for module in critical_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        pytest.fail(f"Missing critical dependencies: {', '.join(missing_modules)}")


@pytest.mark.smoke
def test_agent_modules_structure():
    """Test that agent module structure is intact."""
    try:
        from agent.modules.backend import orchestrator, registry
        assert hasattr(orchestrator, 'Orchestrator')
        assert hasattr(registry, 'Registry')
    except ImportError as e:
        pytest.fail(f"Failed to import agent modules: {e}")
    except AttributeError as e:
        pytest.fail(f"Agent module structure broken: {e}")
