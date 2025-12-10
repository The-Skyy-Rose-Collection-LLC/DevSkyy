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

from .llm_registry import (
    LLMRegistry,
    ModelDefinition,
    ModelCapability,
    ModelProvider,
    ModelTier,
)

from .llm_clients import (
    BaseLLMClient,
    OpenAIClient,
    AnthropicClient,
    GoogleClient,
    MistralClient,
    CohereClient,
    GroqClient,
)

from .llm_orchestrator import (
    LLMOrchestrator,
    TaskType,
    RoutingStrategy,
    CompletionResult,
)

from .tool_registry import (
    ToolRegistry,
    ToolDefinition,
    ToolCategory,
    ToolParameter,
)

from .prompt_engineering import (
    PromptEngineer,
    PromptTechnique,
    PromptTemplate,
    PromptChain,
)

from .langgraph_integration import (
    WorkflowManager,
    AgentNode,
    WorkflowState,
    WorkflowEdge,
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
