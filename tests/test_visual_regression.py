"""
Tests for VisualRegressionTester — SSIM comparison against golden references.

scikit-image is mocked so tests run without the optional dependency.
Real PIL image creation is used for the no-reference and set_golden paths.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

import pytest

from skyyrose.elite_studio.quality.visual_regression import (
    RegressionResult,
    VisualRegressionTester,
)

# ---------------------------------------------------------------------------
# Helpers — create tiny JPEG images for testing
# ---------------------------------------------------------------------------


def _make_jpeg(path: Path, color: tuple[int, int, int] = (128, 128, 128)) -> Path:
    """Create a small solid-colour JPEG at path. Returns path."""
    try:
        from PIL import Image

        img = Image.new("RGB", (64, 64), color=color)
        img.save(str(path), format="JPEG")
    except ImportError:
        # If PIL is not available write a minimal valid-ish JPEG header
        # (tests that don't call SSIM directly will still pass)
        path.write_bytes(
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
        )
    return path


# ---------------------------------------------------------------------------
# RegressionResult dataclass
# ---------------------------------------------------------------------------


class TestRegressionResult:
    def test_frozen(self):
        r = RegressionResult(
            success=True,
            sku="br-001",
            ssim_score=0.9,
            passed=True,
            threshold=0.85,
            has_reference=True,
            report_path="",
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            r.ssim_score = 0.5  # type: ignore[misc]

    def test_default_error_empty(self):
        r = RegressionResult(
            success=True,
            sku="br-001",
            ssim_score=0.9,
            passed=True,
            threshold=0.85,
            has_reference=False,
            report_path="",
        )
        assert r.error == ""


# ---------------------------------------------------------------------------
# No golden reference path
# ---------------------------------------------------------------------------


class TestNoReference:
    def test_returns_passed_true_when_no_golden(self, tmp_path):
        tester = VisualRegressionTester(
            golden_base=tmp_path / "golden", reports_base=tmp_path / "reports"
        )
        gen_img = _make_jpeg(tmp_path / "gen.jpg")

        result = tester.compare(str(gen_img), "br-001")

        assert result.success is True
        assert result.has_reference is False
        assert result.passed is True
        assert result.ssim_score == 1.0
        assert result.report_path == ""


# ---------------------------------------------------------------------------
# set_golden stores reference correctly
# ---------------------------------------------------------------------------


class TestSetGolden:
    def test_set_golden_creates_reference_file(self, tmp_path):
        golden_base = tmp_path / "golden"
        tester = VisualRegressionTester(golden_base=golden_base, reports_base=tmp_path / "reports")
        src = _make_jpeg(tmp_path / "approved.jpg", color=(200, 100, 50))

        tester.set_golden("sg-001", str(src))

        ref_path = golden_base / "sg-001" / "reference.jpg"
        assert ref_path.exists()
        assert ref_path.stat().st_size > 0

    def test_set_golden_overwrites_existing(self, tmp_path):
        golden_base = tmp_path / "golden"
        tester = VisualRegressionTester(golden_base=golden_base, reports_base=tmp_path / "reports")
        src1 = _make_jpeg(tmp_path / "v1.jpg", color=(10, 20, 30))
        src2 = _make_jpeg(tmp_path / "v2.jpg", color=(200, 210, 220))

        tester.set_golden("sg-002", str(src1))
        size1 = (golden_base / "sg-002" / "reference.jpg").stat().st_size

        tester.set_golden("sg-002", str(src2))
        size2 = (golden_base / "sg-002" / "reference.jpg").stat().st_size

        # Both writes succeeded (file exists and is non-empty)
        assert size2 > 0


# ---------------------------------------------------------------------------
# SSIM comparison with mocked scikit-image
# ---------------------------------------------------------------------------


class TestSSIMComparison:
    def _setup(self, tmp_path: Path, ssim_return_value: float):
        """Create golden reference + generated image, mock SSIM to return value."""
        golden_base = tmp_path / "golden"
        reports_base = tmp_path / "reports"
        tester = VisualRegressionTester(golden_base=golden_base, reports_base=reports_base)

        # Create golden reference
        ref = golden_base / "br-001"
        ref.mkdir(parents=True)
        _make_jpeg(ref / "reference.jpg", color=(100, 100, 100))

        # Create generated image
        gen = _make_jpeg(tmp_path / "generated.jpg", color=(110, 100, 90))

        return tester, str(gen), ssim_return_value

    def test_passes_when_ssim_above_threshold(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.92)

        with patch.object(tester, "_compute_ssim", return_value=0.92):
            result = tester.compare(gen_path, "br-001")

        assert result.success is True
        assert result.passed is True
        assert result.ssim_score == pytest.approx(0.92)
        assert result.has_reference is True

    def test_fails_when_ssim_below_threshold(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.70)

        with patch.object(tester, "_compute_ssim", return_value=0.70):
            result = tester.compare(gen_path, "br-001")

        assert result.success is True
        assert result.passed is False
        assert result.ssim_score == pytest.approx(0.70)

    def test_report_generated_when_reference_exists(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.88)

        with patch.object(tester, "_compute_ssim", return_value=0.88):
            result = tester.compare(gen_path, "br-001")

        assert result.report_path != ""
        assert Path(result.report_path).exists()
        html = Path(result.report_path).read_text(encoding="utf-8")
        assert "br-001" in html
        assert "PASS" in html

    def test_report_shows_fail_badge_on_low_ssim(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.60)

        with patch.object(tester, "_compute_ssim", return_value=0.60):
            result = tester.compare(gen_path, "br-001")

        html = Path(result.report_path).read_text(encoding="utf-8")
        assert "FAIL" in html

    def test_graceful_fallback_when_skimage_missing(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.0)

        with patch.object(
            tester, "_compute_ssim", side_effect=ImportError("No module named 'skimage'")
        ):
            result = tester.compare(gen_path, "br-001")

        assert result.success is True
        assert result.passed is True
        assert result.ssim_score == 1.0
        assert "scikit-image" in result.error

    def test_returns_error_result_on_unexpected_exception(self, tmp_path):
        tester, gen_path, _ = self._setup(tmp_path, 0.0)

        with patch.object(tester, "_compute_ssim", side_effect=ValueError("corrupt image")):
            result = tester.compare(gen_path, "br-001")

        assert result.success is False
        assert result.passed is False
        assert "corrupt image" in result.error


# ---------------------------------------------------------------------------
# Custom threshold
# ---------------------------------------------------------------------------


class TestCustomThreshold:
    def test_custom_threshold_applied(self, tmp_path):
        golden_base = tmp_path / "golden"
        reports_base = tmp_path / "reports"
        tester = VisualRegressionTester(
            golden_base=golden_base, reports_base=reports_base, threshold=0.95
        )

        ref = golden_base / "sg-001"
        ref.mkdir(parents=True)
        _make_jpeg(ref / "reference.jpg")
        gen = _make_jpeg(tmp_path / "gen.jpg")

        # SSIM 0.90 is below 0.95 threshold
        with patch.object(tester, "_compute_ssim", return_value=0.90):
            result = tester.compare(str(gen), "sg-001")

        assert result.threshold == 0.95
        assert result.passed is False
