"""Tests for all 7 specialist agent specs — verify role, prompt, capabilities."""

from __future__ import annotations

import pytest

from agents.base import AgentRole, AgentSpec
from agents.accessibility import ACCESSIBILITY_SPEC
from agents.backend_dev import BACKEND_DEV_SPEC
from agents.design_system import DESIGN_SYSTEM_SPEC
from agents.frontend_dev import FRONTEND_DEV_SPEC
from agents.performance import PERFORMANCE_SPEC
from agents.qa import QA_SPEC
from agents.seo_content import SEO_CONTENT_SPEC

# Build ALL_SPECS locally (mirrors agents/__init__.py)
ALL_SPECS: tuple[AgentSpec, ...] = (
    DESIGN_SYSTEM_SPEC,
    FRONTEND_DEV_SPEC,
    BACKEND_DEV_SPEC,
    ACCESSIBILITY_SPEC,
    PERFORMANCE_SPEC,
    SEO_CONTENT_SPEC,
    QA_SPEC,
)


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------


class TestAllSpecs:
    def test_seven_specialists(self) -> None:
        """All 7 specialist agents (not Director) are registered."""
        assert len(ALL_SPECS) == 7

    def test_all_roles_covered(self) -> None:
        """Every non-Director role has a spec."""
        spec_roles = {spec.role for spec in ALL_SPECS}
        expected = {
            AgentRole.DESIGN_SYSTEM,
            AgentRole.FRONTEND_DEV,
            AgentRole.BACKEND_DEV,
            AgentRole.ACCESSIBILITY,
            AgentRole.PERFORMANCE,
            AgentRole.SEO_CONTENT,
            AgentRole.QA,
        }
        assert spec_roles == expected

    def test_no_duplicate_roles(self) -> None:
        roles = [spec.role for spec in ALL_SPECS]
        assert len(roles) == len(set(roles))

    def test_all_specs_have_names(self) -> None:
        for spec in ALL_SPECS:
            assert spec.name, f"{spec.role} has no name"

    def test_all_specs_have_prompts(self) -> None:
        for spec in ALL_SPECS:
            assert len(spec.system_prompt) > 50, (
                f"{spec.name} prompt too short"
            )

    def test_all_specs_have_capabilities(self) -> None:
        for spec in ALL_SPECS:
            assert len(spec.capabilities) >= 3, (
                f"{spec.name} needs at least 3 capabilities"
            )

    def test_capabilities_have_tags(self) -> None:
        for spec in ALL_SPECS:
            for cap in spec.capabilities:
                assert len(cap.tags) > 0, (
                    f"{spec.name}/{cap.name} has no tags"
                )


# ---------------------------------------------------------------------------
# Design System
# ---------------------------------------------------------------------------


class TestDesignSystem:
    def test_role(self) -> None:
        assert DESIGN_SYSTEM_SPEC.role == AgentRole.DESIGN_SYSTEM

    def test_prompt_mentions_tokens(self) -> None:
        assert "token" in DESIGN_SYSTEM_SPEC.system_prompt.lower()

    def test_prompt_mentions_custom_properties(self) -> None:
        assert "custom properties" in DESIGN_SYSTEM_SPEC.system_prompt.lower()

    def test_has_theme_json_capability(self) -> None:
        cap_names = [c.name for c in DESIGN_SYSTEM_SPEC.capabilities]
        assert "theme_json" in cap_names

    def test_has_color_palette_capability(self) -> None:
        cap_names = [c.name for c in DESIGN_SYSTEM_SPEC.capabilities]
        assert "color_palette" in cap_names


# ---------------------------------------------------------------------------
# Frontend Dev
# ---------------------------------------------------------------------------


class TestFrontendDev:
    def test_role(self) -> None:
        assert FRONTEND_DEV_SPEC.role == AgentRole.FRONTEND_DEV

    def test_prompt_mentions_accessibility(self) -> None:
        assert "accessible" in FRONTEND_DEV_SPEC.system_prompt.lower()

    def test_prompt_mentions_enqueue(self) -> None:
        assert "enqueue" in FRONTEND_DEV_SPEC.system_prompt.lower()

    def test_has_javascript_capability(self) -> None:
        cap_names = [c.name for c in FRONTEND_DEV_SPEC.capabilities]
        assert "javascript" in cap_names


# ---------------------------------------------------------------------------
# Backend Dev
# ---------------------------------------------------------------------------


class TestBackendDev:
    def test_role(self) -> None:
        assert BACKEND_DEV_SPEC.role == AgentRole.BACKEND_DEV

    def test_prompt_mentions_parameterized(self) -> None:
        assert "parameterized" in BACKEND_DEV_SPEC.system_prompt.lower()

    def test_prompt_mentions_rest_route(self) -> None:
        """WordPress.com uses index.php?rest_route= not /wp-json/."""
        assert "rest_route" in BACKEND_DEV_SPEC.system_prompt

    def test_has_woocommerce_capability(self) -> None:
        cap_names = [c.name for c in BACKEND_DEV_SPEC.capabilities]
        assert "woocommerce" in cap_names


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------


class TestAccessibility:
    def test_role(self) -> None:
        assert ACCESSIBILITY_SPEC.role == AgentRole.ACCESSIBILITY

    def test_prompt_mentions_contrast_ratios(self) -> None:
        assert "4.5:1" in ACCESSIBILITY_SPEC.system_prompt

    def test_prompt_mentions_wcag(self) -> None:
        assert "WCAG" in ACCESSIBILITY_SPEC.system_prompt

    def test_has_contrast_audit(self) -> None:
        cap_names = [c.name for c in ACCESSIBILITY_SPEC.capabilities]
        assert "contrast_audit" in cap_names


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_role(self) -> None:
        assert PERFORMANCE_SPEC.role == AgentRole.PERFORMANCE

    def test_prompt_mentions_page_speed(self) -> None:
        assert "80" in PERFORMANCE_SPEC.system_prompt

    def test_prompt_mentions_font_display(self) -> None:
        assert "font-display" in PERFORMANCE_SPEC.system_prompt

    def test_has_vitals_audit(self) -> None:
        cap_names = [c.name for c in PERFORMANCE_SPEC.capabilities]
        assert "vitals_audit" in cap_names


# ---------------------------------------------------------------------------
# SEO & Content
# ---------------------------------------------------------------------------


class TestSeoContent:
    def test_role(self) -> None:
        assert SEO_CONTENT_SPEC.role == AgentRole.SEO_CONTENT

    def test_prompt_mentions_json_ld(self) -> None:
        assert "JSON-LD" in SEO_CONTENT_SPEC.system_prompt

    def test_prompt_mentions_meta(self) -> None:
        assert "meta" in SEO_CONTENT_SPEC.system_prompt.lower()

    def test_has_structured_data_capability(self) -> None:
        cap_names = [c.name for c in SEO_CONTENT_SPEC.capabilities]
        assert "structured_data" in cap_names


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


class TestQA:
    def test_role(self) -> None:
        assert QA_SPEC.role == AgentRole.QA

    def test_prompt_mentions_playwright(self) -> None:
        assert "Playwright" in QA_SPEC.system_prompt

    def test_prompt_mentions_coverage_target(self) -> None:
        assert "90%" in QA_SPEC.system_prompt

    def test_has_e2e_testing(self) -> None:
        cap_names = [c.name for c in QA_SPEC.capabilities]
        assert "e2e_testing" in cap_names

    def test_has_lighthouse_ci(self) -> None:
        cap_names = [c.name for c in QA_SPEC.capabilities]
        assert "lighthouse_ci" in cap_names


# ---------------------------------------------------------------------------
# Learning context injection
# ---------------------------------------------------------------------------


class TestLearningInjection:
    def test_all_specs_accept_learning_context(self) -> None:
        """Every spec can inject learning rules into its prompt."""
        learning = "RULE: Rose gold is #B76E79, not #FFB6C1"
        for spec in ALL_SPECS:
            prompt = spec.build_prompt(learning_context=learning)
            assert "Rose gold is #B76E79" in prompt
            assert spec.system_prompt in prompt
