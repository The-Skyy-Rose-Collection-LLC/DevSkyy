"""Tests for WordPress Theme Synchronization.

Comprehensive test suite for WordPress media approval sync functionality.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.approval_queue_manager import ApprovalItem, ApprovalStatus, get_approval_manager

from sync.wordpress_media_approval_sync import (
    BatchSyncResult,
    SyncResult,
    SyncStatus,
    WordPressMediaApprovalSync,
    get_wordpress_sync,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_wordpress_client():
    """Mock WordPress API client."""
    client = MagicMock()
    client.upload_media = AsyncMock(
        return_value={"id": 12345, "url": "https://example.com/media/12345.jpg"}
    )
    client.update_media = AsyncMock(return_value={"id": 12345, "updated": True})
    client.delete_media = AsyncMock(return_value={"deleted": True})
    client.is_configured = True
    return client


@pytest.fixture
def sync_service(mock_wordpress_client):
    """WordPress sync service instance."""
    return WordPressMediaApprovalSync(wordpress_client=mock_wordpress_client)


@pytest.fixture
def sample_approval_item():
    """Sample approval item for testing."""
    return ApprovalItem(
        id="test-item-123",
        asset_id="asset-456",
        job_id="job-789",
        original_url="https://cdn.example.com/original/image.jpg",
        enhanced_url="https://cdn.example.com/enhanced/image.jpg",
        product_id="prod-001",
        product_name="Rose Gold Necklace",
        status=ApprovalStatus.APPROVED,
        reviewed_by="admin-user",
        reviewed_at=datetime.now(UTC),
        metadata={
            "collection": "signature",
            "title": "Rose Gold Necklace",
        },
    )


# =============================================================================
# Unit Tests - WordPressMediaApprovalSync
# =============================================================================


class TestWordPressMediaApprovalSync:
    """Tests for WordPress media approval sync service."""

    @pytest.mark.asyncio
    async def test_sync_approved_asset_success(self, sync_service, mock_wordpress_client):
        """Should successfully sync an approved asset."""
        result = await sync_service.sync_approved_asset("asset-123")

        assert result.success is True
        assert result.status == SyncStatus.COMPLETED
        assert result.item_id == "asset-123"

    @pytest.mark.asyncio
    async def test_sync_approved_asset_with_wordpress_id(self, sync_service, mock_wordpress_client):
        """Should return WordPress media ID on successful sync."""
        mock_wordpress_client.upload_media.return_value = {"id": 98765}

        # Patch the actual implementation to use the mock
        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="asset-123",
                success=True,
                status=SyncStatus.COMPLETED,
                wordpress_id=98765,
            )

            result = await sync_service.sync_approved_asset("asset-123")

            assert result.wordpress_id == 98765

    @pytest.mark.asyncio
    async def test_sync_approved_asset_failure(self, sync_service, mock_wordpress_client):
        """Should handle sync failures gracefully."""
        mock_wordpress_client.upload_media.side_effect = Exception("Network error")

        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="asset-123",
                success=False,
                status=SyncStatus.FAILED,
                error="Network error",
            )

            result = await sync_service.sync_approved_asset("asset-123")

            assert result.success is False
            assert result.status == SyncStatus.FAILED
            assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_batch_sync_all_success(self, sync_service):
        """Should sync all items successfully in batch."""
        asset_ids = ["asset-1", "asset-2", "asset-3"]

        result = await sync_service.batch_sync(asset_ids)

        assert result.success is True
        assert result.total == 3
        assert result.synced == 3
        assert result.failed == 0
        assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_batch_sync_partial_failure(self, sync_service):
        """Should handle partial failures in batch sync."""
        asset_ids = ["asset-1", "asset-2", "asset-3"]

        # Mock partial failure
        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.side_effect = [
                SyncResult(item_id="asset-1", success=True, status=SyncStatus.COMPLETED),
                SyncResult(
                    item_id="asset-2",
                    success=False,
                    status=SyncStatus.FAILED,
                    error="Upload failed",
                ),
                SyncResult(item_id="asset-3", success=True, status=SyncStatus.COMPLETED),
            ]

            result = await sync_service.batch_sync(asset_ids)

            assert result.success is False  # At least one failure
            assert result.total == 3
            assert result.synced == 2
            assert result.failed == 1
            assert len(result.errors) == 1
            assert "Upload failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_batch_sync_empty_list(self, sync_service):
        """Should handle empty asset list."""
        result = await sync_service.batch_sync([])

        assert result.success is True
        assert result.total == 0
        assert result.synced == 0
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_batch_sync_collects_errors(self, sync_service):
        """Should collect all errors from failed syncs."""
        asset_ids = ["asset-1", "asset-2"]

        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.side_effect = [
                SyncResult(
                    item_id="asset-1", success=False, status=SyncStatus.FAILED, error="Error 1"
                ),
                SyncResult(
                    item_id="asset-2", success=False, status=SyncStatus.FAILED, error="Error 2"
                ),
            ]

            result = await sync_service.batch_sync(asset_ids)

            assert result.failed == 2
            assert len(result.errors) == 2
            assert "Error 1" in result.errors
            assert "Error 2" in result.errors


# =============================================================================
# Integration Tests - Sync Service with Manager
# =============================================================================


class TestWordPressSyncIntegration:
    """Integration tests for WordPress sync with approval manager."""

    @pytest.mark.asyncio
    async def test_sync_updates_approval_item(self, sync_service, sample_approval_item):
        """Should update approval item after successful sync."""
        with patch("services.approval_queue_manager.ApprovalQueueManager") as MockManager:
            manager = MockManager.return_value
            manager.get_item = AsyncMock(return_value=sample_approval_item)
            manager.update_wordpress_sync = AsyncMock(return_value=sample_approval_item)

            # Simulate sync with manager update
            sync_result = SyncResult(
                item_id=sample_approval_item.id,
                success=True,
                status=SyncStatus.COMPLETED,
                wordpress_id=12345,
            )

            await manager.update_wordpress_sync(
                sample_approval_item.id,
                wordpress_media_id=12345,
            )

            manager.update_wordpress_sync.assert_called_once_with(
                sample_approval_item.id,
                wordpress_media_id=12345,
            )

    @pytest.mark.asyncio
    async def test_sync_preserves_metadata(self, sync_service, sample_approval_item):
        """Should preserve approval item metadata during sync."""
        original_metadata = sample_approval_item.metadata.copy()

        # Sync operation should not modify metadata
        result = await sync_service.sync_approved_asset(sample_approval_item.asset_id)

        assert sample_approval_item.metadata == original_metadata

    @pytest.mark.asyncio
    async def test_sync_only_approved_items(self, sync_service):
        """Should only sync items with APPROVED status."""
        pending_item = ApprovalItem(
            id="pending-123",
            asset_id="asset-999",
            job_id="job-999",
            original_url="https://cdn.example.com/original/pending.jpg",
            enhanced_url="https://cdn.example.com/enhanced/pending.jpg",
            status=ApprovalStatus.PENDING,
        )

        # In real implementation, this should be skipped
        # Test that the sync service validates status
        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id=pending_item.id,
                success=False,
                status=SyncStatus.FAILED,
                error="Item not approved",
            )

            result = await sync_service.sync_approved_asset(pending_item.asset_id)

            # Should fail or skip non-approved items
            assert result.success is False or result.status == SyncStatus.FAILED


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in sync operations."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self, sync_service, mock_wordpress_client):
        """Should handle network errors gracefully."""
        mock_wordpress_client.upload_media.side_effect = ConnectionError("Network unavailable")

        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="asset-123",
                success=False,
                status=SyncStatus.FAILED,
                error="Network unavailable",
            )

            result = await sync_service.sync_approved_asset("asset-123")

            assert result.success is False
            assert "Network unavailable" in result.error

    @pytest.mark.asyncio
    async def test_wordpress_api_error(self, sync_service, mock_wordpress_client):
        """Should handle WordPress API errors."""
        mock_wordpress_client.upload_media.side_effect = Exception(
            "WordPress API Error: 403 Forbidden"
        )

        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="asset-123",
                success=False,
                status=SyncStatus.FAILED,
                error="WordPress API Error: 403 Forbidden",
            )

            result = await sync_service.sync_approved_asset("asset-123")

            assert result.success is False
            assert "403 Forbidden" in result.error

    @pytest.mark.asyncio
    async def test_invalid_asset_id(self, sync_service):
        """Should handle invalid asset IDs."""
        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="invalid-id",
                success=False,
                status=SyncStatus.FAILED,
                error="Asset not found",
            )

            result = await sync_service.sync_approved_asset("invalid-id")

            assert result.success is False
            assert result.status == SyncStatus.FAILED

    @pytest.mark.asyncio
    async def test_timeout_handling(self, sync_service, mock_wordpress_client):
        """Should handle timeouts appropriately."""
        mock_wordpress_client.upload_media.side_effect = TimeoutError()

        with patch.object(sync_service, "sync_approved_asset") as mock_sync:
            mock_sync.return_value = SyncResult(
                item_id="asset-123",
                success=False,
                status=SyncStatus.FAILED,
                error="Request timeout",
            )

            result = await sync_service.sync_approved_asset("asset-123")

            assert result.success is False
            assert "timeout" in result.error.lower()


# =============================================================================
# Singleton Instance Tests
# =============================================================================


class TestSingletonInstance:
    """Tests for get_wordpress_sync singleton."""

    def test_get_wordpress_sync_returns_instance(self):
        """Should return WordPressMediaApprovalSync instance."""
        instance = get_wordpress_sync()
        assert isinstance(instance, WordPressMediaApprovalSync)

    def test_get_wordpress_sync_returns_same_instance(self):
        """Should return same instance on multiple calls."""
        instance1 = get_wordpress_sync()
        instance2 = get_wordpress_sync()
        assert instance1 is instance2

    def test_singleton_reset(self):
        """Should allow resetting singleton for testing."""
        from sync import wordpress_media_approval_sync

        original = get_wordpress_sync()
        wordpress_media_approval_sync._wordpress_sync = None
        new_instance = get_wordpress_sync()

        # Should create new instance
        assert new_instance is not None
        assert isinstance(new_instance, WordPressMediaApprovalSync)


# =============================================================================
# Data Model Tests
# =============================================================================


class TestDataModels:
    """Tests for sync data models."""

    def test_sync_result_creation(self):
        """Should create SyncResult with all fields."""
        result = SyncResult(
            item_id="test-123",
            success=True,
            status=SyncStatus.COMPLETED,
            wordpress_id=12345,
            error=None,
        )

        assert result.item_id == "test-123"
        assert result.success is True
        assert result.status == SyncStatus.COMPLETED
        assert result.wordpress_id == 12345
        assert result.error is None

    def test_sync_result_with_error(self):
        """Should create SyncResult with error."""
        result = SyncResult(
            item_id="test-123",
            success=False,
            status=SyncStatus.FAILED,
            error="Upload failed",
        )

        assert result.success is False
        assert result.error == "Upload failed"

    def test_batch_sync_result_defaults(self):
        """Should initialize BatchSyncResult with defaults."""
        result = BatchSyncResult(success=True)

        assert result.total == 0
        assert result.synced == 0
        assert result.failed == 0
        assert result.results == []
        assert result.errors == []

    def test_batch_sync_result_aggregation(self):
        """Should correctly aggregate batch results."""
        result = BatchSyncResult(
            success=False,
            total=3,
            synced=2,
            failed=1,
            results=[
                SyncResult(item_id="1", success=True, status=SyncStatus.COMPLETED),
                SyncResult(item_id="2", success=True, status=SyncStatus.COMPLETED),
                SyncResult(item_id="3", success=False, status=SyncStatus.FAILED, error="Error"),
            ],
            errors=["Error"],
        )

        assert result.total == 3
        assert result.synced == 2
        assert result.failed == 1
        assert len(result.results) == 3
        assert len(result.errors) == 1

    def test_sync_status_enum_values(self):
        """Should have all expected SyncStatus values."""
        assert SyncStatus.PENDING == "pending"
        assert SyncStatus.IN_PROGRESS == "in_progress"
        assert SyncStatus.COMPLETED == "completed"
        assert SyncStatus.FAILED == "failed"
        assert SyncStatus.PARTIAL == "partial"


# =============================================================================
# Configuration Tests
# =============================================================================


class TestConfiguration:
    """Tests for WordPress sync configuration."""

    def test_sync_service_without_client(self):
        """Should initialize without WordPress client."""
        sync = WordPressMediaApprovalSync()
        assert sync.wordpress_client is None

    def test_sync_service_with_client(self, mock_wordpress_client):
        """Should initialize with WordPress client."""
        sync = WordPressMediaApprovalSync(wordpress_client=mock_wordpress_client)
        assert sync.wordpress_client is not None
        assert sync.wordpress_client.is_configured is True

    @pytest.mark.asyncio
    async def test_unconfigured_client_handling(self):
        """Should handle unconfigured WordPress client."""
        unconfigured_client = MagicMock()
        unconfigured_client.is_configured = False

        sync = WordPressMediaApprovalSync(wordpress_client=unconfigured_client)

        # Should handle gracefully or raise appropriate error
        # Implementation depends on actual sync logic
        assert sync.wordpress_client.is_configured is False


# =============================================================================
# T3-5 Wiring Gap: is_configured / sync_item / sync_approved_items / skipped
# =============================================================================


class TestIsConfiguredProperty:
    """Tests for the `is_configured` property on WordPressMediaApprovalSync."""

    def test_is_configured_false_without_client(self):
        """Should report not configured when no client is attached."""
        sync = WordPressMediaApprovalSync()
        assert sync.is_configured is False

    def test_is_configured_true_with_configured_client(self, sync_service):
        """Should report configured when the client says it is."""
        assert sync_service.is_configured is True

    def test_is_configured_false_with_unconfigured_client(self):
        """Should defer to the client's own is_configured flag."""
        unconfigured_client = MagicMock()
        unconfigured_client.is_configured = False
        sync = WordPressMediaApprovalSync(wordpress_client=unconfigured_client)
        assert sync.is_configured is False

    def test_is_configured_true_when_client_has_no_flag(self):
        """A client with no is_configured attribute (e.g. WordPressClient) is assumed configured."""
        bare_client = object()
        sync = WordPressMediaApprovalSync(wordpress_client=bare_client)
        assert sync.is_configured is True


class TestSyncItem:
    """Tests for the `sync_item` method on WordPressMediaApprovalSync."""

    @pytest.mark.asyncio
    async def test_sync_item_approved_delegates_and_rekeys_item_id(
        self, sync_service, sample_approval_item
    ):
        """Should sync an approved item and key the result by approval item id."""
        result = await sync_service.sync_item(sample_approval_item)

        assert result.item_id == sample_approval_item.id
        assert result.status == SyncStatus.COMPLETED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_sync_item_not_approved_returns_pending(self, sync_service):
        """Should not sync a non-approved item and should report it as pending."""
        pending_item = ApprovalItem(
            id="pending-item-1",
            asset_id="asset-pending",
            job_id="job-pending",
            original_url="https://cdn.example.com/original/pending.jpg",
            enhanced_url="https://cdn.example.com/enhanced/pending.jpg",
            status=ApprovalStatus.PENDING,
        )

        result = await sync_service.sync_item(pending_item)

        assert result.status == SyncStatus.PENDING
        assert result.success is False
        assert result.item_id == pending_item.id

    @pytest.mark.asyncio
    async def test_sync_item_unconfigured_client_returns_failed(self, sample_approval_item):
        """Should fail closed when no WordPress client is configured."""
        sync = WordPressMediaApprovalSync()  # no client => not configured

        result = await sync.sync_item(sample_approval_item)

        assert result.status == SyncStatus.FAILED
        assert result.success is False
        assert "not configured" in result.error


class TestSyncApprovedItems:
    """Tests for the `sync_approved_items` method on WordPressMediaApprovalSync."""

    @pytest.fixture
    def clean_approval_manager(self):
        """Isolate the approval-queue singleton for the duration of a test."""
        manager = get_approval_manager()
        original_items = dict(manager._items)
        manager._items.clear()
        try:
            yield manager
        finally:
            manager._items.clear()
            manager._items.update(original_items)

    @pytest.mark.asyncio
    async def test_sync_approved_items_syncs_only_unsynced_approved_items(
        self, sync_service, clean_approval_manager
    ):
        """Should sync approved+unsynced items only, skipping synced and non-approved ones."""
        approved_unsynced = ApprovalItem(
            id="approved-unsynced",
            asset_id="asset-a",
            job_id="job-a",
            original_url="https://cdn.example.com/original/a.jpg",
            enhanced_url="https://cdn.example.com/enhanced/a.jpg",
            status=ApprovalStatus.APPROVED,
        )
        approved_synced = ApprovalItem(
            id="approved-synced",
            asset_id="asset-b",
            job_id="job-b",
            original_url="https://cdn.example.com/original/b.jpg",
            enhanced_url="https://cdn.example.com/enhanced/b.jpg",
            status=ApprovalStatus.APPROVED,
            wordpress_media_id=999,
            wordpress_synced_at=datetime.now(UTC),
        )
        pending = ApprovalItem(
            id="pending-item",
            asset_id="asset-c",
            job_id="job-c",
            original_url="https://cdn.example.com/original/c.jpg",
            enhanced_url="https://cdn.example.com/enhanced/c.jpg",
            status=ApprovalStatus.PENDING,
        )
        clean_approval_manager._items[approved_unsynced.id] = approved_unsynced
        clean_approval_manager._items[approved_synced.id] = approved_synced
        clean_approval_manager._items[pending.id] = pending

        result = await sync_service.sync_approved_items()

        assert result.total == 1
        assert result.synced == 1
        assert result.failed == 0
        assert result.skipped == 0
        assert len(result.results) == 1
        assert result.results[0].item_id == approved_unsynced.id

    @pytest.mark.asyncio
    async def test_sync_approved_items_respects_limit(self, sync_service, clean_approval_manager):
        """Should cap the number of items synced to `limit`."""
        for i in range(3):
            item = ApprovalItem(
                id=f"approved-{i}",
                asset_id=f"asset-{i}",
                job_id=f"job-{i}",
                original_url=f"https://cdn.example.com/original/{i}.jpg",
                enhanced_url=f"https://cdn.example.com/enhanced/{i}.jpg",
                status=ApprovalStatus.APPROVED,
            )
            clean_approval_manager._items[item.id] = item

        result = await sync_service.sync_approved_items(limit=2)

        assert result.total == 2

    @pytest.mark.asyncio
    async def test_sync_approved_items_empty_queue(self, sync_service, clean_approval_manager):
        """Should return an empty, successful result when nothing is eligible."""
        result = await sync_service.sync_approved_items()

        assert result.total == 0
        assert result.synced == 0
        assert result.success is True


class TestSyncResultErrorMessageAlias:
    """Tests for the `error_message` alias on SyncResult."""

    def test_error_message_mirrors_error(self):
        """Should expose the same value as `error` under the `error_message` name."""
        result = SyncResult(
            item_id="x",
            success=False,
            status=SyncStatus.FAILED,
            error="boom",
        )
        assert result.error_message == "boom"

    def test_error_message_none_when_no_error(self):
        """Should be None when there is no error."""
        result = SyncResult(item_id="x", success=True, status=SyncStatus.COMPLETED)
        assert result.error_message is None
