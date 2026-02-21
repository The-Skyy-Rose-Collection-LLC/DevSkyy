"""
QA Agent Spec — E2E testing, cross-browser, visual regression, Lighthouse.

Model: Grok 3 (real-time web access for live checks)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """
    Constructs the QA agent specification used by the Elite Web Builder.
    
    Returns:
        spec (dict): Specification dictionary with the following keys:
            - role (str): Agent role identifier, e.g., "qa".
            - name (str): Agent name.
            - system_prompt (str): Detailed system prompt describing QA responsibilities and targets.
            - capabilities (list[dict]): Capability entries each containing `name`, `description`, and `tags`.
            - knowledge_files (list[str]): Paths to knowledge/reference files.
            - preferred_model (dict): Preferred model info with `provider` and `model` keys.
    """
    return {
        "role": "qa",
        "name": "qa",
        "system_prompt": (
            "You are a QA specialist for the Elite Web Builder. "
            "You write and run E2E tests (Playwright), cross-browser tests, "
            "visual regression tests, and integration tests. "
            "You verify: all pages load, forms submit, CTAs link correctly, "
            "mobile renders (375px, 768px), no console errors, "
            "fonts render correctly, collection colors apply. "
            "Coverage target: 90%+. Mobile-first testing. "
            "Lighthouse > 80 on all pages."
        ),
        "capabilities": [
            {
                "name": "e2e_testing",
                "description": "Write and run Playwright E2E tests",
                "tags": ["qa", "e2e", "playwright"],
            },
            {
                "name": "visual_regression",
                "description": "Screenshot-based visual regression testing",
                "tags": ["qa", "visual", "regression"],
            },
            {
                "name": "cross_browser",
                "description": "Test across Chrome, Firefox, Safari, Edge",
                "tags": ["qa", "browser", "compatibility"],
            },
            {
                "name": "lighthouse",
                "description": "Run Lighthouse audits for performance/a11y/SEO",
                "tags": ["qa", "lighthouse", "audit"],
            },
            {
                "name": "shopify_testing",
                "description": "Test Shopify theme compliance and Storefront API integration",
                "tags": ["qa", "shopify", "e2e"],
            },
        ],
        "knowledge_files": [
            "knowledge/wordpress.md",
            "knowledge/shopify.md",
            "knowledge/wcag_checklist.md",
            "knowledge/performance_budgets.md",
        ],
        "preferred_model": {"provider": "xai", "model": "grok-3"},
    }


QA_SPEC = _build_spec()