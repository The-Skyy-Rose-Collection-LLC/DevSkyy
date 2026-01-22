"""
PydanticAI Integration
======================

Integration with PydanticAI v1.30.1 - Type-safe GenAI agent framework.

Features:
- Full type safety with Pydantic validation
- Structured output generation
- Tool decorators with automatic schema
- Multi-model support (OpenAI, Anthropic, Google, etc.)
- Streaming with validation
- MCP and A2A protocol support

Reference: https://ai.pydantic.dev/
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from adk.base import (
    ADKProvider,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    ToolCallResult,
    ToolDefinition,
    agent_factory,
    estimate_cost,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# =============================================================================
# Structured Output Models for SkyyRose
# =============================================================================


class ProductAnalysis(BaseModel):
    """Structured output for product analysis"""

    product_name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    price_recommendation: float = Field(..., description="Recommended price USD")
    target_audience: list[str] = Field(default_factory=list, description="Target demographics")
    marketing_angles: list[str] = Field(default_factory=list, description="Marketing angles")
    seo_keywords: list[str] = Field(default_factory=list, description="SEO keywords")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class CustomerIntent(BaseModel):
    """Structured output for customer intent analysis"""

    intent: str = Field(..., description="Primary intent")
    sentiment: str = Field(..., description="Sentiment: positive/negative/neutral")
    urgency: str = Field(..., description="Urgency: low/medium/high")
    topics: list[str] = Field(default_factory=list, description="Topics mentioned")
    suggested_action: str = Field(..., description="Recommended action")
    escalate: bool = Field(False, description="Should escalate to human")


class ContentPlan(BaseModel):
    """Structured output for content planning"""

    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Type: blog/social/email/ad")
    platform: str = Field(..., description="Target platform")
    key_messages: list[str] = Field(default_factory=list, description="Key messages")
    call_to_action: str = Field(..., description="Primary CTA")
    hashtags: list[str] = Field(default_factory=list, description="Suggested hashtags")
    optimal_length: int = Field(0, description="Optimal word count")


class InventoryForecast(BaseModel):
    """Structured output for inventory forecasting"""

    product_id: str = Field(..., description="Product ID")
    current_stock: int = Field(0, description="Current stock level")
    predicted_demand: int = Field(0, description="30-day demand forecast")
    reorder_point: int = Field(0, description="Recommended reorder point")
    reorder_quantity: int = Field(0, description="Recommended order quantity")
    stockout_risk: str = Field(..., description="Risk level: low/medium/high")
    confidence: float = Field(0.0, ge=0.0, le=1.0)


# =============================================================================
# PydanticAI Agent
# =============================================================================


class PydanticAIAgent(BaseDevSkyyAgent, Generic[T]):
    """
    Agent using PydanticAI framework.

    Features:
    - Type-safe outputs with Pydantic models
    - Automatic tool schema generation
    - Multi-model support
    - Streaming with validation
    - Dependencies injection

    Example:
        agent = PydanticAIAgent[ProductAnalysis](
            config,
            output_type=ProductAnalysis
        )
        result = await agent.run("Analyze BLACK ROSE hoodie")
        analysis: ProductAnalysis = result.structured_output

    Note: Requires API key for chosen model provider
    """

    def __init__(
        self,
        config: AgentConfig,
        output_type: type[T] | None = None,
        deps_type: type | None = None,
    ):
        super().__init__(config)
        self.output_type = output_type
        self.deps_type = deps_type
        self._pydantic_agent = None
        self._tool_handlers: dict[str, Callable] = {}

    async def initialize(self) -> None:
        """Initialize PydanticAI agent"""
        try:
            from pydantic_ai import Agent

            # Determine model string
            model_string = self._get_model_string()

            # Create agent with optional structured output
            agent_kwargs = {
                "model": model_string,
                "system_prompt": self.config.system_prompt or self._default_instruction(),
            }

            if self.output_type:
                agent_kwargs["output_type"] = self.output_type

            if self.deps_type:
                agent_kwargs["deps_type"] = self.deps_type

            self._pydantic_agent = Agent(**agent_kwargs)

            # Register tools
            for tool_def in self.config.tools:
                self._register_pydantic_tool(tool_def)

            logger.info(f"PydanticAI agent initialized: {self.name}")

        except ImportError as e:
            logger.warning(f"PydanticAI not available: {e}")
            raise ImportError(
                "PydanticAI not installed. Install with: pip install pydantic-ai"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize PydanticAI agent: {e}")
            raise

    def _get_model_string(self) -> str:
        """Get PydanticAI model string"""
        model = self.config.model.lower()

        # PydanticAI model format: provider:model-name
        if ":" in self.config.model:
            return self.config.model

        # Map to PydanticAI format
        if "gpt-4o" in model:
            return "openai:gpt-4o"
        elif "gpt-4o-mini" in model or "gpt-4-mini" in model:
            return "openai:gpt-4o-mini"
        elif "gpt-4-turbo" in model:
            return "openai:gpt-4-turbo"
        elif "claude-3-5-sonnet" in model or "claude-sonnet" in model:
            return "anthropic:claude-sonnet-4-0"
        elif "claude-3-opus" in model or "claude-opus" in model:
            return "anthropic:claude-opus-4-0"
        elif "claude-3-haiku" in model or "claude-haiku" in model:
            return "anthropic:claude-3-5-haiku-latest"
        elif "gemini" in model:
            if "flash" in model:
                return "google-gla:gemini-2.0-flash"
            return "google-gla:gemini-1.5-pro"
        elif "mistral" in model:
            return "mistral:mistral-large-latest"
        elif "groq" in model or "llama" in model:
            return "groq:llama-3.1-70b-versatile"

        # Default
        return "openai:gpt-4o-mini"

    def _default_instruction(self) -> str:
        """Default system prompt for SkyyRose"""
        return f"""You are an AI assistant for SkyyRose luxury streetwear.

{self.config.brand_context}

Your responsibilities:
- Provide accurate, helpful information about products
- Maintain the luxury brand voice
- Analyze data with precision
- Generate structured, actionable insights

Always be professional, concise, and focused on value delivery.
"""

    def _register_pydantic_tool(self, tool_def: ToolDefinition) -> None:
        """
        Register a tool with PydanticAI agent.

        Uses ToolRegistry as the single source of truth for tool handlers.
        If no handler is registered in ToolRegistry, creates a handler
        that routes to the ToolRegistry.execute() method.
        """
        if not self._pydantic_agent:
            return

        # Import ToolRegistry here to avoid circular imports
        from core.runtime.tool_registry import ToolCallContext, get_tool_registry

        tool_registry = get_tool_registry()
        tool_name = tool_def.name

        # Check if tool exists in ToolRegistry
        if tool_def.name in self._tools:
            # Use the explicitly registered handler
            handler = self._tools[tool_def.name]
        elif tool_registry.get(tool_name):
            # Tool exists in ToolRegistry - create handler that routes to it
            async def registry_handler(**kwargs):
                """Handler that routes to ToolRegistry."""
                context = ToolCallContext(
                    agent_id=self.name,
                    metadata={"source": "pydantic_adk"},
                )
                result = await tool_registry.execute(tool_name, kwargs, context)
                if result.success:
                    return result.result
                else:
                    raise RuntimeError(f"Tool execution failed: {result.error}")

            handler = registry_handler
        else:
            # Tool not in registry - register it and create forwarding handler
            from core.runtime.tool_registry import ToolCategory, ToolSeverity, ToolSpec

            # Create spec from tool definition
            spec = ToolSpec(
                name=tool_name,
                description=tool_def.description,
                category=ToolCategory.AI,  # Default category for dynamic tools
                severity=ToolSeverity.LOW,
                input_schema=tool_def.parameters or {},
            )

            # Create the forwarding handler
            async def dynamic_handler(**kwargs):
                """Dynamic handler for tools without explicit implementation."""
                # Try to get handler from registry in case it was registered later
                reg_handler = tool_registry.get_handler(tool_name)
                if reg_handler:
                    import inspect

                    if inspect.iscoroutinefunction(reg_handler):
                        return await reg_handler(**kwargs)
                    return reg_handler(**kwargs)

                # No handler available - log and return structured response
                logger.warning(f"No handler for tool {tool_name}, returning parameter echo")
                return {
                    "tool": tool_name,
                    "status": "no_handler",
                    "params_received": kwargs,
                }

            # Register the spec (without handler - handler registered separately)
            tool_registry.register(spec, dynamic_handler)
            handler = dynamic_handler

        # Register with PydanticAI decorator
        @self._pydantic_agent.tool
        async def tool_wrapper(**kwargs):
            return await handler(**kwargs)

        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = tool_def.description

        self._tool_handlers[tool_name] = tool_wrapper

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute PydanticAI agent"""
        start_time = datetime.now(UTC)
        tool_calls: list[ToolCallResult] = []

        try:
            # Get dependencies if provided
            deps = kwargs.get("deps")

            # Run agent
            if deps is not None:
                result = await self._pydantic_agent.run(prompt, deps=deps)
            else:
                result = await self._pydantic_agent.run(prompt)

            # Extract content
            if self.output_type and hasattr(result, "data"):
                content = str(result.data)
                structured = (
                    result.data.model_dump() if hasattr(result.data, "model_dump") else None
                )
            else:
                content = str(result.data) if hasattr(result, "data") else str(result)
                structured = None

            # Get usage stats
            usage = getattr(result, "usage", None)
            input_tokens = (
                getattr(usage, "request_tokens", 0) if usage else len(prompt.split()) * 1.3
            )
            output_tokens = (
                getattr(usage, "response_tokens", 0) if usage else len(content.split()) * 1.3
            )

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.PYDANTIC,
                content=content,
                structured_output=structured,
                status=AgentStatus.COMPLETED,
                iterations=1,
                tool_calls=tool_calls,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens),
                cost_usd=estimate_cost(
                    self.config.model,
                    int(input_tokens),
                    int(output_tokens),
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"PydanticAI execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.PYDANTIC,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )

    async def run_sync(self, prompt: str, **kwargs) -> AgentResult:
        """Synchronous execution wrapper"""
        return await self.run(prompt, **kwargs)

    async def stream(self, prompt: str, **kwargs):
        """Stream response with validation"""
        if not self._initialized:
            await self.initialize()
            self._initialized = True

        try:
            deps = kwargs.get("deps")

            if deps is not None:
                async with self._pydantic_agent.run_stream(prompt, deps=deps) as stream:
                    async for chunk in stream.stream_text():
                        yield chunk
            else:
                async with self._pydantic_agent.run_stream(prompt) as stream:
                    async for chunk in stream.stream_text():
                        yield chunk

        except Exception as e:
            logger.error(f"PydanticAI streaming failed: {e}")
            yield f"Error: {e}"


# =============================================================================
# Specialized PydanticAI Agents
# =============================================================================


class ProductAnalyzerAgent(PydanticAIAgent[ProductAnalysis]):
    """Specialized agent for product analysis"""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="product_analyzer",
                provider=ADKProvider.PYDANTIC,
                model="openai:gpt-4o-mini",
                system_prompt="""You are a luxury streetwear product analyst for SkyyRose.

Analyze products considering:
- Market positioning and pricing
- Target demographics
- Marketing opportunities
- SEO optimization

Provide structured, data-driven insights.
""",
            )
        super().__init__(config, output_type=ProductAnalysis)


class CustomerIntentAgent(PydanticAIAgent[CustomerIntent]):
    """Specialized agent for customer intent analysis"""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="customer_intent",
                provider=ADKProvider.PYDANTIC,
                model="openai:gpt-4o-mini",
                system_prompt="""You are a customer service analyst for SkyyRose luxury streetwear.

Analyze customer messages to determine:
- Primary intent and sentiment
- Urgency level
- Topics of concern
- Recommended actions
- Whether to escalate

Be empathetic and solution-oriented.
""",
            )
        super().__init__(config, output_type=CustomerIntent)


class ContentPlannerAgent(PydanticAIAgent[ContentPlan]):
    """Specialized agent for content planning"""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="content_planner",
                provider=ADKProvider.PYDANTIC,
                model="openai:gpt-4o-mini",
                system_prompt="""You are a content strategist for SkyyRose luxury streetwear.

Create content plans considering:
- Brand voice: sophisticated, bold, emotionally resonant
- Target platforms: Instagram, TikTok, email, blog
- Key collections: BLACK ROSE, LOVE HURTS, SIGNATURE
- Engagement optimization

Focus on driving conversions while building brand equity.
""",
            )
        super().__init__(config, output_type=ContentPlan)


# =============================================================================
# Factory Functions
# =============================================================================


def create_pydantic_agent(
    name: str,
    system_prompt: str = "",
    model: str = "openai:gpt-4o-mini",
    output_type: type[BaseModel] | None = None,
    tools: list = None,
    **kwargs,
) -> PydanticAIAgent:
    """
    Create a PydanticAI agent.

    Args:
        name: Agent name
        system_prompt: System instructions
        model: Model string (provider:model)
        output_type: Pydantic model for structured output
        tools: Tool definitions
        **kwargs: Additional config

    Returns:
        PydanticAIAgent instance

    Example:
        agent = create_pydantic_agent(
            name="analyzer",
            output_type=ProductAnalysis,
            model="anthropic:claude-sonnet-4-0"
        )
    """
    tool_defs = []
    if tools:
        for tool in tools:
            if isinstance(tool, dict):
                tool_defs.append(ToolDefinition(**tool))
            elif isinstance(tool, ToolDefinition):
                tool_defs.append(tool)

    config = AgentConfig(
        name=name,
        provider=ADKProvider.PYDANTIC,
        model=model,
        system_prompt=system_prompt,
        tools=tool_defs,
        **kwargs,
    )

    return PydanticAIAgent(config, output_type=output_type)


def create_structured_agent(
    name: str,
    output_model: type[T],
    system_prompt: str = "",
    model: str = "openai:gpt-4o-mini",
    **kwargs,
) -> PydanticAIAgent[T]:
    """
    Create a PydanticAI agent with structured output.

    Args:
        name: Agent name
        output_model: Pydantic model class for output
        system_prompt: System instructions
        model: Model string
        **kwargs: Additional config

    Returns:
        PydanticAIAgent with typed output
    """
    config = AgentConfig(
        name=name,
        provider=ADKProvider.PYDANTIC,
        model=model,
        system_prompt=system_prompt,
        **kwargs,
    )

    return PydanticAIAgent[T](config, output_type=output_model)


# Register with factory
agent_factory.register(ADKProvider.PYDANTIC, PydanticAIAgent)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Main agent
    "PydanticAIAgent",
    # Output models
    "ProductAnalysis",
    "CustomerIntent",
    "ContentPlan",
    "InventoryForecast",
    # Specialized agents
    "ProductAnalyzerAgent",
    "CustomerIntentAgent",
    "ContentPlannerAgent",
    # Factory
    "create_pydantic_agent",
    "create_structured_agent",
]
