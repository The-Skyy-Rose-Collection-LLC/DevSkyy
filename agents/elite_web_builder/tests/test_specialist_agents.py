"""
Tests for specialist agent specifications.

Validates each agent spec has required fields, proper capabilities,
and correct knowledge file references.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from elite_web_builder.agents.design_system import DESIGN_SYSTEM_SPEC
from elite_web_builder.agents.frontend_dev import FRONTEND_DEV_SPEC
from elite_web_builder.agents.backend_dev import BACKEND_DEV_SPEC
from elite_web_builder.agents.accessibility import ACCESSIBILITY_SPEC
from elite_web_builder.agents.performance import PERFORMANCE_SPEC
from elite_web_builder.agents.seo_content import SEO_CONTENT_SPEC
from elite_web_builder.agents.qa import QA_SPEC

PACKAGE_ROOT = Path(__file__).parent.parent

ALL_SPECS = [
    ("design_system", DESIGN_SYSTEM_SPEC),
    ("frontend_dev", FRONTEND_DEV_SPEC),
    ("backend_dev", BACKEND_DEV_SPEC),
    ("accessibility", ACCESSIBILITY_SPEC),
    ("performance", PERFORMANCE_SPEC),
    ("seo_content", SEO_CONTENT_SPEC),
    ("qa", QA_SPEC),
]


class TestSpecStructure:
    """All agent specs have required fields."""

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_role(self, name, spec):
        assert "role" in spec, f"{name} missing role"
        assert spec["role"] == name

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_name(self, name, spec):
        """
        Validate that the specification contains a "name" entry equal to the expected name.
        
        Parameters:
            name (str): Expected name value for the spec.
            spec (dict): Agent specification dictionary to validate.
        """
        assert "name" in spec
        assert spec["name"] == name

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_system_prompt(self, name, spec):
        assert "system_prompt" in spec
        assert len(spec["system_prompt"]) > 50  # Non-trivial prompt

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_capabilities(self, name, spec):
        assert "capabilities" in spec
        assert len(spec["capabilities"]) >= 1

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_capabilities_have_required_fields(self, name, spec):
        """
        Assert every capability in the given spec includes the required fields: `name`, `description`, and `tags`.
        
        Parameters:
            name (str): The identifier for the spec used in failure messages.
            spec (dict): Specification object containing a `capabilities` iterable of capability dictionaries.
        """
        for cap in spec["capabilities"]:
            assert "name" in cap, f"{name} capability missing name"
            assert "description" in cap, f"{name} capability missing description"
            assert "tags" in cap, f"{name} capability missing tags"

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_knowledge_files(self, name, spec):
        """
        Ensure the agent spec declares a "knowledge_files" entry.
        
        Parameters:
            name (str): The expected role/name of the agent spec used for test identification.
            spec (dict): The agent specification dictionary; must include the "knowledge_files" key.
        """
        assert "knowledge_files" in spec


class TestShopifyCapabilities:
    """Agents that need Shopify support have it."""

    def test_design_system_has_shopify(self):
        cap_names = [c["name"] for c in DESIGN_SYSTEM_SPEC["capabilities"]]
        assert "shopify_theme_settings" in cap_names

    def test_frontend_dev_has_liquid(self):
        cap_names = [c["name"] for c in FRONTEND_DEV_SPEC["capabilities"]]
        assert "liquid_templates" in cap_names

    def test_backend_dev_has_shopify_api(self):
        cap_names = [c["name"] for c in BACKEND_DEV_SPEC["capabilities"]]
        assert "shopify_api" in cap_names

    def test_qa_has_shopify_testing(self):
        cap_names = [c["name"] for c in QA_SPEC["capabilities"]]
        assert "shopify_testing" in cap_names


class TestKnowledgeFileReferences:
    """Knowledge files referenced by agents exist."""

    def test_design_system_knowledge_files_exist(self):
        """
        Check that every file path listed in DESIGN_SYSTEM_SPEC["knowledge_files"] exists under PACKAGE_ROOT.
        
        Asserts existence of each knowledge file and fails with an AssertionError containing "Missing: <path>" if any file is absent.
        """
        for kf in DESIGN_SYSTEM_SPEC["knowledge_files"]:
            assert (PACKAGE_ROOT / kf).exists(), f"Missing: {kf}"

    def test_frontend_dev_knowledge_files_exist(self):
        """
        Verify that every knowledge file referenced by the frontend developer spec exists under the repository root.
        
        Resolves each path in FRONTEND_DEV_SPEC["knowledge_files"] relative to PACKAGE_ROOT and asserts the file exists; raises an AssertionError with the missing path if any file is not found.
        """
        for kf in FRONTEND_DEV_SPEC["knowledge_files"]:
            assert (PACKAGE_ROOT / kf).exists(), f"Missing: {kf}"

    def test_backend_dev_knowledge_files_exist(self):
        for kf in BACKEND_DEV_SPEC["knowledge_files"]:
            assert (PACKAGE_ROOT / kf).exists(), f"Missing: {kf}"

    def test_seo_content_has_knowledge_files(self):
        """
        Verify the SEO content spec declares at least two knowledge files and that each referenced file exists under the repository root.
        
        This test asserts that SEO_CONTENT_SPEC["knowledge_files"] contains two or more entries and that every path listed exists relative to PACKAGE_ROOT.
        """
        assert len(SEO_CONTENT_SPEC["knowledge_files"]) >= 2
        for kf in SEO_CONTENT_SPEC["knowledge_files"]:
            assert (PACKAGE_ROOT / kf).exists(), f"Missing: {kf}"

    def test_qa_has_shopify_knowledge(self):
        assert "knowledge/shopify.md" in QA_SPEC["knowledge_files"]


class TestPreferredModels:
    """Each agent has a preferred model configuration."""

    @pytest.mark.parametrize("name,spec", ALL_SPECS)
    def test_has_preferred_model(self, name, spec):
        assert "preferred_model" in spec
        model = spec["preferred_model"]
        assert "provider" in model
        assert "model" in model