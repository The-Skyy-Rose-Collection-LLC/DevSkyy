"""
Tests for Admin Dashboard API
=============================

Tests the admin dashboard endpoints for asset management,
fidelity reports, sync status, and pipeline controls.
"""

from datetime import UTC, datetime

import pytest

from api.admin_dashboard import (
    Asset3D,
    AssetStatus,
    AssetType,
    DashboardMetrics,
    FidelityReport,
    PipelineInfo,
    PipelineStatus,
    PipelineType,
    SyncChannel,
    storage,
)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test."""
    storage._assets.clear()
    storage._reports.clear()
    storage._pipelines.clear()
    yield


@pytest.fixture
def test_asset():
    """Create a test asset."""
    return Asset3D(
        id="test-asset-001",
        name="Test Product Model",
        type=AssetType.MODEL_3D,
        status=AssetStatus.VALIDATED,
        file_path="/assets/models/test.glb",
        file_size_bytes=1024000,
        format="glb",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        fidelity_score=96.5,
        fidelity_passed=True,
    )


@pytest.fixture
def test_report():
    """Create a test fidelity report."""
    return FidelityReport(
        id="report-001",
        asset_id="test-asset-001",
        asset_name="Test Product Model",
        validation_time=datetime.now(UTC),
        overall_score=96.5,
        passed=True,
        threshold_used=95.0,
        geometry_metrics={"vertex_count": 10000, "is_watertight": True},
        texture_metrics={"resolution": [2048, 2048]},
    )


class TestDashboardMetrics:
    """Tests for dashboard metrics endpoint."""

    def test_get_metrics(self):
        """Test getting dashboard metrics."""
        metrics = storage.get_metrics()

        assert isinstance(metrics, DashboardMetrics)
        assert metrics.total_assets >= 0
        assert 0 <= metrics.fidelity_pass_rate <= 1

    def test_metrics_counts(self, test_asset):
        """Test that metrics count assets correctly."""
        storage.add_asset(test_asset)
        metrics = storage.get_metrics()

        assert metrics.total_assets >= 1
        assert metrics.assets_validated >= 1


class TestAssetEndpoints:
    """Tests for asset management endpoints."""

    def test_add_asset(self, test_asset):
        """Test adding an asset."""
        storage.add_asset(test_asset)
        retrieved = storage.get_asset(test_asset.id)

        assert retrieved is not None
        assert retrieved.id == test_asset.id
        assert retrieved.fidelity_score == 96.5

    def test_get_nonexistent_asset(self):
        """Test getting a non-existent asset."""
        asset = storage.get_asset("nonexistent-id")
        assert asset is None

    def test_delete_asset(self, test_asset):
        """Test deleting an asset."""
        storage.add_asset(test_asset)
        result = storage.delete_asset(test_asset.id)

        assert result is True
        assert storage.get_asset(test_asset.id) is None

    def test_delete_nonexistent_asset(self):
        """Test deleting a non-existent asset."""
        result = storage.delete_asset("nonexistent-id")
        assert result is False

    def test_list_assets_by_status(self, test_asset):
        """Test listing assets filtered by status."""
        storage.add_asset(test_asset)
        assets = storage.list_assets(status=AssetStatus.VALIDATED)

        assert len(assets) >= 1
        assert all(a.status == AssetStatus.VALIDATED for a in assets)

    def test_list_assets_by_type(self, test_asset):
        """Test listing assets filtered by type."""
        storage.add_asset(test_asset)
        assets = storage.list_assets(asset_type=AssetType.MODEL_3D)

        assert len(assets) >= 1
        assert all(a.type == AssetType.MODEL_3D for a in assets)


class TestFidelityReportEndpoints:
    """Tests for fidelity report endpoints."""

    def test_add_fidelity_report(self, test_report):
        """Test adding a fidelity report."""
        storage.add_report(test_report)
        retrieved = storage.get_report(test_report.id)

        assert retrieved is not None
        assert retrieved.overall_score == 96.5
        assert retrieved.passed is True

    def test_list_reports_by_asset(self, test_report):
        """Test listing reports filtered by asset."""
        storage.add_report(test_report)
        reports = storage.list_reports(asset_id="test-asset-001")

        assert len(reports) >= 1
        assert all(r.asset_id == "test-asset-001" for r in reports)

    def test_report_threshold_is_95(self, test_report):
        """Test that reports use 95% threshold."""
        assert test_report.threshold_used == 95.0


class TestPipelineEndpoints:
    """Tests for pipeline control endpoints."""

    def test_add_pipeline(self):
        """Test adding a pipeline."""
        pipeline = PipelineInfo(
            id="pipeline-001",
            type=PipelineType.MODEL_GENERATION,
            status=PipelineStatus.RUNNING,
        )
        storage.add_pipeline(pipeline)
        retrieved = storage.get_pipeline("pipeline-001")

        assert retrieved is not None
        assert retrieved.type == PipelineType.MODEL_GENERATION
        assert retrieved.status == PipelineStatus.RUNNING

    def test_get_nonexistent_pipeline(self):
        """Test getting a non-existent pipeline."""
        pipeline = storage.get_pipeline("nonexistent-id")
        assert pipeline is None


class TestAssetTypes:
    """Tests for asset type enums."""

    def test_asset_types(self):
        """Test all asset types are defined."""
        assert AssetType.MODEL_3D.value == "3d_model"
        assert AssetType.IMAGE.value == "image"
        assert AssetType.VIDEO.value == "video"
        assert AssetType.TEXTURE.value == "texture"

    def test_asset_statuses(self):
        """Test all asset statuses are defined."""
        assert AssetStatus.PENDING.value == "pending"
        assert AssetStatus.PROCESSING.value == "processing"
        assert AssetStatus.VALIDATED.value == "validated"
        assert AssetStatus.FAILED.value == "failed"
        assert AssetStatus.ARCHIVED.value == "archived"


class TestSyncChannels:
    """Tests for sync channel enums."""

    def test_sync_channels(self):
        """Test all sync channels are defined."""
        assert SyncChannel.WOOCOMMERCE.value == "woocommerce"
        assert SyncChannel.WORDPRESS.value == "wordpress"
        assert SyncChannel.SHOPIFY.value == "shopify"


class TestPipelineTypes:
    """Tests for pipeline type enums."""

    def test_pipeline_types(self):
        """Test all pipeline types are defined."""
        assert PipelineType.MODEL_GENERATION.value == "model_generation"
        assert PipelineType.PHOTOSHOOT.value == "photoshoot"
        assert PipelineType.FIDELITY_CHECK.value == "fidelity_check"
        assert PipelineType.SYNC.value == "sync"

    def test_pipeline_statuses(self):
        """Test all pipeline statuses are defined."""
        assert PipelineStatus.QUEUED.value == "queued"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.CANCELLED.value == "cancelled"


class TestDashboardMetricsCalculation:
    """Tests for dashboard metrics calculation."""

    def test_fidelity_pass_rate(self, test_asset):
        """Test fidelity pass rate calculation."""
        # Add passing asset
        storage.add_asset(test_asset)

        # Add failing asset
        failed_asset = Asset3D(
            id="test-asset-002",
            name="Failed Model",
            status=AssetStatus.VALIDATED,
            fidelity_score=80.0,
            fidelity_passed=False,
        )
        storage.add_asset(failed_asset)

        metrics = storage.get_metrics()

        # 1 pass out of 2 validated = 50%
        assert metrics.fidelity_pass_rate == 0.5

    def test_active_pipelines_count(self):
        """Test active pipelines count."""
        # Add running pipeline
        storage.add_pipeline(
            PipelineInfo(
                id="p1",
                type=PipelineType.MODEL_GENERATION,
                status=PipelineStatus.RUNNING,
            )
        )
        # Add queued pipeline
        storage.add_pipeline(
            PipelineInfo(
                id="p2",
                type=PipelineType.PHOTOSHOOT,
                status=PipelineStatus.QUEUED,
            )
        )
        # Add completed pipeline (not active)
        storage.add_pipeline(
            PipelineInfo(
                id="p3",
                type=PipelineType.SYNC,
                status=PipelineStatus.COMPLETED,
            )
        )

        metrics = storage.get_metrics()
        assert metrics.active_pipelines == 2
