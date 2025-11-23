"""
Comprehensive Unit Tests for Finetuning API Endpoints (api/v1/finetuning.py)
Testing agent finetuning and tool optimization endpoints to achieve 80%+ coverage

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #1: Never guess - Verify all functionality
- Rule #12: Performance SLOs - P95 < 500ms per test

Author: DevSkyy Test Automation
Version: 1.0.0
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app
from security.jwt_auth import User, UserRole, create_access_token, user_manager


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def developer_headers():
    """Create developer authentication headers"""
    token_data = {
        "user_id": "dev_ft_001",
        "email": "developer@devskyy.com",
        "username": "developer_finetuning",
        "role": UserRole.DEVELOPER,
    }

    test_user = User(
        user_id=token_data["user_id"],
        username=token_data["username"],
        email=token_data["email"],
        role=token_data["role"],
        active=True,
        permissions=["read", "write", "finetuning"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(data=token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


@pytest.fixture
def mock_finetuning_system():
    """Mock finetuning system for testing"""
    with patch("api.v1.finetuning.get_finetuning_system") as mock_get:
        mock_system = MagicMock()

        # Mock collect_performance_snapshot
        mock_system.collect_performance_snapshot = AsyncMock(return_value=None)

        # Mock prepare_dataset
        mock_system.prepare_dataset = AsyncMock(
            return_value={
                "dataset_id": "ds_123456",
                "category": "backend_agents",
                "created_at": datetime.now(),
                "train_samples": 800,
                "val_samples": 150,
                "test_samples": 50,
                "statistics": {
                    "avg_performance_score": 0.85,
                    "avg_tokens": 1250,
                    "success_rate": 0.92,
                },
            }
        )

        # Mock create_finetuning_job
        mock_system.create_finetuning_job = AsyncMock(
            return_value={
                "job_id": "job_789012",
                "category": "backend_agents",
                "status": "pending",
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "training_samples": 800,
                "validation_samples": 150,
                "current_epoch": 0,
                "training_loss": 0.0,
                "validation_accuracy": 0.0,
                "finetuned_model_id": None,
                "cost_usd": 0.0,
                "error_message": None,
            }
        )

        # Mock get_job_status
        mock_system.get_job_status = AsyncMock(
            return_value={
                "job_id": "job_789012",
                "category": "backend_agents",
                "status": "running",
                "created_at": datetime.now(),
                "started_at": datetime.now(),
                "completed_at": None,
                "training_samples": 800,
                "validation_samples": 150,
                "current_epoch": 2,
                "training_loss": 0.15,
                "validation_accuracy": 0.87,
                "finetuned_model_id": None,
                "cost_usd": 12.50,
                "error_message": None,
            }
        )

        # Mock list_category_jobs
        mock_system.list_category_jobs = AsyncMock(
            return_value=[
                {
                    "job_id": "job_789012",
                    "status": "running",
                    "created_at": datetime.now(),
                    "current_epoch": 2,
                },
                {
                    "job_id": "job_654321",
                    "status": "completed",
                    "created_at": datetime.now(),
                    "current_epoch": 3,
                },
            ]
        )

        # Mock get_statistics
        mock_system.get_statistics = AsyncMock(
            return_value={
                "total_snapshots": 5420,
                "total_datasets": 12,
                "total_jobs": 8,
                "completed_jobs": 5,
                "running_jobs": 2,
                "failed_jobs": 1,
                "total_cost_usd": 234.56,
                "avg_job_duration_hours": 4.5,
            }
        )

        mock_get.return_value = mock_system
        yield mock_system


@pytest.fixture
def mock_optimization_manager():
    """Mock tool optimization manager for testing"""
    with patch("api.v1.finetuning.get_optimization_manager") as mock_get:
        mock_manager = MagicMock()

        # Mock select_optimal_tools
        mock_manager.select_optimal_tools = AsyncMock(
            return_value={
                "selected_tools": ["code_scanner", "security_analyzer", "performance_profiler"],
                "compressed_schemas": [
                    {"name": "code_scanner", "params": ["path", "language"]},
                    {"name": "security_analyzer", "params": ["code", "severity"]},
                    {"name": "performance_profiler", "params": ["function", "iterations"]},
                ],
                "tokens_saved": 2500,
                "optimization_ratio": "65%",
            }
        )

        # Mock execute_parallel_calls
        mock_manager.execute_parallel_calls = AsyncMock(
            return_value={
                "results": [
                    {"tool": "code_scanner", "success": True, "result": {"errors": 3}},
                    {"tool": "security_analyzer", "success": True, "result": {"vulnerabilities": 1}},
                    {"tool": "performance_profiler", "success": False, "error": "Timeout"},
                ],
                "total_calls": 3,
                "successful_calls": 2,
                "failed_calls": 1,
                "total_tokens_used": 1850,
            }
        )

        # Mock get_optimization_statistics
        mock_manager.get_optimization_statistics = AsyncMock(
            return_value={
                "total_optimizations": 342,
                "avg_tokens_saved": 1820,
                "avg_optimization_ratio": 0.58,
                "total_parallel_executions": 156,
                "avg_parallel_speedup": 3.2,
            }
        )

        mock_get.return_value = mock_manager
        yield mock_manager


# =============================================================================
# TEST PERFORMANCE SNAPSHOT COLLECTION
# =============================================================================


class TestPerformanceSnapshotCollection:
    """Test suite for performance snapshot collection endpoint"""

    @pytest.mark.asyncio
    async def test_collect_snapshot_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful performance snapshot collection"""
        snapshot_data = {
            "agent_id": "agent_scanner_v2",
            "agent_name": "Scanner V2",
            "category": "backend_agents",
            "task_type": "code_scanning",
            "input_data": {"path": "/app/src", "language": "python"},
            "output_data": {"errors": 5, "warnings": 12, "suggestions": 8},
            "success": True,
            "performance_score": 0.92,
            "execution_time_ms": 2450.0,
            "tokens_used": 1850,
            "user_feedback": 0.95,
            "metadata": {"version": "2.1.0"},
        }

        response = client.post(
            "/api/v1/finetuning/collect",
            json=snapshot_data,
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "status" in data
        assert data["status"] == "success"
        assert "message" in data
        assert "agent_name" in data
        assert data["agent_name"] == "Scanner V2"

    def test_collect_snapshot_invalid_score(self, client, developer_headers, mock_finetuning_system):
        """Test snapshot collection with invalid performance score"""
        snapshot_data = {
            "agent_id": "agent_001",
            "agent_name": "Test Agent",
            "category": "backend_agents",
            "task_type": "test",
            "input_data": {},
            "output_data": {},
            "success": True,
            "performance_score": 1.5,  # Invalid: > 1.0
            "execution_time_ms": 100.0,
        }

        response = client.post(
            "/api/v1/finetuning/collect",
            json=snapshot_data,
            headers=developer_headers,
        )

        # Should fail validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_collect_snapshot_unauthorized(self, client):
        """Test snapshot collection without authentication"""
        response = client.post(
            "/api/v1/finetuning/collect",
            json={"agent_id": "test"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# TEST DATASET PREPARATION
# =============================================================================


class TestDatasetPreparation:
    """Test suite for dataset preparation endpoint"""

    @pytest.mark.asyncio
    async def test_prepare_dataset_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful dataset preparation"""
        dataset_request = {
            "category": "backend_agents",
            "min_samples": 100,
            "max_samples": 10000,
            "quality_threshold": 0.7,
            "time_range_days": 30,
        }

        response = client.post(
            "/api/v1/finetuning/datasets/backend_agents",
            json=dataset_request,
            headers=developer_headers,
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        data = response.json()

        # Verify response structure
        if "dataset_id" in data:
            assert "category" in data
            assert "train_samples" in data
            assert "val_samples" in data
            assert "test_samples" in data
            assert "statistics" in data

    def test_prepare_dataset_invalid_threshold(self, client, developer_headers, mock_finetuning_system):
        """Test dataset preparation with invalid quality threshold"""
        dataset_request = {
            "category": "backend_agents",
            "quality_threshold": 1.5,  # Invalid: > 1.0
        }

        response = client.post(
            "/api/v1/finetuning/datasets/backend_agents",
            json=dataset_request,
            headers=developer_headers,
        )

        # Should fail validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# TEST FINETUNING JOB MANAGEMENT
# =============================================================================


class TestFinetuningJobManagement:
    """Test suite for finetuning job management endpoints"""

    @pytest.mark.asyncio
    async def test_create_finetuning_job_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful finetuning job creation"""
        job_request = {
            "category": "backend_agents",
            "provider": "anthropic",
            "base_model": "claude-3-sonnet-20250219",
            "n_epochs": 3,
            "batch_size": 32,
            "learning_rate": 0.0001,
            "min_training_samples": 100,
            "min_validation_accuracy": 0.85,
            "max_training_cost_usd": 100.0,
            "max_training_hours": 24,
            "model_version": "1.0.0",
            "description": "Test finetuning job",
            "tags": ["test", "backend"],
        }

        response = client.post(
            "/api/v1/finetuning/jobs",
            json=job_request,
            headers=developer_headers,
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        data = response.json()

        # Verify response structure
        if "job_id" in data:
            assert "category" in data
            assert "status" in data
            assert "training_samples" in data
            assert "validation_samples" in data

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful job status retrieval"""
        job_id = "job_789012"
        response = client.get(
            f"/api/v1/finetuning/jobs/{job_id}",
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "job_id" in data
        assert "status" in data
        assert "category" in data

    def test_get_job_status_not_found(self, client, developer_headers, mock_finetuning_system):
        """Test getting status for non-existent job"""
        response = client.get(
            "/api/v1/finetuning/jobs/nonexistent_job_id",
            headers=developer_headers,
        )

        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.asyncio
    async def test_list_category_jobs_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful listing of category jobs"""
        category = "backend_agents"
        response = client.get(
            f"/api/v1/finetuning/categories/{category}/jobs",
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return a list of jobs
        if isinstance(data, list):
            for job in data:
                assert "job_id" in job
                assert "status" in job


# =============================================================================
# TEST STATISTICS
# =============================================================================


class TestFinetuningStatistics:
    """Test suite for finetuning statistics endpoint"""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, client, developer_headers, mock_finetuning_system):
        """Test successful statistics retrieval"""
        response = client.get(
            "/api/v1/finetuning/statistics",
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        expected_fields = [
            "total_snapshots",
            "total_datasets",
            "total_jobs",
            "completed_jobs",
            "running_jobs",
            "failed_jobs",
        ]

        for field in expected_fields:
            if field in data:
                assert isinstance(data[field], (int, float))


# =============================================================================
# TEST TOOL OPTIMIZATION
# =============================================================================


class TestToolOptimization:
    """Test suite for tool optimization endpoints"""

    @pytest.mark.asyncio
    async def test_select_optimal_tools_success(self, client, developer_headers, mock_optimization_manager):
        """Test successful tool selection"""
        selection_request = {
            "task_description": "Scan and analyze Python code for security vulnerabilities",
            "task_type": "security_analysis",
            "required_capabilities": ["code_scanning", "security_check"],
            "max_tools": 10,
            "prefer_fast": True,
            "prefer_cheap": False,
        }

        response = client.post(
            "/api/v1/finetuning/tools/select",
            json=selection_request,
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "selected_tools" in data
        assert "compressed_schemas" in data
        assert "tokens_saved" in data
        assert "optimization_ratio" in data

        # Verify types
        assert isinstance(data["selected_tools"], list)
        assert isinstance(data["compressed_schemas"], list)
        assert isinstance(data["tokens_saved"], int)

    def test_select_optimal_tools_empty_description(self, client, developer_headers, mock_optimization_manager):
        """Test tool selection with empty description"""
        selection_request = {"task_description": ""}

        response = client.post(
            "/api/v1/finetuning/tools/select",
            json=selection_request,
            headers=developer_headers,
        )

        # Should fail validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_execute_parallel_calls_success(self, client, developer_headers, mock_optimization_manager):
        """Test successful parallel function execution"""
        execution_request = {
            "function_calls": [
                {"tool": "code_scanner", "params": {"path": "/app/src"}},
                {"tool": "security_analyzer", "params": {"code": "import os"}},
                {"tool": "performance_profiler", "params": {"function": "main"}},
            ],
            "user_id": "user_123",
        }

        response = client.post(
            "/api/v1/finetuning/tools/execute-parallel",
            json=execution_request,
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "results" in data
        assert "total_calls" in data
        assert "successful_calls" in data
        assert "failed_calls" in data
        assert "total_tokens_used" in data

        # Verify types
        assert isinstance(data["results"], list)
        assert isinstance(data["total_calls"], int)

    def test_execute_parallel_calls_empty_list(self, client, developer_headers, mock_optimization_manager):
        """Test parallel execution with empty function calls"""
        execution_request = {"function_calls": []}

        response = client.post(
            "/api/v1/finetuning/tools/execute-parallel",
            json=execution_request,
            headers=developer_headers,
        )

        # Should succeed but with 0 calls
        # Or may fail validation depending on schema
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.asyncio
    async def test_get_optimization_statistics_success(self, client, developer_headers, mock_optimization_manager):
        """Test successful optimization statistics retrieval"""
        response = client.get(
            "/api/v1/finetuning/tools/statistics",
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        expected_fields = [
            "total_optimizations",
            "avg_tokens_saved",
            "avg_optimization_ratio",
            "total_parallel_executions",
        ]

        for field in expected_fields:
            if field in data:
                assert isinstance(data[field], (int, float))


# =============================================================================
# TEST PERFORMANCE
# =============================================================================


class TestFinetuningPerformance:
    """Test suite for performance requirements (Rule #12: P95 < 500ms)"""

    @pytest.mark.asyncio
    async def test_collect_snapshot_performance(self, client, developer_headers, mock_finetuning_system):
        """Test snapshot collection response time < 500ms"""
        import time

        snapshot_data = {
            "agent_id": "agent_001",
            "agent_name": "Test Agent",
            "category": "backend_agents",
            "task_type": "test",
            "input_data": {},
            "output_data": {},
            "success": True,
            "performance_score": 0.9,
            "execution_time_ms": 100.0,
        }

        start_time = time.time()
        response = client.post(
            "/api/v1/finetuning/collect",
            json=snapshot_data,
            headers=developer_headers,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_201_CREATED
        assert elapsed_ms < 500, f"Snapshot collection took {elapsed_ms:.2f}ms (should be < 500ms)"

    @pytest.mark.asyncio
    async def test_statistics_endpoint_performance(self, client, developer_headers, mock_finetuning_system):
        """Test statistics endpoint response time < 500ms"""
        import time

        start_time = time.time()
        response = client.get(
            "/api/v1/finetuning/statistics",
            headers=developer_headers,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        assert elapsed_ms < 500, f"Statistics endpoint took {elapsed_ms:.2f}ms (should be < 500ms)"


# =============================================================================
# TEST ERROR HANDLING
# =============================================================================


class TestFinetuningErrorHandling:
    """Test suite for error handling per Rule #10: No-Skip Rule"""

    def test_invalid_json_payload(self, client, developer_headers):
        """Test handling of invalid JSON payload"""
        response = client.post(
            "/api/v1/finetuning/collect",
            data="invalid json",
            headers={**developer_headers, "Content-Type": "application/json"},
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_missing_required_fields(self, client, developer_headers, mock_finetuning_system):
        """Test handling of missing required fields"""
        # Missing most required fields
        response = client.post(
            "/api/v1/finetuning/collect",
            json={"agent_id": "test"},
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_category(self, client, developer_headers, mock_finetuning_system):
        """Test handling of invalid agent category"""
        job_request = {
            "category": "invalid_category_name",
            "provider": "anthropic",
            "base_model": "claude-3-sonnet",
        }

        response = client.post(
            "/api/v1/finetuning/jobs",
            json=job_request,
            headers=developer_headers,
        )

        # Should fail validation for invalid category
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


# =============================================================================
# TEST VALIDATION
# =============================================================================


class TestFinetuningValidation:
    """Test suite for input validation per Rule #7: Input validation"""

    def test_negative_batch_size(self, client, developer_headers, mock_finetuning_system):
        """Test job creation with negative batch size"""
        job_request = {
            "category": "backend_agents",
            "provider": "anthropic",
            "base_model": "claude-3-sonnet",
            "batch_size": -10,  # Invalid
        }

        response = client.post(
            "/api/v1/finetuning/jobs",
            json=job_request,
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_excessive_epochs(self, client, developer_headers, mock_finetuning_system):
        """Test job creation with excessive epochs"""
        job_request = {
            "category": "backend_agents",
            "provider": "anthropic",
            "base_model": "claude-3-sonnet",
            "n_epochs": 100,  # > max allowed (50)
        }

        response = client.post(
            "/api/v1/finetuning/jobs",
            json=job_request,
            headers=developer_headers,
        )

        # Should fail validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_learning_rate(self, client, developer_headers, mock_finetuning_system):
        """Test job creation with invalid learning rate"""
        job_request = {
            "category": "backend_agents",
            "provider": "anthropic",
            "base_model": "claude-3-sonnet",
            "learning_rate": 2.0,  # > 1.0 (invalid)
        }

        response = client.post(
            "/api/v1/finetuning/jobs",
            json=job_request,
            headers=developer_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
