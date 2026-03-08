# tests/api/test_approval_queue.py
"""Tests for approval queue API endpoints.

Implements US-022: WordPress media sync with approval.

Author: DevSkyy Platform Team
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.approval import router
from services.approval_queue_manager import (
    ApprovalItem,
    ApprovalQueueManager,
    ApprovalQueueResponse,
    ApprovalQueueStats,
    ApprovalStatus,
    RevisionItem,
    RevisionPriority,
    RevisionQueueResponse,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> MagicMock:
    """Create mock authenticated user."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="test_jti_123",
        type=TokenType.ACCESS,
        roles=["user", "admin"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def app(mock_user: MagicMock) -> FastAPI:
    """Create test FastAPI app."""
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_item() -> ApprovalItem:
    """Sample approval item."""
    return ApprovalItem(
        id="item_123",
        asset_id="asset_123",
        job_id="job_123",
        original_url="https://example.com/original.jpg",
        enhanced_url="https://example.com/enhanced.jpg",
        product_id="prod_123",
        woocommerce_product_id="456",
        product_name="SkyyRose Hoodie",
        status=ApprovalStatus.PENDING,
    )


# =============================================================================
# Queue Listing Tests
# =============================================================================


class TestQueueListing:
    """Tests for approval queue listing endpoints."""

    @patch("api.v1.approval.get_approval_manager")
    def test_list_queue_default(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should list approval queue with defaults."""
        manager = MagicMock(spec=ApprovalQueueManager)
        manager.list_items = AsyncMock(
            return_value=ApprovalQueueResponse(
                items=[sample_item],
                total=1,
                page=1,
                page_size=20,
                has_more=False,
            )
        )
        mock_get_manager.return_value = manager

        response = client.get("/approval/queue")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "item_123"

    @patch("api.v1.approval.get_approval_manager")
    def test_list_queue_with_filters(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should filter queue by status."""
        manager = MagicMock(spec=ApprovalQueueManager)
        manager.list_items = AsyncMock(
            return_value=ApprovalQueueResponse(
                items=[sample_item],
                total=1,
                page=1,
                page_size=20,
                has_more=False,
            )
        )
        mock_get_manager.return_value = manager

        response = client.get("/approval/queue?status=pending")

        assert response.status_code == 200

    @patch("api.v1.approval.get_approval_manager")
    def test_list_queue_pagination(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
    ) -> None:
        """Should paginate queue results."""
        manager = MagicMock(spec=ApprovalQueueManager)
        manager.list_items = AsyncMock(
            return_value=ApprovalQueueResponse(
                items=[],
                total=50,
                page=2,
                page_size=10,
                has_more=True,
            )
        )
        mock_get_manager.return_value = manager

        response = client.get("/approval/queue?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["has_more"] is True


# =============================================================================
# Get Item Tests
# =============================================================================


class TestGetItem:
    """Tests for getting individual approval items."""

    @patch("api.v1.approval.get_approval_manager")
    def test_get_item_success(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should get approval item by ID."""
        manager = MagicMock(spec=ApprovalQueueManager)
        manager.get_item = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.get("/approval/queue/item_123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "item_123"
        assert data["asset_id"] == "asset_123"

    @patch("api.v1.approval.get_approval_manager")
    def test_get_item_not_found(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
    ) -> None:
        """Should return 404 for non-existent item."""
        from services.approval_queue_manager import ApprovalItemNotFoundError

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.get_item = AsyncMock(side_effect=ApprovalItemNotFoundError("Not found"))
        mock_get_manager.return_value = manager

        response = client.get("/approval/queue/nonexistent")

        assert response.status_code == 404


# =============================================================================
# Action Processing Tests
# =============================================================================


class TestActionProcessing:
    """Tests for approval action endpoints."""

    @patch("api.v1.approval.get_approval_manager")
    def test_approve_item(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should approve pending item."""
        sample_item.status = ApprovalStatus.APPROVED
        sample_item.reviewed_by = "user_123"

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.process_action = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue/item_123/action",
            json={"action": "approve", "notes": "Looks good!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["reviewed_by"] == "user_123"

    @patch("api.v1.approval.get_approval_manager")
    def test_reject_item(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should reject item with reason."""
        sample_item.status = ApprovalStatus.REJECTED
        sample_item.rejection_reason = "Colors incorrect"

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.process_action = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue/item_123/action",
            json={
                "action": "reject",
                "rejection_reason": "Colors incorrect",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    @patch("api.v1.approval.get_approval_manager")
    def test_request_revision(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should request revision with feedback."""
        sample_item.status = ApprovalStatus.REVISION_REQUESTED
        sample_item.revision_feedback = "Adjust lighting"
        sample_item.revision_priority = RevisionPriority.HIGH

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.process_action = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue/item_123/action",
            json={
                "action": "request_revision",
                "revision_feedback": "Adjust lighting",
                "revision_priority": "high",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "revision_requested"

    @patch("api.v1.approval.get_approval_manager")
    def test_action_invalid_state(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
    ) -> None:
        """Should return 400 for invalid action on state."""
        from services.approval_queue_manager import InvalidApprovalActionError

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.process_action = AsyncMock(side_effect=InvalidApprovalActionError("Cannot process"))
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue/item_123/action",
            json={"action": "approve"},
        )

        assert response.status_code == 400


# =============================================================================
# Batch Processing Tests
# =============================================================================


class TestBatchProcessing:
    """Tests for batch approval endpoints."""

    @patch("api.v1.approval.get_approval_manager")
    def test_batch_approve(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should batch approve multiple items."""
        item2 = ApprovalItem(
            id="item_456",
            asset_id="asset_456",
            job_id="job_456",
            original_url="https://example.com/orig2.jpg",
            enhanced_url="https://example.com/enh2.jpg",
            status=ApprovalStatus.APPROVED,
        )

        sample_item.status = ApprovalStatus.APPROVED

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.batch_process = AsyncMock(return_value=[sample_item, item2])
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue/batch",
            json={
                "item_ids": ["item_123", "item_456"],
                "action": "approve",
                "notes": "Batch approved",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["status"] == "approved" for item in data)


# =============================================================================
# Revision Queue Tests
# =============================================================================


class TestRevisionQueue:
    """Tests for revision queue endpoints."""

    @patch("api.v1.approval.get_approval_manager")
    def test_list_revisions(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
    ) -> None:
        """Should list revision queue."""
        revision = RevisionItem(
            id="rev_123",
            approval_item_id="item_123",
            asset_id="asset_123",
            original_url="https://example.com/orig.jpg",
            enhanced_url="https://example.com/enh.jpg",
            feedback="Fix colors",
            priority=RevisionPriority.HIGH,
        )

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.list_revisions = AsyncMock(
            return_value=RevisionQueueResponse(
                items=[revision],
                total=1,
                page=1,
                page_size=20,
            )
        )
        mock_get_manager.return_value = manager

        response = client.get("/approval/revisions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["feedback"] == "Fix colors"

    @patch("api.v1.approval.get_approval_manager")
    def test_complete_revision(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should complete revision and requeue."""
        sample_item.status = ApprovalStatus.PENDING
        sample_item.enhanced_url = "https://example.com/revised.jpg"

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.complete_revision = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/revisions/rev_123/complete",
            json={"new_enhanced_url": "https://example.com/revised.jpg"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for queue statistics endpoints."""

    @patch("api.v1.approval.get_approval_manager")
    def test_get_stats(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
    ) -> None:
        """Should return queue statistics."""
        stats = ApprovalQueueStats(
            total=10,
            pending=5,
            approved=3,
            rejected=1,
            revision_requested=1,
            expired=0,
            oldest_pending_hours=2.5,
        )

        manager = MagicMock(spec=ApprovalQueueManager)
        manager.get_stats = AsyncMock(return_value=stats)
        mock_get_manager.return_value = manager

        response = client.get("/approval/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["pending"] == 5
        assert data["oldest_pending_hours"] == 2.5


# =============================================================================
# WordPress Sync Tests
# =============================================================================


class TestWordPressSync:
    """Tests for WordPress sync endpoint."""

    @patch("api.v1.approval.get_wordpress_sync")
    @patch("api.v1.approval.get_approval_manager")
    def test_trigger_sync(
        self,
        mock_get_manager: MagicMock,
        mock_get_sync: MagicMock,
        client: TestClient,
    ) -> None:
        """Should trigger WordPress sync."""
        from sync.wordpress_media_approval_sync import BatchSyncResult

        sync_result = BatchSyncResult(
            success=True,
            total=3,
            synced=3,
            failed=0,
            skipped=0,
        )

        sync_service = MagicMock()
        sync_service.is_configured = True
        sync_service.sync_approved_items = AsyncMock(return_value=sync_result)
        mock_get_sync.return_value = sync_service

        response = client.post("/approval/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["synced"] == 3

    @patch("api.v1.approval.get_wordpress_sync")
    @patch("api.v1.approval.get_approval_manager")
    def test_sync_not_configured(
        self,
        mock_get_manager: MagicMock,
        mock_get_sync: MagicMock,
        client: TestClient,
    ) -> None:
        """Should return 503 when WordPress not configured."""
        sync_service = MagicMock()
        sync_service.is_configured = False
        mock_get_sync.return_value = sync_service

        response = client.post("/approval/sync")

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]

    @patch("api.v1.approval.get_wordpress_sync")
    @patch("api.v1.approval.get_approval_manager")
    def test_sync_with_limit(
        self,
        mock_get_manager: MagicMock,
        mock_get_sync: MagicMock,
        client: TestClient,
    ) -> None:
        """Should sync with limit parameter."""
        from sync.wordpress_media_approval_sync import BatchSyncResult

        sync_result = BatchSyncResult(
            success=True,
            total=5,
            synced=5,
        )

        sync_service = MagicMock()
        sync_service.is_configured = True
        sync_service.sync_approved_items = AsyncMock(return_value=sync_result)
        mock_get_sync.return_value = sync_service

        response = client.post(
            "/approval/sync",
            json={"limit": 5},
        )

        assert response.status_code == 200
        sync_service.sync_approved_items.assert_called_once_with(limit=5)


# =============================================================================
# Item Creation Tests
# =============================================================================


class TestItemCreation:
    """Tests for creating approval items via API."""

    @patch("api.v1.approval.get_approval_manager")
    def test_create_item(
        self,
        mock_get_manager: MagicMock,
        client: TestClient,
        sample_item: ApprovalItem,
    ) -> None:
        """Should create new approval item."""
        manager = MagicMock(spec=ApprovalQueueManager)
        manager.create_item = AsyncMock(return_value=sample_item)
        mock_get_manager.return_value = manager

        response = client.post(
            "/approval/queue",
            json={
                "asset_id": "asset_123",
                "job_id": "job_123",
                "original_url": "https://example.com/original.jpg",
                "enhanced_url": "https://example.com/enhanced.jpg",
                "product_name": "SkyyRose Hoodie",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "item_123"
        assert data["status"] == "pending"
