"""
Performance Agent Spec — Core Web Vitals, asset optimization, caching.

Model: Gemini 3 Flash (fast metrics analysis)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """
    Builds the performance agent specification for Core Web Vitals, asset optimization, and caching.
    
    Returns:
        spec (dict): Configuration dictionary with the following keys:
            - role: string identifier for the agent (e.g., "performance")
            - name: agent name
            - system_prompt: human-readable prompt describing optimization goals and targets
            - capabilities: list of capability dicts, each containing `name`, `description`, and `tags`
            - knowledge_files: list of related knowledge file paths
            - preferred_model: dict specifying `provider` and `model`
    """
    return {
        "role": "performance",
        "name": "performance",
        "system_prompt": (
            "You are a Performance specialist for the Elite Web Builder. "
            "You optimize for Core Web Vitals: LCP < 2.5s, FID < 100ms, "
            "CLS < 0.1, INP < 200ms. You ensure: lazy loading for images, "
            "critical CSS inlined, async/defer for scripts, "
            "font-display: swap, image compression (WebP/AVIF), "
            "section rendering API usage, and efficient caching. "
            "Target: PageSpeed > 80 mobile."
        ),
        "capabilities": [
            {
                "name": "core_web_vitals",
                "description": "Optimize for LCP, FID, CLS, INP targets",
                "tags": ["perf", "cwv", "metrics"],
            },
            {
                "name": "asset_optimization",
                "description": "Optimize images, fonts, scripts, and stylesheets",
                "tags": ["perf", "assets", "compression"],
            },
            {
                "name": "caching_strategy",
                "description": "Design caching strategy (CDN, browser, server)",
                "tags": ["perf", "caching", "cdn"],
            },
            {
                "name": "lighthouse_audit",
                "description": "Run Lighthouse performance audit",
                "tags": ["perf", "lighthouse", "audit"],
            },
        ],
        "knowledge_files": [
            "knowledge/performance_budgets.md",
        ],
        "preferred_model": {"provider": "google", "model": "gemini-3-flash-preview"},
    }


PERFORMANCE_SPEC = _build_spec()