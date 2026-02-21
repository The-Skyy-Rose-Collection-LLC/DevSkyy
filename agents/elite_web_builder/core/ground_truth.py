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
        """
        Initialize the validator with an optional project root used for path-based checks.
        
        Parameters:
            project_root (Path | None): Root directory to resolve file paths against. If None, defaults to the current working directory (Path(".")).
        """
        self._root = project_root or Path(".")

    def validate_file_reference(self, path: str) -> bool:
        """
        Determine whether a file path exists under the validator's project root.
        
        Parameters:
            path (str): File path to check, interpreted relative to the validator's project root.
        
        Returns:
            bool: True if the resolved path exists on disk, False otherwise.
        """
        full_path = self._root / path
        exists = full_path.exists()
        if not exists:
            logger.warning("File reference does not exist: %s", path)
        return exists

    def validate_json(self, content: str) -> bool:
        """
        Determine whether a string contains valid JSON.
        
        Returns:
            True if content is valid JSON, False otherwise.
        """
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False

    def validate_theme_json(self, content: str) -> tuple[bool, list[str]]:
        """
        Validate the structure and key contents of a WordPress theme.json string.
        
        Parameters:
            content (str): The theme.json content to validate as a raw JSON string.
        
        Returns:
            tuple[bool, list[str]]: A tuple where the first element is True if the content is a valid theme.json according to the checks below, False otherwise; the second element is a list of validation error messages.
        
        Checks performed:
            - The content is valid JSON.
            - Presence of required top-level field "version".
            - Presence of recommended top-level field "$schema".
            - If a "settings" -> "color" -> "palette" array exists:
                - Each palette item must include a "slug".
                - Palette "slug" values must be unique.
                - Each palette item's "color" value, if present, must be a valid hex color matching ^#[0-9a-fA-F]{3,8}$.
        """
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
                    r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", item["color"]
                ):
                    errors.append(f"Invalid hex color: {item['color']}")

        return len(errors) == 0, errors

    def validate_liquid_syntax(self, content: str) -> tuple[bool, list[str]]:
        """
        Checks whether Liquid template tags and output tags are balanced.
        
        Parameters:
            content (str): The Liquid template text to validate.
        
        Returns:
            tuple[bool, list[str]]: True if all tag pairs are balanced, False otherwise; the list contains human-readable error messages describing any unbalanced tags.
        """
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
        """
        Determine whether a string is a valid hex color.

        Returns:
            True if the string is a hex color (#RGB, #RGBA, #RRGGBB, or #RRGGBBAA), False otherwise.
        """
        return bool(re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", color))
