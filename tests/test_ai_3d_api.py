"""
Tests for AI 3D API Endpoints
==============================

Tests for the AI 3D generation API endpoints.

Coverage:
- Model generation endpoint
- Model regeneration endpoint
- Job status and listing
- Model retrieval
- Error handling
"""

from unittest.mock import AsyncMock, patch

import pytest

from api.ai_3d_endpoints import (
    AI3DJobStore,
    AI3DPipelineStatus,
    GenerateModelRequest,
    ModelJobResponse,
    ModelStatusResponse,
    RegenerateModelRequest,
    ai_3d_router,
)

# =============================================================================
# Request Model Tests
# =============================================================================


class TestRequestModels:
    """Tests for request model validation."""

    def test_generate_model_request_minimal(self):
        """Should create request with minimal fields."""
        request = GenerateModelRequest(
            product_sku="SKR-001",
            image_urls=["https://example.com/image.jpg"],
        )

        assert request.product_sku == "SKR-001"
        assert len(request.image_urls) == 1
        assert request.quality_level == "production"  # default

    def test_generate_model_request_full(self):
        """Should create request with all fields."""
        request = GenerateModelRequest(
            product_sku="SKR-001",
            image_urls=[
                "https://example.com/front.jpg",
                "https://example.com/back.jpg",
                "https://example.com/side.jpg",
            ],
            quality_level="draft",
            validate_fidelity=True,
            generate_photoshoot=True,
        )

        assert len(request.image_urls) == 3
        assert request.quality_level == "draft"
        assert request.validate_fidelity is True

    def test_regenerate_model_request(self):
        """Should create regenerate request."""
        request = RegenerateModelRequest(
            product_sku="SKR-001",
            quality_level="production",
            force=True,
        )

        assert request.force is True
        assert request.quality_level == "production"


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Tests for response model structures."""

    def test_model_job_response(self):
        """Should create ModelJobResponse."""
        response = ModelJobResponse(
            job_id="ai3d_abc123",
            product_sku="SKR-001",
            status="completed",
            started_at="2025-01-01T12:00:00Z",
            completed_at="2025-01-01T12:05:00Z",
            model_path="/models/SKR-001.glb",
            thumbnail_path="/thumbnails/SKR-001.jpg",
            polycount=50000,
            fidelity_score=0.95,
            errors=[],
        )

        assert response.job_id == "ai3d_abc123"
        assert response.status == "completed"
        assert response.fidelity_score == 0.95

    def test_model_status_response(self):
        """Should create ModelStatusResponse."""
        response = ModelStatusResponse(
            product_sku="SKR-001",
            has_model=True,
            model_path="/models/SKR-001.glb",
            model_format="glb",
            polycount=50000,
            texture_resolution=2048,
            created_at="2025-01-01T12:00:00Z",
            updated_at="2025-01-01T12:00:00Z",
        )

        assert response.has_model is True
        assert response.polycount == 50000

    def test_pipeline_status(self):
        """Should create AI3DPipelineStatus."""
        status = AI3DPipelineStatus(
            status="operational",
            queue_length=5,
            avg_generation_time_seconds=45.0,
            models_generated_today=25,
            daily_limit=100,
            huggingface_available=True,
            tripo_available=True,
        )

        assert status.status == "operational"
        assert status.queue_length == 5


# =============================================================================
# AI3DJobStore Tests
# =============================================================================


class TestAI3DJobStore:
    """Tests for AI3DJobStore."""

    @pytest.fixture
    def store(self):
        """Create fresh job store."""
        return AI3DJobStore()

    def test_create_job(self, store):
        """Should create new job."""
        job_id = store.create("SKR-001")

        assert job_id.startswith("ai3d_")

        job = store.get(job_id)
        assert job is not None
        assert job["product_sku"] == "SKR-001"
        assert job["status"] == "queued"

    def test_get_job(self, store):
        """Should retrieve job by ID."""
        job_id = store.create("SKR-001")

        job = store.get(job_id)

        assert job is not None
        assert job["job_id"] == job_id

    def test_update_job(self, store):
        """Should update job fields."""
        job_id = store.create("SKR-001")

        store.update(job_id, status="processing", polycount=25000)

        job = store.get(job_id)
        assert job["status"] == "processing"
        assert job["polycount"] == 25000

    def test_complete_job(self, store):
        """Should mark job as completed."""
        job_id = store.create("SKR-001")

        store.complete(
            job_id,
            {
                "model_path": "/models/SKR-001.glb",
                "polycount": 50000,
                "fidelity_score": 0.95,
            },
        )

        job = store.get(job_id)
        assert job["status"] == "completed"
        assert job["model_path"] == "/models/SKR-001.glb"
        assert job["completed_at"] is not None

    def test_fail_job(self, store):
        """Should mark job as failed."""
        job_id = store.create("SKR-001")

        store.fail(job_id, "HuggingFace API error")

        job = store.get(job_id)
        assert job["status"] == "failed"
        assert "HuggingFace API error" in job["errors"]

    def test_list_jobs(self, store):
        """Should list recent jobs."""
        for i in range(5):
            store.create(f"SKR-00{i}")

        jobs = store.list_jobs(limit=3)

        assert len(jobs) == 3


# =============================================================================
# Router Tests
# =============================================================================


class TestAI3DRouter:
    """Tests for AI 3D router endpoints."""

    def test_router_has_prefix(self):
        """Should have correct prefix."""
        assert ai_3d_router.prefix == "/ai-3d"

    def test_router_has_tags(self):
        """Should have tags."""
        assert "AI 3D Generation" in ai_3d_router.tags

    def test_router_has_endpoints(self):
        """Should have expected endpoints."""
        routes = [r.path for r in ai_3d_router.routes]
        prefix = ai_3d_router.prefix

        assert f"{prefix}/status" in routes
        assert f"{prefix}/jobs" in routes
        assert f"{prefix}/generate-model" in routes
        assert f"{prefix}/models/{{product_sku}}" in routes


# =============================================================================
# Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
class TestAI3DEndpoints:
    """Tests for AI 3D endpoint responses."""

    async def test_get_pipeline_status(self):
        """Should return pipeline status."""
        from api.ai_3d_endpoints import get_pipeline_status

        status = await get_pipeline_status()

        assert isinstance(status, AI3DPipelineStatus)
        assert status.status in ["operational", "degraded", "offline"]

    async def test_list_jobs(self):
        """Should list generation jobs."""
        from api.ai_3d_endpoints import list_jobs

        response = await list_jobs(limit=20)

        assert isinstance(response, list)

    async def test_generate_model(self):
        """Should generate 3D model."""
        from api.ai_3d_endpoints import generate_model

        request = GenerateModelRequest(
            product_sku="SKR-001",
            image_urls=["https://example.com/image.jpg"],
        )

        with patch(
            "api.ai_3d_endpoints.run_model_generation", new_callable=AsyncMock
        ):
            response = await generate_model(request, background_tasks=None)

            assert isinstance(response, ModelJobResponse)
            assert response.product_sku == "SKR-001"

    async def test_get_model_status(self):
        """Should get model status."""
        from api.ai_3d_endpoints import get_model_status

        response = await get_model_status("SKR-001")

        assert isinstance(response, ModelStatusResponse)
        assert response.product_sku == "SKR-001"

    async def test_get_job(self):
        """Should get specific job."""
        from api.ai_3d_endpoints import ai_3d_job_store, get_job

        # Create a job first
        job_id = ai_3d_job_store.create("SKR-TEST")

        response = await get_job(job_id)

        assert isinstance(response, ModelJobResponse)
        assert response.job_id == job_id

    async def test_get_job_not_found(self):
        """Should raise 404 for nonexistent job."""
        from fastapi import HTTPException

        from api.ai_3d_endpoints import get_job

        with pytest.raises(HTTPException) as exc_info:
            await get_job("nonexistent_job_id")

        assert exc_info.value.status_code == 404


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai3d_integration(client, auth_headers):
    """Test AI 3D endpoints with authenticated client."""
    # Get pipeline status
    response = await client.get(
        "/api/v1/ai-3d/status",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "status" in data

    # Generate model
    response = await client.post(
        "/api/v1/ai-3d/generate-model",
        json={
            "product_sku": "SKR-TEST",
            "image_urls": ["https://example.com/image.jpg"],
        },
        headers=auth_headers,
    )

    assert response.status_code in [200, 201, 202]
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Get job status
    response = await client.get(
        f"/api/v1/ai-3d/jobs/{job_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id


__all__ = [
    "TestRequestModels",
    "TestResponseModels",
    "TestAI3DJobStore",
    "TestAI3DRouter",
    "TestAI3DEndpoints",
]
