# services/approval_queue_manager.py
"""Approval queue manager for WordPress media sync.

Implements US-022: WordPress media sync with approval.

Features:
- Queue AI-generated images for human review
- Side-by-side comparison (original vs AI-enhanced)
- Batch approval/rejection
- Revision queue for rejected items
- Email notifications for pending approvals

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ApprovalStatus(str, Enum):
    """Status of approval item."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    EXPIRED = "expired"


class ApprovalAction(str, Enum):
    """Action to take on an approval item."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"
    SKIP = "skip"


class RevisionPriority(str, Enum):
    """Priority level for revision requests."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# =============================================================================
# Models
# =============================================================================


class ApprovalItemCreate(BaseModel):
    """Request to create an approval item."""

    asset_id: str
    job_id: str
    original_url: str
    enhanced_url: str
    product_id: str | None = None
    woocommerce_product_id: str | None = None
    product_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalItem(BaseModel):
    """Item in the approval queue."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    asset_id: str
    job_id: str
    original_url: str
    enhanced_url: str
    product_id: str | None = None
    woocommerce_product_id: str | None = None
    product_name: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Review info
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None

    # Rejection/revision info
    rejection_reason: str | None = None
    revision_feedback: str | None = None
    revision_priority: RevisionPriority | None = None

    # WordPress sync info
    wordpress_media_id: int | None = None
    wordpress_synced_at: datetime | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


class ApprovalActionRequest(BaseModel):
    """Request to take action on an approval item."""

    action: ApprovalAction
    notes: str | None = None
    rejection_reason: str | None = None
    revision_feedback: str | None = None
    revision_priority: RevisionPriority = RevisionPriority.NORMAL


class BatchApprovalRequest(BaseModel):
    """Request for batch approval actions."""

    item_ids: list[str]
    action: ApprovalAction
    notes: str | None = None


class ApprovalQueueStats(BaseModel):
    """Statistics for the approval queue."""

    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    revision_requested: int = 0
    expired: int = 0
    oldest_pending_hours: float | None = None


class ApprovalQueueFilter(BaseModel):
    """Filter parameters for approval queue queries."""

    status: ApprovalStatus | None = None
    product_id: str | None = None
    woocommerce_product_id: str | None = None
    reviewed_by: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class ApprovalQueueResponse(BaseModel):
    """Paginated response for approval queue queries."""

    items: list[ApprovalItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class RevisionItem(BaseModel):
    """Item in the revision queue."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    approval_item_id: str
    asset_id: str
    original_url: str
    enhanced_url: str
    feedback: str
    priority: RevisionPriority
    product_name: str | None = None
    assigned_to: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class RevisionQueueResponse(BaseModel):
    """Response for revision queue queries."""

    items: list[RevisionItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# Exceptions
# =============================================================================


class ApprovalQueueError(Exception):
    """Base exception for approval queue operations."""

    def __init__(
        self,
        message: str,
        *,
        item_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.item_id = item_id
        self.correlation_id = correlation_id
        super().__init__(message)


class ApprovalItemNotFoundError(ApprovalQueueError):
    """Raised when an approval item is not found."""

    pass


class InvalidApprovalActionError(ApprovalQueueError):
    """Raised when an invalid action is requested."""

    pass


# =============================================================================
# Approval Queue Manager
# =============================================================================


class ApprovalQueueManager:
    """Manages the approval queue for WordPress media sync.

    Features:
    - Queue items for human approval
    - Track approval status
    - Handle batch operations
    - Manage revision queue for rejected items
    - Trigger notifications

    Usage:
        manager = ApprovalQueueManager()

        # Create approval item
        item = await manager.create_item(ApprovalItemCreate(
            asset_id="asset_123",
            job_id="job_123",
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
        ))

        # Review item
        await manager.process_action(
            item.id,
            ApprovalActionRequest(action=ApprovalAction.APPROVE),
            reviewed_by="user_123",
        )
    """

    def __init__(
        self,
        *,
        default_expiry_hours: int = 168,  # 7 days
        notification_service: Any | None = None,
    ) -> None:
        """Initialize approval queue manager.

        Args:
            default_expiry_hours: Hours until pending items expire
            notification_service: Optional notification service for emails
        """
        self._default_expiry_hours = default_expiry_hours
        self._notification_service = notification_service

        # In-memory storage (replace with database in production)
        self._items: dict[str, ApprovalItem] = {}
        self._revisions: dict[str, RevisionItem] = {}

    async def create_item(
        self,
        request: ApprovalItemCreate,
        *,
        correlation_id: str | None = None,
    ) -> ApprovalItem:
        """Create a new approval queue item.

        Args:
            request: Item creation request
            correlation_id: Optional correlation ID

        Returns:
            Created ApprovalItem
        """
        from datetime import timedelta

        item = ApprovalItem(
            asset_id=request.asset_id,
            job_id=request.job_id,
            original_url=request.original_url,
            enhanced_url=request.enhanced_url,
            product_id=request.product_id,
            woocommerce_product_id=request.woocommerce_product_id,
            product_name=request.product_name,
            metadata=request.metadata,
            expires_at=datetime.now(UTC) + timedelta(hours=self._default_expiry_hours),
        )

        self._items[item.id] = item

        logger.info(
            f"Created approval item {item.id} for asset {item.asset_id}",
            extra={
                "item_id": item.id,
                "asset_id": item.asset_id,
                "correlation_id": correlation_id,
            },
        )

        # Send notification
        if self._notification_service:
            await self._notification_service.send_approval_notification(item)

        return item

    async def get_item(
        self,
        item_id: str,
        *,
        correlation_id: str | None = None,
    ) -> ApprovalItem:
        """Get an approval item by ID.

        Args:
            item_id: Item identifier
            correlation_id: Optional correlation ID

        Returns:
            ApprovalItem

        Raises:
            ApprovalItemNotFoundError: If item not found
        """
        item = self._items.get(item_id)
        if not item:
            raise ApprovalItemNotFoundError(
                f"Approval item not found: {item_id}",
                item_id=item_id,
                correlation_id=correlation_id,
            )
        return item

    async def list_items(
        self,
        *,
        filter_params: ApprovalQueueFilter | None = None,
        page: int = 1,
        page_size: int = 20,
        correlation_id: str | None = None,
    ) -> ApprovalQueueResponse:
        """List approval items with filtering and pagination.

        Args:
            filter_params: Optional filter parameters
            page: Page number (1-indexed)
            page_size: Items per page
            correlation_id: Optional correlation ID

        Returns:
            ApprovalQueueResponse with items and pagination info
        """
        items = list(self._items.values())

        # Apply filters
        if filter_params:
            if filter_params.status:
                items = [i for i in items if i.status == filter_params.status]
            if filter_params.product_id:
                items = [i for i in items if i.product_id == filter_params.product_id]
            if filter_params.woocommerce_product_id:
                items = [
                    i
                    for i in items
                    if i.woocommerce_product_id == filter_params.woocommerce_product_id
                ]
            if filter_params.reviewed_by:
                items = [i for i in items if i.reviewed_by == filter_params.reviewed_by]
            if filter_params.created_after:
                items = [i for i in items if i.created_at >= filter_params.created_after]
            if filter_params.created_before:
                items = [i for i in items if i.created_at <= filter_params.created_before]

        # Sort by created_at descending (newest first)
        items.sort(key=lambda x: x.created_at, reverse=True)

        # Paginate
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        return ApprovalQueueResponse(
            items=page_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=end < total,
        )

    async def process_action(
        self,
        item_id: str,
        request: ApprovalActionRequest,
        *,
        reviewed_by: str,
        correlation_id: str | None = None,
    ) -> ApprovalItem:
        """Process an approval action on an item.

        Args:
            item_id: Item identifier
            request: Action request
            reviewed_by: User ID of reviewer
            correlation_id: Optional correlation ID

        Returns:
            Updated ApprovalItem

        Raises:
            ApprovalItemNotFoundError: If item not found
            InvalidApprovalActionError: If action is invalid for current state
        """
        item = await self.get_item(item_id, correlation_id=correlation_id)

        # Validate action is allowed for current status
        if item.status not in (ApprovalStatus.PENDING, ApprovalStatus.REVISION_REQUESTED):
            raise InvalidApprovalActionError(
                f"Cannot process action on item with status {item.status}",
                item_id=item_id,
                correlation_id=correlation_id,
            )

        # Process action
        now = datetime.now(UTC)

        if request.action == ApprovalAction.APPROVE:
            item.status = ApprovalStatus.APPROVED
            item.reviewed_by = reviewed_by
            item.reviewed_at = now
            item.review_notes = request.notes

            logger.info(
                f"Approved item {item_id}",
                extra={
                    "item_id": item_id,
                    "reviewed_by": reviewed_by,
                    "correlation_id": correlation_id,
                },
            )

        elif request.action == ApprovalAction.REJECT:
            item.status = ApprovalStatus.REJECTED
            item.reviewed_by = reviewed_by
            item.reviewed_at = now
            item.review_notes = request.notes
            item.rejection_reason = request.rejection_reason

            logger.info(
                f"Rejected item {item_id}: {request.rejection_reason}",
                extra={
                    "item_id": item_id,
                    "reviewed_by": reviewed_by,
                    "correlation_id": correlation_id,
                },
            )

        elif request.action == ApprovalAction.REQUEST_REVISION:
            item.status = ApprovalStatus.REVISION_REQUESTED
            item.reviewed_by = reviewed_by
            item.reviewed_at = now
            item.review_notes = request.notes
            item.revision_feedback = request.revision_feedback
            item.revision_priority = request.revision_priority

            # Create revision item
            revision = RevisionItem(
                approval_item_id=item.id,
                asset_id=item.asset_id,
                original_url=item.original_url,
                enhanced_url=item.enhanced_url,
                feedback=request.revision_feedback or "No feedback provided",
                priority=request.revision_priority,
                product_name=item.product_name,
            )
            self._revisions[revision.id] = revision

            logger.info(
                f"Requested revision for item {item_id}",
                extra={
                    "item_id": item_id,
                    "revision_id": revision.id,
                    "priority": request.revision_priority.value,
                    "correlation_id": correlation_id,
                },
            )

        elif request.action == ApprovalAction.SKIP:
            # No state change, just log
            logger.info(
                f"Skipped item {item_id}",
                extra={
                    "item_id": item_id,
                    "reviewed_by": reviewed_by,
                    "correlation_id": correlation_id,
                },
            )

        return item

    async def batch_process(
        self,
        request: BatchApprovalRequest,
        *,
        reviewed_by: str,
        correlation_id: str | None = None,
    ) -> list[ApprovalItem]:
        """Process batch approval actions.

        Args:
            request: Batch action request
            reviewed_by: User ID of reviewer
            correlation_id: Optional correlation ID

        Returns:
            List of updated ApprovalItems
        """
        results = []

        for item_id in request.item_ids:
            try:
                action_request = ApprovalActionRequest(
                    action=request.action,
                    notes=request.notes,
                )
                item = await self.process_action(
                    item_id,
                    action_request,
                    reviewed_by=reviewed_by,
                    correlation_id=correlation_id,
                )
                results.append(item)
            except ApprovalQueueError as e:
                logger.warning(
                    f"Failed to process item {item_id} in batch: {e}",
                    extra={"correlation_id": correlation_id},
                )

        logger.info(
            f"Batch processed {len(results)}/{len(request.item_ids)} items",
            extra={"correlation_id": correlation_id},
        )

        return results

    async def update_wordpress_sync(
        self,
        item_id: str,
        *,
        wordpress_media_id: int,
        correlation_id: str | None = None,
    ) -> ApprovalItem:
        """Update item with WordPress sync info.

        Args:
            item_id: Item identifier
            wordpress_media_id: WordPress media library ID
            correlation_id: Optional correlation ID

        Returns:
            Updated ApprovalItem
        """
        item = await self.get_item(item_id, correlation_id=correlation_id)
        item.wordpress_media_id = wordpress_media_id
        item.wordpress_synced_at = datetime.now(UTC)

        logger.info(
            f"Updated WordPress sync for item {item_id}: media_id={wordpress_media_id}",
            extra={"correlation_id": correlation_id},
        )

        return item

    async def get_stats(
        self,
        *,
        correlation_id: str | None = None,
    ) -> ApprovalQueueStats:
        """Get approval queue statistics.

        Args:
            correlation_id: Optional correlation ID

        Returns:
            ApprovalQueueStats
        """
        items = list(self._items.values())

        # Count by status
        pending = [i for i in items if i.status == ApprovalStatus.PENDING]
        approved = sum(1 for i in items if i.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for i in items if i.status == ApprovalStatus.REJECTED)
        revision = sum(1 for i in items if i.status == ApprovalStatus.REVISION_REQUESTED)
        expired = sum(1 for i in items if i.status == ApprovalStatus.EXPIRED)

        # Find oldest pending
        oldest_hours = None
        if pending:
            oldest = min(pending, key=lambda x: x.created_at)
            age = datetime.now(UTC) - oldest.created_at
            oldest_hours = age.total_seconds() / 3600

        return ApprovalQueueStats(
            total=len(items),
            pending=len(pending),
            approved=approved,
            rejected=rejected,
            revision_requested=revision,
            expired=expired,
            oldest_pending_hours=oldest_hours,
        )

    async def list_revisions(
        self,
        *,
        priority: RevisionPriority | None = None,
        assigned_to: str | None = None,
        page: int = 1,
        page_size: int = 20,
        correlation_id: str | None = None,
    ) -> RevisionQueueResponse:
        """List items in the revision queue.

        Args:
            priority: Filter by priority
            assigned_to: Filter by assignee
            page: Page number
            page_size: Items per page
            correlation_id: Optional correlation ID

        Returns:
            RevisionQueueResponse
        """
        items = list(self._revisions.values())

        # Filter incomplete
        items = [i for i in items if i.completed_at is None]

        # Apply filters
        if priority:
            items = [i for i in items if i.priority == priority]
        if assigned_to:
            items = [i for i in items if i.assigned_to == assigned_to]

        # Sort by priority then created_at
        priority_order = {
            RevisionPriority.URGENT: 0,
            RevisionPriority.HIGH: 1,
            RevisionPriority.NORMAL: 2,
            RevisionPriority.LOW: 3,
        }
        items.sort(key=lambda x: (priority_order.get(x.priority, 2), x.created_at))

        # Paginate
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        return RevisionQueueResponse(
            items=page_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def complete_revision(
        self,
        revision_id: str,
        *,
        new_enhanced_url: str,
        correlation_id: str | None = None,
    ) -> ApprovalItem:
        """Complete a revision and requeue for approval.

        Args:
            revision_id: Revision item ID
            new_enhanced_url: URL of revised enhanced image
            correlation_id: Optional correlation ID

        Returns:
            Updated ApprovalItem ready for re-review
        """
        revision = self._revisions.get(revision_id)
        if not revision:
            raise ApprovalQueueError(
                f"Revision not found: {revision_id}",
                correlation_id=correlation_id,
            )

        # Mark revision complete
        revision.completed_at = datetime.now(UTC)

        # Update original approval item
        item = await self.get_item(
            revision.approval_item_id,
            correlation_id=correlation_id,
        )
        item.enhanced_url = new_enhanced_url
        item.status = ApprovalStatus.PENDING
        item.reviewed_by = None
        item.reviewed_at = None
        item.review_notes = None

        logger.info(
            f"Completed revision {revision_id}, item {item.id} requeued",
            extra={"correlation_id": correlation_id},
        )

        return item

    async def expire_old_items(
        self,
        *,
        correlation_id: str | None = None,
    ) -> int:
        """Expire items that have passed their expiry date.

        Args:
            correlation_id: Optional correlation ID

        Returns:
            Number of items expired
        """
        now = datetime.now(UTC)
        expired_count = 0

        for item in self._items.values():
            if (
                item.status == ApprovalStatus.PENDING
                and item.expires_at
                and item.expires_at < now
            ):
                item.status = ApprovalStatus.EXPIRED
                expired_count += 1

        if expired_count > 0:
            logger.info(
                f"Expired {expired_count} items",
                extra={"correlation_id": correlation_id},
            )

        return expired_count


# Module singleton
_approval_manager: ApprovalQueueManager | None = None


def get_approval_manager() -> ApprovalQueueManager:
    """Get or create the approval queue manager singleton."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalQueueManager()
    return _approval_manager


__all__ = [
    "ApprovalStatus",
    "ApprovalAction",
    "RevisionPriority",
    "ApprovalItemCreate",
    "ApprovalItem",
    "ApprovalActionRequest",
    "BatchApprovalRequest",
    "ApprovalQueueStats",
    "ApprovalQueueFilter",
    "ApprovalQueueResponse",
    "RevisionItem",
    "RevisionQueueResponse",
    "ApprovalQueueError",
    "ApprovalItemNotFoundError",
    "InvalidApprovalActionError",
    "ApprovalQueueManager",
    "get_approval_manager",
]
