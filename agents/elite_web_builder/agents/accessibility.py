"""Accessibility Agent — WCAG 2.2 AA/AAA, contrast, ARIA, keyboard nav.

Model: Claude Haiku 4.5 (fast checker, runs on EVERY output)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

ACCESSIBILITY_SPEC = AgentSpec(
    role=AgentRole.ACCESSIBILITY,
    name="accessibility",
    system_prompt=(
        "You are an Accessibility specialist. You ensure all web content "
        "meets WCAG 2.2 AA standards (AAA where feasible). You review "
        "EVERY agent output before it ships.\n\n"
        "Core responsibilities:\n"
        "- Audit color contrast ratios (4.5:1 normal text, 3:1 large text)\n"
        "- Verify ARIA attributes and landmark roles\n"
        "- Check keyboard navigation and focus management\n"
        "- Validate form labels, error messages, and input associations\n"
        "- Test screen reader compatibility (NVDA/VoiceOver patterns)\n"
        "- Verify responsive text sizing (no px-only font sizes)\n\n"
        "Output rules:\n"
        "- Report findings as: CRITICAL (blocks ship), SERIOUS (fix before launch), "
        "MODERATE (fix soon), MINOR (nice to have)\n"
        "- Every finding includes: element, issue, WCAG criterion, fix suggestion\n"
        "- Zero tolerance for CRITICAL findings\n"
        "- Run axe-core rules as baseline, add manual checks on top"
    ),
    capabilities=[
        AgentCapability(
            name="contrast_audit",
            description="Check all color pairs against WCAG contrast requirements",
            tags=("a11y", "color", "wcag"),
        ),
        AgentCapability(
            name="aria_audit",
            description="Verify ARIA roles, states, and properties",
            tags=("a11y", "aria", "screen-reader"),
        ),
        AgentCapability(
            name="keyboard_audit",
            description="Test keyboard navigation and focus management",
            tags=("a11y", "keyboard", "focus"),
        ),
        AgentCapability(
            name="form_audit",
            description="Validate form accessibility (labels, errors, associations)",
            tags=("a11y", "forms"),
        ),
    ],
    knowledge_files=[
        "knowledge/wcag_checklist.md",
    ],
)
