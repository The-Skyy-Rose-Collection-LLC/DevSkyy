"""
Design System Agent Spec — Color palettes, typography, theme.json, design tokens.

Model: Gemini 3 Pro (fast structured JSON, strong at visual systems)
"""

from __future__ import annotations

from pathlib import Path


def _build_spec() -> dict:
    """
    Constructs the Design System agent specification used by the application.
    
    Returns:
        spec (dict): A dictionary defining the agent specification with keys:
            - role: agent role identifier (str)
            - name: agent name (str)
            - system_prompt: detailed system prompt for the design system specialist (str)
            - capabilities: list of capability entries, each with `name`, `description`, and `tags` (list)
            - knowledge_files: list of paths to knowledge resources (list of str)
            - preferred_model: preferred model specification with `provider` and `model` (dict)
    """
    return {
        "role": "design_system",
        "name": "design_system",
        "system_prompt": (
            "You are a Design System specialist for the Elite Web Builder. "
            "You create color palettes, typography scales, spacing systems, "
            "and design tokens. You generate theme.json for WordPress FSE themes "
            "and settings_schema.json for Shopify themes. "
            "Generate settings_schema.json for Shopify themes alongside WordPress theme.json. "
            "All color values must match brand-variables.css exactly. "
            "All font names must be registered in theme.json fontFamilies. "
            "Use CSS custom properties (var(--rose-gold)) not hardcoded hex values. "
            "WCAG 2.2 AA contrast ratios are mandatory for all color pairs."
        ),
        "capabilities": [
            {
                "name": "color_palette",
                "description": "Generate accessible color palettes from brand guidelines",
                "tags": ["design", "color", "wcag"],
            },
            {
                "name": "typography_scale",
                "description": "Create typographic scale with font families and sizes",
                "tags": ["design", "typography"],
            },
            {
                "name": "theme_json",
                "description": "Generate WordPress FSE theme.json with full schema",
                "tags": ["design", "wordpress", "theme"],
            },
            {
                "name": "design_tokens",
                "description": "Create design token system (CSS custom properties)",
                "tags": ["design", "tokens", "css"],
            },
            {
                "name": "shopify_theme_settings",
                "description": "Build Shopify theme settings schema and design tokens",
                "tags": ["design", "shopify", "settings"],
            },
        ],
        "knowledge_files": [
            "knowledge/wordpress.md",
            "knowledge/shopify.md",
            "knowledge/theme_json_schema.md",
            "knowledge/wcag_checklist.md",
        ],
        "preferred_model": {"provider": "google", "model": "gemini-3-pro-preview"},
    }


DESIGN_SYSTEM_SPEC = _build_spec()