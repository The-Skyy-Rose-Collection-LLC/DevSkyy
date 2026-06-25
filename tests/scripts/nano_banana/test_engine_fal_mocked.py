"""Mock-based tests for FAL engine (refine_with_kontext + generate_flux_fal).

Mocks at the SDK boundary (`fal_client.subscribe`, `_download_image`)
so the wrapper logic — aspect-ratio computation, PNG validation,
error paths, response parsing — gets real coverage without paid calls.

The pure helpers (`_closest_kontext_aspect_ratio`, `_is_png_bytes`)
are exercised by `test_kontext_helpers.py`; this file covers the
HTTP-roundtrip surface above them.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

import nano_banana.engine_fal as engine_fal  # noqa: E402


def _png_bytes(width: int = 100, height: int = 100, color: tuple = (10, 10, 10)) -> bytes:
    """Build a real PNG byte string with valid magic header."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def fake_source_png(tmp_path: Path) -> Path:
    """Create a 200x200 PNG file on disk."""
    path = tmp_path / "source.png"
    path.write_bytes(_png_bytes(width=200, height=200))
    return path


@pytest.fixture()
def fake_source_jpeg(tmp_path: Path) -> Path:
    """Create a 1024x768 JPEG file on disk (4:3 aspect)."""
    img = Image.new("RGB", (1024, 768), color=(50, 50, 50))
    path = tmp_path / "source.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture()
def png_response_bytes() -> bytes:
    """Real PNG bytes for the mocked download to return."""
    return _png_bytes(width=200, height=200, color=(20, 20, 20))


# ── refine_with_kontext ────────────────────────────────────────────────────


def test_refine_with_kontext_happy_path_returns_png_bytes(
    monkeypatch, fake_source_png, png_response_bytes
):
    """Mocked FAL roundtrip returns the downloaded PNG bytes verbatim."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: png_response_bytes)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {
        "images": [
            {
                "url": "https://fal.media/result.png",
                "width": 200,
                "height": 200,
                "content_type": "image/png",
            }
        ]
    }
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    result = engine_fal.refine_with_kontext(fake_source_png, "make logo crisp")

    assert result == png_response_bytes
    # subscribe called once with the kontext model + correct argument shape
    fake_fal.subscribe.assert_called_once()
    args, kwargs = fake_fal.subscribe.call_args
    assert args[0] == engine_fal.FLUX_KONTEXT_MODEL
    arguments = kwargs["arguments"]
    assert arguments["prompt"] == "make logo crisp"
    assert arguments["output_format"] == "png"
    assert arguments["aspect_ratio"] == "1:1"  # 200x200 → 1:1
    # image_url is data URI of the source bytes
    assert arguments["image_url"].startswith("data:image/png;base64,")


def test_refine_with_kontext_no_fal_key_returns_none(monkeypatch, fake_source_png):
    """If `_fal_available()` returns False, refinement aborts cleanly."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: False)

    result = engine_fal.refine_with_kontext(fake_source_png, "...")

    assert result is None


def test_refine_with_kontext_subscribe_raises_returns_none(monkeypatch, fake_source_png):
    """FAL API exception is caught and returns None instead of bubbling."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)

    fake_fal = MagicMock()
    fake_fal.subscribe.side_effect = RuntimeError("FAL infrastructure down")
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    result = engine_fal.refine_with_kontext(fake_source_png, "...")

    assert result is None


def test_refine_with_kontext_empty_response_returns_none(monkeypatch, fake_source_png):
    """FAL returning an empty/malformed result dict yields None."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {}  # missing "images"
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    assert engine_fal.refine_with_kontext(fake_source_png, "...") is None

    fake_fal.subscribe.return_value = {"images": []}  # empty list
    assert engine_fal.refine_with_kontext(fake_source_png, "...") is None

    fake_fal.subscribe.return_value = {"images": [{"width": 100}]}  # no url
    assert engine_fal.refine_with_kontext(fake_source_png, "...") is None


def test_refine_with_kontext_download_fails_returns_none(monkeypatch, fake_source_png):
    """Download failure (URL unreachable) yields None even when FAL succeeded."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: None)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {"images": [{"url": "https://fal.media/r.png"}]}
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    assert engine_fal.refine_with_kontext(fake_source_png, "...") is None


def test_refine_with_kontext_non_png_response_logs_warning_but_returns_bytes(
    monkeypatch, fake_source_png, caplog
):
    """If FAL returns non-PNG bytes, the wrapper logs and still returns them.

    Returning the bytes preserves caller-visibility of the unexpected
    format; the warning surfaces it for the operator to investigate.
    Earlier silent acceptance let mislabeled WebP/JPEG slip through as
    .png on the storefront.
    """
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 200  # JPEG magic header
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: jpeg_bytes)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {"images": [{"url": "https://fal.media/r.png"}]}
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    import logging

    with caplog.at_level(logging.WARNING, logger="nano_banana.engine_fal"):
        result = engine_fal.refine_with_kontext(fake_source_png, "...")

    assert result == jpeg_bytes
    assert any("non-PNG" in rec.message for rec in caplog.records)


def test_refine_with_kontext_aspect_ratio_4x3(monkeypatch, fake_source_jpeg, png_response_bytes):
    """1024x768 input maps to aspect_ratio='4:3' in the FAL arguments."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: png_response_bytes)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {
        "images": [{"url": "https://fal.media/r.png", "width": 1024, "height": 768}]
    }
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    engine_fal.refine_with_kontext(fake_source_jpeg, "...")

    arguments = fake_fal.subscribe.call_args.kwargs["arguments"]
    assert arguments["aspect_ratio"] == "4:3"


def test_refine_with_kontext_logs_shrink_warning_on_significant_downscale(
    monkeypatch, fake_source_jpeg, png_response_bytes, caplog
):
    """When Kontext returns dims < 60% of input, the wrapper warns."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: png_response_bytes)

    fake_fal = MagicMock()
    # Input was 1024x768; FAL returned 400x300 (~39% scale)
    fake_fal.subscribe.return_value = {
        "images": [{"url": "https://fal.media/r.png", "width": 400, "height": 300}]
    }
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    import logging

    with caplog.at_level(logging.WARNING, logger="nano_banana.engine_fal"):
        engine_fal.refine_with_kontext(fake_source_jpeg, "...")

    assert any("smaller than input" in rec.message for rec in caplog.records)


def test_refine_with_kontext_missing_source_returns_none(tmp_path, monkeypatch):
    """If source path doesn't exist, refinement aborts before any API call."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)

    fake_fal = MagicMock()
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    result = engine_fal.refine_with_kontext(tmp_path / "nope.png", "...")

    assert result is None
    fake_fal.subscribe.assert_not_called()


# ── generate_flux_fal ──────────────────────────────────────────────────────


def test_generate_flux_fal_no_source_passes_no_image_url(monkeypatch, png_response_bytes):
    """Without a source image, no `image_url` in arguments — pure text-to-image."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: png_response_bytes)
    # Patch to_webp to passthrough so we can compare bytes by identity
    import nano_banana.utils as utils_mod

    monkeypatch.setattr(utils_mod, "to_webp", lambda b, quality=92: b)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {"images": [{"url": "https://fal.media/r.png"}]}
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    result = engine_fal.generate_flux_fal(None, "luxury crewneck product render")

    assert result == png_response_bytes
    arguments = fake_fal.subscribe.call_args.kwargs["arguments"]
    assert "image_url" not in arguments
    assert arguments["prompt"] == "luxury crewneck product render"
    assert arguments["image_size"] == {"width": 768, "height": 1024}
    assert arguments["output_format"] == "jpeg"
    assert arguments["num_images"] == 1


def test_generate_flux_fal_with_source_passes_data_uri(
    monkeypatch, fake_source_jpeg, png_response_bytes
):
    """When source path is provided, it's passed as base64 data URI in arguments."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)
    monkeypatch.setattr(engine_fal, "_download_image", lambda url: png_response_bytes)
    import nano_banana.utils as utils_mod

    monkeypatch.setattr(utils_mod, "to_webp", lambda b, quality=92: b)

    fake_fal = MagicMock()
    fake_fal.subscribe.return_value = {"images": [{"url": "https://fal.media/r.png"}]}
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    engine_fal.generate_flux_fal(fake_source_jpeg, "render this")

    arguments = fake_fal.subscribe.call_args.kwargs["arguments"]
    assert "image_url" in arguments
    assert arguments["image_url"].startswith("data:image/jpeg;base64,")


def test_generate_flux_fal_no_fal_returns_none(monkeypatch):
    """Without FAL available, generation aborts cleanly with None."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: False)

    assert engine_fal.generate_flux_fal(None, "...") is None


def test_generate_flux_fal_subscribe_raises_returns_none(monkeypatch):
    """API exception in generate_flux_fal returns None (matches refine behavior)."""
    monkeypatch.setattr(engine_fal, "_fal_available", lambda: True)

    fake_fal = MagicMock()
    fake_fal.subscribe.side_effect = ConnectionError("FAL endpoint timeout")
    monkeypatch.setitem(sys.modules, "fal_client", fake_fal)

    assert engine_fal.generate_flux_fal(None, "...") is None
