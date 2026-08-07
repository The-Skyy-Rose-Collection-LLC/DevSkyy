"""
Visual regression testing tool for Elite Web Builder.

Captures page screenshots via Playwright CLI, compares against baselines
using Pillow pixel-level diffing, and generates highlighted diff images.
All result objects are frozen (immutable) dataclasses.

Usage:
    result = compare_screenshots("baseline.png", "current.png", threshold=0.5)
    if not result.passed:
        print(f"Visual regression: {result.diff_percentage:.2f}% changed")
        print(f"Diff image: {result.diff_path}")
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_VIEWPORT = {"width": 1280, "height": 720}
DIFF_HIGHLIGHT_COLOR = (255, 0, 0)  # Red for changed pixels


# ---------------------------------------------------------------------------
# Data models (frozen / immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiffResult:
    """Immutable result of comparing two screenshots."""

    baseline_path: str
    current_path: str
    diff_path: str
    diff_percentage: float
    passed: bool
    threshold: float
    dimensions: tuple[int, int]


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------


def _validate_file_exists(path: str, label: str) -> Path:
    """Validate that a file exists and return its Path."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return file_path


def _validate_dir_exists(path: str, label: str) -> Path:
    """Validate that a directory exists and return its Path."""
    dir_path = Path(path)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"{label} not found: {path}")
    return dir_path


def _url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename for baseline storage."""
    # Strip protocol, replace non-alphanumeric with underscores
    cleaned = re.sub(r"https?://", "", url)
    cleaned = re.sub(r"[^a-zA-Z0-9]", "_", cleaned)
    # Collapse multiple underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_") + ".png"


# ---------------------------------------------------------------------------
# Screenshot capture
# ---------------------------------------------------------------------------


def capture_screenshot(
    url: str,
    output_path: str,
    viewport: dict[str, int] | None = None,
) -> str:
    """
    Capture a page screenshot using Playwright CLI.

    Args:
        url: Page URL to capture.
        output_path: Where to save the screenshot PNG.
        viewport: Dict with 'width' and 'height' keys. Defaults to 1280x720.

    Returns:
        The output_path on success.

    Raises:
        ValueError: If url or output_path is empty.
        RuntimeError: If Playwright screenshot command fails.
    """
    if not url:
        raise ValueError("url must not be empty")
    if not output_path:
        raise ValueError("output_path must not be empty")

    effective_viewport = {**DEFAULT_VIEWPORT, **(viewport or {})}
    width = str(effective_viewport["width"])
    height = str(effective_viewport["height"])

    cmd = [
        "npx", "playwright", "screenshot",
        "--viewport-size", f"{width},{height}",
        url,
        output_path,
    ]

    logger.info("Capturing screenshot: %s -> %s", url, output_path)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Screenshot capture failed (exit {proc.returncode}): {proc.stderr}"
        )

    return output_path


# ---------------------------------------------------------------------------
# Image comparison
# ---------------------------------------------------------------------------


def _load_and_normalize(
    baseline_path: Path, current_path: Path
) -> tuple[Image.Image, Image.Image]:
    """
    Load two images, resizing current to match baseline if sizes differ.

    Returns a new tuple of (baseline_img, current_img) — originals are not
    mutated.
    """
    baseline_img = Image.open(baseline_path).convert("RGB")
    current_img = Image.open(current_path).convert("RGB")

    if baseline_img.size != current_img.size:
        logger.warning(
            "Size mismatch: baseline=%s, current=%s. Resizing current to match.",
            baseline_img.size,
            current_img.size,
        )
        current_img = current_img.resize(baseline_img.size, Image.LANCZOS)

    return baseline_img, current_img


def _compute_pixel_diff(
    baseline_img: Image.Image,
    current_img: Image.Image,
) -> tuple[Image.Image, float]:
    """
    Compute pixel-level diff between two same-size RGB images.

    Changed pixels are highlighted in red on the diff image.
    Returns (diff_image, diff_percentage).
    """
    width, height = baseline_img.size
    total_pixels = width * height

    baseline_pixels = baseline_img.load()
    current_pixels = current_img.load()

    diff_img = Image.new("RGB", (width, height), (0, 0, 0))
    diff_pixels = diff_img.load()

    changed_count = 0

    for y in range(height):
        for x in range(width):
            bp = baseline_pixels[x, y]
            cp = current_pixels[x, y]
            if bp != cp:
                changed_count += 1
                diff_pixels[x, y] = DIFF_HIGHLIGHT_COLOR
            else:
                # Dim version of original for context
                diff_pixels[x, y] = (bp[0] // 3, bp[1] // 3, bp[2] // 3)

    diff_percentage = (changed_count / total_pixels) * 100.0 if total_pixels > 0 else 0.0
    return diff_img, diff_percentage


def compare_screenshots(
    baseline_path: str,
    current_path: str,
    threshold: float = 0.5,
) -> DiffResult:
    """
    Compare two screenshot images pixel-by-pixel.

    Generates a diff image highlighting changed pixels in red. If current
    image has different dimensions, it is resized to match baseline.

    Args:
        baseline_path: Path to the baseline screenshot.
        current_path: Path to the current screenshot.
        threshold: Maximum acceptable diff percentage (0-100). Default 0.5%.

    Returns:
        Frozen DiffResult with comparison metrics and diff image path.

    Raises:
        FileNotFoundError: If either image file does not exist.
        Exception: If an image file cannot be opened/decoded.
    """
    baseline_file = _validate_file_exists(baseline_path, "Baseline image")
    current_file = _validate_file_exists(current_path, "Current image")

    baseline_img, current_img = _load_and_normalize(baseline_file, current_file)

    diff_img, diff_percentage = _compute_pixel_diff(baseline_img, current_img)

    # Save diff image next to the current image
    diff_file = current_file.parent / f"{current_file.stem}_diff.png"
    diff_img.save(str(diff_file))

    return DiffResult(
        baseline_path=str(baseline_file),
        current_path=str(current_file),
        diff_path=str(diff_file),
        diff_percentage=round(diff_percentage, 4),
        passed=diff_percentage <= threshold,
        threshold=threshold,
        dimensions=baseline_img.size,
    )


# ---------------------------------------------------------------------------
# Full visual regression workflow
# ---------------------------------------------------------------------------


def run_visual_regression(
    url: str,
    baselines_dir: str,
    output_dir: str,
    threshold: float = 0.5,
    viewport: dict[str, int] | None = None,
) -> DiffResult | None:
    """
    Run a full visual regression test for a URL.

    Captures a screenshot, then either saves it as a new baseline (if none
    exists) or compares it against the existing baseline.

    Args:
        url: Page URL to test.
        baselines_dir: Directory containing baseline screenshots.
        output_dir: Directory for current screenshots and diff images.
        threshold: Maximum acceptable diff percentage. Default 0.5%.
        viewport: Browser viewport size.

    Returns:
        DiffResult if a baseline existed and comparison was performed.
        None if this was a new baseline (no prior screenshot to compare).

    Raises:
        FileNotFoundError: If baselines_dir or output_dir does not exist.
    """
    baselines_path = _validate_dir_exists(baselines_dir, "baselines_dir")
    output_path = _validate_dir_exists(output_dir, "output_dir")

    filename = _url_to_filename(url)
    baseline_file = baselines_path / filename
    current_file = output_path / filename

    # Capture current screenshot
    capture_screenshot(url, str(current_file), viewport=viewport)

    # If no baseline exists, promote current to baseline
    if not baseline_file.exists():
        logger.info("No baseline for %s — saving current as new baseline", url)
        current_img = Image.open(str(current_file))
        current_img.save(str(baseline_file))
        return None

    # Compare against existing baseline
    return compare_screenshots(
        baseline_path=str(baseline_file),
        current_path=str(current_file),
        threshold=threshold,
    )
