"""
ADK Test Suite
==============

Comprehensive tests for DevSkyy Agent Development Kit.
"""

import sys

import pytest

sys.path.insert(0, "/home/claude/devskyy-platform")


# =============================================================================
# Test Base Module
# =============================================================================


class TestBaseModule:
    """Tests for adk.base module"""

    def test_adk_provider_enum(self):
        """Test ADK provider enumeration"""
        from adk.base import ADKProvider

        assert ADKProvider.GOOGLE == "google_adk"
        assert ADKProvider.PYDANTIC == "pydantic_ai"
        assert ADKProvider.CREWAI == "crewai"
        assert ADKProvider.AUTOGEN == "autogen"
        assert ADKProvider.AGNO == "agno"
        assert ADKProvider.LANGGRAPH == "langgraph"

    def test_agent_capability_enum(self):
        """Test agent capability enumeration"""
        from adk.base import AgentCapability

        assert AgentCapability.TEXT_GENERATION == "text_generation"
        assert AgentCapability.ECOMMERCE == "ecommerce"
        assert AgentCapability.THREE_D_GENERATION == "3d_generation"
        assert AgentCapability.VIRTUAL_TRYON == "virtual_tryon"

    def test_agent_config_creation(self):
        """Test AgentConfig model creation"""
        from adk.base import ADKProvider, AgentCapability, AgentConfig

        config = AgentConfig(
            name="test_agent",
            provider=ADKProvider.PYDANTIC,
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Test prompt",
            capabilities=[AgentCapability.TEXT_GENERATION],
        )

        assert config.name == "test_agent"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert len(config.capabilities) == 1

    def test_agent_config_defaults(self):
        """Test AgentConfig default values"""
        from adk.base import AgentConfig

        config = AgentConfig(name="minimal")

        assert config.provider == "pydantic_ai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.enable_memory is True

    def test_agent_result_creation(self):
        """Test AgentResult model creation"""
        from adk.base import ADKProvider, AgentResult, AgentStatus

        result = AgentResult(
            agent_name="test",
            agent_provider=ADKProvider.PYDANTIC,
            content="Test response",
            status=AgentStatus.COMPLETED,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        assert result.agent_name == "test"
        assert result.status == AgentStatus.COMPLETED
        assert result.total_tokens == 150

    def test_tool_definition(self):
        """Test ToolDefinition model"""
        from adk.base import ToolDefinition

        tool = ToolDefinition(
            name="search",
            description="Search products",
            parameters={"query": "string"},
            required_params=["query"],
        )

        assert tool.name == "search"
        assert "query" in tool.parameters
        assert tool.requires_confirmation is False

    def test_cost_estimation(self):
        """Test cost estimation function"""
        from adk.base import estimate_cost

        # Test GPT-4o-mini pricing
        cost_mini = estimate_cost("gpt-4o-mini", 1000, 500)
        assert cost_mini > 0
        assert cost_mini < 0.01  # Should be cheap for small usage

        # Test Claude pricing
        cost_claude = estimate_cost("claude-3-5-sonnet", 1000, 500)
        assert cost_claude > 0

        # Test unknown model uses default
        cost_unknown = estimate_cost("unknown-model", 1000, 500)
        assert cost_unknown > 0


# =============================================================================
# Test Super Agents
# =============================================================================


class TestSuperAgents:
    """Tests for super agent implementations"""

    def test_super_agent_type_enum(self):
        """Test SuperAgentType enumeration"""
        from adk.super_agents import SuperAgentType

        assert SuperAgentType.COMMERCE == "commerce"
        assert SuperAgentType.CREATIVE == "creative"
        assert SuperAgentType.MARKETING == "marketing"
        assert SuperAgentType.SUPPORT == "support"
        assert SuperAgentType.OPERATIONS == "operations"
        assert SuperAgentType.ANALYTICS == "analytics"

    def test_commerce_agent_creation(self):
        """Test CommerceAgent instantiation"""
        from adk.super_agents import CommerceAgent, SuperAgentType

        agent = CommerceAgent()

        assert agent.name == "commerce_agent"
        assert agent.agent_type == SuperAgentType.COMMERCE
        assert "product_management" in agent.sub_capabilities

    def test_creative_agent_creation(self):
        """Test CreativeAgent instantiation"""
        from adk.super_agents import CreativeAgent, SuperAgentType

        agent = CreativeAgent()

        assert agent.name == "creative_agent"
        assert agent.agent_type == SuperAgentType.CREATIVE
        assert "3d_generation" in agent.sub_capabilities
        assert "virtual_tryon" in agent.sub_capabilities

    def test_marketing_agent_creation(self):
        """Test MarketingAgent instantiation"""
        from adk.super_agents import MarketingAgent, SuperAgentType

        agent = MarketingAgent()

        assert agent.name == "marketing_agent"
        assert agent.agent_type == SuperAgentType.MARKETING
        assert "content_creation" in agent.sub_capabilities

    def test_support_agent_creation(self):
        """Test SupportAgent instantiation"""
        from adk.super_agents import SuperAgentType, SupportAgent

        agent = SupportAgent()

        assert agent.name == "support_agent"
        assert agent.agent_type == SuperAgentType.SUPPORT
        assert "customer_inquiries" in agent.sub_capabilities

    def test_operations_agent_creation(self):
        """Test OperationsAgent instantiation"""
        from adk.super_agents import OperationsAgent, SuperAgentType

        agent = OperationsAgent()

        assert agent.name == "operations_agent"
        assert agent.agent_type == SuperAgentType.OPERATIONS
        assert "wordpress_management" in agent.sub_capabilities

    def test_analytics_agent_creation(self):
        """Test AnalyticsAgent instantiation"""
        from adk.super_agents import AnalyticsAgent, SuperAgentType

        agent = AnalyticsAgent()

        assert agent.name == "analytics_agent"
        assert agent.agent_type == SuperAgentType.ANALYTICS
        assert "sales_reporting" in agent.sub_capabilities

    def test_orchestrator_creation(self):
        """Test SuperAgentOrchestrator instantiation"""
        from adk.super_agents import SuperAgentOrchestrator

        orchestrator = SuperAgentOrchestrator()

        assert orchestrator.agents == {}
        assert orchestrator._initialized is False

    def test_orchestrator_intent_classification(self):
        """Test intent classification routing"""
        from adk.super_agents import SuperAgentOrchestrator, SuperAgentType

        orchestrator = SuperAgentOrchestrator()

        # Commerce keywords
        assert orchestrator._classify_intent("Check order #12345") == SuperAgentType.COMMERCE
        assert orchestrator._classify_intent("Update product inventory") == SuperAgentType.COMMERCE

        # Creative keywords
        assert orchestrator._classify_intent("Generate 3D model") == SuperAgentType.CREATIVE
        assert orchestrator._classify_intent("Create virtual try-on") == SuperAgentType.CREATIVE

        # Marketing keywords
        assert (
            orchestrator._classify_intent("Create social media campaign")
            == SuperAgentType.MARKETING
        )

        # Support keywords
        assert orchestrator._classify_intent("Customer needs help") == SuperAgentType.SUPPORT

        # Operations keywords
        assert orchestrator._classify_intent("Deploy WordPress update") == SuperAgentType.OPERATIONS

        # Analytics keywords
        assert orchestrator._classify_intent("Generate sales report") == SuperAgentType.ANALYTICS

    def test_create_super_agent_factory(self):
        """Test create_super_agent factory function"""
        from adk.super_agents import SuperAgentType, create_super_agent

        commerce = create_super_agent(SuperAgentType.COMMERCE)
        assert commerce.name == "commerce_agent"

        creative = create_super_agent(SuperAgentType.CREATIVE)
        assert creative.name == "creative_agent"


# =============================================================================
# Test PydanticAI Integration
# =============================================================================


class TestPydanticAI:
    """Tests for PydanticAI integration"""

    def test_output_models(self):
        """Test Pydantic output models"""
        from adk.pydantic_adk import CustomerIntent, ProductAnalysis

        # Test ProductAnalysis
        analysis = ProductAnalysis(
            product_name="Black Rose Jacket",
            category="Outerwear",
            price_recommendation=299.99,
            target_audience=["luxury seekers", "streetwear enthusiasts"],
            marketing_angles=["luxury", "streetwear", "limited edition"],
            seo_keywords=["luxury jacket", "streetwear"],
            confidence=0.95,
        )
        assert analysis.product_name == "Black Rose Jacket"
        assert analysis.price_recommendation == 299.99

        # Test CustomerIntent
        intent = CustomerIntent(
            intent="purchase",
            sentiment="positive",
            urgency="medium",
            topics=["jacket", "size"],
            suggested_action="proceed with checkout assistance",
        )
        assert intent.sentiment == "positive"
        assert intent.escalate is False

    def test_pydantic_agent_creation(self):
        """Test PydanticAIAgent instantiation"""
        from adk.base import AgentConfig
        from adk.pydantic_adk import PydanticAIAgent

        config = AgentConfig(
            name="test_pydantic",
            model="gpt-4o-mini",
        )

        agent = PydanticAIAgent(config)
        assert agent.name == "test_pydantic"

    def test_create_pydantic_agent_factory(self):
        """Test create_pydantic_agent factory"""
        from adk.pydantic_adk import create_pydantic_agent

        agent = create_pydantic_agent(
            name="factory_test",
            system_prompt="Test prompt",
            model="gpt-4o-mini",
        )

        assert agent.name == "factory_test"


# =============================================================================
# Test Module Imports
# =============================================================================


class TestModuleImports:
    """Test that all modules import correctly"""

    def test_main_package_import(self):
        """Test main adk package import"""
        import adk

        assert hasattr(adk, "__version__")
        assert adk.__version__ == "1.0.0"

    def test_base_exports(self):
        """Test base module exports"""
        from adk import ADKProvider, AgentCapability, AgentConfig

        assert ADKProvider is not None
        assert AgentCapability is not None
        assert AgentConfig is not None

    def test_super_agent_exports(self):
        """Test super agent exports"""
        from adk import CommerceAgent, SuperAgentOrchestrator

        assert CommerceAgent is not None
        assert SuperAgentOrchestrator is not None

    def test_pydantic_exports(self):
        """Test PydanticAI exports"""
        from adk import PydanticAIAgent, create_pydantic_agent

        assert PydanticAIAgent is not None
        assert create_pydantic_agent is not None

    def test_crewai_exports(self):
        """Test CrewAI exports"""
        from adk import CrewAIAgent

        assert CrewAIAgent is not None

    def test_autogen_exports(self):
        """Test AutoGen exports"""
        from adk import AutoGenAgent

        assert AutoGenAgent is not None

    def test_agno_exports(self):
        """Test Agno exports"""
        from adk import AgnoAgent

        assert AgnoAgent is not None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
