"""
Web Development Sub-Agent (Consolidated)
===========================================

Consolidates: frontend_dev, backend_dev, accessibility, performance, platform_adapter.
Wraps agents/elite_web_builder/agents/ specs into the new hierarchy.

Parent: Web Builder Core Agent
Capabilities: Frontend (HTML/CSS/JS), backend (PHP/Node), a11y, perf, platform adapters.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class WebDevSubAgent(SubAgent):
    """Full-stack web development: frontend, backend, accessibility, performance."""

    name = "web_dev"
    parent_type = CoreAgentType.WEB_BUILDER
    description = (
        "Frontend dev (HTML/CSS/JS/React), backend dev (PHP/Node), "
        "accessibility (WCAG 2.2 AA), performance optimization, platform adapters"
    )
    capabilities = [
        # frontend_dev
        "html_template",
        "css_styling",
        "js_interactive",
        "react_component",
        "block_pattern",
        "animation",
        # backend_dev
        "php_template",
        "rest_api",
        "database_query",
        "server_config",
        # accessibility
        "wcag_audit",
        "aria_check",
        "contrast_check",
        "keyboard_nav",
        # performance
        "lighthouse_audit",
        "lazy_loading",
        "caching_strategy",
        "bundle_optimize",
        # platform_adapter
        "wordpress_adapter",
        "vercel_adapter",
        "shopify_adapter",
    ]

    ALIASES = ("frontend_dev", "backend_dev", "accessibility", "performance", "platform_adapter")

    system_prompt = (
        "You are the Full-Stack Web Development specialist for SkyyRose/DevSkyy. "
        "Frontend: Next.js 15, React 19, Tailwind CSS, Three.js for 3D. "
        "Backend: FastAPI (Python), WordPress/PHP (skyyrose-flagship theme). "
        "You generate HTML templates, React components, PHP templates, REST APIs, "
        "WCAG 2.2 AA accessibility audits, and Lighthouse performance optimizations. "
        "Return production-ready code with proper typing and error handling."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["WebDevSubAgent"]
