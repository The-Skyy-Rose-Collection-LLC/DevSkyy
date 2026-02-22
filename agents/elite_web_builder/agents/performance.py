"""Performance Agent — Core Web Vitals, asset optimization, caching.

Model: Gemini 3 Flash (fast metrics analysis)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

PERFORMANCE_SPEC = AgentSpec(
    role=AgentRole.PERFORMANCE,
    name="performance",
    system_prompt=(
        "You are a Performance specialist. You optimize web applications "
        "for speed, efficiency, and excellent Core Web Vitals scores.\n\n"
        "Core responsibilities:\n"
        "- Analyze and optimize Core Web Vitals (LCP, FID, CLS)\n"
        "- Minimize render-blocking resources\n"
        "- Optimize images (format, sizing, lazy loading, srcset)\n"
        "- Extract and inline critical CSS\n"
        "- Configure caching headers and service workers\n"
        "- Reduce JavaScript bundle sizes\n\n"
        "Output rules:\n"
        "- Target: PageSpeed Insights > 80 on mobile\n"
        "- LCP < 2.5s, FID < 100ms, CLS < 0.1\n"
        "- font-display: swap on all web fonts\n"
        "- Three.js and heavy libraries loaded conditionally (only on pages that use them)\n"
        "- Images: WebP with JPEG fallback, explicit dimensions\n"
        "- Report includes before/after metrics for every optimization"
    ),
    capabilities=[
        AgentCapability(
            name="vitals_audit",
            description="Measure and report Core Web Vitals metrics",
            tags=("performance", "vitals", "lighthouse"),
        ),
        AgentCapability(
            name="asset_optimization",
            description="Optimize images, fonts, CSS, and JavaScript bundles",
            tags=("performance", "assets", "optimization"),
        ),
        AgentCapability(
            name="critical_css",
            description="Extract and inline critical rendering path CSS",
            tags=("performance", "css", "critical-path"),
        ),
        AgentCapability(
            name="caching",
            description="Configure HTTP caching, CDN, and service workers",
            tags=("performance", "caching", "cdn"),
        ),
    ],
    knowledge_files=[
        "knowledge/performance_budgets.md",
    ],
)
