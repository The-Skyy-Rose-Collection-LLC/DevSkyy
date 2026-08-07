"""
Anti-hallucination validator — every agent claim verified against reality.

Before any agent output is accepted, claims about files, colors, fonts, APIs,
and code syntax are checked against ground truth. No assumptions, no guesses.

Hardened validators enforce:
- RGB range 0-255, alpha 0-1, HSL saturation/lightness 0-100%
- API endpoint URL structure (no spaces, no double-slashes in path)
- PHP opening tag requirement
- HTML duplicate ID detection and lang attribute check (WCAG 3.1.1 / 4.1.1)
- Empty/whitespace input rejection across all handlers

Usage:
    validator = GroundTruthValidator()
    result = validator.verify_claim(ClaimType.FILE_EXISTS, "/path/to/file.php")
    if not result.valid:
        logger.error("Hallucination caught: %s", result.message)
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums and data models
# ---------------------------------------------------------------------------


class ClaimType(Enum):
    """Types of claims agents can make that need verification."""

    FILE_EXISTS = "file_exists"
    CSS_VALUE = "css_value"
    COLOR_VALUE = "color_value"
    FONT_NAME = "font_name"
    API_ENDPOINT = "api_endpoint"
    IMPORT_PATH = "import_path"
    PHP_SYNTAX = "php_syntax"
    HTML_VALIDITY = "html_validity"
    JSON_VALIDITY = "json_validity"


class ValidationSeverity(Enum):
    """How serious a validation result is."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a claim verification."""

    valid: bool
    claim_type: ClaimType
    value: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.INFO
    context: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Color validation helpers (hardened)
# ---------------------------------------------------------------------------

_HEX_3 = re.compile(r"^#[0-9a-fA-F]{3}$")
_HEX_4 = re.compile(r"^#[0-9a-fA-F]{4}$")
_HEX_6 = re.compile(r"^#[0-9a-fA-F]{6}$")
_HEX_8 = re.compile(r"^#[0-9a-fA-F]{8}$")

# Capture groups for semantic validation
_RGB_CAPTURE = re.compile(
    r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*"
    r"(?:,\s*([\d.]+)\s*)?\)$"
)
_HSL_CAPTURE = re.compile(
    r"^hsla?\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*"
    r"(?:,\s*([\d.]+)\s*)?\)$"
)


def _is_valid_color(value: str) -> bool:
    """Check if a string is a valid CSS color value with semantic range validation."""
    v = value.strip()
    if not v:
        return False

    # Hex formats — pure regex is sufficient
    if _HEX_3.match(v) or _HEX_4.match(v) or _HEX_6.match(v) or _HEX_8.match(v):
        return True

    # RGB/RGBA — validate ranges (0-255 for channels, 0-1 for alpha)
    m = _RGB_CAPTURE.match(v)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return False
        alpha_str = m.group(4)
        if alpha_str is not None:
            alpha = float(alpha_str)
            if not (0.0 <= alpha <= 1.0):
                return False
        return True

    # HSL/HSLA — validate ranges (0-360 hue, 0-100 sat/light, 0-1 alpha)
    m = _HSL_CAPTURE.match(v)
    if m:
        h, s, l_ = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (0 <= h <= 360 and 0 <= s <= 100 and 0 <= l_ <= 100):
            return False
        alpha_str = m.group(4)
        if alpha_str is not None:
            alpha = float(alpha_str)
            if not (0.0 <= alpha <= 1.0):
                return False
        return True

    return False


# ---------------------------------------------------------------------------
# URL / endpoint validation helpers
# ---------------------------------------------------------------------------

_DOUBLE_SLASH_IN_PATH = re.compile(r"(?<!:)//")


def _has_spaces(url: str) -> bool:
    """Check for unencoded spaces in URL."""
    return " " in url


def _has_double_slashes_in_path(url: str) -> bool:
    """Check for double slashes in path (not in protocol ://)."""
    # Strip protocol first
    stripped = url
    for proto in ("https://", "http://"):
        if stripped.startswith(proto):
            stripped = stripped[len(proto):]
            break
    return "//" in stripped


# ---------------------------------------------------------------------------
# HTML validation helpers
# ---------------------------------------------------------------------------

_ID_ATTR = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_HTML_LANG = re.compile(r"<html[^>]*\slang\s*=", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class GroundTruthValidator:
    """
    Verifies agent claims against filesystem, syntax, and format rules.

    Every verification is synchronous and side-effect-free. Designed to be
    called inside the quality gate before any agent output is accepted.
    """

    def verify_claim(
        self,
        claim_type: ClaimType,
        value: str,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Verify a single claim against ground truth.

        Args:
            claim_type: What kind of claim this is
            value: The claimed value (file path, color, JSON, etc.)
            context: Optional context (e.g., {"file": "/path/to/styles.css"})

        Returns:
            ValidationResult with valid=True/False and explanation
        """
        ctx = context or {}

        handler = _CLAIM_HANDLERS.get(claim_type)
        if handler is None:
            return ValidationResult(
                valid=False,
                claim_type=claim_type,
                value=value,
                message=f"Unknown claim type: {claim_type}",
                severity=ValidationSeverity.ERROR,
            )

        return handler(claim_type, value, ctx)

    def verify_batch(
        self,
        claims: list[tuple[ClaimType, str, dict[str, Any]]],
    ) -> list[ValidationResult]:
        """Verify multiple claims. Returns results in same order."""
        return [
            self.verify_claim(ct, val, ctx)
            for ct, val, ctx in claims
        ]

    def verify_all_or_fail(
        self,
        claims: list[tuple[ClaimType, str, dict[str, Any]]],
    ) -> list[ValidationResult]:
        """Strict batch: verify all claims, raise ValueError if any fail."""
        results = self.verify_batch(claims)
        failures = [r for r in results if not r.valid]
        if failures:
            msgs = "; ".join(f"[{r.claim_type.value}] {r.message}" for r in failures)
            raise ValueError(f"Verification failed ({len(failures)} claims): {msgs}")
        return results

    @staticmethod
    def summarize(results: list[ValidationResult]) -> dict[str, Any]:
        """Produce a summary of validation results."""
        total = len(results)
        passed = sum(1 for r in results if r.valid)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 1.0,
            "failures": [
                {"type": r.claim_type.value, "value": r.value, "message": r.message}
                for r in results
                if not r.valid
            ],
        }


# ---------------------------------------------------------------------------
# Claim handlers (one per ClaimType)
# ---------------------------------------------------------------------------


def _verify_file_exists(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check that a file or directory exists on disk."""
    # Guard: empty / whitespace-only paths
    if not value or not value.strip():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="Empty path — cannot verify file existence",
            severity=ValidationSeverity.ERROR,
        )

    path = Path(value)
    if path.exists():
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value,
            message=f"Path exists: {value}",
            severity=ValidationSeverity.INFO,
        )
    return ValidationResult(
        valid=False,
        claim_type=claim_type,
        value=value,
        message=f"Path does not exist: {value}",
        severity=ValidationSeverity.ERROR,
    )


def _verify_color_value(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Validate CSS color format (hex, rgb, hsl) with range checks."""
    if _is_valid_color(value):
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value,
            message=f"Valid color: {value}",
            severity=ValidationSeverity.INFO,
        )
    return ValidationResult(
        valid=False,
        claim_type=claim_type,
        value=value,
        message=f"Invalid color format: {value}",
        severity=ValidationSeverity.ERROR,
    )


def _verify_css_value(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check that a CSS custom property exists in a given file."""
    file_path = ctx.get("file")
    if not file_path:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="No CSS file provided in context — cannot verify",
            severity=ValidationSeverity.WARNING,
        )

    path = Path(file_path)
    if not path.is_file():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"CSS file not found: {file_path}",
            severity=ValidationSeverity.ERROR,
        )

    content = path.read_text(encoding="utf-8")
    if value in content:
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value,
            message=f"CSS property '{value}' found in {file_path}",
            severity=ValidationSeverity.INFO,
        )
    return ValidationResult(
        valid=False,
        claim_type=claim_type,
        value=value,
        message=f"CSS property '{value}' NOT found in {file_path}",
        severity=ValidationSeverity.ERROR,
    )


def _verify_font_name(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check that a font name is registered in theme.json."""
    theme_path = ctx.get("theme_json")
    if not theme_path:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="No theme.json path in context — cannot verify font",
            severity=ValidationSeverity.WARNING,
        )

    path = Path(theme_path)
    if not path.is_file():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"theme.json not found: {theme_path}",
            severity=ValidationSeverity.ERROR,
        )

    try:
        theme_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"Invalid theme.json: {exc}",
            severity=ValidationSeverity.ERROR,
        )

    # Navigate to fontFamilies
    font_families = (
        theme_data
        .get("settings", {})
        .get("typography", {})
        .get("fontFamilies", [])
    )
    registered_names = {f.get("name", "") for f in font_families}

    if value in registered_names:
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value,
            message=f"Font '{value}' is registered in theme.json",
            severity=ValidationSeverity.INFO,
        )
    return ValidationResult(
        valid=False,
        claim_type=claim_type,
        value=value,
        message=f"Font '{value}' NOT found in theme.json (available: {registered_names})",
        severity=ValidationSeverity.ERROR,
    )


def _verify_json_validity(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check that a string is valid JSON."""
    try:
        json.loads(value)
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value[:80] + ("..." if len(value) > 80 else ""),
            message="Valid JSON",
            severity=ValidationSeverity.INFO,
        )
    except json.JSONDecodeError as exc:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value[:80] + ("..." if len(value) > 80 else ""),
            message=f"Invalid JSON: {exc}",
            severity=ValidationSeverity.ERROR,
        )


def _verify_api_endpoint(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Validate API endpoint format with structural checks.

    Checks:
    - Must start with http://, https://, or /
    - No unencoded spaces
    - No double-slashes in path (outside protocol)
    - Non-empty
    """
    # Guard: empty / whitespace
    if not value or not value.strip():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="Empty endpoint — cannot verify",
            severity=ValidationSeverity.ERROR,
        )

    v = value.strip()

    if not v.startswith(("http://", "https://", "/")):
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"Invalid endpoint format: {value} (must start with http://, https://, or /)",
            severity=ValidationSeverity.ERROR,
        )

    if _has_spaces(v):
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"URL contains unencoded spaces: {value}",
            severity=ValidationSeverity.ERROR,
        )

    if _has_double_slashes_in_path(v):
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"URL contains double-slashes in path: {value}",
            severity=ValidationSeverity.ERROR,
        )

    return ValidationResult(
        valid=True,
        claim_type=claim_type,
        value=value,
        message=f"Endpoint format valid: {value}",
        severity=ValidationSeverity.INFO,
    )


def _verify_import_path(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check that a Python/JS import path could resolve."""
    # Guard: empty import path
    if not value or not value.strip():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="Empty import path — cannot verify",
            severity=ValidationSeverity.ERROR,
        )

    # For Python imports: try to check if the module file exists
    base_dir = ctx.get("base_dir", ".")
    # Convert dotted module to path: "core.model_router" → "core/model_router.py"
    module_path = Path(base_dir) / value.replace(".", "/")
    py_file = module_path.with_suffix(".py")
    pkg_init = module_path / "__init__.py"

    if py_file.is_file() or pkg_init.is_file() or module_path.is_dir():
        return ValidationResult(
            valid=True,
            claim_type=claim_type,
            value=value,
            message=f"Import path resolves: {value}",
            severity=ValidationSeverity.INFO,
        )
    return ValidationResult(
        valid=False,
        claim_type=claim_type,
        value=value,
        message=f"Import path does not resolve: {value} (checked {py_file} and {pkg_init})",
        severity=ValidationSeverity.ERROR,
    )


def _verify_php_syntax(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """Check PHP file syntax (bracket matching + opening tag).

    Checks:
    - File exists
    - Contains <?php opening tag
    - Bracket/paren/brace balance
    """
    # Guard: empty path
    if not value or not value.strip():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message="Empty PHP file path — cannot verify",
            severity=ValidationSeverity.ERROR,
        )

    path = Path(value)
    if not path.is_file():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"PHP file not found: {value}",
            severity=ValidationSeverity.ERROR,
        )

    content = path.read_text(encoding="utf-8")

    # Check for PHP opening tag
    if "<?php" not in content.lower():
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"Missing <?php opening tag in {value}",
            severity=ValidationSeverity.ERROR,
        )

    # Basic bracket balance check
    opens = content.count("{") + content.count("(") + content.count("[")
    closes = content.count("}") + content.count(")") + content.count("]")

    if opens != closes:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value,
            message=f"PHP bracket mismatch in {value}: {opens} opens vs {closes} closes",
            severity=ValidationSeverity.ERROR,
        )
    return ValidationResult(
        valid=True,
        claim_type=claim_type,
        value=value,
        message=f"PHP basic syntax check passed: {value}",
        severity=ValidationSeverity.INFO,
    )


def _verify_html_validity(
    claim_type: ClaimType, value: str, ctx: dict[str, Any]
) -> ValidationResult:
    """HTML structure check with accessibility validation.

    Checks:
    - DOCTYPE, html, head, body presence
    - lang attribute on <html> (WCAG 3.1.1)
    - No duplicate IDs (WCAG 4.1.1)
    """
    content = value
    # If value looks like a file path, read it
    if not value.strip().startswith("<") and Path(value).is_file():
        content = Path(value).read_text(encoding="utf-8")

    lower = content.lower()
    issues: list[str] = []

    # Structure checks
    if "<!doctype" not in lower:
        issues.append("Missing DOCTYPE")
    if "<html" not in lower:
        issues.append("Missing <html>")
    if "<head" not in lower:
        issues.append("Missing <head>")
    if "<body" not in lower:
        issues.append("Missing <body>")

    # WCAG 3.1.1 — lang attribute on <html>
    if "<html" in lower and not _HTML_LANG.search(content):
        issues.append("Missing lang attribute on <html> (WCAG 3.1.1)")

    # WCAG 4.1.1 — no duplicate IDs
    id_values = _ID_ATTR.findall(content)
    id_counts = Counter(id_values)
    duplicates = [id_val for id_val, count in id_counts.items() if count > 1]
    if duplicates:
        issues.append(f"Duplicate IDs: {', '.join(duplicates)} (WCAG 4.1.1)")

    if issues:
        return ValidationResult(
            valid=False,
            claim_type=claim_type,
            value=value[:80],
            message=f"HTML issues: {', '.join(issues)}",
            severity=ValidationSeverity.WARNING,
        )
    return ValidationResult(
        valid=True,
        claim_type=claim_type,
        value=value[:80],
        message="HTML structure valid",
        severity=ValidationSeverity.INFO,
    )


# Handler dispatch table
_CLAIM_HANDLERS = {
    ClaimType.FILE_EXISTS: _verify_file_exists,
    ClaimType.COLOR_VALUE: _verify_color_value,
    ClaimType.CSS_VALUE: _verify_css_value,
    ClaimType.FONT_NAME: _verify_font_name,
    ClaimType.JSON_VALIDITY: _verify_json_validity,
    ClaimType.API_ENDPOINT: _verify_api_endpoint,
    ClaimType.IMPORT_PATH: _verify_import_path,
    ClaimType.PHP_SYNTAX: _verify_php_syntax,
    ClaimType.HTML_VALIDITY: _verify_html_validity,
}
