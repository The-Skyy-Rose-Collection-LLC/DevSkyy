"""
Elite Web Builder — Full-Stack AI Web Development Agency
=========================================================

A multi-agent system that decomposes PRDs into user stories and
executes them through specialist agents with quality gates,
self-healing, and learning journal integration.

Agents:
- Director: Coordinates, plans, reviews all output
- DesignSystem: Color palettes, typography, theme.json, design tokens
- FrontendDev: HTML/CSS/JS, React, Vue, Liquid templates
- BackendDev: PHP, Python, Node.js, APIs, databases
- Accessibility: WCAG 2.2 AA/AAA, contrast, ARIA
- Performance: Core Web Vitals, optimization
- SEOContent: Meta tags, schema.org, copywriting
- QA: E2E testing, cross-browser, visual regression
"""

from .director import (
    AgentRole,
    AgentSpec,
    Director,
    DirectorConfig,
    PlanningError,
    PRDBreakdown,
    ProjectReport,
    StoryStatus,
    UserStory,
)

__all__ = [
    "Director",
    "DirectorConfig",
    "AgentRole",
    "AgentSpec",
    "UserStory",
    "StoryStatus",
    "PRDBreakdown",
    "PlanningError",
    "ProjectReport",
]
