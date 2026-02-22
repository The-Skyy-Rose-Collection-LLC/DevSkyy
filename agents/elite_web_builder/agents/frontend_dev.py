"""Frontend Dev Agent — HTML/CSS/JS, React, Vue, block patterns, animations.

Model: Claude Sonnet 4.6 (best coding model for complex template logic)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

FRONTEND_DEV_SPEC = AgentSpec(
    role=AgentRole.FRONTEND_DEV,
    name="frontend_dev",
    system_prompt=(
        "You are a Frontend Development specialist. You build responsive, "
        "accessible, performant user interfaces using modern web standards.\n\n"
        "Core responsibilities:\n"
        "- Write semantic HTML5 with proper ARIA attributes\n"
        "- Create responsive CSS using Grid, Flexbox, and Container Queries\n"
        "- Build interactive JS with progressive enhancement\n"
        "- Create WordPress block patterns and template parts\n"
        "- Implement animations with GSAP or CSS transitions\n"
        "- Build React/Vue components when needed\n\n"
        "Output rules:\n"
        "- CSS uses custom properties from the design system (never hardcoded)\n"
        "- JavaScript uses Object.freeze for configuration objects\n"
        "- All assets loaded via wp_enqueue_script/wp_enqueue_style\n"
        "- No @import in CSS (use enqueue dependencies instead)\n"
        "- Images use loading='lazy' and explicit width/height\n"
        "- All interactive elements must be keyboard accessible"
    ),
    capabilities=[
        AgentCapability(
            name="html_templates",
            description="Create semantic HTML templates and WordPress template parts",
            tags=("frontend", "html", "wordpress"),
        ),
        AgentCapability(
            name="css_styling",
            description="Write responsive CSS with custom properties and modern layout",
            tags=("frontend", "css", "responsive"),
        ),
        AgentCapability(
            name="javascript",
            description="Build interactive features with vanilla JS or frameworks",
            tags=("frontend", "javascript"),
        ),
        AgentCapability(
            name="block_patterns",
            description="Create WordPress block patterns and Full Site Editing blocks",
            tags=("frontend", "wordpress", "blocks"),
        ),
        AgentCapability(
            name="animations",
            description="Implement smooth animations and transitions",
            tags=("frontend", "animation", "gsap"),
        ),
    ],
    knowledge_files=[
        "knowledge/wordpress.md",
        "knowledge/wordpress_deployment.md",
        "knowledge/photo_generation.md",
    ],
)
