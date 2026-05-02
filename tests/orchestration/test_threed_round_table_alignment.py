"""Tests for 3D round-table CLIP alignment scoring.

The plan adds a `clip_alignment_score` field (0..1) to ThreeDQualityScores
and weights it 0.20 in the total. Existing weights are rebalanced so they
still sum to 1.0.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from orchestration.threed_round_table import (
    HF3DFormat,
    ThreeDProvider,
    ThreeDQualityScores,
    ThreeDResponse,
    ThreeDRoundTable,
)


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


# ---------------------------------------------------------------------------
# Wiring tests: _score_response actually invokes alignment
# ---------------------------------------------------------------------------


def _make_response_with_thumbnail(thumb_url: str) -> ThreeDResponse:
    return ThreeDResponse(
        provider=ThreeDProvider.TRIPO3D,
        model_id="tripo3d-api",
        output_path="/tmp/dummy.glb",
        format=HF3DFormat.GLB,
        generation_time_ms=15000.0,
        polycount=50000,
        has_textures=True,
        metadata={"thumbnail_url": thumb_url},
    )


def test_score_response_invokes_clip_alignment_when_prompt_and_preview_present() -> None:
    """When a prompt + thumbnail_url are available, alignment is computed."""
    rt = ThreeDRoundTable.__new__(ThreeDRoundTable)
    response = _make_response_with_thumbnail("https://example.com/preview.png")

    with patch.object(ThreeDRoundTable, "_maybe_score_alignment", return_value=0.42) as mock_align:
        scores = rt._score_response(response, prompt="a luxury black hoodie")
        assert scores.clip_alignment_score == pytest.approx(0.42)
        mock_align.assert_called_once()


def test_score_response_skips_alignment_when_no_prompt() -> None:
    """No prompt => alignment is 0.0 (no compute, no network call)."""
    rt = ThreeDRoundTable.__new__(ThreeDRoundTable)
    response = _make_response_with_thumbnail("https://example.com/preview.png")

    scores = rt._score_response(response, prompt=None)
    assert scores.clip_alignment_score == 0.0


def test_score_response_skips_alignment_when_no_preview_image() -> None:
    """No preview image (no thumbnail/preview/rendered) => alignment is 0.0."""
    rt = ThreeDRoundTable.__new__(ThreeDRoundTable)
    response = ThreeDResponse(
        provider=ThreeDProvider.TRIPO3D,
        model_id="tripo3d-api",
        output_path="/tmp/dummy.glb",
        format=HF3DFormat.GLB,
        metadata={},  # No thumbnail_url / preview_url / rendered_image
    )

    scores = rt._score_response(response, prompt="a luxury black hoodie")
    assert scores.clip_alignment_score == 0.0


def test_maybe_score_alignment_handles_network_failure_gracefully() -> None:
    """Network/HTTP error during preview download => 0.0, no exception."""
    rt = ThreeDRoundTable.__new__(ThreeDRoundTable)
    response = _make_response_with_thumbnail("https://nonexistent.invalid/preview.png")

    # httpx.get inside _maybe_score_alignment will raise — confirm we swallow it.
    with patch("httpx.get", side_effect=Exception("network down")):
        score = rt._maybe_score_alignment("a hoodie", response)
        assert score == 0.0


def test_maybe_score_alignment_uses_local_path_when_provided() -> None:
    """preview_path (local) is preferred over thumbnail_url (remote)."""
    rt = ThreeDRoundTable.__new__(ThreeDRoundTable)
    response = ThreeDResponse(
        provider=ThreeDProvider.TRIPO3D,
        model_id="tripo3d-api",
        output_path="/tmp/dummy.glb",
        format=HF3DFormat.GLB,
        metadata={
            "preview_path": "/tmp/local-preview.png",
            "thumbnail_url": "https://example.com/preview.png",
        },
    )

    fake_image = MagicMock()
    with (
        patch("PIL.Image.open", return_value=fake_image) as mock_open,
        patch("skyyrose.elite_studio.quality.clip_alignment.score_alignment", return_value=0.31),
    ):
        score = rt._maybe_score_alignment("a hoodie", response)
        assert score == pytest.approx(0.31)
        # Confirms we hit the local path, not httpx
        mock_open.assert_called_once_with("/tmp/local-preview.png")
