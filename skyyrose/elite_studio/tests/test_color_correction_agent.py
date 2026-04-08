"""Tests for ColorCorrectionAgent — PIL brand-palette color correction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.color_correction_agent import (
    ColorCorrectionAgent,
    _BRIGHTNESS_FACTOR,
    _CONTRAST_FACTOR,
    _SATURATION_FACTOR,
    _SHARPNESS_FACTOR,
)
from skyyrose.elite_studio.models import ColorCorrectionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_test_image(tmp_path: Path, name: str = "test.jpg", size=(64, 64)) -> Path:
    """Create a small RGB JPEG test image."""
    img_path = tmp_path / name
    img = Image.new("RGB", size, color=(183, 110, 121))  # rose gold-ish
    img.save(str(img_path), "JPEG")
    return img_path


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestColorCorrectionResultModel:
    def test_frozen(self):
        r = ColorCorrectionResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = ColorCorrectionResult(success=False)
        assert r.output_path == ""
        assert r.adjustments_applied == ()
        assert r.error == ""


# ---------------------------------------------------------------------------
# ColorCorrectionAgent — happy path
# ---------------------------------------------------------------------------


class TestColorCorrectionAgent:
    def setup_method(self):
        self.agent = ColorCorrectionAgent()

    def test_correct_creates_output_file(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))

        assert result.success is True
        assert Path(result.output_path).exists()

    def test_output_has_corrected_suffix(self, tmp_path):
        src = make_test_image(tmp_path, "product.jpg")
        result = self.agent.correct(str(src))

        assert "corrected" in Path(result.output_path).name

    def test_four_adjustments_applied(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))

        assert result.success is True
        assert len(result.adjustments_applied) == 4

    def test_adjustment_names_correct(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))

        names = {a.split(":")[0] for a in result.adjustments_applied}
        assert "contrast_boost" in names
        assert "saturation_nudge" in names
        assert "brightness_correction" in names
        assert "sharpness_pass" in names

    def test_adjustment_factors_recorded(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))

        assert f"contrast_boost:{_CONTRAST_FACTOR}" in result.adjustments_applied
        assert f"saturation_nudge:{_SATURATION_FACTOR}" in result.adjustments_applied
        assert f"brightness_correction:{_BRIGHTNESS_FACTOR}" in result.adjustments_applied
        assert f"sharpness_pass:{_SHARPNESS_FACTOR}" in result.adjustments_applied

    def test_output_is_valid_image(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))

        # Should be openable by PIL
        with Image.open(result.output_path) as img:
            assert img.mode == "RGB"

    def test_rgba_image_converted_to_rgb(self, tmp_path):
        """RGBA images should be converted to RGB before processing."""
        img_path = tmp_path / "rgba.png"
        img = Image.new("RGBA", (64, 64), color=(183, 110, 121, 255))
        img.save(str(img_path))

        result = self.agent.correct(str(img_path))
        assert result.success is True

    def test_result_is_frozen(self, tmp_path):
        src = make_test_image(tmp_path)
        result = self.agent.correct(str(src))
        with pytest.raises((AttributeError, TypeError)):
            result.success = False  # type: ignore[misc]

    # --- Error cases ---

    def test_missing_file_returns_failure(self):
        result = self.agent.correct("/nonexistent/image.jpg")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_exception_returns_failure(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise RuntimeError("PIL exploded")

        monkeypatch.setattr(
            "skyyrose.elite_studio.agents.color_correction_agent.ColorCorrectionAgent._correct",
            _boom,
        )
        result = self.agent.correct("/any/path.jpg")
        assert result.success is False
        assert "PIL exploded" in result.error
