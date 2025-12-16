"""
Agno Integration
================

Integration with Agno v2.3.11 - Ultra-fast lightweight agent framework.

Features:
- Microsecond instantiation (50x faster than alternatives)
- 50x less memory usage
- Native multimodal support
- Automatic FastAPI generation
- Built-in reasoning and memory
- MCP tool integration

Reference: https://docs.agno.dev/
"""

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from adk.base import (
    ADKProvider,
    AgentCapability,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    ToolDefinition,
    agent_factory,
    estimate_cost,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Agno Tool Models
# =============================================================================


class AgnoTool(BaseModel):
    """Tool definition for Agno agents"""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    func: str | None = Field(None, description="Function path")
    parameters: dict[str, Any] = Field(default_factory=dict)


class AgnoMemoryConfig(BaseModel):
    """Memory configuration for Agno agents"""

    enable: bool = Field(True, description="Enable memory")
    memory_type: str = Field("buffer", description="buffer, summary, vector")
    max_messages: int = Field(20, description="Max messages to retain")
    persist: bool = Field(False, description="Persist to storage")


# =============================================================================
# Agno Agent
# =============================================================================


class AgnoAgent(BaseDevSkyyAgent):
    """
    Agent using Agno framework.

    Features:
    - Ultra-fast instantiation (microseconds)
    - Minimal memory footprint
    - Native multimodal (text, image, audio)
    - Automatic API generation
    - Built-in reasoning modes
    - MCP tool support

    Example:
        agent = AgnoAgent(config)
        result = await agent.run("Analyze this product image")

    Performance:
        - 50x faster than LangGraph
        - 50x less memory
        - Production-ready out of the box
    """

    def __init__(
        self,
        config: AgentConfig,
        memory_config: AgnoMemoryConfig | None = None,
        reasoning: bool = False,
    ):
        super().__init__(config)
        self.memory_config = memory_config or AgnoMemoryConfig()
        self.reasoning = reasoning
        self._agno_agent = None
        self._model = None

    async def initialize(self) -> None:
        """Initialize Agno agent"""
        try:
            from agno.agent import Agent
            from agno.models.openai import OpenAIChat

            # Create model
            self._model = self._create_model()

            # Build tools
            tools = self._build_tools()

            # Create agent
            agent_kwargs = {
                "name": self.config.name,
                "model": self._model,
                "instructions": self.config.system_prompt or self._default_instructions(),
                "markdown": True,
            }

            if tools:
                agent_kwargs["tools"] = tools

            if self.reasoning:
                agent_kwargs["reasoning"] = True

            if self.memory_config.enable:
                agent_kwargs["add_history_to_messages"] = True
                agent_kwargs["num_history_responses"] = self.memory_config.max_messages

            self._agno_agent = Agent(**agent_kwargs)

            logger.info(f"Agno agent initialized: {self.name} (ultra-fast mode)")

        except ImportError as e:
            logger.warning(f"Agno not available: {e}")
            raise ImportError("Agno not installed. Install with: pip install agno") from e
        except Exception as e:
            logger.error(f"Failed to initialize Agno agent: {e}")
            raise

    def _create_model(self):
        """Create Agno model"""
        model = self.config.model.lower()

        try:
            # OpenAI models
            if "gpt" in model or "openai" in model:
                from agno.models.openai import OpenAIChat

                model_id = "gpt-4o-mini"
                if "gpt-4o" in model and "mini" not in model:
                    model_id = "gpt-4o"
                elif "gpt-4-turbo" in model:
                    model_id = "gpt-4-turbo"
                elif "o1" in model:
                    model_id = "o1-preview"

                return OpenAIChat(id=model_id)

            # Anthropic models
            elif "claude" in model or "anthropic" in model:
                from agno.models.anthropic import Claude

                model_id = "claude-3-5-sonnet-20241022"
                if "opus" in model:
                    model_id = "claude-3-opus-20240229"
                elif "haiku" in model:
                    model_id = "claude-3-haiku-20240307"

                return Claude(id=model_id)

            # Google models
            elif "gemini" in model:
                from agno.models.google import Gemini

                model_id = "gemini-2.0-flash-exp"
                if "pro" in model:
                    model_id = "gemini-1.5-pro"

                return Gemini(id=model_id)

            # Groq models (fast inference)
            elif "groq" in model or "llama" in model:
                from agno.models.groq import Groq

                model_id = "llama-3.1-70b-versatile"
                if "8b" in model:
                    model_id = "llama-3.1-8b-instant"

                return Groq(id=model_id)

            # Mistral models
            elif "mistral" in model:
                from agno.models.mistral import MistralChat

                return MistralChat(id="mistral-large-latest")

            # Default to OpenAI
            else:
                from agno.models.openai import OpenAIChat

                return OpenAIChat(id="gpt-4o-mini")

        except ImportError as e:
            logger.warning(f"Model provider not available: {e}")
            from agno.models.openai import OpenAIChat

            return OpenAIChat(id="gpt-4o-mini")

    def _build_tools(self) -> list:
        """Build Agno tools from config"""
        tools = []

        for tool_def in self.config.tools:
            # Create tool function
            def make_tool(td):
                def tool_func(**kwargs):
                    return f"Tool {td.name} executed with: {kwargs}"

                tool_func.__name__ = td.name
                tool_func.__doc__ = td.description
                return tool_func

            tools.append(make_tool(tool_def))

        return tools

    def _default_instructions(self) -> str:
        """Default instructions for SkyyRose"""
        return f"""You are an ultra-efficient AI assistant for SkyyRose luxury streetwear.

{self.config.brand_context}

Core capabilities:
- Lightning-fast responses
- Multimodal understanding
- Data analysis
- Creative content

Guidelines:
- Be concise and impactful
- Maintain luxury brand voice
- Focus on actionable insights
- Optimize for speed and accuracy
"""

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute Agno agent"""
        start_time = datetime.now(UTC)

        try:
            # Handle multimodal input
            images = kwargs.get("images", [])
            audio = kwargs.get("audio")

            # Run agent
            if images:
                response = self._agno_agent.run(prompt, images=images)
            elif audio:
                response = self._agno_agent.run(prompt, audio=audio)
            else:
                response = self._agno_agent.run(prompt)

            # Extract content
            content = ""
            if hasattr(response, "content"):
                content = response.content
            elif hasattr(response, "messages"):
                for msg in response.messages:
                    if hasattr(msg, "content"):
                        content += msg.content
            else:
                content = str(response)

            # Get usage metrics
            input_tokens = 0
            output_tokens = 0

            if hasattr(response, "metrics"):
                metrics = response.metrics
                input_tokens = getattr(metrics, "input_tokens", 0)
                output_tokens = getattr(metrics, "output_tokens", 0)

            if input_tokens == 0:
                input_tokens = int(len(prompt.split()) * 1.3)
            if output_tokens == 0:
                output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AGNO,
                content=content,
                status=AgentStatus.COMPLETED,
                iterations=1,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=estimate_cost(
                    self.config.model,
                    input_tokens,
                    output_tokens,
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"Agno execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AGNO,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )

    async def run_with_image(self, prompt: str, image_path: str) -> AgentResult:
        """Run agent with image input"""
        return await self.run(prompt, images=[image_path])

    async def run_with_audio(self, prompt: str, audio_path: str) -> AgentResult:
        """Run agent with audio input"""
        return await self.run(prompt, audio=audio_path)

    def print_response(self, prompt: str, stream: bool = True) -> None:
        """Print response to console (synchronous)"""
        if not self._initialized:
            import asyncio

            asyncio.run(self.initialize())
            self._initialized = True

        self._agno_agent.print_response(prompt, stream=stream)


# =============================================================================
# Agno Team
# =============================================================================


class AgnoTeam(BaseDevSkyyAgent):
    """
    Multi-agent team using Agno.

    Features:
    - Ultra-fast team coordination
    - Minimal overhead
    - Parallel execution
    - Shared context

    Example:
        team = AgnoTeam(
            config,
            agents=[
                {"name": "researcher", "instructions": "..."},
                {"name": "writer", "instructions": "..."},
            ]
        )
        result = await team.run("Research and write about SkyyRose")
    """

    def __init__(
        self,
        config: AgentConfig,
        agent_configs: list[dict],
        mode: str = "coordinate",  # coordinate, parallel
    ):
        super().__init__(config)
        self.agent_configs = agent_configs
        self.mode = mode
        self._agents = []
        self._team = None

    async def initialize(self) -> None:
        """Initialize Agno team"""
        try:
            from agno.agent import Agent
            from agno.models.openai import OpenAIChat
            from agno.team import Team

            # Create model
            model = OpenAIChat(id="gpt-4o-mini")

            # Create agents
            for agent_config in self.agent_configs:
                agent = Agent(
                    name=agent_config.get("name", "agent"),
                    model=model,
                    instructions=agent_config.get("instructions", "Be helpful"),
                    markdown=True,
                )
                self._agents.append(agent)

            # Create team
            self._team = Team(
                name=self.config.name,
                agents=self._agents,
                mode=self.mode,
            )

            logger.info(f"Agno team initialized with {len(self._agents)} agents")

        except ImportError as e:
            raise ImportError("Agno not installed") from e

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute Agno team"""
        start_time = datetime.now(UTC)

        try:
            # Run team
            response = self._team.run(prompt)

            # Extract content
            content = ""
            content = response.content if hasattr(response, "content") else str(response)

            input_tokens = int(len(prompt.split()) * 1.3)
            output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AGNO,
                content=content,
                status=AgentStatus.COMPLETED,
                iterations=len(self._agents),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=estimate_cost(
                    self.config.model,
                    input_tokens,
                    output_tokens,
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"Agno team execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AGNO,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# Specialized Agno Agents
# =============================================================================


class AgnoReasoningAgent(AgnoAgent):
    """Agno agent with chain-of-thought reasoning"""

    def __init__(self, config: AgentConfig):
        super().__init__(config, reasoning=True)


class AgnoVisionAgent(AgnoAgent):
    """Agno agent optimized for image analysis"""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="vision_agent",
                provider=ADKProvider.AGNO,
                model="gpt-4o",  # Vision-capable
                system_prompt="""You are a visual analyst for SkyyRose luxury streetwear.

Analyze images for:
- Product quality and aesthetics
- Brand consistency
- Marketing potential
- Style recommendations

Provide detailed, actionable visual insights.
""",
                capabilities=[AgentCapability.VISION],
            )
        super().__init__(config)


class AgnoSpeedAgent(AgnoAgent):
    """Ultra-fast Agno agent using Groq"""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="speed_agent",
                provider=ADKProvider.AGNO,
                model="groq/llama-3.1-70b-versatile",
                system_prompt="""You are a high-speed assistant for SkyyRose.

Prioritize:
- Speed and efficiency
- Concise responses
- Actionable insights

Respond quickly and accurately.
""",
            )
        super().__init__(config)


# =============================================================================
# Factory Functions
# =============================================================================


def create_agno_agent(
    name: str,
    system_prompt: str = "",
    model: str = "gpt-4o-mini",
    reasoning: bool = False,
    tools: list = None,
    **kwargs,
) -> AgnoAgent:
    """
    Create an Agno agent.

    Args:
        name: Agent name
        system_prompt: Instructions
        model: Model to use
        reasoning: Enable chain-of-thought
        tools: Tool definitions
        **kwargs: Additional config

    Returns:
        AgnoAgent instance
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
        provider=ADKProvider.AGNO,
        model=model,
        system_prompt=system_prompt,
        tools=tool_defs,
        **kwargs,
    )

    return AgnoAgent(config, reasoning=reasoning)


def create_agno_team(
    name: str,
    agents: list[dict],
    mode: str = "coordinate",
    model: str = "gpt-4o-mini",
    **kwargs,
) -> AgnoTeam:
    """
    Create an Agno team.

    Args:
        name: Team name
        agents: List of agent configs
        mode: coordinate or parallel
        model: Model to use
        **kwargs: Additional config

    Returns:
        AgnoTeam instance
    """
    config = AgentConfig(
        name=name,
        provider=ADKProvider.AGNO,
        model=model,
        **kwargs,
    )

    return AgnoTeam(config, agents, mode)


# Pre-built SkyyRose Agno agents
def create_fast_responder() -> AgnoSpeedAgent:
    """Create ultra-fast responder for SkyyRose"""
    return AgnoSpeedAgent()


def create_visual_analyst() -> AgnoVisionAgent:
    """Create visual analyst for SkyyRose"""
    return AgnoVisionAgent()


def create_reasoning_agent() -> AgnoReasoningAgent:
    """Create reasoning agent for complex analysis"""
    config = AgentConfig(
        name="reasoner",
        provider=ADKProvider.AGNO,
        model="gpt-4o",
        system_prompt="""You are an analytical agent for SkyyRose.

Use step-by-step reasoning to:
- Analyze complex business problems
- Evaluate multiple options
- Provide well-reasoned recommendations

Show your thinking process clearly.
""",
    )
    return AgnoReasoningAgent(config)


# Register with factory
agent_factory.register(ADKProvider.AGNO, AgnoAgent)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Models
    "AgnoTool",
    "AgnoMemoryConfig",
    # Agents
    "AgnoAgent",
    "AgnoTeam",
    "AgnoReasoningAgent",
    "AgnoVisionAgent",
    "AgnoSpeedAgent",
    # Factory
    "create_agno_agent",
    "create_agno_team",
    # Pre-built
    "create_fast_responder",
    "create_visual_analyst",
    "create_reasoning_agent",
]
