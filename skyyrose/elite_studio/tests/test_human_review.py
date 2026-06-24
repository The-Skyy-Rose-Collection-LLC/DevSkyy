"""
Tests for HumanReviewGate — approval queue integration.

Tests cover:
- Fail-safe REJECT sentinel when queue unavailable (default, security policy)
- Opt-in auto-approve via SKYYROSE_AUTO_CONFIRM=1 (legacy behavior, gated)
- Submit + poll happy path (mock approval queue)
- Timeout handling → reject by default, approve when opt-in flag is set
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


@pytest.fixture(autouse=True)
def _clear_auto_confirm_env(monkeypatch):
    """Default-fail-safe: tests run without the legacy auto-approve flag set."""
    monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
    yield


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


class TestFailSafeReject:
    """Default behavior (SKYYROSE_AUTO_CONFIRM unset): queue failure → reject."""

    def test_submit_returns_reject_sentinel_when_queue_fails(self):
        gate = HumanReviewGate()
        with patch.object(gate, "_get_manager", side_effect=ImportError("no pydantic")):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id.startswith(
            "auto-reject:"
        ), "Default fail-safe must reject — set SKYYROSE_AUTO_CONFIRM=1 to opt back in"

    def test_get_decision_on_reject_sentinel_returns_reject(self):
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-reject:job-1:ImportError")
        assert decision.decision == "reject"
        assert decision.reviewer == "system"
        assert "fail-safe" in decision.notes.lower()

    def test_reject_review_id_preserved(self):
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-reject:job-xyz:RuntimeError")
        assert decision.review_id == "auto-reject:job-xyz:RuntimeError"


class TestOptInAutoApprove:
    """SKYYROSE_AUTO_CONFIRM=1 restores legacy auto-approve-on-failure."""

    def test_submit_returns_approve_sentinel_when_opted_in(self, monkeypatch):
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
        gate = HumanReviewGate()
        with patch.object(gate, "_get_manager", side_effect=ImportError("no pydantic")):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id.startswith("auto-approve:")

    def test_get_decision_on_approve_sentinel_returns_approve(self):
        # The sentinel decoding does not gate on env — once the sentinel is in
        # play, get_decision honors it. (Gate is on the producer, not reader.)
        gate = HumanReviewGate()
        decision = gate.get_decision("auto-approve:job-1")
        assert decision.decision == "approve"
        assert decision.reviewer == "system"


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

    def test_submit_exception_falls_back_to_reject_by_default(self):
        gate = HumanReviewGate()
        mock_manager = MagicMock()
        mock_manager.create_item = AsyncMock(side_effect=RuntimeError("queue down"))
        with patch.object(gate, "_get_manager", return_value=mock_manager):
            review_id = gate.submit_for_review("br-001", "/tmp/img.jpg", "job-1")
        assert review_id.startswith("auto-reject:")

    def test_submit_exception_falls_back_to_approve_when_opted_in(self, monkeypatch):
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
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
    def _make_pending_manager(self):
        mock_item = MagicMock()
        mock_item.status = MagicMock()
        mock_item.status.value = "pending"  # always pending
        mock_item.reviewed_by = None
        mock_item.review_notes = None
        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(return_value=mock_item)
        return mock_manager

    def test_timeout_returns_reject_by_default(self):
        """Default fail-safe: deadline elapsed → reject (not timeout/approve)."""
        gate = HumanReviewGate(poll_interval=0.001)
        with patch.object(gate, "_get_manager", return_value=self._make_pending_manager()):
            decision = gate.get_decision("review-1", timeout=0.02)
        assert decision.decision == "reject"
        assert decision.reviewer == "system"
        assert "timeout" in decision.notes.lower()

    def test_timeout_returns_timeout_decision_when_opted_in(self, monkeypatch):
        """Legacy behavior under SKYYROSE_AUTO_CONFIRM=1 — returns 'timeout'."""
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
        gate = HumanReviewGate(poll_interval=0.001)
        with patch.object(gate, "_get_manager", return_value=self._make_pending_manager()):
            decision = gate.get_decision("review-1", timeout=0.02)
        assert decision.decision == "timeout"
        assert decision.reviewer == "system"

    def test_timeout_review_id_preserved(self):
        gate = HumanReviewGate(poll_interval=0.001)
        with patch.object(gate, "_get_manager", return_value=self._make_pending_manager()):
            decision = gate.get_decision("review-42", timeout=0.01)
        assert decision.review_id == "review-42"


# ---------------------------------------------------------------------------
# Poll queue error → auto-approve
# ---------------------------------------------------------------------------


class TestPollError:
    def test_queue_error_during_poll_rejects_by_default(self):
        gate = HumanReviewGate(poll_interval=0.001)
        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(side_effect=RuntimeError("DB gone"))

        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-err", timeout=60.0)

        assert decision.decision == "reject"
        assert "fail-safe" in decision.notes.lower()

    def test_queue_error_during_poll_approves_when_opted_in(self, monkeypatch):
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
        gate = HumanReviewGate(poll_interval=0.001)
        mock_manager = MagicMock()
        mock_manager.get_item = AsyncMock(side_effect=RuntimeError("DB gone"))

        with patch.object(gate, "_get_manager", return_value=mock_manager):
            decision = gate.get_decision("review-err", timeout=60.0)

        assert decision.decision == "approve"
        assert "opt-in" in decision.notes.lower() or "auto-approved" in decision.notes.lower()


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
