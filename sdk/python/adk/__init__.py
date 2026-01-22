"""
DevSkyy Agent Development Kit (ADK) Integration
===============================================

Enterprise-grade multi-framework agent system integrating:
- Google ADK (v1.20.0) - Production-grade multi-agent framework
- PydanticAI (v1.30.1) - Type-safe agent framework
- CrewAI (v1.6.1) - Role-based collaboration
- AutoGen (v0.7.5) - Microsoft's actor-model agents
- Agno (v2.3.11) - Ultra-fast lightweight agents
- LangGraph (v1.0.4) - Graph-based workflows

For SkyyRose: Where Love Meets Luxury

Usage:
    from adk import CommerceAgent, SuperAgentOrchestrator

    # Create and use super agent
    commerce = CommerceAgent()
    await commerce.initialize()
    result = await commerce.run("Check inventory for BLACK ROSE jacket")

    # Or use orchestrator for intelligent routing
    orchestrator = SuperAgentOrchestrator()
    await orchestrator.initialize()
    result = await orchestrator.route("Generate marketing content for new collection")
"""

# Agno integration
from adk.agno_adk import AgnoAgent, create_agno_agent

# AutoGen integration
from adk.autogen_adk import AutoGenAgent, create_autogen_team

# Base classes
from adk.base import (
    ADKProvider,
    AgentCapability,
    AgentConfig,
    AgentFactory,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    ModelTier,
    ToolCallResult,
    ToolDefinition,
    agent_factory,
    estimate_cost,
    get_api_key,
)

# CrewAI integration
from adk.crewai_adk import CrewAIAgent, create_crew

# Google ADK integration
from adk.google_adk import GoogleADKAgent, GoogleMultiAgent, create_google_agent

# PydanticAI integration
from adk.pydantic_adk import (
    ContentPlan,
    ContentPlannerAgent,
    CustomerIntent,
    CustomerIntentAgent,
    InventoryForecast,
    ProductAnalysis,
    ProductAnalyzerAgent,
    PydanticAIAgent,
    create_pydantic_agent,
    create_structured_agent,
)

# Super Agents (consolidated 6-agent architecture)
from adk.super_agents import (
    AnalyticsAgent,
    BaseSuperAgent,
    CommerceAgent,
    CreativeAgent,
    MarketingAgent,
    OperationsAgent,
    SuperAgentOrchestrator,
    SuperAgentType,
    SupportAgent,
    create_super_agent,
)

__all__ = [
    # Base classes
    "ADKProvider",
    "AgentCapability",
    "AgentConfig",
    "AgentFactory",
    "AgentResult",
    "AgentStatus",
    "BaseDevSkyyAgent",
    "ModelTier",
    "ToolCallResult",
    "ToolDefinition",
    "agent_factory",
    "estimate_cost",
    "get_api_key",
    # Super Agents
    "SuperAgentType",
    "BaseSuperAgent",
    "CommerceAgent",
    "CreativeAgent",
    "MarketingAgent",
    "SupportAgent",
    "OperationsAgent",
    "AnalyticsAgent",
    "SuperAgentOrchestrator",
    "create_super_agent",
    # PydanticAI
    "PydanticAIAgent",
    "ProductAnalysis",
    "CustomerIntent",
    "ContentPlan",
    "InventoryForecast",
    "ProductAnalyzerAgent",
    "CustomerIntentAgent",
    "ContentPlannerAgent",
    "create_pydantic_agent",
    "create_structured_agent",
    # CrewAI
    "CrewAIAgent",
    "create_crew",
    # AutoGen
    "AutoGenAgent",
    "create_autogen_team",
    # Agno
    "AgnoAgent",
    "create_agno_agent",
    # Google ADK
    "GoogleADKAgent",
    "GoogleMultiAgent",
    "create_google_agent",
]

__version__ = "1.0.0"
