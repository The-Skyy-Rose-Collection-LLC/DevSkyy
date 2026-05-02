"""Tests for 3D round-table CLIP alignment scoring.

The plan adds a `clip_alignment_score` field (0..1) to ThreeDQualityScores
and weights it 0.20 in the total. Existing weights are rebalanced so they
still sum to 1.0.
"""

from __future__ import annotations

import pytest

from orchestration.threed_round_table import ThreeDQualityScores


def test_clip_alignment_score_field_exists() -> None:
    s = ThreeDQualityScores(clip_alignment_score=0.35)
    assert s.clip_alignment_score == pytest.approx(0.35)


def test_clip_alignment_contributes_to_total() -> None:
    """Higher CLIP alignment must increase the weighted total, holding others fixed."""
    high = ThreeDQualityScores(
        geometry_quality=80,
        texture_quality=80,
        file_format_score=80,
        clip_alignment_score=0.40,
    )
    low = ThreeDQualityScores(
        geometry_quality=80,
        texture_quality=80,
        file_format_score=80,
        clip_alignment_score=0.05,
    )
    assert high.total > low.total


def test_clip_alignment_score_in_to_dict() -> None:
    """Scores serialise the new field for audit logs."""
    s = ThreeDQualityScores(clip_alignment_score=0.27)
    d = s.to_dict()
    assert "clip_alignment_score" in d
    assert d["clip_alignment_score"] == pytest.approx(0.27)


def test_perfect_score_with_full_alignment_caps_at_100() -> None:
    """All old metrics at 100 + alignment at 1.0 reaches the 100 cap.

    Confirms the proportional rebalance: old weights * 0.80 + alignment * 0.20 = 1.00.
    """
    s = ThreeDQualityScores(
        geometry_quality=100,
        texture_quality=100,
        polycount_efficiency=100,
        file_format_score=100,
        generation_speed=100,
        web_readiness=100,
        clip_alignment_score=1.0,
    )
    assert s.total == pytest.approx(100.0, abs=0.01)


def test_perfect_old_metrics_zero_alignment_lands_at_80() -> None:
    """Existing-style fixtures (no alignment set) score 80 not 100.

    This is the documented behavior change from the rebalance: old fields
    contribute 0.80 of the weight; alignment contributes 0.20.
    """
    s = ThreeDQualityScores(
        geometry_quality=100,
        texture_quality=100,
        polycount_efficiency=100,
        file_format_score=100,
        generation_speed=100,
        web_readiness=100,
    )
    assert s.total == pytest.approx(80.0, abs=0.01)
