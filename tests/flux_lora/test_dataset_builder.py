"""
tests.flux_lora.test_dataset_builder — Unit tests for dataset_builder.build_dataset().
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from scripts.flux_lora import DatasetError
from scripts.flux_lora.config import DEFAULT_TRIGGER_WORD
from scripts.flux_lora.dataset_builder import build_dataset

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"  # PNG signature
    + b"\x00\x00\x00\rIHDR"  # IHDR chunk length + type
    + struct.pack(">II", 1, 1)  # width=1, height=1
    + b"\x08\x02\x00\x00\x00"  # bit depth=8, colour type=2 (RGB), rest zeros
    + b"\x90wS\xde"  # CRC (pre-computed for this header)
    + b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    + b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_sources(
    tmp_path: Path,
    count: int = 5,
    caption: str | None = None,
    garment: str | None = None,
    use_caption_key: bool = True,
) -> list[dict]:
    """Create count PNG files in tmp_path and return a sources list."""
    sources = []
    for i in range(count):
        img = tmp_path / f"src_{i:02d}.png"
        img.write_bytes(_MINIMAL_PNG)
        src: dict = {"image": str(img)}
        if use_caption_key and caption is not None:
            src["caption"] = caption
        elif not use_caption_key and garment is not None:
            src["garment"] = garment
        else:
            if caption is not None:
                src["caption"] = caption
            if garment is not None:
                src["garment"] = garment
        sources.append(src)
    return sources


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_build_dataset_happy_path(tmp_path: Path) -> None:
    """5 sources with explicit captions → valid dataset returned."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = _make_sources(src_dir, count=5, caption=f"{DEFAULT_TRIGGER_WORD} black hoodie")
    result = build_dataset(sources, dest_dir)

    assert result == dest_dir.resolve()

    # Correct number of images and sidecars
    images = sorted(dest_dir.glob("img_*.png"))
    sidecars = sorted(dest_dir.glob("img_*.txt"))
    assert len(images) == 5
    assert len(sidecars) == 5

    # Every sidecar starts with trigger word
    for txt in sidecars:
        assert txt.read_text(encoding="utf-8").startswith(DEFAULT_TRIGGER_WORD)


def test_build_dataset_preserves_extension(tmp_path: Path) -> None:
    """JPEG source → dest keeps .jpg extension (not coerced to .png)."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = []
    for i in range(5):
        img = src_dir / f"src_{i:02d}.jpg"
        img.write_bytes(_MINIMAL_PNG)  # bytes don't matter for this test
        sources.append({"image": str(img), "caption": f"{DEFAULT_TRIGGER_WORD} garment {i}"})

    build_dataset(sources, dest_dir)
    assert len(list(dest_dir.glob("img_*.jpg"))) == 5
    assert len(list(dest_dir.glob("img_*.png"))) == 0


# ---------------------------------------------------------------------------
# Trigger-word prepend
# ---------------------------------------------------------------------------


def test_caption_without_trigger_gets_prepended(tmp_path: Path) -> None:
    """Caption missing trigger word → trigger prepended automatically."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = _make_sources(src_dir, count=5, caption="a luxury hoodie")
    build_dataset(sources, dest_dir)

    for txt in dest_dir.glob("img_*.txt"):
        content = txt.read_text(encoding="utf-8")
        assert content.startswith(DEFAULT_TRIGGER_WORD)
        assert "a luxury hoodie" in content


def test_caption_with_trigger_not_doubled(tmp_path: Path) -> None:
    """Caption already starting with trigger word → not doubled."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    full_caption = f"{DEFAULT_TRIGGER_WORD} red sneakers"
    sources = _make_sources(src_dir, count=5, caption=full_caption)
    build_dataset(sources, dest_dir)

    for txt in dest_dir.glob("img_*.txt"):
        content = txt.read_text(encoding="utf-8")
        assert content == full_caption
        assert not content.startswith(f"{DEFAULT_TRIGGER_WORD} {DEFAULT_TRIGGER_WORD}")


def test_garment_only_composes_caption(tmp_path: Path) -> None:
    """garment key only → caption = '<trigger> <garment>'."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = []
    for i in range(5):
        img = src_dir / f"src_{i:02d}.png"
        img.write_bytes(_MINIMAL_PNG)
        sources.append({"image": str(img), "garment": "silk dress"})

    build_dataset(sources, dest_dir)

    for txt in dest_dir.glob("img_*.txt"):
        assert txt.read_text(encoding="utf-8") == f"{DEFAULT_TRIGGER_WORD} silk dress"


# ---------------------------------------------------------------------------
# Missing caption + garment → DatasetError
# ---------------------------------------------------------------------------


def test_missing_caption_and_garment_raises(tmp_path: Path) -> None:
    """Source with neither caption nor garment → DatasetError."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = []
    for i in range(5):
        img = src_dir / f"src_{i:02d}.png"
        img.write_bytes(_MINIMAL_PNG)
        sources.append({"image": str(img)})  # no caption, no garment

    with pytest.raises(DatasetError, match="caption.*garment|garment.*caption"):
        build_dataset(sources, dest_dir)


# ---------------------------------------------------------------------------
# Clobber guard
# ---------------------------------------------------------------------------


def test_nonempty_dest_raises_without_overwrite(tmp_path: Path) -> None:
    """Non-empty dest_dir without overwrite=True → DatasetError."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"
    dest_dir.mkdir()
    (dest_dir / "leftover.txt").write_text("stale")  # make it non-empty

    sources = _make_sources(src_dir, count=5, caption=f"{DEFAULT_TRIGGER_WORD} hoodie")
    with pytest.raises(DatasetError, match="non-empty|overwrite"):
        build_dataset(sources, dest_dir, overwrite=False)


def test_nonempty_dest_succeeds_with_overwrite(tmp_path: Path) -> None:
    """Non-empty dest_dir with overwrite=True → stale files cleared, build succeeds."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"
    dest_dir.mkdir()

    # Seed with stale dataset files
    stale_img = dest_dir / "img_01.png"
    stale_img.write_bytes(_MINIMAL_PNG)
    stale_txt = dest_dir / "img_01.txt"
    stale_txt.write_text("old caption")

    sources = _make_sources(src_dir, count=5, caption=f"{DEFAULT_TRIGGER_WORD} dress")
    result = build_dataset(sources, dest_dir, overwrite=True)

    images = list(dest_dir.glob("img_*.png"))
    assert len(images) == 5


# ---------------------------------------------------------------------------
# Missing source image
# ---------------------------------------------------------------------------


def test_missing_source_image_raises(tmp_path: Path) -> None:
    """Source image path that doesn't exist → DatasetError before writing."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()
    dest_dir = tmp_path / "dataset"

    sources = [
        {"image": str(src_dir / "nonexistent.png"), "caption": f"{DEFAULT_TRIGGER_WORD} top"}
    ] * 5

    with pytest.raises(DatasetError, match="not found"):
        build_dataset(sources, dest_dir)

    # dest_dir should be empty (nothing written)
    assert list(dest_dir.glob("img_*")) == []


# ---------------------------------------------------------------------------
# Empty sources list
# ---------------------------------------------------------------------------


def test_empty_sources_raises(tmp_path: Path) -> None:
    """Empty sources list → DatasetError immediately."""
    with pytest.raises(DatasetError, match="empty"):
        build_dataset([], tmp_path / "dataset")
