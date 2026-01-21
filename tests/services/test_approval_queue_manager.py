# tests/services/test_approval_queue_manager.py
"""Tests for approval queue manager service.

Implements US-022: WordPress media sync with approval.

Author: DevSkyy Platform Team
"""

import pytest
from datetime import datetime, UTC

from services.approval_queue_manager import (
    ApprovalAction,
    ApprovalActionRequest,
    ApprovalItem,
    ApprovalItemCreate,
    ApprovalItemNotFoundError,
    ApprovalQueueFilter,
    ApprovalQueueManager,
    ApprovalStatus,
    BatchApprovalRequest,
    InvalidApprovalActionError,
    RevisionPriority,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def manager() -> ApprovalQueueManager:
    """Create approval queue manager for testing."""
    return ApprovalQueueManager()


@pytest.fixture
def sample_create_request() -> ApprovalItemCreate:
    """Sample item creation request."""
    return ApprovalItemCreate(
        asset_id="asset_123",
        job_id="job_123",
        original_url="https://example.com/original.jpg",
        enhanced_url="https://example.com/enhanced.jpg",
        product_id="prod_123",
        woocommerce_product_id="456",
        product_name="SkyyRose Black Hoodie",
        metadata={"source": "test"},
    )


# =============================================================================
# Item Creation Tests
# =============================================================================


class TestItemCreation:
    """Tests for approval item creation."""

    @pytest.mark.asyncio
    async def test_create_item_success(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should create approval item successfully."""
        item = await manager.create_item(sample_create_request)

        assert item.id is not None
        assert item.asset_id == "asset_123"
        assert item.job_id == "job_123"
        assert item.status == ApprovalStatus.PENDING
        assert item.original_url == "https://example.com/original.jpg"
        assert item.enhanced_url == "https://example.com/enhanced.jpg"
        assert item.product_name == "SkyyRose Black Hoodie"
        assert item.expires_at is not None

    @pytest.mark.asyncio
    async def test_create_item_minimal(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should create item with minimal fields."""
        request = ApprovalItemCreate(
            asset_id="asset_min",
            job_id="job_min",
            original_url="https://example.com/orig.jpg",
            enhanced_url="https://example.com/enh.jpg",
        )

        item = await manager.create_item(request)

        assert item.asset_id == "asset_min"
        assert item.product_id is None
        assert item.product_name is None

    @pytest.mark.asyncio
    async def test_get_item_success(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should retrieve created item."""
        created = await manager.create_item(sample_create_request)
        retrieved = await manager.get_item(created.id)

        assert retrieved.id == created.id
        assert retrieved.asset_id == created.asset_id

    @pytest.mark.asyncio
    async def test_get_item_not_found(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should raise error for non-existent item."""
        with pytest.raises(ApprovalItemNotFoundError):
            await manager.get_item("nonexistent_id")


# =============================================================================
# Action Processing Tests
# =============================================================================


class TestActionProcessing:
    """Tests for approval action processing."""

    @pytest.mark.asyncio
    async def test_approve_item(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should approve pending item."""
        item = await manager.create_item(sample_create_request)

        request = ApprovalActionRequest(
            action=ApprovalAction.APPROVE,
            notes="Looks great!",
        )

        updated = await manager.process_action(
            item.id,
            request,
            reviewed_by="user_123",
        )

        assert updated.status == ApprovalStatus.APPROVED
        assert updated.reviewed_by == "user_123"
        assert updated.reviewed_at is not None
        assert updated.review_notes == "Looks great!"

    @pytest.mark.asyncio
    async def test_reject_item(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should reject pending item."""
        item = await manager.create_item(sample_create_request)

        request = ApprovalActionRequest(
            action=ApprovalAction.REJECT,
            rejection_reason="Colors don't match brand guidelines",
        )

        updated = await manager.process_action(
            item.id,
            request,
            reviewed_by="user_456",
        )

        assert updated.status == ApprovalStatus.REJECTED
        assert updated.reviewed_by == "user_456"
        assert updated.rejection_reason == "Colors don't match brand guidelines"

    @pytest.mark.asyncio
    async def test_request_revision(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should request revision for item."""
        item = await manager.create_item(sample_create_request)

        request = ApprovalActionRequest(
            action=ApprovalAction.REQUEST_REVISION,
            revision_feedback="Please adjust the lighting",
            revision_priority=RevisionPriority.HIGH,
        )

        updated = await manager.process_action(
            item.id,
            request,
            reviewed_by="user_789",
        )

        assert updated.status == ApprovalStatus.REVISION_REQUESTED
        assert updated.revision_feedback == "Please adjust the lighting"
        assert updated.revision_priority == RevisionPriority.HIGH

    @pytest.mark.asyncio
    async def test_cannot_process_approved_item(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should not allow action on already approved item."""
        item = await manager.create_item(sample_create_request)

        # First approve
        await manager.process_action(
            item.id,
            ApprovalActionRequest(action=ApprovalAction.APPROVE),
            reviewed_by="user_1",
        )

        # Then try to reject
        with pytest.raises(InvalidApprovalActionError):
            await manager.process_action(
                item.id,
                ApprovalActionRequest(action=ApprovalAction.REJECT),
                reviewed_by="user_2",
            )


# =============================================================================
# Batch Processing Tests
# =============================================================================


class TestBatchProcessing:
    """Tests for batch approval operations."""

    @pytest.mark.asyncio
    async def test_batch_approve(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should batch approve multiple items."""
        # Create multiple items
        items = []
        for i in range(3):
            request = ApprovalItemCreate(
                asset_id=f"asset_{i}",
                job_id=f"job_{i}",
                original_url=f"https://example.com/orig_{i}.jpg",
                enhanced_url=f"https://example.com/enh_{i}.jpg",
            )
            items.append(await manager.create_item(request))

        # Batch approve
        batch_request = BatchApprovalRequest(
            item_ids=[item.id for item in items],
            action=ApprovalAction.APPROVE,
            notes="Batch approved",
        )

        results = await manager.batch_process(
            batch_request,
            reviewed_by="admin_user",
        )

        assert len(results) == 3
        for result in results:
            assert result.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_batch_with_invalid_ids(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should skip invalid IDs in batch."""
        item = await manager.create_item(sample_create_request)

        batch_request = BatchApprovalRequest(
            item_ids=[item.id, "invalid_id_1", "invalid_id_2"],
            action=ApprovalAction.APPROVE,
        )

        results = await manager.batch_process(
            batch_request,
            reviewed_by="admin",
        )

        # Only valid item should be processed
        assert len(results) == 1
        assert results[0].id == item.id


# =============================================================================
# Listing Tests
# =============================================================================


class TestListing:
    """Tests for listing and filtering."""

    @pytest.mark.asyncio
    async def test_list_items_default(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should list items with default pagination."""
        # Create items
        for i in range(5):
            await manager.create_item(
                ApprovalItemCreate(
                    asset_id=f"asset_{i}",
                    job_id=f"job_{i}",
                    original_url=f"https://example.com/orig_{i}.jpg",
                    enhanced_url=f"https://example.com/enh_{i}.jpg",
                )
            )

        response = await manager.list_items()

        assert response.total == 5
        assert len(response.items) == 5
        assert response.page == 1

    @pytest.mark.asyncio
    async def test_list_items_filter_by_status(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should filter items by status."""
        # Create and approve one item
        item1 = await manager.create_item(
            ApprovalItemCreate(
                asset_id="approved_asset",
                job_id="job_1",
                original_url="https://example.com/o1.jpg",
                enhanced_url="https://example.com/e1.jpg",
            )
        )
        await manager.process_action(
            item1.id,
            ApprovalActionRequest(action=ApprovalAction.APPROVE),
            reviewed_by="user",
        )

        # Create pending item
        await manager.create_item(
            ApprovalItemCreate(
                asset_id="pending_asset",
                job_id="job_2",
                original_url="https://example.com/o2.jpg",
                enhanced_url="https://example.com/e2.jpg",
            )
        )

        # Filter by pending
        response = await manager.list_items(
            filter_params=ApprovalQueueFilter(status=ApprovalStatus.PENDING)
        )

        assert response.total == 1
        assert response.items[0].asset_id == "pending_asset"

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should paginate results correctly."""
        for i in range(15):
            await manager.create_item(
                ApprovalItemCreate(
                    asset_id=f"asset_{i}",
                    job_id=f"job_{i}",
                    original_url=f"https://example.com/orig_{i}.jpg",
                    enhanced_url=f"https://example.com/enh_{i}.jpg",
                )
            )

        # Page 1
        response1 = await manager.list_items(page=1, page_size=10)
        assert len(response1.items) == 10
        assert response1.has_more is True

        # Page 2
        response2 = await manager.list_items(page=2, page_size=10)
        assert len(response2.items) == 5
        assert response2.has_more is False


# =============================================================================
# Revision Queue Tests
# =============================================================================


class TestRevisionQueue:
    """Tests for revision queue operations."""

    @pytest.mark.asyncio
    async def test_revision_created_on_request(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should create revision item when revision requested."""
        item = await manager.create_item(sample_create_request)

        await manager.process_action(
            item.id,
            ApprovalActionRequest(
                action=ApprovalAction.REQUEST_REVISION,
                revision_feedback="Fix the background",
                revision_priority=RevisionPriority.URGENT,
            ),
            reviewed_by="reviewer",
        )

        revisions = await manager.list_revisions()

        assert revisions.total == 1
        assert revisions.items[0].feedback == "Fix the background"
        assert revisions.items[0].priority == RevisionPriority.URGENT

    @pytest.mark.asyncio
    async def test_complete_revision(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should complete revision and requeue item."""
        item = await manager.create_item(sample_create_request)

        await manager.process_action(
            item.id,
            ApprovalActionRequest(
                action=ApprovalAction.REQUEST_REVISION,
                revision_feedback="Adjust colors",
            ),
            reviewed_by="reviewer",
        )

        revisions = await manager.list_revisions()
        revision_id = revisions.items[0].id

        # Complete revision
        updated = await manager.complete_revision(
            revision_id,
            new_enhanced_url="https://example.com/revised.jpg",
        )

        assert updated.status == ApprovalStatus.PENDING
        assert updated.enhanced_url == "https://example.com/revised.jpg"
        assert updated.reviewed_by is None

    @pytest.mark.asyncio
    async def test_revisions_sorted_by_priority(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should sort revisions by priority."""
        priorities = [RevisionPriority.LOW, RevisionPriority.URGENT, RevisionPriority.NORMAL]

        for i, priority in enumerate(priorities):
            item = await manager.create_item(
                ApprovalItemCreate(
                    asset_id=f"asset_{i}",
                    job_id=f"job_{i}",
                    original_url=f"https://example.com/o{i}.jpg",
                    enhanced_url=f"https://example.com/e{i}.jpg",
                )
            )
            await manager.process_action(
                item.id,
                ApprovalActionRequest(
                    action=ApprovalAction.REQUEST_REVISION,
                    revision_feedback=f"Feedback {i}",
                    revision_priority=priority,
                ),
                reviewed_by="user",
            )

        revisions = await manager.list_revisions()

        # Should be sorted: URGENT, NORMAL, LOW
        assert revisions.items[0].priority == RevisionPriority.URGENT
        assert revisions.items[1].priority == RevisionPriority.NORMAL
        assert revisions.items[2].priority == RevisionPriority.LOW


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for queue statistics."""

    @pytest.mark.asyncio
    async def test_get_stats(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should return accurate statistics."""
        # Create various items
        item1 = await manager.create_item(
            ApprovalItemCreate(
                asset_id="a1", job_id="j1",
                original_url="http://x/o1", enhanced_url="http://x/e1",
            )
        )
        item2 = await manager.create_item(
            ApprovalItemCreate(
                asset_id="a2", job_id="j2",
                original_url="http://x/o2", enhanced_url="http://x/e2",
            )
        )
        await manager.create_item(
            ApprovalItemCreate(
                asset_id="a3", job_id="j3",
                original_url="http://x/o3", enhanced_url="http://x/e3",
            )
        )

        # Approve one
        await manager.process_action(
            item1.id,
            ApprovalActionRequest(action=ApprovalAction.APPROVE),
            reviewed_by="user",
        )

        # Reject one
        await manager.process_action(
            item2.id,
            ApprovalActionRequest(action=ApprovalAction.REJECT),
            reviewed_by="user",
        )

        stats = await manager.get_stats()

        assert stats.total == 3
        assert stats.pending == 1
        assert stats.approved == 1
        assert stats.rejected == 1
        assert stats.oldest_pending_hours is not None


# =============================================================================
# WordPress Sync Tests
# =============================================================================


class TestWordPressSync:
    """Tests for WordPress sync tracking."""

    @pytest.mark.asyncio
    async def test_update_wordpress_sync(
        self,
        manager: ApprovalQueueManager,
        sample_create_request: ApprovalItemCreate,
    ) -> None:
        """Should update WordPress sync info."""
        item = await manager.create_item(sample_create_request)

        updated = await manager.update_wordpress_sync(
            item.id,
            wordpress_media_id=12345,
        )

        assert updated.wordpress_media_id == 12345
        assert updated.wordpress_synced_at is not None


# =============================================================================
# Expiration Tests
# =============================================================================


class TestExpiration:
    """Tests for item expiration."""

    @pytest.mark.asyncio
    async def test_expire_old_items(
        self,
        manager: ApprovalQueueManager,
    ) -> None:
        """Should expire items past expiry date."""
        from datetime import timedelta

        # Create item
        item = await manager.create_item(
            ApprovalItemCreate(
                asset_id="expiring",
                job_id="job_exp",
                original_url="http://x/o",
                enhanced_url="http://x/e",
            )
        )

        # Manually set expiry to past
        manager._items[item.id].expires_at = datetime.now(UTC) - timedelta(hours=1)

        # Run expiration
        count = await manager.expire_old_items()

        assert count == 1
        assert manager._items[item.id].status == ApprovalStatus.EXPIRED
