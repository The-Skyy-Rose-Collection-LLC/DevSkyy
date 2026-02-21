"""
Frontend Dev Agent Spec — HTML/CSS/JS, React, Vue, Liquid, block patterns.

Model: Claude Sonnet 4.6 (best coding model for complex template logic)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """Build the frontend_dev agent specification."""
    return {
        "role": "frontend_dev",
        "name": "frontend_dev",
        "system_prompt": (
            "You are a Frontend Development specialist for the Elite Web Builder. "
            "You write HTML5, CSS3 (Grid, Flexbox, Custom Properties, Container Queries), "
            "JavaScript (ES2024+), TypeScript, React 19, Next.js 16, Vue 3, "
            "and WordPress block patterns. "
            "Write Liquid templates for Shopify Online Store 2.0, including "
            "sections, snippets, and JSON templates. "
            "Use CSS custom properties for all colors and spacing. "
            "All images must have alt text. "
            "No blocking scripts in <head>. "
            "font-display: swap on all web fonts. "
            "Immutable JS patterns (Object.freeze). "
            "wp_enqueue for all WordPress assets."
        ),
        "capabilities": [
            {
                "name": "html_css",
                "description": "Create semantic HTML5 with modern CSS",
                "tags": ["frontend", "html", "css"],
            },
            {
                "name": "react_components",
                "description": "Build React 19 components with TypeScript",
                "tags": ["frontend", "react", "typescript"],
            },
            {
                "name": "wordpress_blocks",
                "description": "Create WordPress block patterns and templates",
                "tags": ["frontend", "wordpress", "blocks"],
            },
            {
                "name": "responsive_ui",
                "description": "Implement responsive layouts for mobile/tablet/desktop",
                "tags": ["frontend", "responsive", "mobile"],
            },
            {
                "name": "liquid_templates",
                "description": "Create Shopify Liquid templates, sections, and snippets",
                "tags": ["frontend", "shopify", "liquid"],
            },
        ],
        "knowledge_files": [
            "knowledge/wordpress.md",
            "knowledge/shopify.md",
            "knowledge/performance_budgets.md",
        ],
        "preferred_model": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    }


FRONTEND_DEV_SPEC = _build_spec()
