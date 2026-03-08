"""Tests for sub-agent system prompts and LLM wiring.

Verifies all 18 sub-agents:
- Have domain-specific system_prompt
- Route execute() through _llm_execute()
- Inherit from SubAgent base class
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.core.sub_agent import SubAgent

# All sub-agent classes to test
SUB_AGENT_IMPORTS = [
    ("agents.core.commerce.sub_agents.product_ops", "ProductOpsSubAgent"),
    ("agents.core.commerce.sub_agents.wordpress_assets", "WordPressAssetsSubAgent"),
    ("agents.core.commerce.sub_agents.wordpress_bridge", "WordPressBridgeSubAgent"),
    ("agents.core.content.sub_agents.seo_copywriter", "SeoCopywriterSubAgent"),
    ("agents.core.content.sub_agents.collection_content", "CollectionContentSubAgent"),
    ("agents.core.creative.sub_agents.brand_creative", "BrandCreativeSubAgent"),
    ("agents.core.marketing.sub_agents.social_media", "SocialMediaSubAgent"),
    ("agents.core.marketing.sub_agents.campaign_ops", "CampaignOpsSubAgent"),
    ("agents.core.operations.sub_agents.security_monitor", "SecurityMonitorSubAgent"),
    ("agents.core.operations.sub_agents.coding_doctor", "CodingDoctorSubAgent"),
    ("agents.core.operations.sub_agents.deploy_health", "DeployHealthSubAgent"),
    ("agents.core.analytics.sub_agents.analytics_ops", "AnalyticsOpsSubAgent"),
    ("agents.core.imagery.sub_agents.gemini_image", "GeminiImageSubAgent"),
    ("agents.core.imagery.sub_agents.fashn_vton", "FashnVtonSubAgent"),
    ("agents.core.imagery.sub_agents.tripo_3d", "Tripo3dSubAgent"),
    ("agents.core.imagery.sub_agents.meshy_3d", "Meshy3dSubAgent"),
    ("agents.core.imagery.sub_agents.hf_spaces", "HfSpacesSubAgent"),
    ("agents.core.web_builder.sub_agents.web_dev", "WebDevSubAgent"),
]


def _import_agent(module_path: str, class_name: str):
    """Dynamically import a sub-agent class."""
    import importlib

    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


class TestSubAgentInheritance:
    """All sub-agents must inherit from SubAgent."""

    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    def test_inherits_from_sub_agent(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        assert issubclass(cls, SubAgent), f"{class_name} must inherit from SubAgent"


class TestSubAgentSystemPrompts:
    """All sub-agents must have domain-specific system prompts."""

    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    def test_has_system_prompt(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        assert hasattr(cls, "system_prompt"), f"{class_name} missing system_prompt"
        assert isinstance(cls.system_prompt, str), f"{class_name}.system_prompt must be str"
        assert len(cls.system_prompt) > 20, f"{class_name}.system_prompt too short"

    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    def test_system_prompt_mentions_skyyrose(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        prompt = cls.system_prompt.lower()
        assert (
            "skyyrose" in prompt or "skyy" in prompt
        ), f"{class_name}.system_prompt should mention SkyyRose brand"


class TestSubAgentExecute:
    """Sub-agent execute() routes through _llm_execute()."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    async def test_execute_calls_llm_execute(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        agent = cls(correlation_id="test-corr")

        mock_result = {
            "success": True,
            "result": "test response",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "technique": None,
            "latency_ms": 100,
            "agent": agent.name,
        }

        with patch.object(
            agent, "_llm_execute", new_callable=AsyncMock, return_value=mock_result
        ) as mock:
            result = await agent.execute("test task")
            mock.assert_called_once_with("test task")
            assert result["success"] is True


class TestSubAgentNoLegacy:
    """Verify legacy agent pattern is removed."""

    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    def test_no_legacy_agent(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        agent = cls(correlation_id="test")
        assert not hasattr(agent, "_legacy_agent"), f"{class_name} still has _legacy_agent"

    @pytest.mark.parametrize("module_path,class_name", SUB_AGENT_IMPORTS)
    def test_no_get_legacy_method(self, module_path, class_name):
        cls = _import_agent(module_path, class_name)
        assert not hasattr(cls, "_get_legacy"), f"{class_name} still has _get_legacy()"


class TestSubAgentBase:
    """Tests for the SubAgent base class itself."""

    def test_base_has_llm_execute(self):
        assert hasattr(SubAgent, "_llm_execute")

    def test_base_default_name(self):
        agent = SubAgent(correlation_id="test")
        assert agent.name == "unnamed_sub_agent"

    def test_base_has_correlation_id(self):
        agent = SubAgent(correlation_id="test-123")
        assert agent.correlation_id == "test-123"
