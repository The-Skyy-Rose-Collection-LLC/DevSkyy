"""
Comprehensive tests for infrastructure/cicd_integrations.py

WHY: Ensure CI/CD integrations work correctly with ≥65% coverage
HOW: Test webhook processing, pipeline triggering, and event handling for multiple platforms
IMPACT: Validates enterprise CI/CD integration infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥65%
"""

from datetime import datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest

from infrastructure.cicd_integrations import (
    CICDConnection,
    CICDIntegrationManager,
    CICDPlatform,
    PipelineEvent,
    PipelineStatus,
    WebhookEventType,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    client = MagicMock()
    client.post = AsyncMock(return_value=MagicMock(status_code=200, headers={"Location": "http://queue"}, json=lambda: {"id": 123, "web_url": "http://example.com"}))
    client.get = AsyncMock(return_value=MagicMock(status_code=200))
    client.aclose = AsyncMock()
    return client


@pytest.fixture
async def cicd_manager(mock_http_client):
    """Create CICDIntegrationManager instance with mocked HTTP client."""
    with patch("infrastructure.cicd_integrations.AsyncClient", return_value=mock_http_client):
        manager = CICDIntegrationManager()
        yield manager
        await manager.close()


@pytest.fixture
def sample_connection():
    """Create sample CI/CD connection."""
    return CICDConnection(
        platform=CICDPlatform.GITHUB_ACTIONS,
        name="github-prod",
        base_url="https://api.github.com",
        api_token="ghp_test_token",
        organization="my-org",
        project_id="my-repo",
        webhook_secret="secret123",
        enabled=True,
    )


@pytest.fixture
def mock_request():
    """Create mock FastAPI Request."""
    request = MagicMock()
    request.json = AsyncMock(return_value={"test": "data"})
    request.headers = {}
    return request


# ============================================================================
# TEST Enums
# ============================================================================


class TestEnums:
    """Test CI/CD enum values."""

    def test_cicd_platform_values(self):
        """Test all CI/CD platform enum values."""
        assert CICDPlatform.JENKINS.value == "jenkins"
        assert CICDPlatform.GITLAB_CI.value == "gitlab_ci"
        assert CICDPlatform.GITHUB_ACTIONS.value == "github_actions"
        assert CICDPlatform.AZURE_DEVOPS.value == "azure_devops"
        assert CICDPlatform.BITBUCKET_PIPELINES.value == "bitbucket_pipelines"

    def test_pipeline_status_values(self):
        """Test all pipeline status enum values."""
        assert PipelineStatus.PENDING.value == "pending"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.SUCCESS.value == "success"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.CANCELLED.value == "cancelled"
        assert PipelineStatus.SKIPPED.value == "skipped"
        assert PipelineStatus.TIMEOUT.value == "timeout"

    def test_webhook_event_type_values(self):
        """Test webhook event type enum values."""
        assert WebhookEventType.PIPELINE_STARTED.value == "pipeline_started"
        assert WebhookEventType.PIPELINE_COMPLETED.value == "pipeline_completed"
        assert WebhookEventType.PIPELINE_FAILED.value == "pipeline_failed"
        assert WebhookEventType.DEPLOYMENT_COMPLETED.value == "deployment_completed"


# ============================================================================
# TEST PipelineEvent
# ============================================================================


class TestPipelineEvent:
    """Test PipelineEvent dataclass."""

    def test_pipeline_event_initialization(self):
        """Test PipelineEvent initialization."""
        event = PipelineEvent(
            event_id="event123",
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=WebhookEventType.PIPELINE_STARTED,
            pipeline_id="pipeline123",
            pipeline_name="CI Pipeline",
            status=PipelineStatus.RUNNING,
            branch="main",
            commit_hash="abc123",
            commit_message="Test commit",
            author="developer",
            timestamp=datetime.now(),
        )

        assert event.event_id == "event123"
        assert event.platform == CICDPlatform.GITHUB_ACTIONS
        assert event.status == PipelineStatus.RUNNING

    def test_pipeline_event_post_init_defaults(self):
        """Test PipelineEvent __post_init__ sets defaults."""
        event = PipelineEvent(
            event_id="event123",
            platform=CICDPlatform.JENKINS,
            event_type=WebhookEventType.BUILD_COMPLETED,
            pipeline_id="123",
            pipeline_name="Build",
            status=PipelineStatus.SUCCESS,
            branch="main",
            commit_hash="abc",
            commit_message="",
            author="",
            timestamp=datetime.now(),
        )

        assert event.artifacts == []
        assert event.test_results == {}
        assert event.code_quality_metrics == {}
        assert event.security_scan_results == {}
        assert event.raw_payload == {}


# ============================================================================
# TEST CICDConnection
# ============================================================================


class TestCICDConnection:
    """Test CICDConnection dataclass."""

    def test_connection_initialization(self, sample_connection):
        """Test CICDConnection initialization."""
        assert sample_connection.platform == CICDPlatform.GITHUB_ACTIONS
        assert sample_connection.name == "github-prod"
        assert sample_connection.base_url == "https://api.github.com"
        assert sample_connection.api_token == "ghp_test_token"
        assert sample_connection.enabled is True

    def test_connection_optional_fields(self):
        """Test CICDConnection with optional fields."""
        conn = CICDConnection(
            platform=CICDPlatform.JENKINS,
            name="jenkins-test",
            base_url="https://jenkins.example.com",
            api_token="token",
            username="admin",
            project_id="project1",
            rate_limit_per_hour=500,
        )

        assert conn.username == "admin"
        assert conn.project_id == "project1"
        assert conn.rate_limit_per_hour == 500


# ============================================================================
# TEST CICDIntegrationManager Initialization
# ============================================================================


class TestCICDIntegrationManagerInitialization:
    """Test CICDIntegrationManager initialization."""

    def test_manager_initialization(self, cicd_manager):
        """Test manager initializes correctly."""
        assert isinstance(cicd_manager.connections, dict)
        assert isinstance(cicd_manager.webhook_handlers, dict)
        assert isinstance(cicd_manager.event_history, list)
        assert isinstance(cicd_manager.metrics, dict)

    def test_webhook_handlers_setup(self, cicd_manager):
        """Test webhook handlers are set up for all platforms."""
        assert CICDPlatform.JENKINS in cicd_manager.webhook_handlers
        assert CICDPlatform.GITLAB_CI in cicd_manager.webhook_handlers
        assert CICDPlatform.GITHUB_ACTIONS in cicd_manager.webhook_handlers
        assert CICDPlatform.AZURE_DEVOPS in cicd_manager.webhook_handlers
        assert CICDPlatform.BITBUCKET_PIPELINES in cicd_manager.webhook_handlers

    def test_metrics_initialization(self, cicd_manager):
        """Test metrics are initialized."""
        assert cicd_manager.metrics["total_webhooks_received"] == 0
        assert cicd_manager.metrics["total_api_calls"] == 0
        assert cicd_manager.metrics["successful_api_calls"] == 0
        assert cicd_manager.metrics["failed_api_calls"] == 0


# ============================================================================
# TEST Connection Management
# ============================================================================


class TestConnectionManagement:
    """Test CI/CD connection management."""

    def test_add_connection(self, cicd_manager, sample_connection):
        """Test adding new connection."""
        cicd_manager.add_connection(sample_connection)

        assert "github-prod" in cicd_manager.connections
        assert cicd_manager.connections["github-prod"] == sample_connection

    def test_remove_connection(self, cicd_manager, sample_connection):
        """Test removing connection."""
        cicd_manager.add_connection(sample_connection)
        cicd_manager.remove_connection("github-prod")

        assert "github-prod" not in cicd_manager.connections

    def test_remove_nonexistent_connection(self, cicd_manager):
        """Test removing non-existent connection doesn't error."""
        cicd_manager.remove_connection("nonexistent")
        # Should not raise exception


# ============================================================================
# TEST Webhook Processing
# ============================================================================


class TestWebhookProcessing:
    """Test webhook processing logic."""

    @pytest.mark.asyncio
    async def test_process_webhook_success(self, cicd_manager, sample_connection, mock_request):
        """Test successful webhook processing."""
        cicd_manager.add_connection(sample_connection)

        # Mock handler
        mock_event = PipelineEvent(
            event_id="event123",
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=WebhookEventType.PIPELINE_STARTED,
            pipeline_id="123",
            pipeline_name="Test",
            status=PipelineStatus.RUNNING,
            branch="main",
            commit_hash="abc",
            commit_message="",
            author="",
            timestamp=datetime.now(),
        )

        with patch.object(cicd_manager, "_handle_github_webhook", return_value=mock_event):
            result = await cicd_manager.process_webhook(
                platform=CICDPlatform.GITHUB_ACTIONS,
                request=mock_request,
                connection_name="github-prod",
            )

        assert result["status"] == "processed"
        assert result["event_id"] == "event123"

    @pytest.mark.asyncio
    async def test_process_webhook_no_connection(self, cicd_manager, mock_request):
        """Test webhook processing with no active connection."""
        with pytest.raises(HTTPException) as exc_info:
            await cicd_manager.process_webhook(
                platform=CICDPlatform.JENKINS,
                request=mock_request,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_process_webhook_signature_verification(self, cicd_manager, sample_connection, mock_request):
        """Test webhook signature verification."""
        cicd_manager.add_connection(sample_connection)

        # Mock signature verification
        with patch.object(cicd_manager, "_verify_webhook_signature") as mock_verify:
            with patch.object(cicd_manager, "_handle_github_webhook") as mock_handler:
                mock_handler.return_value = PipelineEvent(
                    event_id="test",
                    platform=CICDPlatform.GITHUB_ACTIONS,
                    event_type=WebhookEventType.PIPELINE_STARTED,
                    pipeline_id="123",
                    pipeline_name="Test",
                    status=PipelineStatus.PENDING,
                    branch="main",
                    commit_hash="abc",
                    commit_message="",
                    author="",
                    timestamp=datetime.now(),
                )

                await cicd_manager.process_webhook(
                    platform=CICDPlatform.GITHUB_ACTIONS,
                    request=mock_request,
                    connection_name="github-prod",
                )

                # Verify signature verification was called
                assert mock_verify.called

    @pytest.mark.asyncio
    async def test_process_webhook_updates_metrics(self, cicd_manager, sample_connection, mock_request):
        """Test webhook processing updates metrics."""
        cicd_manager.add_connection(sample_connection)
        initial_webhooks = cicd_manager.metrics["total_webhooks_received"]

        with patch.object(cicd_manager, "_handle_github_webhook") as mock_handler:
            mock_handler.return_value = PipelineEvent(
                event_id="test",
                platform=CICDPlatform.GITHUB_ACTIONS,
                event_type=WebhookEventType.PIPELINE_STARTED,
                pipeline_id="123",
                pipeline_name="Test",
                status=PipelineStatus.PENDING,
                branch="main",
                commit_hash="abc",
                commit_message="",
                author="",
                timestamp=datetime.now(),
            )

            await cicd_manager.process_webhook(
                platform=CICDPlatform.GITHUB_ACTIONS,
                request=mock_request,
                connection_name="github-prod",
            )

        assert cicd_manager.metrics["total_webhooks_received"] == initial_webhooks + 1

    @pytest.mark.asyncio
    async def test_process_webhook_stores_history(self, cicd_manager, sample_connection, mock_request):
        """Test webhook processing stores event in history."""
        cicd_manager.add_connection(sample_connection)
        initial_history_len = len(cicd_manager.event_history)

        with patch.object(cicd_manager, "_handle_github_webhook") as mock_handler:
            mock_handler.return_value = PipelineEvent(
                event_id="test",
                platform=CICDPlatform.GITHUB_ACTIONS,
                event_type=WebhookEventType.PIPELINE_STARTED,
                pipeline_id="123",
                pipeline_name="Test",
                status=PipelineStatus.PENDING,
                branch="main",
                commit_hash="abc",
                commit_message="",
                author="",
                timestamp=datetime.now(),
            )

            await cicd_manager.process_webhook(
                platform=CICDPlatform.GITHUB_ACTIONS,
                request=mock_request,
                connection_name="github-prod",
            )

        assert len(cicd_manager.event_history) == initial_history_len + 1

    @pytest.mark.asyncio
    async def test_process_webhook_history_limit(self, cicd_manager, sample_connection, mock_request):
        """Test webhook history is limited to 1000 entries."""
        cicd_manager.add_connection(sample_connection)

        # Fill history beyond limit
        cicd_manager.event_history = [MagicMock() for _ in range(1005)]

        with patch.object(cicd_manager, "_handle_github_webhook") as mock_handler:
            mock_handler.return_value = PipelineEvent(
                event_id="test",
                platform=CICDPlatform.GITHUB_ACTIONS,
                event_type=WebhookEventType.PIPELINE_STARTED,
                pipeline_id="123",
                pipeline_name="Test",
                status=PipelineStatus.PENDING,
                branch="main",
                commit_hash="abc",
                commit_message="",
                author="",
                timestamp=datetime.now(),
            )

            await cicd_manager.process_webhook(
                platform=CICDPlatform.GITHUB_ACTIONS,
                request=mock_request,
                connection_name="github-prod",
            )

        assert len(cicd_manager.event_history) == 1000


# ============================================================================
# TEST Webhook Signature Verification
# ============================================================================


class TestWebhookSignatureVerification:
    """Test webhook signature verification."""

    @pytest.mark.asyncio
    async def test_verify_github_signature_valid(self, cicd_manager):
        """Test GitHub webhook signature verification with valid signature."""
        import hmac

        payload = {"test": "data"}
        secret = "secret123"
        payload_json = json.dumps(payload, separators=(",", ":"))
        expected_signature = hmac.new(secret.encode(), payload_json.encode(), "sha256").hexdigest()

        headers = {"x-hub-signature-256": f"sha256={expected_signature}"}

        # Should not raise exception
        await cicd_manager._verify_webhook_signature(
            platform=CICDPlatform.GITHUB_ACTIONS,
            headers=headers,
            payload=payload,
            secret=secret,
        )

    @pytest.mark.asyncio
    async def test_verify_github_signature_invalid(self, cicd_manager):
        """Test GitHub webhook signature verification with invalid signature."""
        payload = {"test": "data"}
        headers = {"x-hub-signature-256": "sha256=invalid"}

        with pytest.raises(HTTPException) as exc_info:
            await cicd_manager._verify_webhook_signature(
                platform=CICDPlatform.GITHUB_ACTIONS,
                headers=headers,
                payload=payload,
                secret="secret123",
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_github_signature_missing(self, cicd_manager):
        """Test GitHub webhook signature verification with missing signature."""
        headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await cicd_manager._verify_webhook_signature(
                platform=CICDPlatform.GITHUB_ACTIONS,
                headers=headers,
                payload={},
                secret="secret123",
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_gitlab_token_valid(self, cicd_manager):
        """Test GitLab webhook token verification with valid token."""
        headers = {"x-gitlab-token": "secret123"}

        # Should not raise exception
        await cicd_manager._verify_webhook_signature(
            platform=CICDPlatform.GITLAB_CI,
            headers=headers,
            payload={},
            secret="secret123",
        )

    @pytest.mark.asyncio
    async def test_verify_gitlab_token_invalid(self, cicd_manager):
        """Test GitLab webhook token verification with invalid token."""
        headers = {"x-gitlab-token": "wrong"}

        with pytest.raises(HTTPException) as exc_info:
            await cicd_manager._verify_webhook_signature(
                platform=CICDPlatform.GITLAB_CI,
                headers=headers,
                payload={},
                secret="secret123",
            )

        assert exc_info.value.status_code == 401


# ============================================================================
# TEST Webhook Handlers
# ============================================================================


class TestWebhookHandlers:
    """Test platform-specific webhook handlers."""

    @pytest.mark.asyncio
    async def test_handle_jenkins_webhook(self, cicd_manager, sample_connection):
        """Test Jenkins webhook handling."""
        payload = {
            "name": "Test Job",
            "build": {
                "number": 123,
                "status": "SUCCESS",
                "phase": "COMPLETED",
                "full_url": "http://jenkins/job/test/123",
                "duration": 300000,
                "scm": {"branch": "main", "commit": "abc123"},
            },
        }

        event = await cicd_manager._handle_jenkins_webhook(payload, {}, sample_connection)

        assert event.platform == CICDPlatform.JENKINS
        assert event.status == PipelineStatus.SUCCESS
        assert event.event_type == WebhookEventType.PIPELINE_COMPLETED

    @pytest.mark.asyncio
    async def test_handle_gitlab_webhook(self, cicd_manager, sample_connection):
        """Test GitLab CI webhook handling."""
        payload = {
            "object_kind": "pipeline",
            "object_attributes": {
                "id": 456,
                "status": "success",
                "ref": "main",
                "created_at": datetime.now().isoformat(),
            },
            "commit": {
                "id": "def456",
                "message": "Test commit",
                "author": {"name": "Developer"},
            },
            "project": {"name": "Test Project"},
        }

        event = await cicd_manager._handle_gitlab_webhook(payload, {}, sample_connection)

        assert event.platform == CICDPlatform.GITLAB_CI
        assert event.status == PipelineStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_handle_github_webhook(self, cicd_manager, sample_connection):
        """Test GitHub Actions webhook handling."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 789,
                "name": "CI Workflow",
                "status": "completed",
                "conclusion": "success",
                "head_branch": "main",
                "head_sha": "ghi789",
                "created_at": datetime.now().isoformat(),
                "run_number": 42,
                "logs_url": "http://github/logs",
                "head_commit": {
                    "message": "Test",
                    "author": {"name": "Dev"},
                },
            },
        }

        event = await cicd_manager._handle_github_webhook(payload, {}, sample_connection)

        assert event.platform == CICDPlatform.GITHUB_ACTIONS
        assert event.status == PipelineStatus.SUCCESS
        assert event.event_type == WebhookEventType.PIPELINE_COMPLETED

    @pytest.mark.asyncio
    async def test_handle_azure_webhook(self, cicd_manager, sample_connection):
        """Test Azure DevOps webhook handling."""
        payload = {
            "resource": {
                "id": 101,
                "result": "succeeded",
                "status": "completed",
                "sourceBranch": "refs/heads/main",
                "sourceVersion": "jkl101",
                "startTime": datetime.now().isoformat(),
                "buildNumber": 55,
                "definition": {"name": "Build Pipeline"},
                "requestedFor": {"displayName": "User"},
                "_links": {"web": {"href": "http://azure/build"}},
            },
        }

        event = await cicd_manager._handle_azure_webhook(payload, {}, sample_connection)

        assert event.platform == CICDPlatform.AZURE_DEVOPS
        assert event.status == PipelineStatus.SUCCESS


# ============================================================================
# TEST Pipeline Triggering
# ============================================================================


class TestPipelineTriggering:
    """Test pipeline triggering via API."""

    @pytest.mark.asyncio
    async def test_trigger_jenkins_pipeline(self, cicd_manager, mock_http_client):
        """Test triggering Jenkins pipeline."""
        conn = CICDConnection(
            platform=CICDPlatform.JENKINS,
            name="jenkins",
            base_url="http://jenkins",
            api_token="token",
            username="admin",
        )
        cicd_manager.add_connection(conn)

        result = await cicd_manager.trigger_pipeline("jenkins", "test-job")

        assert result["status"] == "triggered"
        assert result["platform"] == "jenkins"
        assert mock_http_client.post.called

    @pytest.mark.asyncio
    async def test_trigger_gitlab_pipeline(self, cicd_manager, mock_http_client):
        """Test triggering GitLab CI pipeline."""
        conn = CICDConnection(
            platform=CICDPlatform.GITLAB_CI,
            name="gitlab",
            base_url="https://gitlab.com",
            api_token="token",
        )
        cicd_manager.add_connection(conn)

        result = await cicd_manager.trigger_pipeline("gitlab", "project123", branch="develop")

        assert result["status"] == "triggered"
        assert result["platform"] == "gitlab_ci"

    @pytest.mark.asyncio
    async def test_trigger_github_workflow(self, cicd_manager, mock_http_client):
        """Test triggering GitHub Actions workflow."""
        conn = CICDConnection(
            platform=CICDPlatform.GITHUB_ACTIONS,
            name="github",
            base_url="https://api.github.com",
            api_token="token",
            organization="org",
            project_id="repo",
        )
        cicd_manager.add_connection(conn)

        result = await cicd_manager.trigger_pipeline("github", "workflow.yml", branch="main")

        assert result["status"] == "triggered"
        assert result["platform"] == "github_actions"

    @pytest.mark.asyncio
    async def test_trigger_pipeline_nonexistent_connection(self, cicd_manager):
        """Test triggering pipeline with non-existent connection."""
        with pytest.raises(ValueError, match="Connection not found"):
            await cicd_manager.trigger_pipeline("nonexistent", "pipeline")

    @pytest.mark.asyncio
    async def test_trigger_pipeline_updates_metrics(self, cicd_manager, mock_http_client):
        """Test pipeline triggering updates metrics."""
        conn = CICDConnection(
            platform=CICDPlatform.JENKINS,
            name="jenkins",
            base_url="http://jenkins",
            api_token="token",
        )
        cicd_manager.add_connection(conn)

        initial_calls = cicd_manager.metrics["total_api_calls"]

        await cicd_manager.trigger_pipeline("jenkins", "test-job")

        assert cicd_manager.metrics["total_api_calls"] == initial_calls + 1
        assert cicd_manager.metrics["successful_api_calls"] > 0


# ============================================================================
# TEST Event Handlers
# ============================================================================


class TestEventHandlers:
    """Test event handling logic."""

    @pytest.mark.asyncio
    async def test_is_fashion_related_pipeline(self, cicd_manager):
        """Test fashion-related pipeline detection."""
        event = PipelineEvent(
            event_id="test",
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=WebhookEventType.PIPELINE_STARTED,
            pipeline_id="123",
            pipeline_name="fashion-trend-analysis",
            status=PipelineStatus.RUNNING,
            branch="main",
            commit_hash="abc",
            commit_message="",
            author="",
            timestamp=datetime.now(),
        )

        assert cicd_manager._is_fashion_related_pipeline(event) is True

    @pytest.mark.asyncio
    async def test_handle_fashion_pipeline_event(self, cicd_manager):
        """Test fashion pipeline event handling."""
        event = PipelineEvent(
            event_id="test",
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=WebhookEventType.PIPELINE_COMPLETED,
            pipeline_id="123",
            pipeline_name="inventory-sync",
            status=PipelineStatus.SUCCESS,
            branch="main",
            commit_hash="abc",
            commit_message="",
            author="",
            timestamp=datetime.now(),
        )

        # Should not raise exception
        await cicd_manager._handle_fashion_pipeline_event(event)


# ============================================================================
# TEST Metrics and Health Check
# ============================================================================


class TestMetricsAndHealthCheck:
    """Test metrics and health check operations."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, cicd_manager, sample_connection):
        """Test getting CI/CD integration metrics."""
        cicd_manager.add_connection(sample_connection)

        metrics = await cicd_manager.get_metrics()

        assert "api_metrics" in metrics
        assert "connections" in metrics
        assert "recent_events" in metrics
        assert "event_counts" in metrics

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, cicd_manager, sample_connection, mock_http_client):
        """Test health check returns healthy status."""
        cicd_manager.add_connection(sample_connection)

        result = await cicd_manager.health_check()

        assert result["status"] == "healthy"
        assert "connections" in result
        assert "total_connections" in result
        assert "active_connections" in result

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, cicd_manager, sample_connection, mock_http_client):
        """Test health check returns degraded status with connection issues."""
        cicd_manager.add_connection(sample_connection)
        mock_http_client.get = AsyncMock(return_value=MagicMock(status_code=500))

        result = await cicd_manager.health_check()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, cicd_manager, mock_http_client):
        """Test health check returns unhealthy status on exception."""
        with patch.object(cicd_manager, "get_metrics", side_effect=Exception("Error")):
            result = await cicd_manager.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result


# ============================================================================
# TEST Global Instance
# ============================================================================


def test_global_cicd_manager():
    """Test global cicd_manager instance exists."""
    from infrastructure.cicd_integrations import cicd_manager

    assert cicd_manager is not None
    assert isinstance(cicd_manager, CICDIntegrationManager)
