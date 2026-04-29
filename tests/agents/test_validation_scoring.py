"""Tests for agents.core.validation_scoring.compute_validation_scores.

Replaces the hardcoded ``quality_score = 0.9`` baseline in Tripo/Meshy.
Each test pins one branch of the scoring contract.
"""

from __future__ import annotations

import pytest

from agents.core.validation_scoring import compute_validation_scores


class TestComputeValidationScores:
    """Contract tests — each branch documents an intended behavior."""

    def test_measured_score_in_zero_to_hundred_range_is_normalized(self) -> None:
        quality, confidence = compute_validation_scores({"fidelity_score": 87.5}, warning_count=0)
        assert quality == 0.875
        assert confidence == 0.95

    def test_measured_score_in_zero_to_one_range_passes_through(self) -> None:
        quality, confidence = compute_validation_scores({"fidelity_score": 0.92}, warning_count=0)
        assert quality == 0.92
        assert confidence == 0.95

    def test_measured_score_ignores_warning_count(self) -> None:
        # Real fidelity is the source of truth; warnings don't reduce it.
        quality, _ = compute_validation_scores({"fidelity_score": 80.0}, warning_count=10)
        assert quality == 0.8

    def test_no_asset_validation_returns_unmeasured_baseline(self) -> None:
        quality, confidence = compute_validation_scores(None, warning_count=0)
        assert quality == 0.6
        assert confidence == 0.5

    def test_empty_asset_validation_returns_unmeasured_baseline(self) -> None:
        quality, confidence = compute_validation_scores({}, warning_count=0)
        assert quality == 0.6
        assert confidence == 0.5

    def test_unmeasured_baseline_degrades_linearly_per_warning(self) -> None:
        quality, _ = compute_validation_scores({}, warning_count=4)
        assert quality == pytest.approx(0.4, abs=1e-9)

    def test_unmeasured_baseline_clamped_at_minimum(self) -> None:
        # Many warnings must not push quality below the floor.
        quality, _ = compute_validation_scores({}, warning_count=100)
        assert quality == 0.2

    def test_garbage_fidelity_falls_back_to_baseline(self) -> None:
        quality, confidence = compute_validation_scores({"fidelity_score": "oops"}, warning_count=0)
        assert quality == 0.6
        assert confidence == 0.5

    def test_negative_fidelity_clamped_to_zero(self) -> None:
        quality, confidence = compute_validation_scores({"fidelity_score": -10.0}, warning_count=0)
        assert quality == 0.0
        assert confidence == 0.95

    def test_above_one_hundred_fidelity_clamped_to_one(self) -> None:
        quality, _ = compute_validation_scores({"fidelity_score": 150.0}, warning_count=0)
        assert quality == 1.0

    def test_never_returns_hardcoded_zero_point_nine(self) -> None:
        # Pin: the bug we're fixing was a fabricated 0.9 baseline.
        scenarios = [
            (None, 0),
            ({}, 0),
            ({"fidelity_score": None}, 0),
            ({"fidelity_score": "bad"}, 5),
        ]
        for asset_validation, warnings in scenarios:
            quality, _ = compute_validation_scores(asset_validation, warning_count=warnings)
            assert quality != 0.9, f"Should not produce 0.9 for asset_validation={asset_validation}"
