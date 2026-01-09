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

import pytest

from api.ai_3d_endpoints import (
    GenerateModelRequest,
    GenerateModelResponse,
    JobStore,
    ModelInfoResponse,
    PipelineStatusResponse,
    RegenerateRequest,
    ai_3d_router,
    get_job,
    get_model_info,
    get_pipeline_status,
    list_jobs,
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
        )

        assert request.product_sku == "SKR-001"
        assert request.quality_level == "high"  # default
        assert request.validate_fidelity is True  # default

    def test_generate_model_request_full(self):
        """Should create request with all fields."""
        request = GenerateModelRequest(
            product_sku="SKR-001",
            quality_level="draft",
            validate_fidelity=False,
        )

        assert request.quality_level == "draft"
        assert request.validate_fidelity is False

    def test_generate_model_request_quality_levels(self):
        """Should accept valid quality levels."""
        for level in ["draft", "standard", "high"]:
            request = GenerateModelRequest(
                product_sku="SKR-001",
                quality_level=level,
            )
            assert request.quality_level == level

    def test_regenerate_request(self):
        """Should create regenerate request."""
        request = RegenerateRequest(
            product_sku="SKR-001",
            feedback={"reason": "texture_quality", "notes": "Need better PBR materials"},
        )

        assert request.product_sku == "SKR-001"
        assert "reason" in request.feedback

    def test_regenerate_request_empty_feedback(self):
        """Should allow empty feedback dict."""
        request = RegenerateRequest(
            product_sku="SKR-001",
        )

        assert request.feedback == {}


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Tests for response model structures."""

    def test_generate_model_response(self):
        """Should create GenerateModelResponse."""
        response = GenerateModelResponse(
            job_id="ai3d_abc123",
            product_sku="SKR-001",
            status="queued",
            created_at="2026-01-01T12:00:00Z",
        )

        assert response.job_id == "ai3d_abc123"
        assert response.product_sku == "SKR-001"
        assert response.status == "queued"
        assert response.model_url is None
        assert response.thumbnail_url is None

    def test_generate_model_response_completed(self):
        """Should create completed response with URLs."""
        response = GenerateModelResponse(
            job_id="ai3d_abc123",
            product_sku="SKR-001",
            status="completed",
            created_at="2026-01-01T12:00:00Z",
            model_url="/assets/models/SKR-001.glb",
            thumbnail_url="/assets/thumbnails/SKR-001_thumb.png",
            metrics={"vertex_count": 50000, "face_count": 25000},
            validation={"fidelity_score": 0.95, "passed": True},
        )

        assert response.model_url == "/assets/models/SKR-001.glb"
        assert response.metrics["vertex_count"] == 50000
        assert response.validation["fidelity_score"] == 0.95

    def test_model_info_response_exists(self):
        """Should create ModelInfoResponse for existing model."""
        response = ModelInfoResponse(
            product_sku="SKR-001",
            model_path="/models/SKR-001.glb",
            model_url="/assets/models/SKR-001.glb",
            thumbnail_url="/assets/thumbnails/SKR-001_thumb.png",
            exists=True,
            fidelity_score=0.95,
            vertex_count=50000,
            face_count=25000,
            file_size_mb=1.5,
            created_at="2026-01-01T12:00:00Z",
        )

        assert response.exists is True
        assert response.fidelity_score == 0.95
        assert response.vertex_count == 50000

    def test_model_info_response_not_exists(self):
        """Should create ModelInfoResponse for non-existent model."""
        response = ModelInfoResponse(
            product_sku="SKR-001",
            exists=False,
        )

        assert response.exists is False
        assert response.model_path is None
        assert response.model_url is None

    def test_pipeline_status_response(self):
        """Should create PipelineStatusResponse."""
        status = PipelineStatusResponse(
            status="operational",
            active_jobs=5,
            completed_jobs=100,
            failed_jobs=3,
            available_models=["triposr", "hunyuan3d"],
            last_generation="2026-01-01T12:00:00Z",
        )

        assert status.status == "operational"
        assert status.active_jobs == 5
        assert status.completed_jobs == 100
        assert "triposr" in status.available_models


# =============================================================================
# JobStore Tests
# =============================================================================


class TestJobStore:
    """Tests for JobStore."""

    @pytest.fixture
    def store(self):
        """Create fresh job store."""
        return JobStore()

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

    def test_get_nonexistent_job(self, store):
        """Should return None for nonexistent job."""
        job = store.get("nonexistent_job_id")

        assert job is None

    def test_update_job(self, store):
        """Should update job fields."""
        job_id = store.create("SKR-001")

        store.update(job_id, status="processing")

        job = store.get(job_id)
        assert job["status"] == "processing"

    def test_complete_job(self, store):
        """Should mark job as completed."""
        job_id = store.create("SKR-001")

        store.complete(
            job_id,
            {
                "model_path": "/models/SKR-001.glb",
                "fidelity_score": 0.95,
            },
        )

        job = store.get(job_id)
        assert job["status"] == "completed"
        assert job["result"]["model_path"] == "/models/SKR-001.glb"
        assert job["completed_at"] is not None

    def test_fail_job(self, store):
        """Should mark job as failed."""
        job_id = store.create("SKR-001")

        store.fail(job_id, "HuggingFace API error")

        job = store.get(job_id)
        assert job["status"] == "failed"
        assert job["error"] == "HuggingFace API error"
        assert job["completed_at"] is not None

    def test_list_jobs(self, store):
        """Should list recent jobs."""
        for i in range(5):
            store.create(f"SKR-00{i}")

        jobs = store.list_jobs(limit=3)

        assert len(jobs) == 3

    def test_list_jobs_ordered_by_date(self, store):
        """Should return jobs ordered by created_at descending."""
        for i in range(5):
            store.create(f"SKR-00{i}")

        jobs = store.list_jobs()

        # Most recent first
        assert len(jobs) == 5

    def test_stats(self, store):
        """Should calculate job statistics."""
        job_id1 = store.create("SKR-001")
        job_id2 = store.create("SKR-002")
        store.create("SKR-003")  # stays queued (active)

        store.complete(job_id1, {"success": True})
        store.fail(job_id2, "Error")

        stats = store.stats

        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["active"] == 1


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

        # Routes are relative to prefix
        assert "/ai-3d/status" in routes
        assert "/ai-3d/jobs" in routes
        assert "/ai-3d/generate-model" in routes
        assert "/ai-3d/models/{product_sku}" in routes


# =============================================================================
# Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
class TestAI3DEndpoints:
    """Tests for AI 3D endpoint responses."""

    async def test_get_pipeline_status(self):
        """Should return pipeline status."""
        status = await get_pipeline_status()

        assert isinstance(status, PipelineStatusResponse)
        assert status.status == "operational"
        assert status.active_jobs >= 0
        assert len(status.available_models) > 0

    async def test_list_jobs(self):
        """Should list generation jobs."""
        response = await list_jobs(limit=20)

        assert isinstance(response, list)

    async def test_list_jobs_with_limit(self):
        """Should respect limit parameter."""
        response = await list_jobs(limit=5)

        assert isinstance(response, list)
        assert len(response) <= 5

    async def test_get_job_not_found(self):
        """Should raise 404 for nonexistent job."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_job("nonexistent_job_id")

        assert exc_info.value.status_code == 404

    async def test_get_model_info_not_exists(self):
        """Should return exists=False for non-existent model."""
        response = await get_model_info("NONEXISTENT-SKU")

        assert isinstance(response, ModelInfoResponse)
        assert response.product_sku == "NONEXISTENT-SKU"
        assert response.exists is False


# =============================================================================
# Alias Tests (backwards compatibility)
# =============================================================================


class TestAliases:
    """Tests for backwards compatible aliases."""

    def test_ai3d_job_store_alias(self):
        """AI3DJobStore should be alias for JobStore."""
        from api.ai_3d_endpoints import AI3DJobStore

        assert AI3DJobStore is JobStore

    def test_ai3d_pipeline_status_alias(self):
        """AI3DPipelineStatus should be alias for PipelineStatusResponse."""
        from api.ai_3d_endpoints import AI3DPipelineStatus

        assert AI3DPipelineStatus is PipelineStatusResponse

    def test_regenerate_model_request_alias(self):
        """RegenerateModelRequest should be alias for RegenerateRequest."""
        from api.ai_3d_endpoints import RegenerateModelRequest

        assert RegenerateModelRequest is RegenerateRequest

    def test_model_job_response_alias(self):
        """ModelJobResponse should be alias for GenerateModelResponse."""
        from api.ai_3d_endpoints import ModelJobResponse

        assert ModelJobResponse is GenerateModelResponse


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Integration test: Requires running FastAPI app with 3D pipeline. "
    "Run with: pytest -m integration --run-integration"
)
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


__all__ = [
    "TestRequestModels",
    "TestResponseModels",
    "TestJobStore",
    "TestAI3DRouter",
    "TestAI3DEndpoints",
    "TestAliases",
]
