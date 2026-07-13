"""Tests for scripts/font_generator: template generation, manifest validation, font build.

Unit tests cover the pure logic (template layout, manifest shape/consistency,
build_font input guards) and run everywhere. The end-to-end vectorization test
needs the `potrace` binary plus fontTools, so it is skipped when potrace is
absent (e.g. minimal CI) rather than failing.
"""

from __future__ import annotations

import json
import shutil

import pytest
from PIL import Image, ImageDraw

from scripts.font_generator import pipeline, template

pytestmark = pytest.mark.unit

_HAS_POTRACE = shutil.which("potrace") is not None


# --------------------------------------------------------------------------- #
# template.generate_template / save_template
# --------------------------------------------------------------------------- #
def test_generate_template_shape() -> None:
    image, manifest = template.generate_template(chars="ABCD", cols=2, cell_size=(100, 120))
    assert image.size == (200, 240)  # 2 cols * 100, 2 rows * 120
    assert manifest["image_size"] == [200, 240]
    assert manifest["grid"] == {"cols": 2, "rows": 2}
    assert [c["char"] for c in manifest["cells"]] == ["A", "B", "C", "D"]
    assert manifest["cells"][0]["codepoint"] == ord("A")
    assert len(manifest["chars_fingerprint"]) == 12


def test_generate_template_empty_chars_raises() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        template.generate_template(chars="")


def test_generate_template_cols_below_one_raises() -> None:
    with pytest.raises(ValueError, match="cols must be >= 1"):
        template.generate_template(chars="AB", cols=0)


def test_generate_template_duplicate_chars_raises() -> None:
    with pytest.raises(ValueError, match="duplicate characters"):
        template.generate_template(chars="AAB")


def test_generate_template_fingerprint_deterministic_and_sensitive() -> None:
    _, m1 = template.generate_template(chars="AB", cols=2)
    _, m2 = template.generate_template(chars="AB", cols=2)
    _, m3 = template.generate_template(chars="AB", cols=1)
    assert m1["chars_fingerprint"] == m2["chars_fingerprint"]
    assert m1["chars_fingerprint"] != m3["chars_fingerprint"]  # cols feed the fingerprint


def test_save_template_writes_files(tmp_path) -> None:
    png_path, manifest_path = template.save_template(tmp_path, chars="AB", cols=2)
    assert png_path.exists() and manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    pipeline._validate_manifest(manifest)  # generated manifest is always valid


# --------------------------------------------------------------------------- #
# pipeline._validate_manifest
# --------------------------------------------------------------------------- #
def _valid_manifest() -> dict:
    _, manifest = template.generate_template(chars="AB", cols=2, cell_size=(100, 100))
    return manifest


def test_validate_manifest_accepts_generated() -> None:
    pipeline._validate_manifest(_valid_manifest())  # no raise


@pytest.mark.parametrize("missing", ["image_size", "cells"])
def test_validate_manifest_missing_top_key(missing) -> None:
    m = _valid_manifest()
    del m[missing]
    with pytest.raises(ValueError, match=f"missing required key '{missing}'"):
        pipeline._validate_manifest(m)


def test_validate_manifest_bad_image_size() -> None:
    m = _valid_manifest()
    m["image_size"] = [200]
    with pytest.raises(ValueError, match="image_size' must be a 2-element"):
        pipeline._validate_manifest(m)


def test_validate_manifest_cells_not_list() -> None:
    m = _valid_manifest()
    m["cells"] = {"nope": 1}
    with pytest.raises(ValueError, match="cells' must be a list"):
        pipeline._validate_manifest(m)


def test_validate_manifest_cell_missing_key() -> None:
    m = _valid_manifest()
    del m["cells"][0]["bbox"]
    with pytest.raises(ValueError, match="missing required key 'bbox'"):
        pipeline._validate_manifest(m)


def test_validate_manifest_duplicate_char() -> None:
    m = _valid_manifest()
    m["cells"][1]["char"] = m["cells"][0]["char"]
    m["cells"][1]["codepoint"] = m["cells"][0]["codepoint"] + 1  # isolate the char check
    with pytest.raises(ValueError, match="duplicate char"):
        pipeline._validate_manifest(m)


def test_validate_manifest_duplicate_codepoint() -> None:
    m = _valid_manifest()
    m["cells"][1]["codepoint"] = m["cells"][0]["codepoint"]
    with pytest.raises(ValueError, match="duplicate codepoint"):
        pipeline._validate_manifest(m)


def test_validate_manifest_bbox_wrong_length() -> None:
    m = _valid_manifest()
    m["cells"][0]["bbox"] = [0, 0, 100]
    with pytest.raises(ValueError, match="bbox must have 4 elements"):
        pipeline._validate_manifest(m)


def test_validate_manifest_bbox_out_of_bounds() -> None:
    m = _valid_manifest()
    m["cells"][0]["bbox"] = [0, 0, 9999, 100]
    with pytest.raises(ValueError, match="out of bounds"):
        pipeline._validate_manifest(m)


# --------------------------------------------------------------------------- #
# pipeline.build_font input guards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("threshold", [0, 256, -5])
def test_build_font_threshold_out_of_range(tmp_path, threshold) -> None:
    with pytest.raises(ValueError, match="threshold must be between 1 and 255"):
        pipeline.build_font(
            tmp_path / "nope.png", tmp_path / "nope.json", tmp_path / "out.ttf", threshold=threshold
        )


def test_build_font_missing_filled_image(tmp_path) -> None:
    _, manifest_path = template.save_template(tmp_path, chars="A", cols=1)
    with pytest.raises(FileNotFoundError, match="filled image not found"):
        pipeline.build_font(tmp_path / "absent.png", manifest_path, tmp_path / "out.ttf")


def test_build_font_missing_manifest(tmp_path) -> None:
    png_path, _ = template.save_template(tmp_path, chars="A", cols=1)
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        pipeline.build_font(png_path, tmp_path / "absent.json", tmp_path / "out.ttf")


def test_build_font_invalid_manifest_json(tmp_path) -> None:
    png_path, _ = template.save_template(tmp_path, chars="A", cols=1)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        pipeline.build_font(png_path, bad, tmp_path / "out.ttf")


def test_build_font_dimension_mismatch(tmp_path) -> None:
    _, manifest_path = template.save_template(tmp_path, chars="A", cols=1, cell_size=(120, 120))
    wrong = tmp_path / "wrong.png"
    Image.new("RGB", (50, 50), (255, 255, 255)).save(wrong)
    with pytest.raises(ValueError, match="do not match template dimensions"):
        pipeline.build_font(wrong, manifest_path, tmp_path / "out.ttf")


# --------------------------------------------------------------------------- #
# end-to-end vectorization (needs potrace + fontTools)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not _HAS_POTRACE, reason="potrace binary not installed")
def test_build_font_end_to_end(tmp_path) -> None:
    png_path, manifest_path = template.save_template(
        tmp_path, chars="A", cols=1, cell_size=(120, 120)
    )

    # Ink the single cell with a solid black shape inside its inset region.
    img = Image.open(png_path).convert("RGB")
    ImageDraw.Draw(img).rectangle([40, 30, 80, 90], fill=(0, 0, 0))
    filled = tmp_path / "filled.png"
    img.save(filled)

    out_ttf = tmp_path / "out.ttf"
    result = pipeline.build_font(filled, manifest_path, out_ttf, family="TestFont", threshold=140)

    assert "A" in result["built"]
    assert out_ttf.exists() and out_ttf.stat().st_size > 0

    from fontTools.ttLib import TTFont  # opening a corrupt file would raise

    font = TTFont(out_ttf)
    assert ord("A") in font.getBestCmap()
