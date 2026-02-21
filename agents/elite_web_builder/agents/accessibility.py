"""
Accessibility Agent Spec — WCAG 2.2 AA/AAA, contrast, ARIA, keyboard nav.

Model: Claude Haiku 4.5 (fast checker, runs on EVERY output)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """Build the accessibility agent specification."""
    return {
        "role": "accessibility",
        "name": "accessibility",
        "system_prompt": (
            "You are an Accessibility specialist for the Elite Web Builder. "
            "You audit all output for WCAG 2.2 AA compliance (AAA preferred). "
            "You check: contrast ratios (4.5:1 normal text, 3:1 large text), "
            "ARIA attributes, keyboard navigation, focus management, "
            "screen reader compatibility, alt text, form labels, "
            "heading hierarchy, and color-independence. "
            "You run on EVERY agent output before it can be marked GREEN. "
            "Zero tolerance for critical or serious axe-core violations."
        ),
        "capabilities": [
            {
                "name": "contrast_check",
                "description": "Verify WCAG contrast ratios for all color pairs",
                "tags": ["a11y", "contrast", "wcag"],
            },
            {
                "name": "aria_audit",
                "description": "Audit ARIA attributes, roles, and states",
                "tags": ["a11y", "aria", "screenreader"],
            },
            {
                "name": "keyboard_nav",
                "description": "Verify keyboard navigation and focus management",
                "tags": ["a11y", "keyboard", "focus"],
            },
            {
                "name": "axe_core",
                "description": "Run axe-core automated accessibility testing",
                "tags": ["a11y", "testing", "automated"],
            },
        ],
        "knowledge_files": [
            "knowledge/wcag_checklist.md",
        ],
        "preferred_model": {"provider": "anthropic", "model": "claude-haiku-4-5"},
    }


ACCESSIBILITY_SPEC = _build_spec()
