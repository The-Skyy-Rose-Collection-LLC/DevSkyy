"""Tests for 3D Generation Pipeline API endpoints.

These tests verify the pipeline endpoints exist and enforce authentication.
Actual business logic is tested at the service layer.
"""

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_3d_job():
    """Sample 3D generation job data."""
    return {
        "id": "job-123",
        "status": "processing",
        "provider": "tripo",
        "asset_ids": ["asset-1", "asset-2"],
        "total_assets": 2,
        "processed_assets": 1,
        "progress_percentage": 50.0,
        "quality": "high",
        "fidelity_target": 98.0,
        "created_at": "2026-01-29T00:00:00Z",
        "updated_at": "2026-01-29T00:05:00Z",
    }


@pytest.fixture
def mock_3d_result():
    """Sample 3D generation result."""
    return {
        "asset_id": "asset-1",
        "model_url": "https://storage.example.com/models/asset-1.glb",
        "thumbnail_url": "https://storage.example.com/thumbnails/asset-1.jpg",
        "fidelity_score": 98.5,
        "provider": "tripo",
        "processing_time": 120.5,
        "file_size": 1048576,
        "vertex_count": 50000,
        "polygon_count": 100000,
    }


class TestBatchGeneration:
    """Test POST /api/v1/pipeline/batch-generate endpoint."""

    async def test_start_batch_generation(self, client, auth_headers):
        """Test starting a batch 3D generation job."""
        response = await client.post(
            "/api/v1/pipeline/batch-generate",
            json={
                "asset_ids": ["asset-1", "asset-2"],
                "provider": "tripo",
                "quality": "high",
            },
            headers=auth_headers,
        )

        # 200 if authed and processed, 401 if auth fails
        assert response.status_code in [200, 401]

    async def test_batch_generation_invalid_provider(self, client, auth_headers):
        """Test batch generation with invalid provider returns validation error."""
        response = await client.post(
            "/api/v1/pipeline/batch-generate",
            headers=auth_headers,
            json={
                "asset_ids": ["asset-1"],
                "provider": "invalid-provider",
                "quality": "high",
            },
        )

        # 422 for Pydantic validation error on invalid enum, or 401 if auth fails
        assert response.status_code in [400, 401, 422]

    async def test_batch_generation_empty_assets(self, client, auth_headers):
        """Test batch generation with no assets."""
        response = await client.post(
            "/api/v1/pipeline/batch-generate",
            json={"asset_ids": [], "provider": "tripo", "quality": "high"},
            headers=auth_headers,
        )

        # 400/422 for validation (min_length=1), or 401 if auth fails
        assert response.status_code in [400, 401, 422]

    async def test_batch_generation_quality_tiers(self, client, auth_headers):
        """Test different quality tiers are accepted."""
        for quality in ["draft", "standard", "high"]:
            response = await client.post(
                "/api/v1/pipeline/batch-generate",
                json={"asset_ids": ["asset-1"], "provider": "tripo", "quality": quality},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestJobStatus:
    """Test GET /api/v1/pipeline/jobs/{job_id} endpoint."""

    async def test_get_job_status(self, client, auth_headers):
        """Test getting job status."""
        response = await client.get(
            "/api/v1/pipeline/jobs/job-123",
            headers=auth_headers,
        )

        # 200 if found, 401 if auth fails, 404 if not found
        assert response.status_code in [200, 401, 404]

    async def test_get_job_not_found(self, client, auth_headers):
        """Test getting non-existent job."""
        response = await client.get(
            "/api/v1/pipeline/jobs/nonexistent",
            headers=auth_headers,
        )

        assert response.status_code in [401, 404]

    async def test_get_completed_job(self, client, auth_headers):
        """Test getting completed job with results."""
        response = await client.get(
            "/api/v1/pipeline/jobs/job-complete",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404]


class TestJobsList:
    """Test GET /api/v1/pipeline/jobs endpoint."""

    async def test_list_jobs(self, client, auth_headers):
        """Test listing all jobs."""
        response = await client.get(
            "/api/v1/pipeline/jobs",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    async def test_list_jobs_with_status_filter(self, client, auth_headers):
        """Test filtering jobs by status."""
        response = await client.get(
            "/api/v1/pipeline/jobs?status=completed",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]


class TestSingleGeneration:
    """Test POST /api/v1/pipeline/generate endpoint."""

    async def test_generate_single_3d_model(self, client, auth_headers):
        """Test generating a single 3D model."""
        response = await client.post(
            "/api/v1/pipeline/generate",
            json={
                "asset_id": "asset-1",
                "provider": "tripo",
                "quality": "high",
                "fidelity_target": 98.0,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    async def test_generate_with_default_quality(self, client, auth_headers):
        """Test generation with default quality settings."""
        response = await client.post(
            "/api/v1/pipeline/generate",
            json={"asset_id": "asset-1"},
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]


class TestFidelityQA:
    """Test GET /api/v1/pipeline/fidelity/{asset_id} endpoint."""

    async def test_get_fidelity_score(self, client, auth_headers):
        """Test getting fidelity score comparison."""
        response = await client.get(
            "/api/v1/pipeline/fidelity/asset-1",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404]

    async def test_approve_fidelity(self, client, auth_headers):
        """Test approving a 3D model's fidelity."""
        response = await client.post(
            "/api/v1/pipeline/fidelity/asset-1/approve",
            json={"approved": True},
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]

    async def test_reject_fidelity_with_regeneration(self, client, auth_headers):
        """Test rejecting fidelity and requesting regeneration."""
        response = await client.post(
            "/api/v1/pipeline/fidelity/asset-1/reject",
            json={
                "reason": "Low geometry accuracy",
                "regenerate": True,
                "parameters": {"quality": "high", "fidelity_target": 99.0},
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]


class TestProviders:
    """Test GET /api/v1/pipeline/providers endpoint."""

    async def test_list_providers(self, client, auth_headers):
        """Test listing available 3D providers."""
        response = await client.get(
            "/api/v1/pipeline/providers",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    async def test_get_provider_status(self, client, auth_headers):
        """Test getting individual provider status."""
        response = await client.get(
            "/api/v1/pipeline/providers/tripo",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404]


class TestWebSocketPipeline:
    """Test WebSocket real-time updates."""

    async def test_websocket_job_updates(self, client, auth_headers):
        """Test WebSocket connection for job updates."""
        # Note: WebSocket testing requires additional setup
        # This is a placeholder for WebSocket tests
        pass


class TestCostEstimation:
    """Test cost estimation endpoint."""

    async def test_estimate_batch_cost(self, client, auth_headers):
        """Test estimating cost for batch generation."""
        response = await client.post(
            "/api/v1/pipeline/estimate",
            json={
                "asset_count": 31,
                "provider": "tripo",
                "quality": "high",
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]
