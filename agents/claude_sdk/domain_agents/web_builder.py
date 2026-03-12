"""
SDK Web Builder Domain Agents
================================

SDK-powered sub-agents for the Web Builder core domain.
These agents can read/write templates, run builds, test pages,
and modify the WordPress theme directly.

Agents:
    SDKThemeDevAgent       — Edit theme files, run builds, test
    SDKTemplateBuilderAgent — Generate WordPress templates with proper hooks
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import ToolProfile
from agents.core.base import CoreAgentType


class SDKThemeDevAgent(SDKSubAgent):
    """WordPress theme developer with full file access.

    Can read the skyyrose-flagship theme, edit PHP/CSS/JS files,
    run build commands, and verify changes.
    """

    name = "sdk_theme_dev"
    parent_type = CoreAgentType.WEB_BUILDER
    description = "Edit WordPress theme, run builds, verify changes"
    capabilities = [
        "theme_edit",
        "template_create",
        "css_modify",
        "js_modify",
        "build_verify",
        "hook_register",
    ]
    sdk_tools = ToolProfile.WEB_BUILDER
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/web_builder/theme")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Theme Developer for the SkyyRose "
            "WordPress theme (skyyrose-flagship).\n\n"
            "Theme location: wordpress-theme/skyyrose-flagship/\n"
            "Key files:\n"
            "- functions.php (hooks, enqueues, custom post types)\n"
            "- style.css (theme header + styles)\n"
            "- template-*.php (page templates)\n"
            "- assets/js/immersive-world.js (Three.js 3D experiences)\n"
            "- assets/css/ (collection-specific styles)\n\n"
            "WordPress rules (CRITICAL):\n"
            "- Extend via hooks (actions/filters), NEVER modify core\n"
            "- API: index.php?rest_route= NOT /wp-json/\n"
            "- Escape on output: esc_html(), esc_attr(), esc_url()\n"
            "- Sanitize on input: sanitize_text_field()\n"
            "- Always $wpdb->prepare() — never concatenate\n"
            "- Nonce + capability checks on all write actions\n\n"
            "Read the existing template before modifying it. "
            "Verify PHP syntax after edits."
        )


class SDKTemplateBuilderAgent(SDKSubAgent):
    """Template builder for new WordPress page templates.

    Generates complete PHP templates with proper WordPress hooks,
    escape functions, and brand styling.
    """

    name = "sdk_template_builder"
    parent_type = CoreAgentType.WEB_BUILDER
    description = "Generate WordPress page templates with proper hooks"
    capabilities = [
        "page_template",
        "collection_template",
        "immersive_template",
        "catalog_template",
        "block_pattern",
    ]
    sdk_tools = ToolProfile.WEB_BUILDER
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/web_builder/templates")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Template Builder for SkyyRose.\n\n"
            "You create WordPress page templates following the existing "
            "conventions in the skyyrose-flagship theme.\n\n"
            "Template types:\n"
            "- Immersive: 3D storytelling (Three.js via CDN), hero scene "
            "per collection, used for Black Rose, Love Hurts, Signature\n"
            "- Catalog: product grids, used for Kids Capsule\n"
            "- Experience: interactive brand experiences\n\n"
            "Before creating a template:\n"
            "1. Read existing templates to match conventions\n"
            "2. Read functions.php for registered hooks/styles\n"
            "3. Use get_template_part() for reusable sections\n"
            "4. Include proper WordPress template header comment\n"
            "5. Enqueue scripts/styles via wp_enqueue_script()\n\n"
            "Brand colors: #B76E79 rose gold, #0A0A0A dark, "
            "#D4AF37 gold, #DC143C crimson, #C0C0C0 silver"
        )

    def _build_task_prompt(self, task: str, **kwargs: Any) -> str:
        """Enrich with template type context."""
        base = super()._build_task_prompt(task, **kwargs)
        template_type = kwargs.get("template_type")
        if template_type:
            base += (
                f"\n\nTemplate type: {template_type}\n"
                "Read an existing template of the same type first "
                "to match the established pattern."
            )
        return base


__all__ = [
    "SDKThemeDevAgent",
    "SDKTemplateBuilderAgent",
]
