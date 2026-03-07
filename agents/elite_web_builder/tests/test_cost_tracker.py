"""Tests for core.cost_tracker — token usage and cost tracking."""

from __future__ import annotations

import pytest

from core.cost_tracker import CostSummary, CostTracker, TokenRecord


class TestComputeCost:
    def test_sonnet_pricing(self) -> None:
        # claude-sonnet-4-6: $3/1M in, $15/1M out
        cost = CostTracker.compute_cost("claude-sonnet-4-6", 1000, 2000)
        expected = (1000 * 3.0 + 2000 * 15.0) / 1_000_000
        assert cost == pytest.approx(expected, abs=0.000001)

    def test_haiku_pricing(self) -> None:
        # claude-haiku-4-5: $0.80/1M in, $4.0/1M out
        cost = CostTracker.compute_cost("claude-haiku-4-5", 5000, 10000)
        expected = (5000 * 0.80 + 10000 * 4.0) / 1_000_000
        assert cost == pytest.approx(expected, abs=0.000001)

    def test_opus_pricing(self) -> None:
        # claude-opus-4-6: $15/1M in, $75/1M out
        cost = CostTracker.compute_cost("claude-opus-4-6", 2000, 5000)
        expected = (2000 * 15.0 + 5000 * 75.0) / 1_000_000
        assert cost == pytest.approx(expected, abs=0.000001)

    def test_unknown_model_uses_default(self) -> None:
        # Default: $3/1M in, $15/1M out
        cost = CostTracker.compute_cost("unknown-model-xyz", 1000, 1000)
        expected = (1000 * 3.0 + 1000 * 15.0) / 1_000_000
        assert cost == pytest.approx(expected, abs=0.000001)

    def test_zero_tokens(self) -> None:
        cost = CostTracker.compute_cost("claude-sonnet-4-6", 0, 0)
        assert cost == 0.0


class TestRecord:
    def test_record_returns_token_record(self) -> None:
        tracker = CostTracker()
        rec = tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        assert isinstance(rec, TokenRecord)
        assert rec.story_id == "US-001"
        assert rec.input_tokens == 1000
        assert rec.output_tokens == 2000
        assert rec.cost_usd > 0

    def test_multiple_records(self) -> None:
        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        tracker.record("US-002", "google", "gemini-3-pro-preview", 500, 1000)
        assert len(tracker.records) == 2

    def test_total_cost(self) -> None:
        tracker = CostTracker()
        r1 = tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        r2 = tracker.record("US-002", "google", "gemini-3-pro-preview", 500, 1000)
        assert tracker.total_cost == pytest.approx(r1.cost_usd + r2.cost_usd, abs=0.000001)

    def test_total_tokens(self) -> None:
        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        tracker.record("US-002", "google", "gemini-3-pro-preview", 500, 1000)
        assert tracker.total_input_tokens == 1500
        assert tracker.total_output_tokens == 3000


class TestSummary:
    def test_summary_structure(self) -> None:
        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        tracker.record("US-002", "google", "gemini-3-pro-preview", 500, 1000)
        s = tracker.summary()
        assert isinstance(s, CostSummary)
        assert s.records_count == 2
        assert "anthropic" in s.by_provider
        assert "google" in s.by_provider
        assert "US-001" in s.by_story
        assert "US-002" in s.by_story

    def test_empty_summary(self) -> None:
        tracker = CostTracker()
        s = tracker.summary()
        assert s.total_cost_usd == 0.0
        assert s.records_count == 0

    def test_by_model(self) -> None:
        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        tracker.record("US-002", "anthropic", "claude-sonnet-4-6", 500, 1000)
        s = tracker.summary()
        assert "claude-sonnet-4-6" in s.by_model
        assert len(s.by_model) == 1  # same model used twice


class TestToDict:
    def test_serializable(self) -> None:
        import json

        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        data = tracker.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(data)
        assert "total_cost_usd" in json_str
        assert "by_provider" in json_str


class TestReset:
    def test_reset_clears_all(self) -> None:
        tracker = CostTracker()
        tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1000, 2000)
        assert len(tracker.records) == 1
        tracker.reset()
        assert len(tracker.records) == 0
        assert tracker.total_cost == 0.0
