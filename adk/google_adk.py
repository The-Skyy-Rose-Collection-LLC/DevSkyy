"""
Google ADK Integration
======================

Integration with Google's Agent Development Kit (ADK) v1.20.0

Features:
- Multi-agent hierarchies
- Tool confirmation (HITL)
- Session management
- Built-in streaming
- Vertex AI integration

Reference: https://google.github.io/adk-docs/
"""

import logging
from datetime import UTC, datetime
from typing import Any

from adk.base import (
    ADKProvider,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    ToolCallResult,
    agent_factory,
    estimate_cost,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Google ADK Agent
# =============================================================================


class GoogleADKAgent(BaseDevSkyyAgent):
    """
    Agent using Google's Agent Development Kit.

    Features:
    - Native Gemini integration
    - Multi-agent orchestration
    - Tool confirmation flows
    - Session state management
    - Built-in tracing

    Example:
        agent = GoogleADKAgent(config)
        result = await agent.run("Search for SkyyRose products")

    Note: Requires GOOGLE_API_KEY environment variable
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._adk_agent = None
        self._session = None
        self._runner = None

    async def initialize(self) -> None:
        """Initialize Google ADK agent"""
        try:
            from google.adk.agents import Agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService

            # Build tools list
            tools = []
            for tool_def in self.config.tools:
                # Convert to ADK tool format
                tools.append(self._create_adk_tool(tool_def))

            # Create agent
            self._adk_agent = Agent(
                name=self.config.name,
                model=self._get_model_string(),
                instruction=self.config.system_prompt or self._default_instruction(),
                description=self.config.description,
                tools=tools if tools else None,
            )

            # Create session service
            session_service = InMemorySessionService()

            # Create runner
            self._runner = Runner(
                agent=self._adk_agent,
                app_name="devskyy",
                session_service=session_service,
            )

            # Create session
            self._session = await session_service.create_session(
                app_name="devskyy",
                user_id="skyyrose",
            )

            logger.info(f"Google ADK agent initialized: {self.name}")

        except ImportError as e:
            logger.warning(f"Google ADK not available: {e}")
            raise ImportError(
                "Google ADK not installed. Install with: pip install google-adk"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Google ADK agent: {e}")
            raise

    def _get_model_string(self) -> str:
        """Get Google model string"""
        model = self.config.model.lower()

        # Map common model names to Gemini
        model_map = {
            "gpt-4o": "gemini-2.0-flash",
            "gpt-4o-mini": "gemini-2.0-flash",
            "claude-3-5-sonnet": "gemini-2.0-flash",
            "gemini-flash": "gemini-2.0-flash",
            "gemini-pro": "gemini-1.5-pro",
        }

        for key, value in model_map.items():
            if key in model:
                return value

        # Return as-is if already Gemini format
        if "gemini" in model:
            return model

        # Default
        return "gemini-2.0-flash"

    def _default_instruction(self) -> str:
        """Default system instruction for SkyyRose"""
        return f"""You are an AI assistant for SkyyRose, a luxury streetwear brand.

Brand Context:
{self.config.brand_context}

Collections:
- BLACK ROSE: Limited edition dark elegance pieces
- LOVE HURTS: Emotional expression collection
- SIGNATURE: Foundation wardrobe essentials

Guidelines:
- Maintain luxury brand voice
- Be helpful and professional
- Focus on customer satisfaction
- Emphasize quality and craftsmanship
"""

    def _create_adk_tool(self, tool_def) -> Any:
        """Create ADK tool from definition"""

        # For now, return function-based tools
        # In production, integrate with actual handlers
        def tool_handler(**kwargs):
            return f"Tool {tool_def.name} executed with: {kwargs}"

        tool_handler.__name__ = tool_def.name
        tool_handler.__doc__ = tool_def.description

        return tool_handler

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute Google ADK agent"""
        start_time = datetime.now(UTC)
        tool_calls = []

        try:
            from google.genai import types

            # Create content
            content = types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )

            # Run agent
            response_text = ""
            input_tokens = 0
            output_tokens = 0

            async for event in self._runner.run_async(
                user_id="skyyrose",
                session_id=self._session.id,
                new_message=content,
            ):
                # Handle different event types
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                response_text += part.text

                # Track tool calls
                if hasattr(event, "tool_calls"):
                    for tc in event.tool_calls:
                        tool_calls.append(
                            ToolCallResult(
                                tool_name=tc.name,
                                arguments=tc.args or {},
                                result=tc.result if hasattr(tc, "result") else None,
                                success=True,
                            )
                        )

                # Track usage
                if hasattr(event, "usage"):
                    input_tokens = getattr(event.usage, "input_tokens", 0)
                    output_tokens = getattr(event.usage, "output_tokens", 0)

            # Estimate tokens if not provided
            if input_tokens == 0:
                input_tokens = len(prompt.split()) * 1.3
            if output_tokens == 0:
                output_tokens = len(response_text.split()) * 1.3

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.GOOGLE,
                content=response_text or "No response generated",
                status=AgentStatus.COMPLETED,
                iterations=1,
                tool_calls=tool_calls,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens),
                cost_usd=estimate_cost(
                    self._get_model_string(),
                    int(input_tokens),
                    int(output_tokens),
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"Google ADK execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.GOOGLE,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# Multi-Agent Google ADK
# =============================================================================


class GoogleMultiAgent(BaseDevSkyyAgent):
    """
    Multi-agent system using Google ADK hierarchies.

    Supports:
    - Coordinator agents
    - Sub-agent delegation
    - Tool sharing
    - State management
    """

    def __init__(self, config: AgentConfig, sub_agents: list[AgentConfig] = None):
        super().__init__(config)
        self.sub_agent_configs = sub_agents or []
        self._coordinator = None
        self._sub_agents = {}

    async def initialize(self) -> None:
        """Initialize multi-agent system"""
        try:
            from google.adk.agents import Agent

            # Create sub-agents first
            sub_agent_instances = []
            for sub_config in self.sub_agent_configs:
                sub_agent = Agent(
                    name=sub_config.name,
                    model="gemini-2.0-flash",
                    instruction=sub_config.system_prompt,
                    description=sub_config.description,
                )
                self._sub_agents[sub_config.name] = sub_agent
                sub_agent_instances.append(sub_agent)

            # Create coordinator with sub-agents
            self._coordinator = Agent(
                name=self.config.name,
                model="gemini-2.0-flash",
                instruction=self.config.system_prompt or self._coordinator_instruction(),
                description="Coordinator agent for SkyyRose operations",
                sub_agents=sub_agent_instances if sub_agent_instances else None,
            )

            logger.info(
                f"Google Multi-Agent initialized: {self.name} with {len(self._sub_agents)} sub-agents"
            )

        except ImportError as e:
            raise ImportError("Google ADK not available") from e

    def _coordinator_instruction(self) -> str:
        return """You are the coordinator for SkyyRose AI operations.

Delegate tasks to appropriate sub-agents:
- Commerce Agent: Product, orders, inventory
- Creative Agent: 3D assets, images, virtual try-on
- Marketing Agent: Content, campaigns, SEO
- Support Agent: Customer service, tickets
- Operations Agent: WordPress, deployment
- Analytics Agent: Reports, forecasting

Route each request to the most appropriate agent.
Synthesize responses when multiple agents are involved.
"""

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute multi-agent workflow"""
        start_time = datetime.now(UTC)

        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            # Create session
            session_service = InMemorySessionService()
            runner = Runner(
                agent=self._coordinator,
                app_name="devskyy",
                session_service=session_service,
            )

            session = await session_service.create_session(
                app_name="devskyy",
                user_id="skyyrose",
            )

            # Execute
            content = types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )

            response_text = ""
            async for event in runner.run_async(
                user_id="skyyrose",
                session_id=session.id,
                new_message=content,
            ):
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                response_text += part.text

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.GOOGLE,
                content=response_text,
                status=AgentStatus.COMPLETED,
                started_at=start_time,
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.GOOGLE,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# Factory Functions
# =============================================================================


def create_google_agent(
    name: str,
    system_prompt: str = "",
    model: str = "gemini-2.0-flash",
    tools: list = None,
    **kwargs,
) -> GoogleADKAgent:
    """
    Create a Google ADK agent.

    Args:
        name: Agent name
        system_prompt: System instructions
        model: Model to use
        tools: Tool definitions
        **kwargs: Additional config

    Returns:
        GoogleADKAgent instance
    """
    from adk.base import AgentConfig, ToolDefinition

    tool_defs = []
    if tools:
        for tool in tools:
            if isinstance(tool, dict):
                tool_defs.append(ToolDefinition(**tool))
            elif isinstance(tool, ToolDefinition):
                tool_defs.append(tool)

    config = AgentConfig(
        name=name,
        provider=ADKProvider.GOOGLE,
        model=model,
        system_prompt=system_prompt,
        tools=tool_defs,
        **kwargs,
    )

    return GoogleADKAgent(config)


def create_google_multi_agent(
    name: str,
    sub_agents: list[dict],
    system_prompt: str = "",
    **kwargs,
) -> GoogleMultiAgent:
    """
    Create a Google multi-agent system.

    Args:
        name: Coordinator name
        sub_agents: List of sub-agent configs
        system_prompt: Coordinator instructions
        **kwargs: Additional config

    Returns:
        GoogleMultiAgent instance
    """
    from adk.base import AgentConfig

    config = AgentConfig(
        name=name,
        provider=ADKProvider.GOOGLE,
        system_prompt=system_prompt,
        **kwargs,
    )

    sub_configs = [AgentConfig(**sa) for sa in sub_agents]

    return GoogleMultiAgent(config, sub_configs)


# Register with factory
agent_factory.register(ADKProvider.GOOGLE, GoogleADKAgent)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "GoogleADKAgent",
    "GoogleMultiAgent",
    "create_google_agent",
    "create_google_multi_agent",
]
