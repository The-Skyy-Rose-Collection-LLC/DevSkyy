"""Tests for core/ground_truth.py — Anti-hallucination validator.

Every claim an agent makes (file paths, CSS values, API endpoints, etc.)
must be verified against reality before being accepted into output.

Hardened test suite covering ALL claim handlers, edge cases, input
sanitization, and common hallucination patterns.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ground_truth import (
    ClaimType,
    GroundTruthValidator,
    ValidationResult,
    ValidationSeverity,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def validator() -> GroundTruthValidator:
    return GroundTruthValidator()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temp directory with test files for all validators."""
    # CSS file
    (tmp_path / "styles.css").write_text(
        ":root { --rose-gold: #B76E79; }\n.btn { color: var(--rose-gold); }\n"
    )

    # Theme JSON
    (tmp_path / "theme.json").write_text(
        json.dumps({
            "settings": {
                "typography": {
                    "fontFamilies": [
                        {"slug": "playfair-display", "name": "Playfair Display"},
                        {"slug": "montserrat", "name": "Montserrat"},
                    ]
                }
            }
        })
    )

    # Corrupt theme JSON
    (tmp_path / "bad-theme.json").write_text("{not valid json at all")

    # Valid PHP
    (tmp_path / "component.php").write_text(
        '<?php\nfunction hello() {\n  echo "Hello";\n}\n'
    )

    # Broken PHP — mismatched brackets
    (tmp_path / "broken.php").write_text("<?php\nfunction broken( {\n")

    # PHP missing opening tag
    (tmp_path / "no-tag.php").write_text("function oops() { return 1; }\n")

    # Valid HTML
    (tmp_path / "index.html").write_text(
        '<!DOCTYPE html>\n<html lang="en"><head><title>Test</title></head>'
        "<body><h1>Hello</h1></body></html>\n"
    )

    # HTML with duplicate IDs
    (tmp_path / "dup-ids.html").write_text(
        '<!DOCTYPE html>\n<html lang="en"><head><title>Test</title></head>'
        '<body><div id="main">A</div><div id="main">B</div></body></html>\n'
    )

    # HTML missing lang
    (tmp_path / "no-lang.html").write_text(
        "<!DOCTYPE html>\n<html><head><title>Test</title></head>"
        "<body><h1>Hello</h1></body></html>\n"
    )

    # Python module structure
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "module.py").write_text("x = 1\n")
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "__init__.py").write_text("")

    return tmp_path


# ---------------------------------------------------------------------------
# ClaimType enum
# ---------------------------------------------------------------------------


class TestClaimType:
    def test_all_claim_types_exist(self) -> None:
        expected = {
            "FILE_EXISTS", "CSS_VALUE", "COLOR_VALUE", "FONT_NAME",
            "API_ENDPOINT", "IMPORT_PATH", "PHP_SYNTAX", "HTML_VALIDITY",
            "JSON_VALIDITY",
        }
        actual = {ct.name for ct in ClaimType}
        assert expected.issubset(actual)


# ---------------------------------------------------------------------------
# ValidationResult immutability
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_frozen(self) -> None:
        result = ValidationResult(
            valid=True, claim_type=ClaimType.FILE_EXISTS, value="x", message="ok"
        )
        with pytest.raises(AttributeError):
            result.valid = False  # type: ignore[misc]

    def test_default_severity(self) -> None:
        result = ValidationResult(
            valid=True, claim_type=ClaimType.FILE_EXISTS, value="x", message="ok"
        )
        assert result.severity == ValidationSeverity.INFO

    def test_context_default_none(self) -> None:
        result = ValidationResult(
            valid=True, claim_type=ClaimType.FILE_EXISTS, value="x", message="ok"
        )
        assert result.context is None


# ---------------------------------------------------------------------------
# Unknown claim type
# ---------------------------------------------------------------------------


class TestUnknownClaimType:
    def test_unknown_claim_type_returns_error(self, validator: GroundTruthValidator) -> None:
        """If a new ClaimType is added without a handler, verify_claim gracefully fails."""
        # Temporarily create a fake claim type value
        fake = MagicMock(spec=ClaimType)
        fake.name = "FAKE"
        fake.value = "fake"
        result = validator.verify_claim(fake, "some value")
        assert result.valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "unknown" in result.message.lower() or "Unknown" in result.message


# ---------------------------------------------------------------------------
# File existence validation
# ---------------------------------------------------------------------------


class TestFileExists:
    def test_valid_file(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.FILE_EXISTS,
            str(temp_dir / "styles.css"),
        )
        assert result.valid is True
        assert result.severity == ValidationSeverity.INFO

    def test_missing_file(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(
            ClaimType.FILE_EXISTS,
            "/nonexistent/path/to/file.txt",
        )
        assert result.valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "does not exist" in result.message.lower()

    def test_directory_exists(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.FILE_EXISTS,
            str(temp_dir),
        )
        assert result.valid is True

    def test_empty_path(self, validator: GroundTruthValidator) -> None:
        """Empty string should fail — common hallucination output."""
        result = validator.verify_claim(ClaimType.FILE_EXISTS, "")
        assert result.valid is False

    def test_whitespace_only_path(self, validator: GroundTruthValidator) -> None:
        """Whitespace-only paths should be rejected."""
        result = validator.verify_claim(ClaimType.FILE_EXISTS, "   ")
        assert result.valid is False


# ---------------------------------------------------------------------------
# Color value validation (hardened)
# ---------------------------------------------------------------------------


class TestColorValue:
    def test_valid_hex_6(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#B76E79")
        assert result.valid is True

    def test_valid_hex_6_lowercase(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#b76e79")
        assert result.valid is True

    def test_valid_hex_3(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#FFF")
        assert result.valid is True

    def test_valid_hex_4_with_alpha(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#FFFA")
        assert result.valid is True

    def test_valid_hex_8_with_alpha(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#B76E79FF")
        assert result.valid is True

    def test_invalid_hex_letters(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#ZZZZZZ")
        assert result.valid is False

    def test_invalid_hex_too_long(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#B76E79FFA")
        assert result.valid is False

    def test_invalid_hex_too_short(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#FF")
        assert result.valid is False

    def test_valid_rgb(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgb(183, 110, 121)")
        assert result.valid is True

    def test_valid_rgba(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgba(183, 110, 121, 0.5)")
        assert result.valid is True

    def test_rgb_out_of_range_rejects(self, validator: GroundTruthValidator) -> None:
        """RGB values must be 0-255. 999 is a hallucination."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgb(999, 0, 0)")
        assert result.valid is False

    def test_rgb_256_rejects(self, validator: GroundTruthValidator) -> None:
        """256 is just over the boundary — must reject."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgb(256, 0, 0)")
        assert result.valid is False

    def test_rgb_255_accepts(self, validator: GroundTruthValidator) -> None:
        """255 is the maximum valid value."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgb(255, 255, 255)")
        assert result.valid is True

    def test_rgba_alpha_out_of_range_rejects(self, validator: GroundTruthValidator) -> None:
        """Alpha must be 0-1. 1.5 is invalid."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgba(0, 0, 0, 1.5)")
        assert result.valid is False

    def test_rgba_alpha_1_accepts(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgba(0, 0, 0, 1)")
        assert result.valid is True

    def test_rgba_alpha_0_accepts(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "rgba(0, 0, 0, 0)")
        assert result.valid is True

    def test_valid_hsl(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "hsl(350, 50%, 60%)")
        assert result.valid is True

    def test_valid_hsla(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "hsla(350, 50%, 60%, 0.8)")
        assert result.valid is True

    def test_hsl_saturation_over_100_rejects(self, validator: GroundTruthValidator) -> None:
        """Saturation must be 0-100%."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "hsl(350, 150%, 60%)")
        assert result.valid is False

    def test_hsl_lightness_over_100_rejects(self, validator: GroundTruthValidator) -> None:
        """Lightness must be 0-100%."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "hsl(350, 50%, 150%)")
        assert result.valid is False

    def test_invalid_format(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "not-a-color")
        assert result.valid is False

    def test_empty_string_rejects(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "")
        assert result.valid is False

    def test_named_css_color_rejects(self, validator: GroundTruthValidator) -> None:
        """Named colors like 'red' are ambiguous — require exact hex values."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "red")
        assert result.valid is False

    def test_whitespace_padded_hex(self, validator: GroundTruthValidator) -> None:
        """Leading/trailing whitespace should be stripped and validated."""
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "  #B76E79  ")
        assert result.valid is True


# ---------------------------------------------------------------------------
# CSS value validation
# ---------------------------------------------------------------------------


class TestCSSValue:
    def test_valid_css_property(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.CSS_VALUE,
            "--rose-gold",
            context={"file": str(temp_dir / "styles.css")},
        )
        assert result.valid is True

    def test_missing_css_property(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.CSS_VALUE,
            "--nonexistent-var",
            context={"file": str(temp_dir / "styles.css")},
        )
        assert result.valid is False

    def test_no_context_file(self, validator: GroundTruthValidator) -> None:
        """Without a file context, CSS validation should degrade gracefully."""
        result = validator.verify_claim(ClaimType.CSS_VALUE, "--rose-gold")
        assert result.severity in (ValidationSeverity.WARNING, ValidationSeverity.ERROR)

    def test_css_file_not_found(self, validator: GroundTruthValidator) -> None:
        """CSS file doesn't exist on disk."""
        result = validator.verify_claim(
            ClaimType.CSS_VALUE,
            "--rose-gold",
            context={"file": "/nonexistent/styles.css"},
        )
        assert result.valid is False
        assert result.severity == ValidationSeverity.ERROR


# ---------------------------------------------------------------------------
# Font name validation
# ---------------------------------------------------------------------------


class TestFontName:
    def test_valid_font_in_theme(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.FONT_NAME,
            "Playfair Display",
            context={"theme_json": str(temp_dir / "theme.json")},
        )
        assert result.valid is True

    def test_invalid_font_in_theme(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.FONT_NAME,
            "Comic Sans MS",
            context={"theme_json": str(temp_dir / "theme.json")},
        )
        assert result.valid is False
        assert "available:" in result.message.lower() or "not found" in result.message.lower()

    def test_no_theme_json_context(self, validator: GroundTruthValidator) -> None:
        """Without theme.json path, should warn — not crash."""
        result = validator.verify_claim(ClaimType.FONT_NAME, "Montserrat")
        assert result.valid is False
        assert result.severity == ValidationSeverity.WARNING

    def test_theme_json_not_found(self, validator: GroundTruthValidator) -> None:
        """Theme JSON path given but file doesn't exist."""
        result = validator.verify_claim(
            ClaimType.FONT_NAME,
            "Montserrat",
            context={"theme_json": "/nonexistent/theme.json"},
        )
        assert result.valid is False
        assert result.severity == ValidationSeverity.ERROR

    def test_corrupt_theme_json(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """theme.json exists but isn't valid JSON."""
        result = validator.verify_claim(
            ClaimType.FONT_NAME,
            "Montserrat",
            context={"theme_json": str(temp_dir / "bad-theme.json")},
        )
        assert result.valid is False
        assert "invalid" in result.message.lower() or "json" in result.message.lower()


# ---------------------------------------------------------------------------
# JSON validity
# ---------------------------------------------------------------------------


class TestJSONValidity:
    def test_valid_json(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(
            ClaimType.JSON_VALIDITY,
            '{"key": "value", "num": 42}',
        )
        assert result.valid is True

    def test_invalid_json(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(
            ClaimType.JSON_VALIDITY,
            '{key: value}',
        )
        assert result.valid is False
        assert "json" in result.message.lower()

    def test_empty_json_string(self, validator: GroundTruthValidator) -> None:
        """Empty string is not valid JSON."""
        result = validator.verify_claim(ClaimType.JSON_VALIDITY, "")
        assert result.valid is False

    def test_json_array(self, validator: GroundTruthValidator) -> None:
        """JSON arrays are valid."""
        result = validator.verify_claim(ClaimType.JSON_VALIDITY, '[1, 2, 3]')
        assert result.valid is True

    def test_long_json_truncated_in_value(self, validator: GroundTruthValidator) -> None:
        """Long JSON strings should be truncated in the result value."""
        long_json = json.dumps({"key": "x" * 200})
        result = validator.verify_claim(ClaimType.JSON_VALIDITY, long_json)
        assert result.valid is True
        assert len(result.value) <= 83  # 80 + "..."


# ---------------------------------------------------------------------------
# API endpoint validation (hardened)
# ---------------------------------------------------------------------------


class TestAPIEndpoint:
    def test_valid_https_endpoint(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "https://api.skyyrose.co/v1/products")
        assert result.valid is True

    def test_valid_http_endpoint(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "http://localhost:3001/health")
        assert result.valid is True

    def test_valid_relative_endpoint(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "/api/v1/products")
        assert result.valid is True

    def test_rejects_no_protocol_or_slash(self, validator: GroundTruthValidator) -> None:
        """Bare domains without protocol should be rejected."""
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "api.skyyrose.co/v1")
        assert result.valid is False

    def test_rejects_spaces_in_url(self, validator: GroundTruthValidator) -> None:
        """URLs with spaces are hallucinated."""
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "https://api.example.com/path with spaces")
        assert result.valid is False

    def test_rejects_empty_string(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "")
        assert result.valid is False

    def test_rejects_whitespace_only(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "   ")
        assert result.valid is False

    def test_rejects_double_slashes_in_path(self, validator: GroundTruthValidator) -> None:
        """Double slashes in path (not protocol) are suspicious."""
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "https://api.example.com//v1//products")
        assert result.valid is False

    def test_wordpress_rest_route(self, validator: GroundTruthValidator) -> None:
        """WordPress.com's index.php?rest_route= should be valid."""
        result = validator.verify_claim(
            ClaimType.API_ENDPOINT,
            "https://skyyrose.co/index.php?rest_route=/wp/v2/posts",
        )
        assert result.valid is True

    def test_valid_with_query_params(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(
            ClaimType.API_ENDPOINT,
            "https://api.example.com/v1/search?q=test&limit=10",
        )
        assert result.valid is True

    def test_valid_with_port(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "http://localhost:8080/api")
        assert result.valid is True


# ---------------------------------------------------------------------------
# Import path validation
# ---------------------------------------------------------------------------


class TestImportPath:
    def test_valid_module_file(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """mypackage.module should resolve to mypackage/module.py"""
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "mypackage.module",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is True

    def test_valid_package_init(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """mypackage should resolve via mypackage/__init__.py"""
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "mypackage",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is True

    def test_valid_subpackage(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """mypackage.sub should resolve via mypackage/sub/__init__.py"""
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "mypackage.sub",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is True

    def test_nonexistent_module(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "mypackage.nonexistent",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is False
        assert "does not resolve" in result.message.lower()

    def test_completely_bogus_module(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "hallucinated.module.that.never.existed",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is False

    def test_default_base_dir(self, validator: GroundTruthValidator) -> None:
        """Without base_dir, defaults to '.' — should not crash."""
        result = validator.verify_claim(ClaimType.IMPORT_PATH, "nonexistent_module")
        # Likely fails because module doesn't exist, but shouldn't crash
        assert isinstance(result, ValidationResult)

    def test_empty_import_path(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """Empty string is not a valid import."""
        result = validator.verify_claim(
            ClaimType.IMPORT_PATH,
            "",
            context={"base_dir": str(temp_dir)},
        )
        assert result.valid is False


# ---------------------------------------------------------------------------
# PHP syntax validation (hardened)
# ---------------------------------------------------------------------------


class TestPHPSyntax:
    def test_valid_php_file(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.PHP_SYNTAX,
            str(temp_dir / "component.php"),
        )
        assert result.valid is True
        assert "passed" in result.message.lower()

    def test_mismatched_brackets(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.PHP_SYNTAX,
            str(temp_dir / "broken.php"),
        )
        assert result.valid is False
        assert "mismatch" in result.message.lower() or "bracket" in result.message.lower()

    def test_php_file_not_found(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.PHP_SYNTAX, "/nonexistent/file.php")
        assert result.valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "not found" in result.message.lower()

    def test_missing_php_opening_tag(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """PHP files without <?php opening tag are suspicious."""
        result = validator.verify_claim(
            ClaimType.PHP_SYNTAX,
            str(temp_dir / "no-tag.php"),
        )
        assert result.valid is False
        assert "<?php" in result.message.lower() or "opening tag" in result.message.lower()

    def test_empty_php_path(self, validator: GroundTruthValidator) -> None:
        """Empty path should fail."""
        result = validator.verify_claim(ClaimType.PHP_SYNTAX, "")
        assert result.valid is False


# ---------------------------------------------------------------------------
# HTML validity (hardened)
# ---------------------------------------------------------------------------


class TestHTMLValidity:
    def test_valid_html(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        result = validator.verify_claim(
            ClaimType.HTML_VALIDITY,
            str(temp_dir / "index.html"),
        )
        assert result.valid is True

    def test_valid_inline_html(self, validator: GroundTruthValidator) -> None:
        """HTML content passed as string, not file path."""
        html = '<!DOCTYPE html>\n<html lang="en"><head><title>T</title></head><body></body></html>'
        result = validator.verify_claim(ClaimType.HTML_VALIDITY, html)
        assert result.valid is True

    def test_missing_doctype(self, validator: GroundTruthValidator) -> None:
        html = '<html lang="en"><head><title>T</title></head><body></body></html>'
        result = validator.verify_claim(ClaimType.HTML_VALIDITY, html)
        assert result.valid is False
        assert "doctype" in result.message.lower()

    def test_missing_html_tag(self, validator: GroundTruthValidator) -> None:
        html = "<!DOCTYPE html>\n<head><title>T</title></head><body></body>"
        result = validator.verify_claim(ClaimType.HTML_VALIDITY, html)
        assert result.valid is False
        assert "html" in result.message.lower()

    def test_missing_head(self, validator: GroundTruthValidator) -> None:
        html = '<!DOCTYPE html>\n<html lang="en"><body></body></html>'
        result = validator.verify_claim(ClaimType.HTML_VALIDITY, html)
        assert result.valid is False
        assert "head" in result.message.lower()

    def test_missing_body(self, validator: GroundTruthValidator) -> None:
        html = '<!DOCTYPE html>\n<html lang="en"><head><title>T</title></head></html>'
        result = validator.verify_claim(ClaimType.HTML_VALIDITY, html)
        assert result.valid is False
        assert "body" in result.message.lower()

    def test_duplicate_ids_detected(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """Duplicate IDs are an HTML validity error (WCAG 4.1.1)."""
        result = validator.verify_claim(
            ClaimType.HTML_VALIDITY,
            str(temp_dir / "dup-ids.html"),
        )
        assert result.valid is False
        assert "duplicate" in result.message.lower()

    def test_missing_lang_attribute(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """<html> without lang attribute is a WCAG 3.1.1 violation."""
        result = validator.verify_claim(
            ClaimType.HTML_VALIDITY,
            str(temp_dir / "no-lang.html"),
        )
        assert result.valid is False
        assert "lang" in result.message.lower()

    def test_from_file_path(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        """When value looks like a file path, should read the file."""
        result = validator.verify_claim(
            ClaimType.HTML_VALIDITY,
            str(temp_dir / "index.html"),
        )
        assert result.valid is True


# ---------------------------------------------------------------------------
# Input sanitization (all handlers)
# ---------------------------------------------------------------------------


class TestInputSanitization:
    def test_empty_file_path(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.FILE_EXISTS, "")
        assert result.valid is False

    def test_empty_color(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "")
        assert result.valid is False

    def test_empty_json(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.JSON_VALIDITY, "")
        assert result.valid is False

    def test_empty_api_endpoint(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.API_ENDPOINT, "")
        assert result.valid is False

    def test_empty_import_path(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.IMPORT_PATH, "")
        assert result.valid is False

    def test_empty_php_path(self, validator: GroundTruthValidator) -> None:
        result = validator.verify_claim(ClaimType.PHP_SYNTAX, "")
        assert result.valid is False


# ---------------------------------------------------------------------------
# verify_all_or_fail strict mode
# ---------------------------------------------------------------------------


class TestVerifyAllOrFail:
    def test_all_pass_returns_results(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        claims = [
            (ClaimType.FILE_EXISTS, str(temp_dir / "styles.css"), {}),
            (ClaimType.COLOR_VALUE, "#B76E79", {}),
        ]
        results = validator.verify_all_or_fail(claims)
        assert len(results) == 2
        assert all(r.valid for r in results)

    def test_any_fail_raises(self, validator: GroundTruthValidator) -> None:
        claims = [
            (ClaimType.COLOR_VALUE, "#B76E79", {}),
            (ClaimType.FILE_EXISTS, "/nonexistent", {}),
            (ClaimType.JSON_VALIDITY, '{"ok": true}', {}),
        ]
        with pytest.raises(ValueError, match="failed"):
            validator.verify_all_or_fail(claims)


# ---------------------------------------------------------------------------
# Batch validation
# ---------------------------------------------------------------------------


class TestBatchValidation:
    def test_batch_all_pass(self, validator: GroundTruthValidator, temp_dir: Path) -> None:
        claims = [
            (ClaimType.FILE_EXISTS, str(temp_dir / "styles.css"), {}),
            (ClaimType.COLOR_VALUE, "#B76E79", {}),
            (ClaimType.JSON_VALIDITY, '{"ok": true}', {}),
        ]
        results = validator.verify_batch(claims)
        assert len(results) == 3
        assert all(r.valid for r in results)

    def test_batch_some_fail(self, validator: GroundTruthValidator) -> None:
        claims = [
            (ClaimType.FILE_EXISTS, "/nonexistent", {}),
            (ClaimType.COLOR_VALUE, "#B76E79", {}),
            (ClaimType.JSON_VALIDITY, "broken{json", {}),
        ]
        results = validator.verify_batch(claims)
        assert len(results) == 3
        assert results[0].valid is False
        assert results[1].valid is True
        assert results[2].valid is False

    def test_batch_empty(self, validator: GroundTruthValidator) -> None:
        results = validator.verify_batch([])
        assert results == []


# ---------------------------------------------------------------------------
# Validation summary
# ---------------------------------------------------------------------------


class TestValidationSummary:
    def test_summary_counts(self, validator: GroundTruthValidator) -> None:
        results = [
            ValidationResult(valid=True, claim_type=ClaimType.FILE_EXISTS, value="a", message="ok"),
            ValidationResult(valid=True, claim_type=ClaimType.COLOR_VALUE, value="b", message="ok"),
            ValidationResult(valid=False, claim_type=ClaimType.JSON_VALIDITY, value="c", message="bad"),
        ]
        summary = validator.summarize(results)
        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(2 / 3, rel=0.01)

    def test_summary_empty(self, validator: GroundTruthValidator) -> None:
        summary = validator.summarize([])
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["pass_rate"] == 1.0

    def test_summary_all_pass(self, validator: GroundTruthValidator) -> None:
        results = [
            ValidationResult(valid=True, claim_type=ClaimType.FILE_EXISTS, value="a", message="ok"),
        ]
        summary = validator.summarize(results)
        assert summary["pass_rate"] == 1.0
        assert summary["failures"] == []
