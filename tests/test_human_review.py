"""
Tests for HumanReviewGate — human approval queue integration.

The ApprovalQueueManager is mocked throughout so no real queue or
network calls are made.
"""

from __future__ import annotations

import asyncio
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.quality.human_review import (
    HumanReviewGate,
    ReviewDecision,
)


# ---------------------------------------------------------------------------
# ReviewDecision dataclass
# ---------------------------------------------------------------------------


class TestReviewDecision:
    def test_frozen(self):
        d = ReviewDecision(review_id="r1", decision="approve", reviewer="alice")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            d.decision = "reject"  # type: ignore[misc]

    def test_default_notes_empty(self):
        d = ReviewDecision(review_id="r1", decision="approve", reviewer="bob")
        assert d.notes == ""


# ---------------------------------------------------------------------------
# Auto-approve sentinel
# ---------------------------------------------------------------------------


class TestAutoApprove:
    def test_submit_returns_auto_approve_when_queue_unavailable(self):
        gate = HumanReviewGate()

        with patch.object(gate, "_get_manager", side_effect=ImportError("no services")):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")

        assert review_id.startswith("auto-approve:")

    def test_get_decision_on_auto_approve_sentinel(self):
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-approve:job-1")

        assert decision.decision == "approve"
        assert decision.reviewer == "system"
        assert "Auto-approved" in decision.notes

    def test_get_decision_defaults_to_approve_on_queue_error(self):
        gate = HumanReviewGate()

        with patch.object(gate, "_get_manager", side_effect=RuntimeError("queue crashed")):
            decision = gate.get_decision("real-review-id-123", timeout=0.01)

        assert decision.decision == "approve"
        assert decision.reviewer == "system"


# ---------------------------------------------------------------------------
# Normal submit → poll cycle
# ---------------------------------------------------------------------------


class _FakeApprovalItem:
    """Minimal mock of ApprovalItem returned by the queue manager."""

    def __init__(self, item_id: str, status_value: str, reviewer: str = "human"):
        self.id = item_id
        self.status = MagicMock()
        self.status.value = status_value
        self.reviewed_by = reviewer
        self.review_notes = "looks good"


class TestSubmitPollCycle:
    def _make_manager(self, item: _FakeApprovalItem) -> MagicMock:
        manager = MagicMock()
        manager.create_item = AsyncMock(return_value=item)
        manager.get_item = AsyncMock(return_value=item)
        return manager

    def test_submit_for_review_returns_item_id(self):
        item = _FakeApprovalItem("review-abc", "pending")
        manager = self._make_manager(item)

        gate = HumanReviewGate(poll_interval=0.0)

        with patch.object(gate, "_get_manager", return_value=manager):
            with patch(
                "skyyrose.elite_studio.quality.human_review.asyncio.get_event_loop"
            ) as mock_loop:
                loop = asyncio.new_event_loop()
                mock_loop.return_value = loop
                try:
                    review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
                finally:
                    loop.close()

        assert review_id == "review-abc"

    def test_get_decision_returns_approve_on_approved_status(self):
        item = _FakeApprovalItem("review-abc", "approved", reviewer="reviewer_1")
        manager = self._make_manager(item)

        gate = HumanReviewGate(poll_interval=0.0)

        with patch.object(gate, "_get_manager", return_value=manager):
            with patch(
                "skyyrose.elite_studio.quality.human_review.asyncio.get_event_loop"
            ) as mock_loop:
                loop = asyncio.new_event_loop()
                mock_loop.return_value = loop
                try:
                    decision = gate.get_decision("review-abc", timeout=5.0)
                finally:
                    loop.close()

        assert decision.decision == "approve"
        assert decision.reviewer == "reviewer_1"
        assert decision.review_id == "review-abc"

    def test_get_decision_returns_reject_on_rejected_status(self):
        item = _FakeApprovalItem("review-xyz", "rejected", reviewer="reviewer_2")
        manager = self._make_manager(item)

        gate = HumanReviewGate(poll_interval=0.0)

        with patch.object(gate, "_get_manager", return_value=manager):
            with patch(
                "skyyrose.elite_studio.quality.human_review.asyncio.get_event_loop"
            ) as mock_loop:
                loop = asyncio.new_event_loop()
                mock_loop.return_value = loop
                try:
                    decision = gate.get_decision("review-xyz", timeout=5.0)
                finally:
                    loop.close()

        assert decision.decision == "reject"
        assert decision.reviewer == "reviewer_2"

    def test_get_decision_times_out_and_defaults_to_timeout(self):
        """When the item stays pending past the timeout window, decision is 'timeout'."""
        item = _FakeApprovalItem("review-pending", "pending")
        manager = self._make_manager(item)

        # Very short timeout and poll interval to keep test fast
        gate = HumanReviewGate(poll_interval=0.001)

        with patch.object(gate, "_get_manager", return_value=manager):
            with patch(
                "skyyrose.elite_studio.quality.human_review.asyncio.get_event_loop"
            ) as mock_loop:
                loop = asyncio.new_event_loop()
                mock_loop.return_value = loop
                try:
                    decision = gate.get_decision("review-pending", timeout=0.005)
                finally:
                    loop.close()

        assert decision.decision == "timeout"
        assert decision.reviewer == "system"


# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------


class TestStatusMapping:
    @pytest.mark.parametrize(
        "status,expected",
        [
            ("approved", "approve"),
            ("rejected", "reject"),
            ("pending", "pending"),
            ("revision_requested", "pending"),
            ("expired", "timeout"),
            ("unknown_value", "pending"),
        ],
    )
    def test_map_status(self, status: str, expected: str):
        result = HumanReviewGate._map_status(status)
        assert result == expected
