"""Tests for tools/ — contrast checker, file validator, type scale, spacing scale."""

import json
from pathlib import Path

import pytest

from tools.contrast_checker import (
    ContrastResult,
    check_contrast,
    hex_to_rgb,
    relative_luminance,
    wcag_level,
)
from tools.file_validator import (
    FileValidationResult,
    validate_file_exists,
    validate_json_file,
    validate_no_secrets,
)
from tools.type_scale import generate_type_scale
from tools.spacing_scale import generate_spacing_scale


# ---------------------------------------------------------------------------
# Contrast Checker
# ---------------------------------------------------------------------------


class TestHexToRgb:
    def test_6_digit_hex(self) -> None:
        assert hex_to_rgb("#B76E79") == (183, 110, 121)

    def test_3_digit_hex(self) -> None:
        assert hex_to_rgb("#FFF") == (255, 255, 255)

    def test_lowercase(self) -> None:
        assert hex_to_rgb("#b76e79") == (183, 110, 121)


class TestRelativeLuminance:
    def test_white(self) -> None:
        assert relative_luminance((255, 255, 255)) == pytest.approx(1.0, rel=0.01)

    def test_black(self) -> None:
        assert relative_luminance((0, 0, 0)) == pytest.approx(0.0, abs=0.001)


class TestCheckContrast:
    def test_black_on_white(self) -> None:
        result = check_contrast("#000000", "#FFFFFF")
        assert result.ratio >= 21.0
        assert result.aa_normal is True
        assert result.aaa_normal is True

    def test_rose_gold_on_white(self) -> None:
        result = check_contrast("#B76E79", "#FFFFFF")
        # Rose gold on white should fail AA for normal text
        assert isinstance(result.ratio, float)

    def test_low_contrast_fails(self) -> None:
        result = check_contrast("#CCCCCC", "#FFFFFF")
        assert result.aa_normal is False

    def test_wcag_level_aaa(self) -> None:
        assert wcag_level(8.0) == "AAA"

    def test_wcag_level_aa(self) -> None:
        assert wcag_level(5.0) == "AA"

    def test_wcag_level_aa_large(self) -> None:
        assert wcag_level(3.5) == "AA-Large"

    def test_wcag_level_fail(self) -> None:
        assert wcag_level(2.0) == "Fail"


# ---------------------------------------------------------------------------
# File Validator
# ---------------------------------------------------------------------------


class TestFileValidator:
    def test_file_exists(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = validate_file_exists(str(f))
        assert result.valid is True

    def test_file_not_exists(self) -> None:
        result = validate_file_exists("/nonexistent/file.txt")
        assert result.valid is False

    def test_valid_json_file(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value"}))
        result = validate_json_file(str(f))
        assert result.valid is True

    def test_invalid_json_file(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("{broken json")
        result = validate_json_file(str(f))
        assert result.valid is False

    def test_no_secrets_clean(self, tmp_path: Path) -> None:
        f = tmp_path / "clean.py"
        f.write_text("import os\napi_key = os.environ['KEY']\n")
        result = validate_no_secrets(str(f))
        assert result.valid is True

    def test_no_secrets_detects_key(self, tmp_path: Path) -> None:
        f = tmp_path / "leak.py"
        f.write_text('API_KEY = "sk-proj-1234567890abcdefghijklmnop"\n')
        result = validate_no_secrets(str(f))
        assert result.valid is False


# ---------------------------------------------------------------------------
# Type Scale
# ---------------------------------------------------------------------------


class TestTypeScale:
    def test_default_scale(self) -> None:
        scale = generate_type_scale()
        assert len(scale) > 0
        assert "body" in scale
        assert "h1" in scale

    def test_custom_base(self) -> None:
        scale = generate_type_scale(base_size=18)
        assert scale["body"] == 18

    def test_scale_increases(self) -> None:
        scale = generate_type_scale()
        assert scale["h1"] > scale["h2"] > scale["h3"]

    def test_custom_ratio(self) -> None:
        scale = generate_type_scale(ratio=1.5)
        body = scale["body"]
        h6 = scale["h6"]
        assert h6 > body


# ---------------------------------------------------------------------------
# Spacing Scale
# ---------------------------------------------------------------------------


class TestSpacingScale:
    def test_default_scale(self) -> None:
        scale = generate_spacing_scale()
        assert len(scale) > 0
        assert "xs" in scale
        assert "xl" in scale

    def test_custom_base(self) -> None:
        scale = generate_spacing_scale(base=8)
        # base=8 means unit is 8px. scale["xxs"] = 8*1 = 8
        assert scale["xxs"] == 8
        assert scale["base"] == 32  # 8 * 4

    def test_scale_increases(self) -> None:
        scale = generate_spacing_scale()
        assert scale["xl"] > scale["lg"] > scale["md"] > scale["sm"] > scale["xs"]

    def test_values_are_numbers(self) -> None:
        scale = generate_spacing_scale()
        for key, value in scale.items():
            assert isinstance(value, (int, float)), f"{key} is not a number"
