"""Tests for agents/base.py — AgentRole, AgentSpec, AgentOutput, AgentCapability."""

from __future__ import annotations

import pytest

from agents.base import AgentCapability, AgentOutput, AgentRole, AgentSpec


# ---------------------------------------------------------------------------
# AgentRole
# ---------------------------------------------------------------------------


class TestAgentRole:
    def test_all_eight_roles_exist(self) -> None:
        roles = [r.value for r in AgentRole]
        assert len(roles) == 8
        assert "director" in roles
        assert "design_system" in roles
        assert "frontend_dev" in roles
        assert "backend_dev" in roles
        assert "accessibility" in roles
        assert "performance" in roles
        assert "seo_content" in roles
        assert "qa" in roles

    def test_role_values_are_snake_case(self) -> None:
        for role in AgentRole:
            assert role.value == role.value.lower()
            assert " " not in role.value


# ---------------------------------------------------------------------------
# AgentCapability
# ---------------------------------------------------------------------------


class TestAgentCapability:
    def test_create_capability(self) -> None:
        cap = AgentCapability(
            name="contrast_check",
            description="Check WCAG contrast ratios",
            tags=("a11y", "wcag"),
        )
        assert cap.name == "contrast_check"
        assert "a11y" in cap.tags

    def test_capability_is_frozen(self) -> None:
        cap = AgentCapability(name="test", description="test")
        with pytest.raises(AttributeError):
            cap.name = "changed"  # type: ignore[misc]

    def test_default_tags_empty(self) -> None:
        cap = AgentCapability(name="x", description="y")
        assert cap.tags == ()


# ---------------------------------------------------------------------------
# AgentOutput
# ---------------------------------------------------------------------------


class TestAgentOutput:
    def test_create_output(self) -> None:
        out = AgentOutput(
            agent="frontend_dev",
            story_id="US-001",
            content="<div>Hello</div>",
            files_changed=("index.html",),
            metadata={"lines_added": 10},
        )
        assert out.agent == "frontend_dev"
        assert out.story_id == "US-001"
        assert "index.html" in out.files_changed

    def test_output_is_frozen(self) -> None:
        out = AgentOutput(agent="qa", story_id="US-002", content="OK")
        with pytest.raises(AttributeError):
            out.content = "changed"  # type: ignore[misc]

    def test_default_files_empty(self) -> None:
        out = AgentOutput(agent="qa", story_id="US-003", content="pass")
        assert out.files_changed == ()

    def test_default_metadata_empty(self) -> None:
        out = AgentOutput(agent="qa", story_id="US-004", content="pass")
        assert out.metadata == {}


# ---------------------------------------------------------------------------
# AgentSpec
# ---------------------------------------------------------------------------


class TestAgentSpec:
    def test_create_spec(self) -> None:
        spec = AgentSpec(
            role=AgentRole.FRONTEND_DEV,
            name="frontend_dev",
            system_prompt="You are a frontend developer.",
        )
        assert spec.role == AgentRole.FRONTEND_DEV
        assert spec.name == "frontend_dev"

    def test_build_prompt_no_learning(self) -> None:
        spec = AgentSpec(
            role=AgentRole.QA,
            name="qa",
            system_prompt="You are a QA engineer.",
        )
        prompt = spec.build_prompt()
        assert "You are a QA engineer." in prompt

    def test_build_prompt_with_learning(self) -> None:
        spec = AgentSpec(
            role=AgentRole.DESIGN_SYSTEM,
            name="design_system",
            system_prompt="You design systems.",
        )
        learning = "RULE: Rose gold is #B76E79"
        prompt = spec.build_prompt(learning_context=learning)
        assert "You design systems." in prompt
        assert "Rose gold is #B76E79" in prompt

    def test_build_prompt_empty_learning_ignored(self) -> None:
        spec = AgentSpec(
            role=AgentRole.ACCESSIBILITY,
            name="a11y",
            system_prompt="Check accessibility.",
        )
        prompt_no_learning = spec.build_prompt(learning_context="")
        assert prompt_no_learning == "Check accessibility."

    def test_default_capabilities_empty(self) -> None:
        spec = AgentSpec(
            role=AgentRole.BACKEND_DEV,
            name="backend",
            system_prompt="Backend.",
        )
        assert spec.capabilities == []

    def test_default_knowledge_files_empty(self) -> None:
        spec = AgentSpec(
            role=AgentRole.SEO_CONTENT,
            name="seo",
            system_prompt="SEO.",
        )
        assert spec.knowledge_files == []

    def test_spec_with_capabilities(self) -> None:
        cap = AgentCapability(
            name="wcag_check",
            description="WCAG audit",
            tags=("a11y",),
        )
        spec = AgentSpec(
            role=AgentRole.ACCESSIBILITY,
            name="a11y",
            system_prompt="A11y agent.",
            capabilities=[cap],
        )
        assert len(spec.capabilities) == 1
        assert spec.capabilities[0].name == "wcag_check"
