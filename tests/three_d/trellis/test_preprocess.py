"""Unit tests for the TRELLIS image preprocessor.

These tests only exercise the file-handling + dimensions path. The optional
``rembg`` / advanced color-correction stages skip themselves gracefully when
deps are missing, which is checked here too.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pil = pytest.importorskip("PIL.Image", reason="Pillow not installed")

from services.three_d.trellis.config import TrellisConfig  # noqa: E402
from services.three_d.trellis.preprocess import (  # noqa: E402
    PreprocessError,
    TrellisPreprocessor,
)


def _make_test_image(path: Path, *, size: tuple[int, int] = (600, 800)) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Black rectangle in the middle = "the garment"
    cx, cy = size[0] // 2, size[1] // 2
    draw.rectangle(
        [cx - 100, cy - 200, cx + 100, cy + 200],
        fill=(20, 20, 20, 255),
    )
    img.save(path)
    return path


class TestTrellisPreprocessor:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        cfg = TrellisConfig(cache_dir=str(tmp_path / "cache"), output_dir=str(tmp_path / "out"))
        prep = TrellisPreprocessor(cfg)
        with pytest.raises(PreprocessError):
            prep.prepare(tmp_path / "missing.png")

    def test_prepare_produces_square_target(self, tmp_path: Path) -> None:
        cfg = TrellisConfig(
            cache_dir=str(tmp_path / "cache"),
            output_dir=str(tmp_path / "out"),
            enable_background_removal=False,
        )
        prep = TrellisPreprocessor(cfg)

        src = _make_test_image(tmp_path / "tee.png", size=(800, 1200))
        result = prep.prepare(src)

        assert result.image.width == TrellisPreprocessor.TARGET_RESOLUTION
        assert result.image.height == TrellisPreprocessor.TARGET_RESOLUTION
        assert Path(result.image.path).exists()
        assert 0.0 <= result.quality_score <= 1.0

    def test_passthrough_copies_unchanged(self, tmp_path: Path) -> None:
        cfg = TrellisConfig(cache_dir=str(tmp_path / "cache"), output_dir=str(tmp_path / "out"))
        prep = TrellisPreprocessor(cfg)

        src = _make_test_image(tmp_path / "src.png", size=(400, 500))
        result = prep.passthrough(src)

        assert result.bypassed
        assert Path(result.image.path).exists()
        assert result.image.width == 400
        assert result.image.height == 500

    def test_small_input_emits_warning(self, tmp_path: Path) -> None:
        cfg = TrellisConfig(
            cache_dir=str(tmp_path / "cache"),
            output_dir=str(tmp_path / "out"),
            enable_background_removal=False,
            min_input_resolution=512,
        )
        prep = TrellisPreprocessor(cfg)

        src = _make_test_image(tmp_path / "tiny.png", size=(128, 128))
        result = prep.prepare(src)

        assert any("below" in w for w in result.warnings)
