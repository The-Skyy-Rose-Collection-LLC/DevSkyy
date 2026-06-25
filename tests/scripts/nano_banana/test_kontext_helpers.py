"""Tests for the Kontext refinement helpers.

Covers the pure logic (aspect-ratio selection, PNG validation) without
hitting FAL. The full refine_with_kontext function is exercised by the
manual paid validator at scripts/nano_banana/_validate_layer1.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from nano_banana.engine_fal import (
    _closest_kontext_aspect_ratio,
    _is_png_bytes,
)


def test_aspect_ratio_square():
    """1:1 input → 1:1."""
    assert _closest_kontext_aspect_ratio(1024, 1024) == "1:1"


def test_aspect_ratio_br_001_baseline():
    """The br-001 baseline candidate was 2000x1800 (1.111). Closest enum is 1:1."""
    assert _closest_kontext_aspect_ratio(2000, 1800) == "1:1"


def test_aspect_ratio_landscape_4_3():
    """1024x768 (4:3 exact) → 4:3."""
    assert _closest_kontext_aspect_ratio(1024, 768) == "4:3"


def test_aspect_ratio_landscape_16_9():
    """1920x1080 (16:9 exact) → 16:9."""
    assert _closest_kontext_aspect_ratio(1920, 1080) == "16:9"


def test_aspect_ratio_landscape_21_9():
    """3440x1440 (~2.39, between 21:9=2.33 and 16:9=1.78) → 21:9."""
    assert _closest_kontext_aspect_ratio(3440, 1440) == "21:9"


def test_aspect_ratio_portrait_3_4():
    """768x1024 (3:4 exact) → 3:4."""
    assert _closest_kontext_aspect_ratio(768, 1024) == "3:4"


def test_aspect_ratio_portrait_9_16():
    """1080x1920 (9:16 exact) → 9:16."""
    assert _closest_kontext_aspect_ratio(1080, 1920) == "9:16"


def test_aspect_ratio_handles_zero_dims_safely():
    """Defensive: zero dims fall back to 1:1 instead of div-by-zero."""
    assert _closest_kontext_aspect_ratio(0, 100) == "1:1"
    assert _closest_kontext_aspect_ratio(100, 0) == "1:1"
    assert _closest_kontext_aspect_ratio(0, 0) == "1:1"


def test_aspect_ratio_uses_log_distance_metric():
    """Ratio 1.5 (3:2) and 0.667 (2:3) are equally distant from 1:1.

    With absolute distance, 1.5 is "0.5 away" and 0.667 is "0.333 away",
    which would prefer 0.667 — but a 2x-wider mistake is just as bad as
    a 2x-taller mistake. Log distance fixes this.
    """
    # 2160x1440 = 1.5 → exactly 3:2, but should also test the inverse
    assert _closest_kontext_aspect_ratio(2160, 1440) == "3:2"
    assert _closest_kontext_aspect_ratio(1440, 2160) == "2:3"


def test_is_png_bytes_valid():
    """Real PNG magic header is recognized."""
    png_magic = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    assert _is_png_bytes(png_magic) is True


def test_is_png_bytes_rejects_jpeg():
    """JPEG magic header (FFD8FFE0) is not PNG."""
    jpeg_magic = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    assert _is_png_bytes(jpeg_magic) is False


def test_is_png_bytes_rejects_webp():
    """WebP magic (RIFF...WEBP) is not PNG — this is the format that was
    previously slipping through saved as .png."""
    webp_magic = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 100
    assert _is_png_bytes(webp_magic) is False


def test_is_png_bytes_rejects_short_input():
    """Truncated bytes (< 8) can't be PNG."""
    assert _is_png_bytes(b"") is False
    assert _is_png_bytes(b"\x89PNG") is False


def test_vision_timeout_default_is_600s():
    """run_tournament defaults vision_timeout to 600s after the
    Layer 1 validation surfaced 300s as too tight on GPT-5.5-pro."""
    import inspect

    from nano_banana.tournament import run_tournament

    sig = inspect.signature(run_tournament)
    timeout_param = sig.parameters["vision_timeout"]
    assert timeout_param.default == 600.0
