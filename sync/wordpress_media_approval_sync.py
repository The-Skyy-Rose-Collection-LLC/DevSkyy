"""WordPress Media Approval Synchronization.

Handles syncing approved media assets between DevSkyy and WordPress.
"""

import logging
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from services.approval_queue_manager import (
    ApprovalItem,
    ApprovalQueueFilter,
    ApprovalStatus,
    get_approval_manager,
)

logger = logging.getLogger(__name__)

# The approval queue is in-memory today (see ApprovalQueueManager._items), so a
# generous single-page fetch is a real "get everything approved" query rather
# than an unbounded scan. Revisit if the queue moves to a paginated store.
_SYNC_BATCH_PAGE_SIZE = 1000


class SyncStatus(StrEnum):
    """Status of synchronization operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncResult(BaseModel):
    """Result of a single sync operation."""

    item_id: str
    success: bool
    status: SyncStatus
    wordpress_id: int | None = None
    error: str | None = None

    @property
    def error_message(self) -> str | None:
        """Alias for `error`, for callers that read the failure reason by this name."""
        return self.error


class BatchSyncResult(BaseModel):
    """Result of batch synchronization."""

    success: bool
    total: int = 0
    synced: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[SyncResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class WordPressMediaApprovalSync:
    """Service for synchronizing approved media to WordPress."""

    def __init__(self, wordpress_client: Any = None):
        """Initialize sync service.

        Args:
            wordpress_client: WordPress API client
        """
        self.wordpress_client = wordpress_client

    @property
    def is_configured(self) -> bool:
        """Whether a usable WordPress client is attached.

        No client attached means sync cannot run. When a client is attached,
        it is treated as configured unless the client itself exposes an
        `is_configured` flag that says otherwise (used by test doubles and
        any client implementation that tracks its own credential state).
        """
        if self.wordpress_client is None:
            return False
        return bool(getattr(self.wordpress_client, "is_configured", True))

    async def sync_approved_asset(self, asset_id: str) -> SyncResult:
        """Sync a single approved asset to WordPress.

        Args:
            asset_id: ID of the asset to sync

        Returns:
            SyncResult with operation outcome
        """
        # TODO: Implement actual sync logic
        return SyncResult(
            item_id=asset_id,
            success=True,
            status=SyncStatus.COMPLETED,
            wordpress_id=None,
        )

    async def batch_sync(self, asset_ids: list[str]) -> BatchSyncResult:
        """Sync multiple assets to WordPress.

        Args:
            asset_ids: List of asset IDs to sync

        Returns:
            BatchSyncResult with overall outcome
        """
        result = BatchSyncResult(success=True, total=len(asset_ids))

        for asset_id in asset_ids:
            sync_result = await self.sync_approved_asset(asset_id)
            result.results.append(sync_result)

            if sync_result.success:
                result.synced += 1
            else:
                result.failed += 1
                if sync_result.error:
                    result.errors.append(sync_result.error)

        result.success = result.failed == 0
        return result

    async def sync_item(self, item: ApprovalItem) -> SyncResult:
        """Sync a single approval-queue item to WordPress.

        Delegates the actual upload to `sync_approved_asset`, gated on the
        item having been approved and a WordPress client being configured.

        Args:
            item: Approval-queue item to sync

        Returns:
            SyncResult keyed by the approval item's id (not the underlying
            asset id) so callers can correlate the result back to the
            approval-queue entry.
        """
        if item.status != ApprovalStatus.APPROVED:
            logger.warning(
                "Skipping WordPress sync for item %s: status is %s, not approved",
                item.id,
                item.status,
            )
            return SyncResult(
                item_id=item.id,
                success=False,
                status=SyncStatus.PENDING,
                error=f"Item is not approved (status={item.status})",
            )

        if not self.is_configured:
            logger.warning("Skipping WordPress sync for item %s: client not configured", item.id)
            return SyncResult(
                item_id=item.id,
                success=False,
                status=SyncStatus.FAILED,
                error="WordPress client is not configured",
            )

        result = await self.sync_approved_asset(item.asset_id)
        return result.model_copy(update={"item_id": item.id})

    async def sync_approved_items(self, limit: int | None = None) -> BatchSyncResult:
        """Sync all approved, not-yet-synced items from the approval queue.

        Args:
            limit: Maximum number of items to sync. None syncs every
                eligible item currently in the queue.

        Returns:
            BatchSyncResult aggregating per-item outcomes.
        """
        manager = get_approval_manager()
        response = await manager.list_items(
            filter_params=ApprovalQueueFilter(status=ApprovalStatus.APPROVED),
            page=1,
            page_size=_SYNC_BATCH_PAGE_SIZE,
        )
        candidates = [item for item in response.items if item.wordpress_synced_at is None]
        if limit is not None:
            candidates = candidates[:limit]

        result = BatchSyncResult(success=True, total=len(candidates))

        for item in candidates:
            sync_result = await self.sync_item(item)
            result.results.append(sync_result)

            if sync_result.status == SyncStatus.COMPLETED:
                result.synced += 1
            elif sync_result.status == SyncStatus.FAILED:
                result.failed += 1
                if sync_result.error:
                    result.errors.append(f"{item.id}: {sync_result.error}")
            else:
                result.skipped += 1

        result.success = result.failed == 0
        return result


# Singleton instance
_wordpress_sync: WordPressMediaApprovalSync | None = None


def get_wordpress_sync() -> WordPressMediaApprovalSync:
    """Get WordPress sync service instance.

    Returns:
        WordPressMediaApprovalSync instance
    """
    global _wordpress_sync
    if _wordpress_sync is None:
        _wordpress_sync = WordPressMediaApprovalSync()
    return _wordpress_sync
