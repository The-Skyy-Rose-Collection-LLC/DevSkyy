"""
Tests for Virtual Try-On API
============================

Tests for the virtual try-on router and job management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.virtual_tryon import (
    GarmentCategory,
    TryOnMode,
    TryOnProvider,
    JobStatus,
    ModelGender,
    TryOnRequest,
    BatchTryOnRequest,
    GenerateModelRequest,
    JobResponse,
    BatchJobResponse,
    ModelGenerationResponse,
    PipelineStatus,
    ProviderInfo,
    TryOnJobStore,
    virtual_tryon_router,
)


class TestEnums:
    """Test enum values."""

    def test_garment_categories(self):
        """Should have garment categories."""
        assert GarmentCategory.TOPS.value == "tops"
        assert GarmentCategory.BOTTOMS.value == "bottoms"
        assert GarmentCategory.DRESSES.value == "dresses"
        assert GarmentCategory.OUTERWEAR.value == "outerwear"
        assert GarmentCategory.FULL_BODY.value == "full_body"

    def test_tryon_modes(self):
        """Should have try-on modes."""
        assert TryOnMode.QUALITY.value == "quality"
        assert TryOnMode.BALANCED.value == "balanced"
        assert TryOnMode.FAST.value == "fast"

    def test_providers(self):
        """Should have providers."""
        assert TryOnProvider.FASHN.value == "fashn"
        assert TryOnProvider.IDM_VTON.value == "idm_vton"
        assert TryOnProvider.ROUND_TABLE.value == "round_table"

    def test_job_status(self):
        """Should have job statuses."""
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"

    def test_model_gender(self):
        """Should have model genders."""
        assert ModelGender.FEMALE.value == "female"
        assert ModelGender.MALE.value == "male"
        assert ModelGender.NEUTRAL.value == "neutral"


class TestRequestModels:
    """Test request model validation."""

    def test_tryon_request_defaults(self):
        """Should have sensible defaults."""
        request = TryOnRequest(
            model_image_url="https://example.com/model.jpg",
            garment_image_url="https://example.com/garment.jpg",
        )

        assert request.category == GarmentCategory.TOPS
        assert request.mode == TryOnMode.BALANCED
        assert request.provider == TryOnProvider.FASHN
        assert request.product_id is None

    def test_tryon_request_custom(self):
        """Should accept custom values."""
        request = TryOnRequest(
            model_image_url="https://example.com/model.jpg",
            garment_image_url="https://example.com/dress.jpg",
            category=GarmentCategory.DRESSES,
            mode=TryOnMode.QUALITY,
            provider=TryOnProvider.IDM_VTON,
            product_id="SKR-001",
        )

        assert request.category == GarmentCategory.DRESSES
        assert request.mode == TryOnMode.QUALITY
        assert request.provider == TryOnProvider.IDM_VTON
        assert request.product_id == "SKR-001"

    def test_batch_request_validation(self):
        """Should validate batch request."""
        request = BatchTryOnRequest(
            model_image_url="https://example.com/model.jpg",
            garments=[
                {"garment_image_url": "https://example.com/shirt.jpg", "category": "tops"},
                {"garment_image_url": "https://example.com/pants.jpg", "category": "bottoms"},
            ],
        )

        assert len(request.garments) == 2
        assert request.mode == TryOnMode.BALANCED

    def test_model_generation_request(self):
        """Should create model generation request."""
        request = GenerateModelRequest(
            prompt="Professional model in studio",
            gender=ModelGender.FEMALE,
            style="editorial",
        )

        assert request.gender == ModelGender.FEMALE
        assert request.style == "editorial"


class TestJobStore:
    """Test job store operations."""

    def test_create_tryon_job(self):
        """Should create try-on job."""
        store = TryOnJobStore()

        job = store.create_tryon_job(
            provider=TryOnProvider.FASHN,
            category=GarmentCategory.TOPS,
            metadata={"product_id": "SKR-001"},
        )

        assert job.job_id.startswith("tryon_")
        assert job.status == JobStatus.QUEUED
        assert job.provider == "fashn"
        assert job.category == "tops"
        assert job.metadata["product_id"] == "SKR-001"

    def test_get_tryon_job(self):
        """Should retrieve job by ID."""
        store = TryOnJobStore()
        created = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        retrieved = store.get_tryon_job(created.job_id)

        assert retrieved is not None
        assert retrieved.job_id == created.job_id

    def test_get_nonexistent_job(self):
        """Should return None for nonexistent job."""
        store = TryOnJobStore()

        result = store.get_tryon_job("nonexistent_id")

        assert result is None

    def test_update_tryon_job(self):
        """Should update job fields."""
        store = TryOnJobStore()
        job = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.update_tryon_job(job.job_id, status=JobStatus.PROCESSING, progress=0.5)

        updated = store.get_tryon_job(job.job_id)
        assert updated.status == JobStatus.PROCESSING
        assert updated.progress == 0.5

    def test_complete_tryon_job(self):
        """Should mark job as completed."""
        store = TryOnJobStore()
        job = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.complete_tryon_job(
            job.job_id,
            result_url="https://cdn.example.com/result.jpg",
            result_path="/assets/tryon/result.jpg",
            duration_ms=12000,
            cost_usd=0.075,
        )

        completed = store.get_tryon_job(job.job_id)
        assert completed.status == JobStatus.COMPLETED
        assert completed.result_url == "https://cdn.example.com/result.jpg"
        assert completed.cost_usd == 0.075
        assert completed.progress == 1.0

    def test_fail_tryon_job(self):
        """Should mark job as failed."""
        store = TryOnJobStore()
        job = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.fail_tryon_job(job.job_id, "API timeout")

        failed = store.get_tryon_job(job.job_id)
        assert failed.status == JobStatus.FAILED
        assert failed.error == "API timeout"

    def test_create_batch_job(self):
        """Should create batch job."""
        store = TryOnJobStore()

        jobs = [
            store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS),
            store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.BOTTOMS),
        ]

        batch = store.create_batch_job(jobs)

        assert batch.batch_id.startswith("batch_")
        assert batch.total_items == 2
        assert batch.completed_items == 0
        assert len(batch.jobs) == 2

    def test_update_batch_progress(self):
        """Should update batch progress based on jobs."""
        store = TryOnJobStore()

        jobs = [
            store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS),
            store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.BOTTOMS),
        ]
        batch = store.create_batch_job(jobs)

        # Complete first job
        store.complete_tryon_job(
            jobs[0].job_id,
            result_url="https://example.com/1.jpg",
            result_path="/assets/1.jpg",
            duration_ms=10000,
        )

        store.update_batch_progress(batch.batch_id)
        updated_batch = store.get_batch_job(batch.batch_id)

        assert updated_batch.completed_items == 1
        assert updated_batch.status == JobStatus.PROCESSING

    def test_list_tryon_jobs(self):
        """Should list recent jobs."""
        store = TryOnJobStore()

        for _ in range(5):
            store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        jobs = store.list_tryon_jobs(limit=3)

        assert len(jobs) == 3

    def test_queue_length(self):
        """Should count queued/processing jobs."""
        store = TryOnJobStore()

        job1 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)
        job2 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)
        job3 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.update_tryon_job(job1.job_id, status=JobStatus.PROCESSING)
        store.complete_tryon_job(
            job2.job_id, "url", "path", 1000
        )

        assert store.queue_length == 2  # 1 queued + 1 processing

    def test_total_generated(self):
        """Should count completed jobs."""
        store = TryOnJobStore()

        job1 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)
        job2 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.complete_tryon_job(job1.job_id, "url1", "path1", 1000)
        store.complete_tryon_job(job2.job_id, "url2", "path2", 1500)

        assert store.total_generated == 2

    def test_avg_time_seconds(self):
        """Should calculate average processing time."""
        store = TryOnJobStore()

        job1 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)
        job2 = store.create_tryon_job(TryOnProvider.FASHN, GarmentCategory.TOPS)

        store.complete_tryon_job(job1.job_id, "url1", "path1", 10000)  # 10s
        store.complete_tryon_job(job2.job_id, "url2", "path2", 14000)  # 14s

        assert store.avg_time_seconds == 12.0  # (10 + 14) / 2

    def test_create_model_job(self):
        """Should create model generation job."""
        store = TryOnJobStore()

        job = store.create_model_job(
            prompt="Professional model",
            gender=ModelGender.FEMALE,
        )

        assert job.job_id.startswith("model_")
        assert job.status == JobStatus.QUEUED
        assert job.prompt == "Professional model"
        assert job.gender == "female"


class TestResponseModels:
    """Test response model structure."""

    def test_job_response(self):
        """Should create job response."""
        response = JobResponse(
            job_id="tryon_abc123",
            status=JobStatus.COMPLETED,
            provider="fashn",
            category="tops",
            created_at="2025-01-01T00:00:00Z",
            completed_at="2025-01-01T00:00:12Z",
            result_url="https://example.com/result.jpg",
            cost_usd=0.075,
        )

        assert response.job_id == "tryon_abc123"
        assert response.cost_usd == 0.075

    def test_pipeline_status(self):
        """Should create pipeline status."""
        status = PipelineStatus(
            status="operational",
            providers=[
                {"name": "fashn", "status": "available"},
                {"name": "idm_vton", "status": "available"},
            ],
            queue_length=5,
            avg_processing_time_seconds=12.5,
            last_generated="2025-01-01T00:00:00Z",
            total_generated=100,
            daily_limit=1000,
            daily_used=50,
        )

        assert status.status == "operational"
        assert len(status.providers) == 2
        assert status.daily_limit == 1000

    def test_provider_info(self):
        """Should create provider info."""
        info = ProviderInfo(
            name="fashn",
            display_name="FASHN AI",
            description="Commercial virtual try-on API",
            status="available",
            avg_time_seconds=12.0,
            cost_per_image=0.075,
            supported_categories=["tops", "bottoms", "dresses"],
            features=["batch_processing", "high_quality"],
        )

        assert info.name == "fashn"
        assert info.cost_per_image == 0.075
        assert "tops" in info.supported_categories


class TestRouterEndpoints:
    """Test router endpoint definitions."""

    def test_router_has_prefix(self):
        """Should have correct prefix."""
        assert virtual_tryon_router.prefix == "/virtual-tryon"

    def test_router_has_tags(self):
        """Should have tags."""
        assert "Virtual Try-On" in virtual_tryon_router.tags

    def test_router_has_endpoints(self):
        """Should have expected endpoints."""
        routes = [r.path for r in virtual_tryon_router.routes]

        assert "/status" in routes
        assert "/providers" in routes
        assert "/categories" in routes
        assert "/jobs" in routes
        assert "/jobs/{job_id}" in routes
        assert "/generate" in routes
        assert "/generate/upload" in routes
        assert "/batch" in routes
        assert "/batch/{batch_id}" in routes
        assert "/models/generate" in routes
        assert "/models/jobs/{job_id}" in routes


@pytest.mark.asyncio
class TestEndpointResponses:
    """Test endpoint response handling."""

    async def test_list_categories(self):
        """Should return category list."""
        from api.virtual_tryon import list_categories

        categories = await list_categories()

        assert len(categories) == 5
        assert any(c["id"] == "tops" for c in categories)
        assert any(c["id"] == "dresses" for c in categories)

    async def test_list_providers(self):
        """Should return provider list."""
        from api.virtual_tryon import list_providers

        providers = await list_providers()

        assert len(providers) >= 2
        names = [p.name for p in providers]
        assert "fashn" in names
        assert "idm_vton" in names

    async def test_get_pipeline_status(self):
        """Should return pipeline status."""
        from api.virtual_tryon import get_pipeline_status

        status = await get_pipeline_status()

        assert status.status == "operational"
        assert status.daily_limit > 0
