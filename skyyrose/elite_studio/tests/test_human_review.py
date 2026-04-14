"""
Tests for HumanReviewGate — approval queue integration.

Tests cover:
- Auto-approve sentinel when queue unavailable
- Submit + poll happy path (mock approval queue)
- Timeout handling → approve
- Reject decision propagation
- Status mapping from ApprovalStatus → decision string
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.quality.human_review import (
    HumanReviewGate,
    ReviewDecision,
)


# ---------------------------------------------------------------------------
# ReviewDecision data class
# ---------------------------------------------------------------------------


class TestReviewDecision:
    def test_frozen(self):
        decision = ReviewDecision(review_id="r1", decision="approve", reviewer="alice")
        with pytest.raises((AttributeError, TypeError)):
            decision.decision = "reject"  # type: ignore[misc]

    def test_defaults(self):
        d = ReviewDecision(review_id="r1", decision="approve", reviewer="bob")
        assert d.notes == ""

    def test_all_fields(self):
        d = ReviewDecision(
            review_id="r123",
            decision="reject",
            reviewer="carol",
            notes="bad crop",
        )
        assert d.review_id == "r123"
        assert d.decision == "reject"
        assert d.reviewer == "carol"
        assert d.notes == "bad crop"


# ---------------------------------------------------------------------------
# Auto-approve sentinel (queue unavailable)
# ---------------------------------------------------------------------------


class TestAutoApprove:
    def test_submit_returns_sentinel_when_queue_fails(self):
        gate = HumanReviewGate()
        with patch.object(gate, "_get_manager", side_effect=ImportError("no pydantic")):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id.startswith("auto-approve:")

    def test_get_decision_on_sentinel_returns_approve(self):
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-approve:job-1")
        assert decision.decision == "approve"
        assert decision.reviewer == "system"
        assert "unavailable" in decision.notes.lower()

    def test_auto_approve_review_id_preserved(self):
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-approve:job-xyz")
        assert decision.review_id == "auto-approve:job-xyz"


# ---------------------------------------------------------------------------
# Happy path — submit + poll
# ---------------------------------------------------------------------------


class TestHappyPath:
    def _make_manager(self, status: str, reviewed_by: str = "admin", notes: str = ""):
        """Build a mock ApprovalQueueManager that returns the given item status."""
        mock_item = MagicMock()
        mock_item.id = "review-999"
        mock_item.status = MagicMock()
        mock_item.status.value = status
        mock_item.reviewed_by = reviewed_by
        mock_item.review_notes = notes

        manager = MagicMock()
        manager.create_item = AsyncMock(return_value=mock_item)
        manager.get_item = AsyncMock(return_value=mock_item)
        return manager

    def test_submit_returns_review_id(self):
        gate = HumanReviewGate()
        mock_manager = self._make_manager("pending")
        with patch.object(gate, "_get_manager", return_value=mock_manager):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id == "review-999"

    def test_get_decision_approved(self):
        gate = HumanReviewGate(poll_interval=0.001)
        mock_manager = self._make_manager("approved", reviewed_by="alice", notes="looks great")
        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-999")
        assert decision.decision == "approve"
        assert decision.reviewer == "alice"
        assert decision.notes == "looks great"

    def test_get_decision_rejected(self):
        gate = HumanReviewGate(poll_interval=0.001)
        mock_manager = self._make_manager("rejected", reviewed_by="bob", notes="wrong color")
        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-999")
        assert decision.decision == "reject"

    def test_submit_exception_falls_back_to_auto_approve(self):
        gate = HumanReviewGate()
        mock_manager = MagicMock()
        mock_manager.create_item = AsyncMock(side_effect=RuntimeError("queue down"))
        with patch.object(gate, "_get_manager", return_value=mock_manager):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id.startswith("auto-approve:")


# ---------------------------------------------------------------------------
# Timeout handling
# ---------------------------------------------------------------------------


class TestTimeout:
    def test_timeout_returns_timeout_decision(self):
        """When deadline passes before a decision, returns decision='timeout'."""
        gate = HumanReviewGate(poll_interval=0.001)

        mock_item = MagicMock()
        mock_item.status = MagicMock()
        mock_item.status.value = "pending"  # always pending
        mock_item.reviewed_by = None
        mock_item.review_notes = None

        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(return_value=mock_item)

        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-1", timeout=0.02)

        assert decision.decision == "timeout"
        assert decision.reviewer == "system"

    def test_timeout_review_id_preserved(self):
        gate = HumanReviewGate(poll_interval=0.001)
        mock_item = MagicMock()
        mock_item.status = MagicMock()
        mock_item.status.value = "pending"
        mock_item.reviewed_by = None
        mock_item.review_notes = None

        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(return_value=mock_item)

        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-42", timeout=0.01)

        assert decision.review_id == "review-42"


# ---------------------------------------------------------------------------
# Poll queue error → auto-approve
# ---------------------------------------------------------------------------


class TestPollError:
    def test_queue_error_during_poll_auto_approves(self):
        gate = HumanReviewGate(poll_interval=0.001)
        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(side_effect=RuntimeError("DB gone"))

        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-err", timeout=60.0)

        assert decision.decision == "approve"
        assert "auto-approved" in decision.notes.lower()


# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------


class TestStatusMapping:
    @pytest.mark.parametrize(
        "raw_status, expected",
        [
            ("approved", "approve"),
            ("rejected", "reject"),
            ("pending", "pending"),
            ("revision_requested", "pending"),
            ("expired", "timeout"),
            ("unknown_state", "pending"),
        ],
    )
    def test_map_status(self, raw_status: str, expected: str):
        result = HumanReviewGate._map_status(raw_status)
        assert result == expected
