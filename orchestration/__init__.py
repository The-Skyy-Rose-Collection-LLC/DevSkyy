"""
DevSkyy Orchestration Module
============================

Multi-agent orchestration and LLM management:
- LLM Registry: Model definitions and routing
- LLM Clients: Provider-specific API clients
- LLM Orchestrator: Intelligent model selection
- Tool Registry: Tool definitions and validation
- Prompt Engineering: Advanced prompting techniques
- LangGraph Integration: Multi-agent workflows

Usage:
    from orchestration import LLMOrchestrator, ToolRegistry

    # Get optimal model for task
    orchestrator = LLMOrchestrator()
    response = await orchestrator.complete(
        prompt="Analyze this fashion trend...",
        task_type="analysis",
        requirements={"speed": "fast", "quality": "high"}
    )

    # Register and use tools
    registry = ToolRegistry()
    tool = registry.get_tool("web_search")
    result = await tool.execute(query="luxury streetwear trends")
"""

from .langgraph_integration import (
    AgentNode,
    WorkflowEdge,
    WorkflowManager,
    WorkflowState,
)
from .llm_clients import (
    AnthropicClient,
    BaseLLMClient,
    CohereClient,
    GoogleClient,
    GroqClient,
    MistralClient,
    OpenAIClient,
)
from .llm_orchestrator import (
    CompletionResult,
    LLMOrchestrator,
    RoutingStrategy,
    TaskType,
)
from .llm_registry import (
    LLMRegistry,
    ModelCapability,
    ModelDefinition,
    ModelProvider,
    ModelTier,
)
from .prompt_engineering import (
    PromptChain,
    PromptEngineer,
    PromptTechnique,
    PromptTemplate,
)
from .tool_registry import (
    ToolCategory,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
)

__all__ = [
    # LLM Registry
    "LLMRegistry",
    "ModelDefinition",
    "ModelCapability",
    "ModelProvider",
    "ModelTier",
    # LLM Clients
    "BaseLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "GoogleClient",
    "MistralClient",
    "CohereClient",
    "GroqClient",
    # LLM Orchestrator
    "LLMOrchestrator",
    "TaskType",
    "RoutingStrategy",
    "CompletionResult",
    # Tool Registry
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "ToolParameter",
    # Prompt Engineering
    "PromptEngineer",
    "PromptTechnique",
    "PromptTemplate",
    "PromptChain",
    # LangGraph
    "WorkflowManager",
    "AgentNode",
    "WorkflowState",
    "WorkflowEdge",
]
