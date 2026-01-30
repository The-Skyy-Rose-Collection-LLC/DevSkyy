"""Tests for 3D Generation Pipeline API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

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

    async def test_start_batch_generation(self, client, mock_3d_job, auth_headers):
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

        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["total_assets"] == 2
        assert data["status"] == "processing"

    async def test_batch_generation_invalid_provider(self, client, auth_headers):
        """Test batch generation with invalid provider."""
        response = client.post(
            "/api/v1/pipeline/batch-generate",
            json={
                "asset_ids": ["asset-1"],
                "provider": "invalid-provider",
                "quality": "high",
            },
        )

        assert response.status_code == 400

    async def test_batch_generation_empty_assets(self, client, auth_headers):
        """Test batch generation with no assets."""
        response = client.post(
            "/api/v1/pipeline/batch-generate",
            json={"asset_ids": [], "provider": "tripo", "quality": "high"},
        )

        assert response.status_code == 400

    async def test_batch_generation_quality_tiers(self, client, auth_headers):
        """Test different quality tiers."""
        for quality in ["draft", "standard", "high"]:
            with patch("api.v1.pipeline.start_batch_generation") as mock_start:
                mock_start.return_value = {"id": f"job-{quality}", "quality": quality}

                response = client.post(
                    "/api/v1/pipeline/batch-generate",
                    json={"asset_ids": ["asset-1"], "provider": "tripo", "quality": quality},
                )

                assert response.status_code == 200


class TestJobStatus:
    """Test GET /api/v1/pipeline/jobs/{job_id} endpoint."""

    async def test_get_job_status(self, client, auth_headers, mock_3d_job):
        """Test getting job status."""
        with patch("api.v1.pipeline.get_job") as mock_get:
            mock_get.return_value = mock_3d_job

            response = client.get("/api/v1/pipeline/jobs/job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "job-123"
            assert data["progress_percentage"] == 50.0

    async def test_get_job_not_found(self, client, auth_headers):
        """Test getting non-existent job."""
        with patch("api.v1.pipeline.get_job") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/pipeline/jobs/nonexistent")

            assert response.status_code == 404

    async def test_get_completed_job(self, client, auth_headers):
        """Test getting completed job with results."""
        completed_job = {
            "id": "job-complete",
            "status": "completed",
            "total_assets": 2,
            "processed_assets": 2,
            "progress_percentage": 100.0,
            "results": [
                {"asset_id": "asset-1", "fidelity_score": 98.5},
                {"asset_id": "asset-2", "fidelity_score": 99.1},
            ],
        }

        with patch("api.v1.pipeline.get_job") as mock_get:
            mock_get.return_value = completed_job

            response = client.get("/api/v1/pipeline/jobs/job-complete")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert len(data["results"]) == 2


class TestJobsList:
    """Test GET /api/v1/pipeline/jobs endpoint."""

    async def test_list_jobs(self, client, auth_headers, mock_3d_job):
        """Test listing all jobs."""
        with patch("api.v1.pipeline.list_jobs") as mock_list:
            mock_list.return_value = {
                "jobs": [mock_3d_job],
                "total": 1,
                "page": 1,
                "page_size": 20,
            }

            response = client.get("/api/v1/pipeline/jobs")

            assert response.status_code == 200
            data = response.json()
            assert len(data["jobs"]) == 1

    async def test_list_jobs_with_status_filter(self, client, auth_headers):
        """Test filtering jobs by status."""
        response = client.get("/api/v1/pipeline/jobs?status=completed")

        assert response.status_code == 200


class TestSingleGeneration:
    """Test POST /api/v1/pipeline/generate endpoint."""

    async def test_generate_single_3d_model(self, client, auth_headers, mock_3d_result):
        """Test generating a single 3D model."""
        with patch("api.v1.pipeline.generate_3d_model") as mock_gen:
            mock_gen.return_value = mock_3d_result

            response = client.post(
                "/api/v1/pipeline/generate",
                json={
                    "asset_id": "asset-1",
                    "provider": "tripo",
                    "quality": "high",
                    "fidelity_target": 98.0,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["asset_id"] == "asset-1"
            assert data["fidelity_score"] >= 98.0

    async def test_generate_with_default_quality(self, client, auth_headers):
        """Test generation with default quality settings."""
        with patch("api.v1.pipeline.generate_3d_model") as mock_gen:
            mock_gen.return_value = {"asset_id": "asset-1", "quality": "standard"}

            response = client.post(
                "/api/v1/pipeline/generate",
                json={"asset_id": "asset-1"},
            )

            assert response.status_code == 200


class TestFidelityQA:
    """Test GET /api/v1/pipeline/fidelity/{asset_id} endpoint."""

    async def test_get_fidelity_score(self, client, auth_headers):
        """Test getting fidelity score comparison."""
        fidelity_data = {
            "asset_id": "asset-1",
            "reference_url": "https://storage.example.com/assets/asset-1.jpg",
            "model_url": "https://storage.example.com/models/asset-1.glb",
            "fidelity_score": 98.5,
            "breakdown": {
                "geometry": 98.0,
                "materials": 99.0,
                "colors": 99.5,
                "proportions": 97.0,
            },
            "approved": True,
        }

        with patch("api.v1.pipeline.get_fidelity") as mock_fidelity:
            mock_fidelity.return_value = fidelity_data

            response = client.get("/api/v1/pipeline/fidelity/asset-1")

            assert response.status_code == 200
            data = response.json()
            assert data["fidelity_score"] == 98.5
            assert data["breakdown"]["colors"] == 99.5

    async def test_approve_fidelity(self, client, auth_headers):
        """Test approving a 3D model's fidelity."""
        with patch("api.v1.pipeline.approve_fidelity") as mock_approve:
            mock_approve.return_value = {"asset_id": "asset-1", "approved": True}

            response = client.post(
                "/api/v1/pipeline/fidelity/asset-1/approve",
                json={"approved": True},
            )

            assert response.status_code == 200

    async def test_reject_fidelity_with_regeneration(self, client, auth_headers):
        """Test rejecting fidelity and requesting regeneration."""
        with patch("api.v1.pipeline.reject_fidelity") as mock_reject:
            mock_reject.return_value = {"asset_id": "asset-1", "regenerate": True}

            response = client.post(
                "/api/v1/pipeline/fidelity/asset-1/reject",
                json={
                    "reason": "Low geometry accuracy",
                    "regenerate": True,
                    "parameters": {"quality": "high", "fidelity_target": 99.0},
                },
            )

            assert response.status_code == 200


class TestProviders:
    """Test GET /api/v1/pipeline/providers endpoint."""

    async def test_list_providers(self, client, auth_headers):
        """Test listing available 3D providers."""
        providers = {
            "providers": [
                {
                    "id": "tripo",
                    "name": "Tripo3D",
                    "available": True,
                    "quality_tiers": ["draft", "standard", "high"],
                    "avg_processing_time": 120.0,
                    "fidelity_rating": 98.5,
                },
                {
                    "id": "replicate",
                    "name": "Replicate",
                    "available": True,
                    "quality_tiers": ["standard", "high"],
                    "avg_processing_time": 180.0,
                    "fidelity_rating": 96.0,
                },
            ]
        }

        with patch("api.v1.pipeline.get_providers") as mock_providers:
            mock_providers.return_value = providers

            response = client.get("/api/v1/pipeline/providers")

            assert response.status_code == 200
            data = response.json()
            assert len(data["providers"]) >= 2

    async def test_get_provider_status(self, client, auth_headers):
        """Test getting individual provider status."""
        with patch("api.v1.pipeline.get_provider_status") as mock_status:
            mock_status.return_value = {
                "id": "tripo",
                "available": True,
                "queue_length": 5,
                "est_wait_time": 300.0,
            }

            response = client.get("/api/v1/pipeline/providers/tripo")

            assert response.status_code == 200


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
        with patch("api.v1.pipeline.estimate_cost") as mock_cost:
            mock_cost.return_value = {
                "total_cost": 15.50,
                "per_asset_cost": 0.50,
                "asset_count": 31,
                "provider": "tripo",
                "quality": "high",
            }

            response = client.post(
                "/api/v1/pipeline/estimate",
                json={
                    "asset_count": 31,
                    "provider": "tripo",
                    "quality": "high",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_cost"] == 15.50
