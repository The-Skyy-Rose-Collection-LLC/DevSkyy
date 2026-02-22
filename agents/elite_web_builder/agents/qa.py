"""QA Agent — E2E testing, cross-browser, visual regression, Lighthouse.

Model: Grok 3 (real-time web access for live checks)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

QA_SPEC = AgentSpec(
    role=AgentRole.QA,
    name="qa",
    system_prompt=(
        "You are a Quality Assurance specialist. You ensure every feature "
        "works correctly across browsers, devices, and screen sizes before "
        "it ships.\n\n"
        "Core responsibilities:\n"
        "- Write and run E2E tests (Playwright) for critical user flows\n"
        "- Cross-browser testing (Chrome, Firefox, Safari, Edge)\n"
        "- Mobile testing (375px, 768px, 1024px breakpoints)\n"
        "- Visual regression testing (screenshot comparison)\n"
        "- Integration testing (API endpoints, form submissions)\n"
        "- Lighthouse CI for performance, a11y, best practices, SEO\n\n"
        "Output rules:\n"
        "- Test coverage target: 90%+\n"
        "- Critical flows: Homepage > Collection > Product > Cart > Checkout\n"
        "- Every test has clear assertion messages\n"
        "- Flaky tests are quarantined, not deleted\n"
        "- Test data is isolated (no shared state between tests)\n"
        "- Report includes: pass/fail counts, screenshots of failures, "
        "performance scores"
    ),
    capabilities=[
        AgentCapability(
            name="e2e_testing",
            description="Write and run Playwright E2E tests for critical flows",
            tags=("qa", "e2e", "playwright"),
        ),
        AgentCapability(
            name="cross_browser",
            description="Test across Chrome, Firefox, Safari, Edge",
            tags=("qa", "browser", "compatibility"),
        ),
        AgentCapability(
            name="visual_regression",
            description="Screenshot comparison for visual regression detection",
            tags=("qa", "visual", "regression"),
        ),
        AgentCapability(
            name="lighthouse_ci",
            description="Run Lighthouse CI for automated quality scoring",
            tags=("qa", "lighthouse", "ci"),
        ),
    ],
    knowledge_files=[
        "knowledge/wordpress.md",
        "knowledge/wordpress_deployment.md",
        "knowledge/photo_generation.md",
        "knowledge/performance_budgets.md",
        "knowledge/wcag_checklist.md",
    ],
)
