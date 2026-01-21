# api/v1/approval.py
"""Approval queue API endpoints.

Implements US-022: WordPress media sync with approval.

Endpoints:
- GET /approval/queue - List pending approvals
- GET /approval/queue/{id} - Get approval item
- POST /approval/queue/{id}/action - Take action on item
- POST /approval/queue/batch - Batch actions
- GET /approval/revisions - List revision queue
- POST /approval/revisions/{id}/complete - Complete revision
- GET /approval/stats - Get queue statistics
- POST /approval/sync - Trigger WordPress sync

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from security.jwt_oauth2_auth import TokenPayload, get_current_user
from services.approval_queue_manager import (
    ApprovalAction,
    ApprovalActionRequest,
    ApprovalItem,
    ApprovalItemCreate,
    ApprovalItemNotFoundError,
    ApprovalQueueFilter,
    ApprovalQueueManager,
    ApprovalQueueResponse,
    ApprovalQueueStats,
    ApprovalStatus,
    BatchApprovalRequest,
    InvalidApprovalActionError,
    RevisionPriority,
    RevisionQueueResponse,
    get_approval_manager,
)
from sync.wordpress_media_approval_sync import (
    BatchSyncResult,
    WordPressMediaApprovalSync,
    get_wordpress_sync,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["Approval Queue"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ActionRequest(BaseModel):
    """Request to take action on an approval item."""

    action: ApprovalAction
    notes: str | None = None
    rejection_reason: str | None = None
    revision_feedback: str | None = None
    revision_priority: RevisionPriority = RevisionPriority.NORMAL


class BatchActionRequest(BaseModel):
    """Request for batch actions."""

    item_ids: list[str]
    action: ApprovalAction
    notes: str | None = None


class RevisionCompleteRequest(BaseModel):
    """Request to complete a revision."""

    new_enhanced_url: str


class SyncTriggerRequest(BaseModel):
    """Request to trigger WordPress sync."""

    limit: int | None = Field(None, description="Maximum items to sync")
    item_ids: list[str] | None = Field(None, description="Specific items to sync")


class QueueSummary(BaseModel):
    """Summary of approval queue state."""

    stats: ApprovalQueueStats
    wordpress_configured: bool
    email_configured: bool


# =============================================================================
# Dependencies
# =============================================================================


def get_manager() -> ApprovalQueueManager:
    """Get approval queue manager."""
    return get_approval_manager()


def get_sync() -> WordPressMediaApprovalSync:
    """Get WordPress sync service."""
    return get_wordpress_sync()


# =============================================================================
# Queue Endpoints
# =============================================================================


@router.get("/queue", response_model=ApprovalQueueResponse)
async def list_approval_queue(
    status_filter: ApprovalStatus | None = Query(None, alias="status"),
    product_id: str | None = Query(None),
    woocommerce_product_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalQueueResponse:
    """
    List items in the approval queue.

    Supports filtering by:
    - **status**: pending, approved, rejected, revision_requested
    - **product_id**: Internal product ID
    - **woocommerce_product_id**: WooCommerce product ID

    Requires authentication.
    """
    filter_params = ApprovalQueueFilter(
        status=status_filter,
        product_id=product_id,
        woocommerce_product_id=woocommerce_product_id,
    )

    return await manager.list_items(
        filter_params=filter_params,
        page=page,
        page_size=page_size,
    )


@router.get("/queue/{item_id}", response_model=ApprovalItem)
async def get_approval_item(
    item_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalItem:
    """
    Get a specific approval item by ID.

    Returns the item with all details including review status.
    """
    try:
        return await manager.get_item(item_id)
    except ApprovalItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval item not found: {item_id}",
        )


@router.post("/queue/{item_id}/action", response_model=ApprovalItem)
async def process_approval_action(
    item_id: str,
    request: ActionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalItem:
    """
    Take an action on an approval item.

    Actions:
    - **approve**: Approve for WordPress sync
    - **reject**: Reject with reason
    - **request_revision**: Request changes with feedback
    - **skip**: Skip without action

    Requires authentication. User ID is tracked as reviewer.
    """
    try:
        action_request = ApprovalActionRequest(
            action=request.action,
            notes=request.notes,
            rejection_reason=request.rejection_reason,
            revision_feedback=request.revision_feedback,
            revision_priority=request.revision_priority,
        )

        return await manager.process_action(
            item_id,
            action_request,
            reviewed_by=current_user.sub,
        )

    except ApprovalItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval item not found: {item_id}",
        )
    except InvalidApprovalActionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/queue/batch", response_model=list[ApprovalItem])
async def batch_process_approvals(
    request: BatchActionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> list[ApprovalItem]:
    """
    Process multiple approval items with the same action.

    Useful for bulk approve/reject operations.
    Returns list of updated items (skips items that fail).
    """
    batch_request = BatchApprovalRequest(
        item_ids=request.item_ids,
        action=request.action,
        notes=request.notes,
    )

    return await manager.batch_process(
        batch_request,
        reviewed_by=current_user.sub,
    )


# =============================================================================
# Revision Endpoints
# =============================================================================


@router.get("/revisions", response_model=RevisionQueueResponse)
async def list_revision_queue(
    priority: RevisionPriority | None = Query(None),
    assigned_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> RevisionQueueResponse:
    """
    List items in the revision queue.

    These are items that were rejected with revision feedback.
    Sorted by priority (urgent first) then creation date.
    """
    return await manager.list_revisions(
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )


@router.post("/revisions/{revision_id}/complete", response_model=ApprovalItem)
async def complete_revision(
    revision_id: str,
    request: RevisionCompleteRequest,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalItem:
    """
    Complete a revision and requeue for approval.

    Provide the new enhanced image URL after addressing feedback.
    The item will be returned to pending status for re-review.
    """
    try:
        return await manager.complete_revision(
            revision_id,
            new_enhanced_url=request.new_enhanced_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Stats & Sync Endpoints
# =============================================================================


@router.get("/stats", response_model=ApprovalQueueStats)
async def get_queue_stats(
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalQueueStats:
    """
    Get approval queue statistics.

    Returns counts by status and age of oldest pending item.
    """
    return await manager.get_stats()


@router.get("/summary", response_model=QueueSummary)
async def get_queue_summary(
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
    sync: WordPressMediaApprovalSync = Depends(get_sync),
) -> QueueSummary:
    """
    Get complete queue summary including configuration status.

    Useful for dashboard overview.
    """
    from services.notifications import get_email_service

    stats = await manager.get_stats()
    email_service = get_email_service()

    return QueueSummary(
        stats=stats,
        wordpress_configured=sync.is_configured,
        email_configured=email_service.is_configured,
    )


@router.post("/sync", response_model=BatchSyncResult)
async def trigger_wordpress_sync(
    request: SyncTriggerRequest | None = None,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
    sync: WordPressMediaApprovalSync = Depends(get_sync),
) -> BatchSyncResult:
    """
    Trigger WordPress sync for approved items.

    Options:
    - No parameters: Sync all approved items not yet synced
    - **limit**: Maximum number of items to sync
    - **item_ids**: Specific items to sync

    Returns detailed results including any failures.
    """
    if not sync.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WordPress is not configured",
        )

    request = request or SyncTriggerRequest()

    # If specific items requested
    if request.item_ids:
        from sync.wordpress_media_approval_sync import BatchSyncResult, SyncStatus

        result = BatchSyncResult(success=True)
        result.total = len(request.item_ids)

        for item_id in request.item_ids:
            try:
                item = await manager.get_item(item_id)
                sync_result = await sync.sync_item(item)
                result.results.append(sync_result)

                if sync_result.status == SyncStatus.COMPLETED:
                    result.synced += 1
                elif sync_result.status == SyncStatus.FAILED:
                    result.failed += 1
                    result.errors.append(f"{item_id}: {sync_result.error_message}")
                else:
                    result.skipped += 1

            except ApprovalItemNotFoundError:
                result.failed += 1
                result.errors.append(f"{item_id}: Item not found")

        result.success = result.failed == 0
        return result

    # Otherwise sync all approved items
    return await sync.sync_approved_items(
        limit=request.limit,
    )


# =============================================================================
# Admin Endpoints
# =============================================================================


@router.post("/expire", response_model=dict[str, int])
async def expire_old_items(
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> dict[str, int]:
    """
    Expire old pending items that have passed their expiry date.

    Admin-only operation. Returns count of expired items.
    """
    # TODO: Add role check for admin

    count = await manager.expire_old_items()
    return {"expired_count": count}


@router.post("/queue", response_model=ApprovalItem)
async def create_approval_item(
    request: ApprovalItemCreate,
    current_user: TokenPayload = Depends(get_current_user),
    manager: ApprovalQueueManager = Depends(get_manager),
) -> ApprovalItem:
    """
    Create a new approval queue item.

    Typically called automatically by the processing pipeline,
    but can be used manually for testing or manual submissions.
    """
    return await manager.create_item(request)
