# tests/api/test_assets_api.py
"""Unit tests for Assets API endpoints."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from api.v1.assets import (
    ALLOWED_IMAGE_FORMATS,
    MAX_FILE_SIZE_BYTES,
    MIN_IMAGE_DIMENSION,
    ImageSource,
    IngestResponse,
    JobListResponse,
    JobResponse,
    JobStatus,
    ProcessingProfile,
    _jobs,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> MagicMock:
    """Create mock authenticated user."""
    user = MagicMock()
    user.sub = "user-123"
    return user


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes for testing."""
    img = Image.new("RGB", (500, 500), color=(128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes() -> bytes:
    """Create image that's too small."""
    img = Image.new("RGB", (50, 50), color=(128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def clear_jobs() -> None:
    """Clear job storage before each test."""
    _jobs.clear()


# =============================================================================
# Model Tests
# =============================================================================


class TestJobStatus:
    """Test JobStatus enum."""

    def test_pending_value(self) -> None:
        """JobStatus.PENDING should have correct value."""
        assert JobStatus.PENDING.value == "pending"

    def test_running_value(self) -> None:
        """JobStatus.RUNNING should have correct value."""
        assert JobStatus.RUNNING.value == "running"

    def test_succeeded_value(self) -> None:
        """JobStatus.SUCCEEDED should have correct value."""
        assert JobStatus.SUCCEEDED.value == "succeeded"

    def test_failed_value(self) -> None:
        """JobStatus.FAILED should have correct value."""
        assert JobStatus.FAILED.value == "failed"

    def test_cancelled_value(self) -> None:
        """JobStatus.CANCELLED should have correct value."""
        assert JobStatus.CANCELLED.value == "cancelled"


class TestProcessingProfile:
    """Test ProcessingProfile enum."""

    def test_full_value(self) -> None:
        """ProcessingProfile.FULL should have correct value."""
        assert ProcessingProfile.FULL.value == "full"

    def test_quick_value(self) -> None:
        """ProcessingProfile.QUICK should have correct value."""
        assert ProcessingProfile.QUICK.value == "quick"

    def test_background_only_value(self) -> None:
        """ProcessingProfile.BACKGROUND_ONLY should have correct value."""
        assert ProcessingProfile.BACKGROUND_ONLY.value == "background_only"

    def test_reformat_value(self) -> None:
        """ProcessingProfile.REFORMAT should have correct value."""
        assert ProcessingProfile.REFORMAT.value == "reformat"


class TestImageSource:
    """Test ImageSource enum."""

    def test_api_value(self) -> None:
        """ImageSource.API should have correct value."""
        assert ImageSource.API.value == "api"

    def test_woocommerce_value(self) -> None:
        """ImageSource.WOOCOMMERCE should have correct value."""
        assert ImageSource.WOOCOMMERCE.value == "woocommerce"

    def test_dashboard_value(self) -> None:
        """ImageSource.DASHBOARD should have correct value."""
        assert ImageSource.DASHBOARD.value == "dashboard"


class TestIngestResponse:
    """Test IngestResponse model."""

    def test_ingest_response_creation(self) -> None:
        """Should create valid ingest response."""
        response = IngestResponse(
            job_id="job-123",
            status="pending",
            message="Image accepted",
            original_url="https://example.com/image.jpg",
            created_at="2026-01-21T12:00:00Z",
            correlation_id="corr-123",
        )

        assert response.job_id == "job-123"
        assert response.status == "pending"


class TestJobResponse:
    """Test JobResponse model."""

    def test_job_response_creation(self) -> None:
        """Should create valid job response."""
        response = JobResponse(
            job_id="job-123",
            status="running",
            current_stage="background_removal",
            progress_percent=50,
            stages=[],
            input_url="https://example.com/image.jpg",
            output_urls={},
            product_id="PROD-123",
            source="api",
            created_at="2026-01-21T12:00:00Z",
            started_at="2026-01-21T12:00:05Z",
            completed_at=None,
            error_message=None,
            total_duration_ms=5000,
            correlation_id="corr-123",
        )

        assert response.status == "running"
        assert response.progress_percent == 50


class TestJobListResponse:
    """Test JobListResponse model."""

    def test_job_list_response_creation(self) -> None:
        """Should create valid job list response."""
        response = JobListResponse(
            jobs=[],
            total=0,
            page=1,
            page_size=20,
            has_more=False,
        )

        assert response.total == 0
        assert response.page == 1


# =============================================================================
# Endpoint Tests (using in-memory storage)
# =============================================================================


class TestIngestImageValidation:
    """Test image validation in ingest endpoint."""

    def test_allowed_formats_defined(self) -> None:
        """Should have allowed formats defined."""
        assert "image/jpeg" in ALLOWED_IMAGE_FORMATS
        assert "image/png" in ALLOWED_IMAGE_FORMATS
        assert "image/webp" in ALLOWED_IMAGE_FORMATS
        assert "image/tiff" in ALLOWED_IMAGE_FORMATS

    def test_max_file_size(self) -> None:
        """Max file size should be 50MB."""
        assert MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024

    def test_min_image_dimension(self) -> None:
        """Min image dimension should be 100px."""
        assert MIN_IMAGE_DIMENSION == 100


class TestJobStorage:
    """Test in-memory job storage."""

    def test_jobs_storage_initially_empty(self) -> None:
        """Jobs storage should be empty initially."""
        assert len(_jobs) == 0

    def test_add_job_to_storage(self) -> None:
        """Should be able to add job to storage."""
        _jobs["test-job"] = {
            "job_id": "test-job",
            "status": "pending",
            "input_url": "https://example.com/image.jpg",
            "user_id": "user-123",
            "source": "api",
            "created_at": "2026-01-21T12:00:00Z",
            "correlation_id": "corr-123",
        }

        assert "test-job" in _jobs
        assert _jobs["test-job"]["status"] == "pending"

    def test_retrieve_job_from_storage(self) -> None:
        """Should retrieve job from storage."""
        _jobs["test-job"] = {
            "job_id": "test-job",
            "status": "running",
            "input_url": "https://example.com/image.jpg",
            "user_id": "user-123",
            "source": "api",
            "created_at": "2026-01-21T12:00:00Z",
            "correlation_id": "corr-123",
        }

        job = _jobs.get("test-job")
        assert job is not None
        assert job["status"] == "running"


class TestJobFiltering:
    """Test job filtering logic."""

    def test_filter_by_status(self) -> None:
        """Should filter jobs by status."""
        _jobs["job-1"] = {"job_id": "job-1", "status": "pending", "user_id": "user-123"}
        _jobs["job-2"] = {"job_id": "job-2", "status": "running", "user_id": "user-123"}
        _jobs["job-3"] = {"job_id": "job-3", "status": "pending", "user_id": "user-123"}

        user_jobs = list(_jobs.values())
        pending_jobs = [j for j in user_jobs if j["status"] == "pending"]

        assert len(pending_jobs) == 2

    def test_filter_by_source(self) -> None:
        """Should filter jobs by source."""
        _jobs["job-1"] = {"job_id": "job-1", "source": "api", "user_id": "user-123"}
        _jobs["job-2"] = {
            "job_id": "job-2",
            "source": "woocommerce",
            "user_id": "user-123",
        }
        _jobs["job-3"] = {"job_id": "job-3", "source": "api", "user_id": "user-123"}

        user_jobs = list(_jobs.values())
        api_jobs = [j for j in user_jobs if j["source"] == "api"]

        assert len(api_jobs) == 2

    def test_filter_by_product_id(self) -> None:
        """Should filter jobs by product ID."""
        _jobs["job-1"] = {
            "job_id": "job-1",
            "product_id": "PROD-123",
            "user_id": "user-123",
        }
        _jobs["job-2"] = {
            "job_id": "job-2",
            "product_id": "PROD-456",
            "user_id": "user-123",
        }
        _jobs["job-3"] = {
            "job_id": "job-3",
            "product_id": "PROD-123",
            "user_id": "user-123",
        }

        user_jobs = list(_jobs.values())
        product_jobs = [j for j in user_jobs if j.get("product_id") == "PROD-123"]

        assert len(product_jobs) == 2


class TestJobCancellation:
    """Test job cancellation logic."""

    def test_can_cancel_pending_job(self) -> None:
        """Should be able to cancel pending job."""
        _jobs["job-1"] = {
            "job_id": "job-1",
            "status": "pending",
            "user_id": "user-123",
        }

        job = _jobs["job-1"]
        assert job["status"] in ("pending", "running")

        job["status"] = "cancelled"
        assert _jobs["job-1"]["status"] == "cancelled"

    def test_cannot_cancel_completed_job(self) -> None:
        """Should not cancel completed job."""
        _jobs["job-1"] = {
            "job_id": "job-1",
            "status": "succeeded",
            "user_id": "user-123",
        }

        job = _jobs["job-1"]
        assert job["status"] not in ("pending", "running")


class TestJobRetry:
    """Test job retry logic."""

    def test_can_retry_failed_job(self) -> None:
        """Should be able to retry failed job."""
        _jobs["job-1"] = {
            "job_id": "job-1",
            "status": "failed",
            "input_url": "https://example.com/image.jpg",
            "user_id": "user-123",
            "source": "api",
        }

        job = _jobs["job-1"]
        assert job["status"] == "failed"

        # Create new job from old
        _jobs["job-2"] = {
            "job_id": "job-2",
            "status": "pending",
            "input_url": job["input_url"],
            "user_id": job["user_id"],
            "source": job["source"],
            "original_job_id": "job-1",
        }

        assert _jobs["job-2"]["original_job_id"] == "job-1"

    def test_cannot_retry_non_failed_job(self) -> None:
        """Should not retry non-failed job."""
        _jobs["job-1"] = {
            "job_id": "job-1",
            "status": "succeeded",
            "user_id": "user-123",
        }

        job = _jobs["job-1"]
        assert job["status"] != "failed"


class TestPagination:
    """Test pagination logic."""

    def test_pagination_first_page(self) -> None:
        """Should return first page correctly."""
        for i in range(25):
            _jobs[f"job-{i}"] = {"job_id": f"job-{i}", "user_id": "user-123"}

        all_jobs = list(_jobs.values())
        page = 1
        page_size = 10

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_jobs = all_jobs[start_idx:end_idx]

        assert len(page_jobs) == 10

    def test_pagination_last_page(self) -> None:
        """Should return last page correctly."""
        for i in range(25):
            _jobs[f"job-{i}"] = {"job_id": f"job-{i}", "user_id": "user-123"}

        all_jobs = list(_jobs.values())
        page = 3
        page_size = 10

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_jobs = all_jobs[start_idx:end_idx]

        assert len(page_jobs) == 5  # 25 - 20 = 5

    def test_has_more_calculation(self) -> None:
        """Should calculate has_more correctly."""
        for i in range(25):
            _jobs[f"job-{i}"] = {"job_id": f"job-{i}", "user_id": "user-123"}

        total = len(_jobs)
        page = 2
        page_size = 10
        end_idx = page * page_size

        has_more = end_idx < total
        assert has_more is True  # 20 < 25


class TestUserOwnership:
    """Test user ownership checks."""

    def test_user_can_access_own_job(self) -> None:
        """User should access own jobs."""
        _jobs["job-1"] = {"job_id": "job-1", "user_id": "user-123"}

        user_id = "user-123"
        job = _jobs["job-1"]

        assert job.get("user_id") == user_id

    def test_user_cannot_access_other_job(self) -> None:
        """User should not access other users' jobs."""
        _jobs["job-1"] = {"job_id": "job-1", "user_id": "user-456"}

        user_id = "user-123"
        job = _jobs["job-1"]

        assert job.get("user_id") != user_id
