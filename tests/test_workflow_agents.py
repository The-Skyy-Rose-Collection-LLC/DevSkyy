"""
Workflow Agents Test Suite
==========================

Tests for ADK Workflow Agents (SequentialAgent, ParallelAgent, LoopAgent).

These tests validate the module structure, pipeline factories, token savings
estimation, and the DevSkyy wrapper — all without requiring Google ADK to be
installed (graceful fallback).
"""

import os
import sys

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Test Enums & Config
# ============================================================================


class TestPipelineType:
    """Tests for PipelineType enum."""

    def test_pipeline_type_values(self):
        from adk.workflow_agents import PipelineType

        assert PipelineType.PRODUCT_LAUNCH == "product_launch"
        assert PipelineType.CONTENT_CREATION == "content_creation"
        assert PipelineType.CUSTOMER_JOURNEY == "customer_journey"
        assert PipelineType.QUALITY_ASSURANCE == "quality_assurance"
        assert PipelineType.CAMPAIGN_BLITZ == "campaign_blitz"

    def test_pipeline_type_count(self):
        from adk.workflow_agents import PipelineType

        assert len(PipelineType) == 5

    def test_pipeline_type_membership(self):
        from adk.workflow_agents import PipelineType

        assert "product_launch" in [p.value for p in PipelineType]
        assert "nonexistent" not in [p.value for p in PipelineType]


# ============================================================================
# Test TokenSavings
# ============================================================================


class TestTokenSavings:
    """Tests for TokenSavings dataclass."""

    def test_token_savings_creation(self):
        from adk.workflow_agents import TokenSavings

        savings = TokenSavings(
            pipeline_name="test_pipeline",
            leaf_agent_count=4,
            estimated_llm_routing_tokens=1400,
            actual_leaf_tokens=3200,
        )

        assert savings.pipeline_name == "test_pipeline"
        assert savings.leaf_agent_count == 4
        assert savings.estimated_llm_routing_tokens == 1400
        assert savings.actual_leaf_tokens == 3200

    def test_token_savings_calculate(self):
        from adk.workflow_agents import TokenSavings

        savings = TokenSavings(
            pipeline_name="test",
            leaf_agent_count=4,
            estimated_llm_routing_tokens=1000,
            actual_leaf_tokens=4000,
        )
        savings.calculate()

        # 1000 / (1000 + 4000) = 20%
        assert savings.savings_pct == pytest.approx(20.0)
        assert savings.orchestration_tokens_saved == 1000

    def test_token_savings_calculate_zero_total(self):
        from adk.workflow_agents import TokenSavings

        savings = TokenSavings(
            pipeline_name="empty",
            leaf_agent_count=0,
            estimated_llm_routing_tokens=0,
            actual_leaf_tokens=0,
        )
        savings.calculate()

        assert savings.savings_pct == 0.0
        assert savings.orchestration_tokens_saved == 0

    def test_token_savings_high_routing_overhead(self):
        from adk.workflow_agents import TokenSavings

        savings = TokenSavings(
            pipeline_name="heavy_routing",
            leaf_agent_count=8,
            estimated_llm_routing_tokens=5000,
            actual_leaf_tokens=5000,
        )
        savings.calculate()

        # 5000 / 10000 = 50%
        assert savings.savings_pct == pytest.approx(50.0)


# ============================================================================
# Test Pipeline Savings Estimation
# ============================================================================


class TestPipelineSavingsEstimation:
    """Tests for estimate_pipeline_savings function."""

    def test_estimate_product_launch_savings(self):
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        savings = estimate_pipeline_savings(PipelineType.PRODUCT_LAUNCH)

        assert savings.pipeline_name == "product_launch"
        assert savings.leaf_agent_count == 7
        assert savings.estimated_llm_routing_tokens > 0
        assert savings.savings_pct > 0

    def test_estimate_content_creation_savings(self):
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        savings = estimate_pipeline_savings(PipelineType.CONTENT_CREATION)

        assert savings.pipeline_name == "content_creation"
        assert savings.leaf_agent_count == 4
        assert savings.savings_pct > 0

    def test_estimate_customer_journey_savings(self):
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        savings = estimate_pipeline_savings(PipelineType.CUSTOMER_JOURNEY)

        assert savings.pipeline_name == "customer_journey"
        assert savings.leaf_agent_count == 3
        assert savings.savings_pct > 0

    def test_estimate_quality_assurance_savings(self):
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        savings = estimate_pipeline_savings(PipelineType.QUALITY_ASSURANCE)

        assert savings.pipeline_name == "quality_assurance"
        assert savings.leaf_agent_count == 4
        assert savings.savings_pct > 0

    def test_estimate_campaign_blitz_savings(self):
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        savings = estimate_pipeline_savings(PipelineType.CAMPAIGN_BLITZ)

        assert savings.pipeline_name == "campaign_blitz"
        assert savings.leaf_agent_count == 8
        assert savings.savings_pct > 0

    def test_all_pipelines_save_tokens(self):
        """Every pipeline should show positive savings over LLM routing."""
        from adk.workflow_agents import PipelineType, estimate_pipeline_savings

        for pipeline_type in PipelineType:
            savings = estimate_pipeline_savings(pipeline_type)
            assert savings.orchestration_tokens_saved > 0, (
                f"{pipeline_type.value} should save tokens"
            )
            assert savings.savings_pct > 0, (
                f"{pipeline_type.value} should have positive savings %"
            )


# ============================================================================
# Test get_pipeline Factory
# ============================================================================


class TestGetPipeline:
    """Tests for get_pipeline factory function."""

    def test_get_pipeline_invalid_type(self):
        from adk.workflow_agents import get_pipeline

        with pytest.raises(ValueError, match="Unknown pipeline type"):
            get_pipeline("nonexistent_type")

    def test_get_pipeline_returns_none_without_adk(self):
        """Without google-adk installed, pipelines return None."""
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, PipelineType, get_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            for pipeline_type in PipelineType:
                result = get_pipeline(pipeline_type)
                assert result is None


# ============================================================================
# Test Leaf Agent Factories (without ADK)
# ============================================================================


class TestLeafAgentFactories:
    """Test leaf agent factory functions return None when ADK unavailable."""

    def test_leaf_factories_graceful_without_adk(self):
        from adk.workflow_agents import (
            ADK_WORKFLOW_AVAILABLE,
            _create_analytics_leaf,
            _create_commerce_leaf,
            _create_creative_leaf,
            _create_marketing_leaf,
            _create_operations_leaf,
            _create_quality_reviewer_leaf,
            _create_refiner_leaf,
            _create_support_leaf,
            _create_synthesizer_leaf,
        )

        if not ADK_WORKFLOW_AVAILABLE:
            assert _create_commerce_leaf() is None
            assert _create_creative_leaf() is None
            assert _create_marketing_leaf() is None
            assert _create_support_leaf() is None
            assert _create_operations_leaf() is None
            assert _create_analytics_leaf() is None
            assert _create_quality_reviewer_leaf() is None
            assert _create_refiner_leaf() is None
            assert _create_synthesizer_leaf(keys=["a", "b"]) is None


# ============================================================================
# Test Pipeline Factories (without ADK)
# ============================================================================


class TestPipelineFactories:
    """Test pipeline factory functions."""

    def test_product_launch_pipeline_without_adk(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_product_launch_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            assert create_product_launch_pipeline() is None

    def test_content_creation_pipeline_without_adk(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_content_creation_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            assert create_content_creation_pipeline() is None

    def test_customer_journey_pipeline_without_adk(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_customer_journey_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            assert create_customer_journey_pipeline() is None

    def test_quality_assurance_pipeline_without_adk(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_quality_assurance_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            assert create_quality_assurance_pipeline() is None

    def test_campaign_blitz_pipeline_without_adk(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_campaign_blitz_pipeline

        if not ADK_WORKFLOW_AVAILABLE:
            assert create_campaign_blitz_pipeline() is None

    def test_content_creation_accepts_max_refinements(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_content_creation_pipeline

        # Should not raise regardless of ADK availability
        result = create_content_creation_pipeline(max_refinements=5)
        if not ADK_WORKFLOW_AVAILABLE:
            assert result is None

    def test_campaign_blitz_accepts_max_iterations(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, create_campaign_blitz_pipeline

        result = create_campaign_blitz_pipeline(max_iterations=4)
        if not ADK_WORKFLOW_AVAILABLE:
            assert result is None


# ============================================================================
# Test WorkflowPipelineAgent
# ============================================================================


class TestWorkflowPipelineAgent:
    """Tests for WorkflowPipelineAgent DevSkyy wrapper."""

    def test_from_pipeline_factory(self):
        from adk.workflow_agents import PipelineType, WorkflowPipelineAgent

        agent = WorkflowPipelineAgent.from_pipeline(PipelineType.PRODUCT_LAUNCH)

        assert agent.name == "workflow_product_launch"
        assert agent._pipeline_type == PipelineType.PRODUCT_LAUNCH

    def test_from_pipeline_all_types(self):
        from adk.workflow_agents import PipelineType, WorkflowPipelineAgent

        for pipeline_type in PipelineType:
            agent = WorkflowPipelineAgent.from_pipeline(pipeline_type)
            assert agent.name == f"workflow_{pipeline_type.value}"
            assert agent._pipeline_type == pipeline_type

    def test_agent_config_provider(self):
        from adk.base import ADKProvider
        from adk.workflow_agents import PipelineType, WorkflowPipelineAgent

        agent = WorkflowPipelineAgent.from_pipeline(PipelineType.CUSTOMER_JOURNEY)

        assert agent.config.provider == ADKProvider.GOOGLE.value

    def test_agent_is_base_devskyy_agent(self):
        from adk.base import BaseDevSkyyAgent
        from adk.workflow_agents import PipelineType, WorkflowPipelineAgent

        agent = WorkflowPipelineAgent.from_pipeline(PipelineType.QUALITY_ASSURANCE)

        assert isinstance(agent, BaseDevSkyyAgent)

    def test_initialize_fails_without_adk(self):
        import asyncio

        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE, PipelineType, WorkflowPipelineAgent

        if not ADK_WORKFLOW_AVAILABLE:
            agent = WorkflowPipelineAgent.from_pipeline(PipelineType.PRODUCT_LAUNCH)
            with pytest.raises(ImportError, match="Google ADK not installed"):
                asyncio.get_event_loop().run_until_complete(agent.initialize())

    def test_agent_custom_model(self):
        from adk.workflow_agents import PipelineType, WorkflowPipelineAgent

        agent = WorkflowPipelineAgent.from_pipeline(
            PipelineType.CONTENT_CREATION,
            model="gemini-1.5-pro",
        )

        assert agent.config.model == "gemini-1.5-pro"


# ============================================================================
# Test Module Imports
# ============================================================================


class TestWorkflowModuleImports:
    """Test that workflow module exports are accessible from adk package."""

    def test_pipeline_type_import(self):
        from adk import PipelineType

        assert PipelineType is not None

    def test_token_savings_import(self):
        from adk import TokenSavings

        assert TokenSavings is not None

    def test_workflow_pipeline_agent_import(self):
        from adk import WorkflowPipelineAgent

        assert WorkflowPipelineAgent is not None

    def test_pipeline_factories_import(self):
        from adk import (
            create_campaign_blitz_pipeline,
            create_content_creation_pipeline,
            create_customer_journey_pipeline,
            create_product_launch_pipeline,
            create_quality_assurance_pipeline,
        )

        assert create_product_launch_pipeline is not None
        assert create_content_creation_pipeline is not None
        assert create_customer_journey_pipeline is not None
        assert create_quality_assurance_pipeline is not None
        assert create_campaign_blitz_pipeline is not None

    def test_utility_imports(self):
        from adk import estimate_pipeline_savings, get_pipeline

        assert get_pipeline is not None
        assert estimate_pipeline_savings is not None


# ============================================================================
# Test ADK Availability Flag
# ============================================================================


class TestADKAvailability:
    """Test the ADK availability flag."""

    def test_availability_flag_is_boolean(self):
        from adk.workflow_agents import ADK_WORKFLOW_AVAILABLE

        assert isinstance(ADK_WORKFLOW_AVAILABLE, bool)

    def test_module_loads_regardless_of_adk(self):
        """Module should import successfully even without google-adk."""
        import adk.workflow_agents

        assert hasattr(adk.workflow_agents, "PipelineType")
        assert hasattr(adk.workflow_agents, "WorkflowPipelineAgent")
        assert hasattr(adk.workflow_agents, "get_pipeline")
        assert hasattr(adk.workflow_agents, "estimate_pipeline_savings")


# ============================================================================
# Integration Smoke Tests (with ADK if available)
# ============================================================================


@pytest.mark.skipif(
    not __import__("adk.workflow_agents", fromlist=["ADK_WORKFLOW_AVAILABLE"]).ADK_WORKFLOW_AVAILABLE,
    reason="Google ADK not installed",
)
class TestWithADK:
    """Integration tests that only run when Google ADK is installed."""

    def test_product_launch_pipeline_structure(self):
        from adk.workflow_agents import create_product_launch_pipeline

        pipeline = create_product_launch_pipeline()

        assert pipeline is not None
        assert pipeline.name == "product_launch_pipeline"
        assert len(pipeline.sub_agents) == 5

    def test_content_creation_pipeline_structure(self):
        from adk.workflow_agents import create_content_creation_pipeline

        pipeline = create_content_creation_pipeline(max_refinements=2)

        assert pipeline is not None
        assert pipeline.name == "content_creation_pipeline"
        assert len(pipeline.sub_agents) == 3

    def test_customer_journey_pipeline_structure(self):
        from adk.workflow_agents import create_customer_journey_pipeline

        pipeline = create_customer_journey_pipeline()

        assert pipeline is not None
        assert pipeline.name == "customer_journey_pipeline"
        assert len(pipeline.sub_agents) == 3

    def test_quality_assurance_pipeline_structure(self):
        from adk.workflow_agents import create_quality_assurance_pipeline

        pipeline = create_quality_assurance_pipeline()

        assert pipeline is not None
        assert pipeline.name == "quality_assurance_pipeline"
        assert len(pipeline.sub_agents) == 2

    def test_campaign_blitz_pipeline_structure(self):
        from adk.workflow_agents import create_campaign_blitz_pipeline

        pipeline = create_campaign_blitz_pipeline(max_iterations=1)

        assert pipeline is not None
        assert pipeline.name == "campaign_blitz_pipeline"
        assert len(pipeline.sub_agents) == 4

    def test_leaf_agents_have_output_keys(self):
        from adk.workflow_agents import (
            _create_analytics_leaf,
            _create_commerce_leaf,
            _create_creative_leaf,
            _create_marketing_leaf,
            _create_operations_leaf,
            _create_support_leaf,
        )

        assert _create_commerce_leaf().output_key == "commerce_result"
        assert _create_creative_leaf().output_key == "creative_result"
        assert _create_marketing_leaf().output_key == "marketing_result"
        assert _create_support_leaf().output_key == "support_result"
        assert _create_operations_leaf().output_key == "operations_result"
        assert _create_analytics_leaf().output_key == "analytics_result"

    def test_leaf_agents_custom_output_key(self):
        from adk.workflow_agents import _create_commerce_leaf

        leaf = _create_commerce_leaf(output_key="custom_key")

        assert leaf.output_key == "custom_key"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
