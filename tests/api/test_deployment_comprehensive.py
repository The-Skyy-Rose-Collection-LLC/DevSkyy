"""
Comprehensive Tests for Deployment API Endpoints (api/v1/deployment.py)
Tests deployment job management, validation, approvals, and infrastructure management
Coverage target: ≥80% for api/v1/deployment.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

from datetime import datetime

# Patch the problematic imports before loading the deployment module
import sys
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
import pytest


mock_shap = Mock()
mock_joblib = Mock()
mock_torch = Mock()
mock_torch.nn = Mock()
mock_torch.optim = Mock()
mock_transformers = Mock()

sys.modules['shap'] = mock_shap
sys.modules['joblib'] = mock_joblib
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = mock_torch.nn
sys.modules['torch.optim'] = mock_torch.optim
sys.modules['transformers'] = mock_transformers


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "sub": "user123",
        "email": "test@example.com",
        "username": "testuser",
        "role": "admin",
    }


# ============================================================================
# TEST JOB SUBMISSION
# ============================================================================


class TestSubmitJob:
    """Test POST /api/v1/deployment/jobs endpoint"""

    @pytest.mark.asyncio
    async def test_submit_job_success(self, mock_current_user):
        """Should successfully submit a deployment job"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch, \
             patch("api.v1.deployment.JobDefinition") as mock_job_def:

            # Mock job definition instance
            job_instance = Mock()
            job_instance.job_id = "job_test123"
            job_instance.estimated_tokens = 5000
            job_instance.estimated_cost_usd = 0.05
            mock_job_def.return_value = job_instance

            # Mock orchestrator
            mock_orch = Mock()
            mock_orch.submit_job = AsyncMock(
                return_value={
                    "status": "approved",
                    "job_id": "job_test123",
                    "deployment_id": "deploy_test123",
                    "can_proceed": True,
                    "validation": {"is_ready": True},
                    "approval": {"final_decision": "approved"},
                }
            )
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import SubmitJobRequest, submit_job

            request = Mock(spec=SubmitJobRequest)
            request.job_name = "Test Job"
            request.job_description = "Test deployment"
            request.category = Mock(value="coding")
            request.primary_agent = "coding-agent-1"
            request.supporting_agents = ["coding-agent-2"]
            request.required_tools = []
            request.required_resources = []
            request.max_execution_time_seconds = 300
            request.max_retries = 3
            request.priority = 5
            request.max_budget_usd = 1.0
            request.input_schema = {}
            request.output_schema = {}
            request.tags = []

            result = await submit_job(request, mock_current_user)

            assert result["status"] == "success"
            assert "job_id" in result
            assert result["can_proceed"] is True

    @pytest.mark.asyncio
    async def test_submit_job_failure(self, mock_current_user):
        """Should handle job submission failure"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.submit_job = AsyncMock(side_effect=Exception("Orchestrator error"))
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import SubmitJobRequest, submit_job

            request = Mock(spec=SubmitJobRequest)
            request.job_name = "Failing Job"
            request.job_description = "This should fail"
            request.category = Mock(value="coding")
            request.primary_agent = "coding-agent-1"
            request.supporting_agents = []
            request.required_tools = []
            request.required_resources = []
            request.max_execution_time_seconds = 300
            request.max_retries = 3
            request.priority = 5
            request.max_budget_usd = 1.0
            request.input_schema = {}
            request.output_schema = {}
            request.tags = []

            with pytest.raises(HTTPException) as exc_info:
                await submit_job(request, mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Failed to submit job" in str(exc_info.value.detail)


# ============================================================================
# TEST JOB STATUS
# ============================================================================


class TestGetJobStatus:
    """Test GET /api/v1/deployment/jobs/{job_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, mock_current_user):
        """Should get job status successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.get_job_status.return_value = {
                "job": {
                    "job_id": "job_test123",
                    "job_name": "Test Job",
                    "category": "coding",
                    "estimated_tokens": 5000,
                    "estimated_cost_usd": 0.05,
                },
                "validation": {"is_ready": True},
                "approval": {"final_decision": "approved"},
                "deployment": {
                    "status": "running",
                    "actual_tokens_used": 1000,
                    "actual_cost_usd": 0.01,
                },
            }
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_job_status

            result = await get_job_status("job_test123", mock_current_user)

            assert result.job_id == "job_test123"
            assert result.job_name == "Test Job"
            assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, mock_current_user):
        """Should return 404 for non-existent job"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.get_job_status.return_value = None
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_job_status

            with pytest.raises(HTTPException) as exc_info:
                await get_job_status("nonexistent_job", mock_current_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_status_no_deployment(self, mock_current_user):
        """Should handle job with no deployment yet"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.get_job_status.return_value = {
                "job": {
                    "job_id": "job_test123",
                    "job_name": "Pending Job",
                    "category": "coding",
                    "estimated_tokens": 3000,
                    "estimated_cost_usd": 0.03,
                },
                "validation": {"is_ready": True},
                "deployment": None,
            }
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_job_status

            result = await get_job_status("job_test123", mock_current_user)

            assert result.job_id == "job_test123"
            assert result.status == "pending_validation"
            assert result.actual_tokens_used == 0


# ============================================================================
# TEST LIST JOBS
# ============================================================================


class TestListJobs:
    """Test GET /api/v1/deployment/jobs endpoint"""

    @pytest.mark.asyncio
    async def test_list_all_jobs(self, mock_current_user):
        """Should list all deployment jobs"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            job1 = Mock()
            job1.job_id = "job1"
            job1.job_name = "Job 1"
            job1.category = Mock(value="coding")
            job1.primary_agent = "agent1"
            job1.estimated_tokens = 1000
            job1.estimated_cost_usd = 0.01
            job1.created_at = datetime.now()
            job1.created_by = "user1"

            job2 = Mock()
            job2.job_id = "job2"
            job2.job_name = "Job 2"
            job2.category = Mock(value="devops")
            job2.primary_agent = "agent2"
            job2.estimated_tokens = 2000
            job2.estimated_cost_usd = 0.02
            job2.created_at = datetime.now()
            job2.created_by = "user2"

            mock_orch = Mock()
            mock_orch.jobs = {"job1": job1, "job2": job2}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import list_jobs

            result = await list_jobs(None, mock_current_user)

            assert result["total"] == 2
            assert len(result["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_list_jobs_filtered_by_category(self, mock_current_user):
        """Should filter jobs by category"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            coding_category = Mock(value="coding")
            devops_category = Mock(value="devops")

            job1 = Mock()
            job1.job_id = "job1"
            job1.job_name = "Coding Job"
            job1.category = coding_category
            job1.primary_agent = "agent1"
            job1.estimated_tokens = 1000
            job1.estimated_cost_usd = 0.01
            job1.created_at = datetime.now()
            job1.created_by = "user1"

            job2 = Mock()
            job2.job_id = "job2"
            job2.job_name = "DevOps Job"
            job2.category = devops_category
            job2.primary_agent = "agent2"
            job2.estimated_tokens = 2000
            job2.estimated_cost_usd = 0.02
            job2.created_at = datetime.now()
            job2.created_by = "user2"

            mock_orch = Mock()
            mock_orch.jobs = {"job1": job1, "job2": job2}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import list_jobs

            result = await list_jobs(coding_category, mock_current_user)

            assert result["total"] == 1
            assert result["jobs"][0]["category"] == "coding"

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, mock_current_user):
        """Should return empty list when no jobs"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.jobs = {}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import list_jobs

            result = await list_jobs(None, mock_current_user)

            assert result["total"] == 0
            assert result["jobs"] == []


# ============================================================================
# TEST VALIDATION
# ============================================================================


class TestValidateJob:
    """Test POST /api/v1/deployment/validate endpoint"""

    @pytest.mark.asyncio
    async def test_validate_job_success(self, mock_current_user):
        """Should validate job successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            validation_result = Mock()
            validation_result.is_ready = True
            validation_result.checks_passed = 5
            validation_result.checks_failed = 0
            validation_result.missing_tools = []
            validation_result.missing_resources = []
            validation_result.warnings = ["Consider adding more resources"]
            validation_result.detailed_results = {"all_checks": "passed"}

            mock_orch = Mock()
            mock_orch.cost_estimator.estimate_job_cost.return_value = (5000, 0.05)
            mock_orch.validator.validate_job = AsyncMock(return_value=validation_result)
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import ValidateJobRequest, validate_job

            request = Mock(spec=ValidateJobRequest)
            request.job_definition = Mock()

            result = await validate_job(request, mock_current_user)

            assert result["is_ready"] is True
            assert result["checks_passed"] == 5
            assert result["checks_failed"] == 0
            assert result["estimated_tokens"] == 5000

    @pytest.mark.asyncio
    async def test_validate_job_not_ready(self, mock_current_user):
        """Should return validation failures"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            validation_result = Mock()
            validation_result.is_ready = False
            validation_result.checks_passed = 3
            validation_result.checks_failed = 2
            validation_result.missing_tools = ["docker", "kubernetes"]
            validation_result.missing_resources = ["gpu"]
            validation_result.warnings = ["Insufficient resources"]
            validation_result.detailed_results = {"docker": "not_available"}

            mock_orch = Mock()
            mock_orch.cost_estimator.estimate_job_cost.return_value = (5000, 0.05)
            mock_orch.validator.validate_job = AsyncMock(return_value=validation_result)
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import ValidateJobRequest, validate_job

            request = Mock(spec=ValidateJobRequest)
            request.job_definition = Mock()

            result = await validate_job(request, mock_current_user)

            assert result["is_ready"] is False
            assert result["checks_failed"] == 2
            assert "docker" in result["missing_tools"]

    @pytest.mark.asyncio
    async def test_validate_job_error(self, mock_current_user):
        """Should handle validation errors"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.cost_estimator.estimate_job_cost.side_effect = Exception("Cost error")
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import ValidateJobRequest, validate_job

            request = Mock(spec=ValidateJobRequest)
            request.job_definition = Mock()

            with pytest.raises(HTTPException) as exc_info:
                await validate_job(request, mock_current_user)

            assert exc_info.value.status_code == 500


# ============================================================================
# TEST APPROVALS
# ============================================================================


class TestGetApprovalStatus:
    """Test GET /api/v1/deployment/approvals/{job_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_approval_status_success(self, mock_current_user):
        """Should get approval status successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            approval1 = Mock()
            approval1.agent_name = "Coding Lead"
            approval1.approval_status = Mock(value="approved")
            approval1.confidence = 0.95
            approval1.reasoning = "Looks good"
            approval1.concerns = []
            approval1.recommendations = ["Add tests"]
            approval1.timestamp = datetime.now()

            approval_result = Mock()
            approval_result.workflow_id = "workflow_123"
            approval_result.required_approvals = 2
            approval_result.approved_count = 1
            approval_result.rejected_count = 0
            approval_result.final_decision = Mock(value="pending")
            approval_result.consensus_reasoning = "Waiting for more approvals"
            approval_result.approvals = [approval1]
            approval_result.timestamp = datetime.now()

            mock_orch = Mock()
            mock_orch.approvals = {"job_test123": approval_result}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_approval_status

            result = await get_approval_status("job_test123", mock_current_user)

            assert result["workflow_id"] == "workflow_123"
            assert result["required_approvals"] == 2
            assert result["approved_count"] == 1

    @pytest.mark.asyncio
    async def test_get_approval_status_not_found(self, mock_current_user):
        """Should return 404 for non-existent approval"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.approvals = {}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_approval_status

            with pytest.raises(HTTPException) as exc_info:
                await get_approval_status("nonexistent_job", mock_current_user)

            assert exc_info.value.status_code == 404


# ============================================================================
# TEST TOOL REGISTRATION
# ============================================================================


class TestRegisterTool:
    """Test POST /api/v1/deployment/tools/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_tool_success(self, mock_current_user):
        """Should register tool successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.validator.register_tool = Mock()
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import RegisterToolRequest, register_tool

            request = Mock(spec=RegisterToolRequest)
            request.tool_name = "jira_api"
            request.tool_type = "api"
            request.rate_limit = 1000
            request.metadata = {"endpoint": "https://api.atlassian.com"}

            result = await register_tool(request, mock_current_user)

            assert result["status"] == "success"
            assert result["tool_name"] == "jira_api"
            mock_orch.validator.register_tool.assert_called_once()


# ============================================================================
# TEST RESOURCE REGISTRATION
# ============================================================================


class TestRegisterResource:
    """Test POST /api/v1/deployment/resources/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_resource_success(self, mock_current_user):
        """Should register resource successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.validator.register_resource = Mock()
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import RegisterResourceRequest, register_resource

            request = Mock(spec=RegisterResourceRequest)
            request.resource_type = Mock(value="compute")
            request.amount = 8.0
            request.unit = "cores"

            result = await register_resource(request, mock_current_user)

            assert result["status"] == "success"
            assert result["resource_type"] == "compute"
            assert result["amount"] == 8.0


# ============================================================================
# TEST INFRASTRUCTURE STATUS
# ============================================================================


class TestGetInfrastructureStatus:
    """Test GET /api/v1/deployment/infrastructure endpoint"""

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_success(self, mock_current_user):
        """Should get infrastructure status successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.validator.available_tools = {
                "github_api": {"available": True, "rate_limit": 5000},
                "jira_api": {"available": True, "rate_limit": 1000},
                "slack_api": {"available": False, "rate_limit": 0},
            }

            compute_type = Mock(value="compute")
            memory_type = Mock(value="memory")
            storage_type = Mock(value="storage")

            mock_orch.validator.available_resources = {
                compute_type: 8.0,
                memory_type: 16384,
                storage_type: 500,
            }
            mock_orch.validator.api_keys = {
                "github": True,
                "jira": True,
                "slack": False,
            }
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_infrastructure_status

            result = await get_infrastructure_status(mock_current_user)

            assert result.total_tools == 3
            assert result.total_resources == 3
            assert "github_api" in result.available_tools

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_empty(self, mock_current_user):
        """Should handle empty infrastructure"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.validator.available_tools = {}
            mock_orch.validator.available_resources = {}
            mock_orch.validator.api_keys = {}
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_infrastructure_status

            result = await get_infrastructure_status(mock_current_user)

            assert result.total_tools == 0
            assert result.total_resources == 0
            assert result.readiness_score == 0.0


# ============================================================================
# TEST STATISTICS
# ============================================================================


class TestGetStatistics:
    """Test GET /api/v1/deployment/statistics endpoint"""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, mock_current_user):
        """Should get deployment statistics successfully"""
        with patch("api.v1.deployment.get_deployment_orchestrator") as mock_get_orch:
            mock_orch = Mock()
            mock_orch.get_statistics.return_value = {
                "total_jobs": 100,
                "completed_jobs": 85,
                "failed_jobs": 10,
                "running_jobs": 5,
                "total_tokens_used": 500000,
                "total_cost_usd": 5.00,
            }
            mock_get_orch.return_value = mock_orch

            from api.v1.deployment import get_statistics

            result = await get_statistics(mock_current_user)

            assert result["total_jobs"] == 100
            assert result["completed_jobs"] == 85
            assert result["running_jobs"] == 5


# ============================================================================
# TEST HEALTH CHECK
# ============================================================================


class TestHealthCheck:
    """Test GET /api/v1/deployment/health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Should return healthy status"""
        from api.v1.deployment import health_check

        result = await health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "agent_deployment"
        assert "timestamp" in result
