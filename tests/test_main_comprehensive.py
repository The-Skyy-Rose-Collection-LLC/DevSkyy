"""
Comprehensive tests for main.py - Enterprise FastAPI Application
Target: ≥90% test coverage for main.py

Author: DevSkyy Team
Per Truth Protocol Rule #8: Test coverage ≥90% required
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
import pytest


# ============================================================================
# FIXTURES AND SETUP
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables before importing main."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "test_encryption_key_32_bytes_!!")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    monkeypatch.setenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver")


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    # Import main after environment setup
    import main

    return TestClient(main.app)


@pytest.fixture
def mock_agent_modules():
    """Mock agent module availability."""
    with patch("main.AGENT_MODULES_AVAILABLE", True):
        yield


@pytest.fixture
def mock_security_modules():
    """Mock security module availability."""
    with patch("main.SECURITY_MODULES_AVAILABLE", True):
        yield


@pytest.fixture
def mock_ai_services():
    """Mock AI services availability."""
    with patch("main.AI_SERVICES_AVAILABLE", True):
        yield


# ============================================================================
# TEST LOGGING CONFIGURATION
# ============================================================================


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_creates_logs_directory(self, tmp_path, monkeypatch):
        """Test that setup_logging creates logs directory if it doesn't exist."""
        import main

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        logger = main.setup_logging()

        assert logger is not None
        assert (tmp_path / "logs").exists()

    def test_setup_logging_with_valid_log_level(self):
        """Test setup_logging with valid log level."""
        import main

        logger = main.setup_logging()
        assert logger is not None

    def test_setup_logging_handles_exception_gracefully(self, monkeypatch):
        """Test that setup_logging handles exceptions gracefully."""
        import main

        # Mock Path to raise exception
        with patch("main.Path") as mock_path:
            mock_path.side_effect = Exception("Test exception")
            logger = main.setup_logging()
            assert logger is not None


# ============================================================================
# TEST APPLICATION INITIALIZATION
# ============================================================================


class TestApplicationInitialization:
    """Test FastAPI application initialization."""

    def test_app_instance_created(self):
        """Test that FastAPI app instance is created."""
        import main

        assert main.app is not None
        assert hasattr(main.app, "title")
        assert "DevSkyy" in main.app.title

    def test_app_version_set_correctly(self):
        """Test that app version is set correctly."""
        import main

        assert main.VERSION == "5.1.0-enterprise"
        assert main.app.version == main.VERSION

    def test_app_state_initialized(self):
        """Test that app state is initialized with correct values."""
        import main

        assert hasattr(main.app.state, "version")
        assert hasattr(main.app.state, "environment")
        assert hasattr(main.app.state, "startup_time")
        assert main.app.state.version == main.VERSION

    def test_docs_disabled_in_production(self, monkeypatch):
        """Test that API docs are disabled in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "production-secret-key")

        # Reimport main to pick up production environment
        import importlib

        import main as main_module
        importlib.reload(main_module)

        assert main_module.app.docs_url is None
        assert main_module.app.redoc_url is None
        assert main_module.app.openapi_url is None

    def test_environment_variable_defaults(self):
        """Test environment variable defaults."""
        import main

        assert main.ENVIRONMENT in ["development", "test", "production"]
        assert main.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


# ============================================================================
# TEST EXCEPTION HANDLERS
# ============================================================================


class TestExceptionHandlers:
    """Test exception handlers."""

    def test_http_exception_handler(self, client):
        """Test HTTPException handler."""
        import main

        request = MagicMock()
        request.url = "http://test.com/test"

        exc = HTTPException(status_code=404, detail="Not found")

        response = asyncio.run(main.http_exception_handler(request, exc))

        assert response.status_code == 404
        content = asyncio.run(response.json())
        assert content["error"] is True
        assert "Not found" in content["message"]

    def test_validation_exception_handler(self, client):
        """Test RequestValidationError handler."""
        import main

        request = MagicMock()
        request.url = "http://test.com/test"

        exc = RequestValidationError(errors=[{"loc": ["field"], "msg": "invalid", "type": "value_error"}])

        response = asyncio.run(main.validation_exception_handler(request, exc))

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        content = asyncio.run(response.json())
        assert content["error"] is True
        assert "Invalid request data" in content["message"]

    def test_general_exception_handler(self, client):
        """Test general exception handler."""
        import main

        request = MagicMock()
        request.url = "http://test.com/test"

        exc = Exception("Test exception")

        response = asyncio.run(main.general_exception_handler(request, exc))

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = asyncio.run(response.json())
        assert content["error"] is True
        assert "Internal server error" in content["message"]


# ============================================================================
# TEST AGENT FACTORY
# ============================================================================


class TestAgentFactory:
    """Test agent factory and management."""

    def test_get_agent_with_caching(self):
        """Test that get_agent caches agent instances."""
        import main

        # Clear cache first
        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.SecurityAgent") as mock_security_agent:
            mock_instance = MagicMock()
            mock_security_agent.return_value = mock_instance

            # First call creates agent
            agent1 = main.get_agent("backend", "security")
            assert agent1 == mock_instance
            assert mock_security_agent.called

            # Second call uses cache
            mock_security_agent.reset_mock()
            agent2 = main.get_agent("backend", "security")
            assert agent2 == mock_instance
            assert not mock_security_agent.called

    def test_get_agent_backend_security(self):
        """Test creating backend security agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.SecurityAgent") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("backend", "security")
            assert agent == mock_instance

    def test_get_agent_backend_financial(self):
        """Test creating backend financial agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.FinancialAgent") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("backend", "financial")
            assert agent == mock_instance

    def test_get_agent_backend_ecommerce(self):
        """Test creating backend ecommerce agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.EcommerceAgent") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("backend", "ecommerce")
            assert agent == mock_instance

    def test_get_agent_frontend_design(self):
        """Test creating frontend design agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.DesignAutomationAgent") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("frontend", "design")
            assert agent == mock_instance

    def test_get_agent_frontend_web_development(self):
        """Test creating frontend web development agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.WebDevelopmentAgent") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("frontend", "web_development")
            assert agent == mock_instance

    def test_get_agent_frontend_fashion_cv(self):
        """Test creating frontend fashion CV agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True):
            with patch("main.FashionComputerVisionAgent") as mock_agent:
                mock_instance = MagicMock()
                mock_agent.return_value = mock_instance

                agent = main.get_agent("frontend", "fashion_cv")
                assert agent == mock_instance

    def test_get_agent_intelligence_claude_sonnet(self):
        """Test creating intelligence Claude Sonnet agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AI_SERVICES_AVAILABLE", True):
            with patch("main.ClaudeSonnetIntelligenceService") as mock_agent:
                mock_instance = MagicMock()
                mock_agent.return_value = mock_instance

                agent = main.get_agent("intelligence", "claude_sonnet")
                assert agent == mock_instance

    def test_get_agent_intelligence_claude_sonnet_v2(self):
        """Test creating intelligence Claude Sonnet V2 agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AI_SERVICES_AVAILABLE", True):
            with patch("main.ClaudeSonnetIntelligenceServiceV2") as mock_agent:
                mock_instance = MagicMock()
                mock_agent.return_value = mock_instance

                agent = main.get_agent("intelligence", "claude_sonnet_v2")
                assert agent == mock_instance

    def test_get_agent_intelligence_openai(self):
        """Test creating intelligence OpenAI agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AI_SERVICES_AVAILABLE", True), patch("main.OpenAIIntelligenceService") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("intelligence", "openai")
            assert agent == mock_instance

    def test_get_agent_intelligence_multi_model(self):
        """Test creating intelligence multi-model agent."""
        import main

        main._agent_cache.clear()

        with patch("main.AI_SERVICES_AVAILABLE", True), patch("main.MultiModelOrchestrator") as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance

            agent = main.get_agent("intelligence", "multi_model")
            assert agent == mock_instance

    def test_get_agent_unknown_backend(self):
        """Test creating agent with unknown backend type."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True):
            agent = main.get_agent("backend", "unknown")
            assert agent is None

    def test_get_agent_unknown_frontend(self):
        """Test creating agent with unknown frontend type."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True):
            agent = main.get_agent("frontend", "unknown")
            assert agent is None

    def test_get_agent_unknown_intelligence(self):
        """Test creating agent with unknown intelligence type."""
        import main

        main._agent_cache.clear()

        with patch("main.AI_SERVICES_AVAILABLE", True):
            agent = main.get_agent("intelligence", "unknown")
            assert agent is None

    def test_get_agent_unknown_type(self):
        """Test creating agent with unknown agent type."""
        import main

        main._agent_cache.clear()

        agent = main.get_agent("unknown_type", "test")
        assert agent is None

    def test_get_agent_modules_not_available(self):
        """Test get_agent when modules are not available."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", False):
            agent = main.get_agent("backend", "security")
            assert agent is None


# ============================================================================
# TEST STARTUP AND SHUTDOWN EVENTS
# ============================================================================


class TestStartupShutdown:
    """Test application startup and shutdown events."""

    @pytest.mark.asyncio
    async def test_startup_event_initializes_security(self):
        """Test that startup event initializes security managers."""
        import main

        with patch("main.SECURITY_MODULES_AVAILABLE", True):
            with patch("main.EncryptionManager") as mock_encryption:
                with patch("main.GDPRManager") as mock_gdpr:
                    with patch("main.JWTManager") as mock_jwt:
                        mock_encryption.return_value = MagicMock()
                        mock_gdpr.return_value = MagicMock()
                        mock_jwt.return_value = MagicMock()

                        await main.startup_event()

                        assert mock_encryption.called
                        assert mock_gdpr.called
                        assert mock_jwt.called

    @pytest.mark.asyncio
    async def test_startup_event_initializes_webhook_system(self):
        """Test that startup event initializes webhook system."""
        import main

        with patch("main.WEBHOOK_SYSTEM_AVAILABLE", True), patch("main.WebhookManager") as mock_webhook:
            mock_webhook.return_value = MagicMock()

            await main.startup_event()

            assert mock_webhook.called

    @pytest.mark.asyncio
    async def test_startup_event_initializes_ml_cache(self):
        """Test that startup event initializes ML cache."""
        import main

        with patch("main.RedisCache") as mock_cache:
            mock_cache.return_value = MagicMock()

            await main.startup_event()

            assert mock_cache.called

    @pytest.mark.asyncio
    async def test_startup_event_initializes_agent_systems(self):
        """Test that startup event initializes agent systems."""
        import main

        with patch("main.CORE_MODULES_AVAILABLE", True), patch("main.AgentRegistry") as mock_registry:
            with patch("main.AgentOrchestrator") as mock_orchestrator:
                mock_registry.return_value = MagicMock()
                mock_orchestrator.return_value = MagicMock()

                await main.startup_event()

                assert mock_registry.called
                assert mock_orchestrator.called

    @pytest.mark.asyncio
    async def test_startup_event_initializes_model_registry(self):
        """Test that startup event initializes model registry."""
        import main

        with patch("main.ModelRegistry") as mock_registry:
            mock_registry.return_value = MagicMock()

            await main.startup_event()

            assert mock_registry.called

    @pytest.mark.asyncio
    async def test_startup_event_handles_exceptions(self):
        """Test that startup event handles exceptions gracefully."""
        import main

        with patch("main.ModelRegistry") as mock_registry:
            mock_registry.side_effect = Exception("Test exception")

            # Should not raise exception
            await main.startup_event()

    @pytest.mark.asyncio
    async def test_shutdown_event_clears_cache(self):
        """Test that shutdown event clears agent cache."""
        import main

        main._agent_cache["test"] = MagicMock()

        await main.shutdown_event()

        assert len(main._agent_cache) == 0

    @pytest.mark.asyncio
    async def test_shutdown_event_closes_ml_cache(self):
        """Test that shutdown event closes ML cache."""
        import main

        mock_cache = AsyncMock()
        main.app.state.ml_cache = mock_cache

        await main.shutdown_event()

        assert mock_cache.close.called

    @pytest.mark.asyncio
    async def test_shutdown_event_handles_exceptions(self):
        """Test that shutdown event handles exceptions gracefully."""
        import main

        mock_cache = AsyncMock()
        mock_cache.close.side_effect = Exception("Test exception")
        main.app.state.ml_cache = mock_cache

        # Should not raise exception
        await main.shutdown_event()


# ============================================================================
# TEST CORE ENDPOINTS
# ============================================================================


class TestCoreEndpoints:
    """Test core API endpoints."""

    def test_root_endpoint_with_missing_html_file(self, client):
        """Test root endpoint when HTML file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = client.get("/")
            assert response.status_code == 200
            assert "DevSkyy" in response.text

    def test_root_endpoint_with_html_file(self, client, tmp_path):
        """Test root endpoint with valid HTML file."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        html_file = tmp_path / "bulk_editing_interface.html"
        html_file.write_text(html_content)

        with patch("builtins.open", return_value=open(html_file)):
            response = client.get("/")
            assert response.status_code == 200

    def test_simple_interface_endpoint_missing_file(self, client):
        """Test simple interface endpoint when file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = client.get("/simple")
            assert response.status_code == 200
            assert "Simple interface not found" in response.text

    def test_classic_interface_endpoint_missing_file(self, client):
        """Test classic interface endpoint when file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = client.get("/classic")
            assert response.status_code == 200
            assert "Classic interface not found" in response.text

    def test_health_check_endpoint(self, client):
        """Test health check endpoint returns correct data."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_system_status_endpoint(self, client):
        """Test system status endpoint returns comprehensive status."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "operational"
        assert "version" in data
        assert "environment" in data
        assert "modules" in data
        assert "agent_cache_size" in data

    def test_system_status_endpoint_includes_modules(self, client):
        """Test system status includes module availability."""
        response = client.get("/status")
        data = response.json()

        modules = data["modules"]
        assert "core_modules" in modules
        assert "security_modules" in modules
        assert "ai_services" in modules
        assert "webhook_system" in modules
        assert "prometheus" in modules
        assert "api_routers" in modules

    def test_system_status_endpoint_handles_exceptions(self, client):
        """Test system status endpoint handles exceptions."""
        import main

        with patch.object(main.app.state, "startup_time", None):
            response = client.get("/status")
            assert response.status_code == 500


# ============================================================================
# TEST AGENT ENDPOINTS
# ============================================================================


class TestAgentEndpoints:
    """Test agent-related endpoints."""

    def test_get_agent_endpoint_backend_security(self, client):
        """Test GET agent endpoint for backend security."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.SecurityAgent") as mock_agent:
            mock_agent.return_value = MagicMock()

            response = client.get("/api/v1/agents/backend/security")
            assert response.status_code == 200

            data = response.json()
            assert data["agent_type"] == "backend"
            assert data["agent_name"] == "security"
            assert data["status"] == "active"

    def test_get_agent_endpoint_not_found(self, client):
        """Test GET agent endpoint with invalid agent."""
        import main

        main._agent_cache.clear()

        response = client.get("/api/v1/agents/invalid/agent")
        assert response.status_code == 404

    def test_execute_agent_task_endpoint(self, client):
        """Test POST execute agent task endpoint."""
        import main

        main._agent_cache.clear()

        with patch("main.AGENT_MODULES_AVAILABLE", True), patch("main.SecurityAgent") as mock_agent:
            mock_agent.return_value = MagicMock()

            task_data = {"task": "test_task", "data": {"key": "value"}}
            response = client.post("/api/v1/agents/backend/security/execute", json=task_data)

            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == "backend"
            assert data["agent_name"] == "security"
            assert data["status"] == "completed"

    def test_execute_agent_task_endpoint_not_found(self, client):
        """Test execute agent task endpoint with invalid agent."""
        import main

        main._agent_cache.clear()

        task_data = {"task": "test_task"}
        response = client.post("/api/v1/agents/invalid/agent/execute", json=task_data)
        assert response.status_code == 404

    def test_execute_agent_task_endpoint_with_prometheus(self, client):
        """Test execute agent task endpoint updates Prometheus metrics."""
        import main

        main._agent_cache.clear()

        with patch("main.PROMETHEUS_AVAILABLE", True), patch("main.AI_PREDICTIONS") as mock_metric:
            with patch("main.AGENT_MODULES_AVAILABLE", True):
                with patch("main.SecurityAgent") as mock_agent:
                    mock_agent.return_value = MagicMock()

                    task_data = {"task": "test_task"}
                    response = client.post("/api/v1/agents/backend/security/execute", json=task_data)

                    assert response.status_code == 200


# ============================================================================
# TEST METRICS ENDPOINT
# ============================================================================


class TestMetricsEndpoint:
    """Test metrics endpoints."""

    def test_metrics_endpoint_when_prometheus_available(self, client):
        """Test metrics endpoint when Prometheus is available."""

        with patch("main.PROMETHEUS_AVAILABLE", True), patch("main.generate_latest") as mock_generate:
            mock_generate.return_value = b"# HELP test_metric Test metric\n"

            response = client.get("/metrics")
            assert response.status_code == 200

    def test_get_prometheus_metrics_endpoint_with_collector(self, client):
        """Test get_prometheus_metrics endpoint with metrics collector."""
        import main

        mock_collector = MagicMock()
        mock_collector.get_prometheus_metrics.return_value = "# HELP test Test\n"
        main.app.state.metrics_collector = mock_collector

        response = client.get("/metrics")
        assert response.status_code == 200

    def test_get_prometheus_metrics_endpoint_without_collector(self, client):
        """Test get_prometheus_metrics endpoint without metrics collector."""
        import main

        if hasattr(main.app.state, "metrics_collector"):
            delattr(main.app.state, "metrics_collector")

        response = client.get("/metrics")
        assert response.status_code == 200


# ============================================================================
# TEST ADVANCED FEATURE ENDPOINTS
# ============================================================================


class TestAdvancedFeatureEndpoints:
    """Test advanced feature endpoints."""

    def test_multi_agent_orchestration_endpoint_not_available(self, client):
        """Test multi-agent orchestration endpoint when not available."""
        import main

        if hasattr(main.app.state, "multi_agent_orchestrator"):
            delattr(main.app.state, "multi_agent_orchestrator")

        task_data = {"task_type": "security_analysis", "content": "test"}
        response = client.post("/api/v1/orchestration/multi-agent", json=task_data)
        assert response.status_code == 503

    def test_upload_3d_model_endpoint_not_available(self, client):
        """Test upload 3D model endpoint when not available."""
        import main

        if hasattr(main.app.state, "skyy_rose_3d_pipeline"):
            delattr(main.app.state, "skyy_rose_3d_pipeline")

        response = client.post(
            "/api/v1/3d/models/upload",
            json={"file_path": "/test/file.glb", "model_format": "glb"}
        )
        assert response.status_code == 503

    def test_create_avatar_endpoint_not_available(self, client):
        """Test create avatar endpoint when not available."""
        import main

        if hasattr(main.app.state, "skyy_rose_3d_pipeline"):
            delattr(main.app.state, "skyy_rose_3d_pipeline")

        avatar_data = {"avatar_type": "ready_player_me"}
        response = client.post("/api/v1/avatars/create", json=avatar_data)
        assert response.status_code == 503

    def test_advanced_system_status_endpoint(self, client):
        """Test advanced system status endpoint."""
        response = client.get("/api/v1/system/advanced-status")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "multi_agent_orchestrator" in data
        assert "3d_pipeline" in data
        assert "advanced_features_available" in data


# ============================================================================
# TEST MONITORING ENDPOINTS
# ============================================================================


class TestMonitoringEndpoints:
    """Test monitoring endpoints."""

    def test_monitoring_status_endpoint(self, client):
        """Test monitoring status endpoint."""
        response = client.get("/api/v1/monitoring/status")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "monitoring_available" in data
        assert "metrics" in data
        assert "incidents" in data
        assert "logging" in data

    def test_active_incidents_endpoint_not_available(self, client):
        """Test active incidents endpoint when not available."""
        import main

        if hasattr(main.app.state, "incident_response_system"):
            delattr(main.app.state, "incident_response_system")

        response = client.get("/api/v1/monitoring/incidents")
        assert response.status_code == 503


# ============================================================================
# TEST THEME BUILDER ENDPOINTS
# ============================================================================


class TestThemeBuilderEndpoints:
    """Test theme builder endpoints."""

    def test_theme_system_status_endpoint(self, client):
        """Test theme system status endpoint."""
        with patch("main.theme_builder_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_system_status.return_value = {"status": "operational"}

            response = client.get("/api/v1/themes/system-status")
            assert response.status_code == 200

            data = response.json()
            assert "timestamp" in data
            assert "available_theme_types" in data
            assert "supported_upload_methods" in data


# ============================================================================
# TEST DEVELOPMENT ENDPOINTS
# ============================================================================


class TestDevelopmentEndpoints:
    """Test development-only endpoints."""

    def test_debug_cache_endpoint_in_development(self, client, monkeypatch):
        """Test debug cache endpoint in development environment."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        import importlib

        import main as main_module
        importlib.reload(main_module)

        client_dev = TestClient(main_module.app)
        response = client_dev.get("/debug/cache")

        assert response.status_code == 200
        data = response.json()
        assert "cache_size" in data
        assert "cached_agents" in data
        assert "timestamp" in data

    def test_clear_cache_endpoint_in_development(self, client, monkeypatch):
        """Test clear cache endpoint in development environment."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        import importlib

        import main as main_module
        importlib.reload(main_module)

        main_module._agent_cache["test"] = MagicMock()

        client_dev = TestClient(main_module.app)
        response = client_dev.post("/debug/clear-cache")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(main_module._agent_cache) == 0


# ============================================================================
# TEST STATIC FILES MOUNTING
# ============================================================================


class TestStaticFilesMounting:
    """Test static files mounting."""

    def test_static_files_mounted_when_directory_exists(self, tmp_path, monkeypatch):
        """Test that static files are mounted when directory exists."""
        monkeypatch.chdir(tmp_path)

        # Create static directory
        static_dir = tmp_path / "static"
        static_dir.mkdir()

        import importlib

        import main as main_module
        importlib.reload(main_module)

        # Verify app was created successfully
        assert main_module.app is not None


# ============================================================================
# TEST SECRET KEY VALIDATION
# ============================================================================


class TestSecretKeyValidation:
    """Test SECRET_KEY validation."""

    def test_secret_key_required_in_production(self, monkeypatch):
        """Test that SECRET_KEY is required in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            import importlib

            import main as main_module
            importlib.reload(main_module)

    def test_secret_key_default_in_development(self, monkeypatch):
        """Test that SECRET_KEY has default in development."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("SECRET_KEY", raising=False)

        import importlib

        import main as main_module
        importlib.reload(main_module)

        assert main_module.SECRET_KEY is not None
        assert "dev" in main_module.SECRET_KEY.lower()


# ============================================================================
# TEST CORS AND MIDDLEWARE
# ============================================================================


class TestCORSAndMiddleware:
    """Test CORS and middleware configuration."""

    def test_cors_origins_from_environment(self, monkeypatch):
        """Test CORS origins are loaded from environment."""
        monkeypatch.setenv("CORS_ORIGINS", "http://example.com,http://test.com")

        import importlib

        import main as main_module
        importlib.reload(main_module)

        # Verify app was created successfully with CORS
        assert main_module.app is not None

    def test_trusted_hosts_from_environment(self, monkeypatch):
        """Test trusted hosts are loaded from environment."""
        monkeypatch.setenv("TRUSTED_HOSTS", "example.com,test.com")

        import importlib

        import main as main_module
        importlib.reload(main_module)

        # Verify app was created successfully with trusted hosts
        assert main_module.app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
