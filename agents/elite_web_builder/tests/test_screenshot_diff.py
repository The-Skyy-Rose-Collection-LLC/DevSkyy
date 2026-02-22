"""Tests for tools/screenshot_diff.py — Visual regression testing tool.

Uses Pillow to create test images in-memory (no external file dependencies).
Mocks subprocess/Playwright for capture_screenshot tests.
Uses tmp_path pytest fixture for all file I/O.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from tools.screenshot_diff import (
    DiffResult,
    capture_screenshot,
    compare_screenshots,
    run_visual_regression,
)


# ---------------------------------------------------------------------------
# Helpers — create test images in-memory, save to tmp_path
# ---------------------------------------------------------------------------


def _save_solid_image(
    path: Path,
    color: str | tuple[int, int, int],
    size: tuple[int, int] = (100, 100),
) -> Path:
    """Create and save a solid-color image. Returns the path."""
    img = Image.new("RGB", size, color)
    img.save(str(path))
    return path


def _save_half_red_half_blue(path: Path, size: tuple[int, int] = (100, 100)) -> Path:
    """Create an image that is half red (left) and half blue (right)."""
    img = Image.new("RGB", size, "red")
    half_width = size[0] // 2
    for x in range(half_width, size[0]):
        for y in range(size[1]):
            img.putpixel((x, y), (0, 0, 255))
    img.save(str(path))
    return path


# ---------------------------------------------------------------------------
# DiffResult dataclass
# ---------------------------------------------------------------------------


class TestDiffResult:
    def test_creation(self) -> None:
        result = DiffResult(
            baseline_path="/a.png",
            current_path="/b.png",
            diff_path="/diff.png",
            diff_percentage=1.5,
            passed=True,
            threshold=5.0,
            dimensions=(1280, 720),
        )
        assert result.baseline_path == "/a.png"
        assert result.current_path == "/b.png"
        assert result.diff_path == "/diff.png"
        assert result.diff_percentage == 1.5
        assert result.passed is True
        assert result.threshold == 5.0
        assert result.dimensions == (1280, 720)

    def test_immutability(self) -> None:
        result = DiffResult(
            baseline_path="/a.png",
            current_path="/b.png",
            diff_path="/diff.png",
            diff_percentage=0.0,
            passed=True,
            threshold=0.5,
            dimensions=(100, 100),
        )
        with pytest.raises(AttributeError):
            result.diff_percentage = 99.0  # type: ignore[misc]

    def test_passed_reflects_threshold(self) -> None:
        passing = DiffResult(
            baseline_path="/a.png",
            current_path="/b.png",
            diff_path="/diff.png",
            diff_percentage=0.3,
            passed=True,
            threshold=0.5,
            dimensions=(100, 100),
        )
        assert passing.passed is True

        failing = DiffResult(
            baseline_path="/a.png",
            current_path="/b.png",
            diff_path="/diff.png",
            diff_percentage=5.0,
            passed=False,
            threshold=0.5,
            dimensions=(100, 100),
        )
        assert failing.passed is False


# ---------------------------------------------------------------------------
# compare_screenshots — identical images
# ---------------------------------------------------------------------------


class TestCompareIdentical:
    def test_identical_images_zero_diff(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        current = _save_solid_image(tmp_path / "current.png", "red")

        result = compare_screenshots(str(baseline), str(current), threshold=0.5)

        assert result.diff_percentage == 0.0
        assert result.passed is True
        assert result.dimensions == (100, 100)

    def test_identical_generates_diff_image(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "blue")
        current = _save_solid_image(tmp_path / "current.png", "blue")

        result = compare_screenshots(str(baseline), str(current))

        assert os.path.exists(result.diff_path)

    def test_identical_large_images(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(
            tmp_path / "baseline.png", "green", size=(500, 500)
        )
        current = _save_solid_image(
            tmp_path / "current.png", "green", size=(500, 500)
        )

        result = compare_screenshots(str(baseline), str(current))
        assert result.diff_percentage == 0.0
        assert result.dimensions == (500, 500)


# ---------------------------------------------------------------------------
# compare_screenshots — different images
# ---------------------------------------------------------------------------


class TestCompareDifferent:
    def test_completely_different_images(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        current = _save_solid_image(tmp_path / "current.png", "blue")

        result = compare_screenshots(str(baseline), str(current), threshold=0.5)

        assert result.diff_percentage > 0.0
        assert result.passed is False

    def test_partially_different_images(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        current = _save_half_red_half_blue(tmp_path / "current.png")

        result = compare_screenshots(str(baseline), str(current), threshold=0.5)

        # Roughly 50% should differ
        assert 40.0 <= result.diff_percentage <= 60.0
        assert result.passed is False

    def test_diff_image_highlights_changes(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        current = _save_solid_image(tmp_path / "current.png", "blue")

        result = compare_screenshots(str(baseline), str(current))

        # The diff image should exist and be loadable
        diff_img = Image.open(result.diff_path)
        assert diff_img.size == (100, 100)

    def test_single_pixel_difference(self, tmp_path: Path) -> None:
        """A single changed pixel on a 100x100 image = 0.01% diff."""
        baseline = _save_solid_image(tmp_path / "baseline.png", "white")
        # Create current with one changed pixel
        current_img = Image.new("RGB", (100, 100), "white")
        current_img.putpixel((50, 50), (0, 0, 0))
        current_path = tmp_path / "current.png"
        current_img.save(str(current_path))

        result = compare_screenshots(str(baseline), str(current_path), threshold=1.0)

        assert 0.0 < result.diff_percentage < 1.0
        assert result.passed is True  # within 1.0% threshold

    def test_high_threshold_passes(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        current = _save_solid_image(tmp_path / "current.png", "blue")

        result = compare_screenshots(str(baseline), str(current), threshold=100.0)
        assert result.passed is True


# ---------------------------------------------------------------------------
# compare_screenshots — size mismatch
# ---------------------------------------------------------------------------


class TestCompareSizeMismatch:
    def test_different_sizes_resizes_current(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(
            tmp_path / "baseline.png", "red", size=(200, 200)
        )
        current = _save_solid_image(
            tmp_path / "current.png", "red", size=(100, 100)
        )

        result = compare_screenshots(str(baseline), str(current))

        # Dimensions should match baseline
        assert result.dimensions == (200, 200)

    def test_different_sizes_still_compares(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(
            tmp_path / "baseline.png", "red", size=(200, 200)
        )
        current = _save_solid_image(
            tmp_path / "current.png", "blue", size=(150, 150)
        )

        result = compare_screenshots(str(baseline), str(current))

        assert result.diff_percentage > 0.0
        assert result.dimensions == (200, 200)


# ---------------------------------------------------------------------------
# compare_screenshots — error handling
# ---------------------------------------------------------------------------


class TestCompareErrors:
    def test_missing_baseline_raises(self, tmp_path: Path) -> None:
        current = _save_solid_image(tmp_path / "current.png", "red")
        with pytest.raises(FileNotFoundError):
            compare_screenshots("/nonexistent/baseline.png", str(current))

    def test_missing_current_raises(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        with pytest.raises(FileNotFoundError):
            compare_screenshots(str(baseline), "/nonexistent/current.png")

    def test_invalid_image_raises(self, tmp_path: Path) -> None:
        baseline = _save_solid_image(tmp_path / "baseline.png", "red")
        invalid_path = tmp_path / "invalid.png"
        invalid_path.write_text("not an image")

        with pytest.raises(Exception):
            compare_screenshots(str(baseline), str(invalid_path))

    def test_both_missing_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            compare_screenshots("/no/baseline.png", "/no/current.png")


# ---------------------------------------------------------------------------
# capture_screenshot
# ---------------------------------------------------------------------------


class TestCaptureScreenshot:
    @patch("tools.screenshot_diff.subprocess.run")
    def test_capture_calls_playwright(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        output = tmp_path / "shot.png"

        result = capture_screenshot("https://example.com", str(output))

        assert result == str(output)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "playwright" in cmd[0] or "npx" in cmd[0]

    @patch("tools.screenshot_diff.subprocess.run")
    def test_capture_with_custom_viewport(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        output = tmp_path / "shot.png"
        viewport = {"width": 1920, "height": 1080}

        capture_screenshot("https://example.com", str(output), viewport=viewport)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "1920" in cmd_str

    @patch("tools.screenshot_diff.subprocess.run")
    def test_capture_default_viewport(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        output = tmp_path / "shot.png"

        capture_screenshot("https://example.com", str(output))

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "1280" in cmd_str

    @patch("tools.screenshot_diff.subprocess.run")
    def test_capture_failure_raises(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="failed")

        with pytest.raises(RuntimeError, match="Screenshot capture failed"):
            capture_screenshot(
                "https://example.com", str(tmp_path / "shot.png")
            )

    def test_capture_empty_url_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="url"):
            capture_screenshot("", str(tmp_path / "shot.png"))

    def test_capture_empty_output_path_raises(self) -> None:
        with pytest.raises(ValueError, match="output_path"):
            capture_screenshot("https://example.com", "")


# ---------------------------------------------------------------------------
# run_visual_regression
# ---------------------------------------------------------------------------


class TestRunVisualRegression:
    @patch("tools.screenshot_diff.capture_screenshot")
    def test_no_baseline_creates_new(
        self, mock_capture: MagicMock, tmp_path: Path
    ) -> None:
        baselines_dir = tmp_path / "baselines"
        baselines_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock capture to create a real image at the output location
        def fake_capture(url: str, output_path: str, viewport: dict | None = None) -> str:
            _save_solid_image(Path(output_path), "red")
            return output_path

        mock_capture.side_effect = fake_capture

        result = run_visual_regression(
            url="https://example.com",
            baselines_dir=str(baselines_dir),
            output_dir=str(output_dir),
        )

        # No existing baseline => returns None, saves as new baseline
        assert result is None
        baseline_files = list(baselines_dir.iterdir())
        assert len(baseline_files) == 1

    @patch("tools.screenshot_diff.capture_screenshot")
    def test_with_existing_baseline_returns_diff(
        self, mock_capture: MagicMock, tmp_path: Path
    ) -> None:
        baselines_dir = tmp_path / "baselines"
        baselines_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create an existing baseline
        _save_solid_image(baselines_dir / "example_com.png", "red")

        # Mock capture to create a different image
        def fake_capture(url: str, output_path: str, viewport: dict | None = None) -> str:
            _save_solid_image(Path(output_path), "blue")
            return output_path

        mock_capture.side_effect = fake_capture

        result = run_visual_regression(
            url="https://example.com",
            baselines_dir=str(baselines_dir),
            output_dir=str(output_dir),
        )

        assert result is not None
        assert isinstance(result, DiffResult)
        assert result.diff_percentage > 0.0

    @patch("tools.screenshot_diff.capture_screenshot")
    def test_with_matching_baseline_passes(
        self, mock_capture: MagicMock, tmp_path: Path
    ) -> None:
        baselines_dir = tmp_path / "baselines"
        baselines_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Baseline is red
        _save_solid_image(baselines_dir / "example_com.png", "red")

        # Current screenshot is also red
        def fake_capture(url: str, output_path: str, viewport: dict | None = None) -> str:
            _save_solid_image(Path(output_path), "red")
            return output_path

        mock_capture.side_effect = fake_capture

        result = run_visual_regression(
            url="https://example.com",
            baselines_dir=str(baselines_dir),
            output_dir=str(output_dir),
        )

        assert result is not None
        assert result.passed is True
        assert result.diff_percentage == 0.0

    @patch("tools.screenshot_diff.capture_screenshot")
    def test_custom_threshold(
        self, mock_capture: MagicMock, tmp_path: Path
    ) -> None:
        baselines_dir = tmp_path / "baselines"
        baselines_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        _save_solid_image(baselines_dir / "example_com.png", "red")

        def fake_capture(url: str, output_path: str, viewport: dict | None = None) -> str:
            _save_solid_image(Path(output_path), "blue")
            return output_path

        mock_capture.side_effect = fake_capture

        # Very high threshold — should pass even with completely different images
        result = run_visual_regression(
            url="https://example.com",
            baselines_dir=str(baselines_dir),
            output_dir=str(output_dir),
            threshold=100.0,
        )

        assert result is not None
        assert result.passed is True

    def test_invalid_baselines_dir_raises(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="baselines_dir"):
            run_visual_regression(
                url="https://example.com",
                baselines_dir="/nonexistent/baselines",
                output_dir=str(output_dir),
            )

    def test_invalid_output_dir_raises(self, tmp_path: Path) -> None:
        baselines_dir = tmp_path / "baselines"
        baselines_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="output_dir"):
            run_visual_regression(
                url="https://example.com",
                baselines_dir=str(baselines_dir),
                output_dir="/nonexistent/output",
            )
