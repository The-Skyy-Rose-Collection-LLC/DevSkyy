"""
Ground Truth Validator — Anti-hallucination verification.

Every claim must be verified against actual files/APIs before
being accepted into any output.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class GroundTruthValidator:
    """Validates agent claims against reality."""

    RULES = {
        "file_references": "MUST exist on disk (glob check before accepting)",
        "css_properties": "MUST be valid (stylelint check before accepting)",
        "php_syntax": "MUST parse (php -l before accepting)",
        "html_validity": "MUST validate (htmlhint before accepting)",
        "color_values": "MUST match brand-variables.css (grep check)",
        "font_names": "MUST be in theme.json fontFamilies (grep check)",
        "import_paths": "MUST resolve (node/python import check)",
        "theme_json": "MUST be valid JSON with required fields",
        "liquid_syntax": "MUST have balanced tags",
        "woocommerce_hooks": "MUST match registered hook names",
    }

    def __init__(self, project_root: Path | None = None) -> None:
        self._root = project_root or Path(".")

    def validate_file_reference(self, path: str) -> bool:
        """Check if a file reference actually exists."""
        full_path = self._root / path
        exists = full_path.exists()
        if not exists:
            logger.warning("File reference does not exist: %s", path)
        return exists

    def validate_json(self, content: str) -> bool:
        """Check if content is valid JSON."""
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False

    def validate_theme_json(self, content: str) -> tuple[bool, list[str]]:
        """Validate theme.json structure."""
        errors: list[str] = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            return False, [f"Invalid JSON: {exc}"]

        if "version" not in data:
            errors.append("Missing required field: version")
        if "$schema" not in data:
            errors.append("Missing recommended field: $schema")

        settings = data.get("settings", {})
        if "color" in settings:
            palette = settings["color"].get("palette", [])
            slugs = set()
            for item in palette:
                if "slug" not in item:
                    errors.append(f"Color palette item missing 'slug': {item}")
                elif item["slug"] in slugs:
                    errors.append(f"Duplicate color slug: {item['slug']}")
                else:
                    slugs.add(item["slug"])
                if "color" in item and not re.match(
                    r"^#[0-9a-fA-F]{3,8}$", item["color"]
                ):
                    errors.append(f"Invalid hex color: {item['color']}")

        return len(errors) == 0, errors

    def validate_liquid_syntax(self, content: str) -> tuple[bool, list[str]]:
        """Basic Liquid template syntax validation."""
        errors: list[str] = []
        # Check balanced tags
        opens = len(re.findall(r"\{%", content))
        closes = len(re.findall(r"%\}", content))
        if opens != closes:
            errors.append(f"Unbalanced Liquid tags: {opens} opens, {closes} closes")

        output_opens = len(re.findall(r"\{\{", content))
        output_closes = len(re.findall(r"\}\}", content))
        if output_opens != output_closes:
            errors.append(
                f"Unbalanced output tags: {output_opens} opens, {output_closes} closes"
            )

        return len(errors) == 0, errors

    def validate_color_hex(self, color: str) -> bool:
        """Check if a color value is a valid hex color."""
        return bool(re.match(r"^#[0-9a-fA-F]{3,8}$", color))
