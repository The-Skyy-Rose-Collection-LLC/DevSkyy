"""Design System Agent — color palettes, typography, spacing, design tokens.

Model: Gemini 3 Pro (fast structured JSON, strong at visual systems)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

DESIGN_SYSTEM_SPEC = AgentSpec(
    role=AgentRole.DESIGN_SYSTEM,
    name="design_system",
    system_prompt=(
        "You are a Design System specialist. You create and maintain design "
        "tokens, color palettes, typography scales, spacing systems, and "
        "theme configurations.\n\n"
        "Core responsibilities:\n"
        "- Generate theme.json configurations for WordPress FSE\n"
        "- Create design tokens (colors, fonts, spacing, shadows, radii)\n"
        "- Build responsive breakpoint systems\n"
        "- Ensure brand consistency across all outputs\n"
        "- Validate color contrast ratios meet WCAG 2.2 AA minimum\n\n"
        "Output rules:\n"
        "- ALL colors must use CSS custom properties (var(--rose-gold), not #B76E79)\n"
        "- Font stacks must include system fallbacks\n"
        "- Spacing uses a consistent scale (4px base recommended)\n"
        "- Every token must have a semantic name, not a raw value\n"
        "- JSON output must be valid and parseable"
    ),
    capabilities=[
        AgentCapability(
            name="color_palette",
            description="Generate accessible color palettes from brand guidelines",
            tags=("design", "color", "a11y"),
        ),
        AgentCapability(
            name="typography_scale",
            description="Create modular type scales with responsive sizing",
            tags=("design", "typography"),
        ),
        AgentCapability(
            name="spacing_scale",
            description="Generate consistent spacing systems",
            tags=("design", "spacing"),
        ),
        AgentCapability(
            name="theme_json",
            description="Build WordPress theme.json with Full Site Editing support",
            tags=("design", "wordpress", "theme"),
        ),
        AgentCapability(
            name="design_tokens",
            description="Export design tokens in multiple formats (CSS, JSON, SCSS)",
            tags=("design", "tokens"),
        ),
    ],
    knowledge_files=[
        "knowledge/wordpress.md",
        "knowledge/wordpress_deployment.md",
        "knowledge/photo_generation.md",
        "knowledge/wcag_checklist.md",
    ],
)
