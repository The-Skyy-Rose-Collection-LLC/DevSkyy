"""
Google ADK Integration
======================

Integration with Google's Agent Development Kit (ADK).

Architecture:
    Google ADK is the orchestration shell — it owns session management,
    streaming, HITL confirmation, and A2A protocol readiness. The actual
    reasoning model is configurable per agent: by default we route
    reasoning through Claude Sonnet (via the LiteLlm extension) and
    reserve Gemini Flash for high-throughput vision tasks.

Features:
    - Claude Sonnet 4.6 as the default reasoning engine
    - Gemini 2.0 Flash for vision / high-throughput
    - Multi-agent hierarchies, tool confirmation (HITL)
    - Session management, streaming, Vertex AI integration

Installation:
    pip install 'google-adk[extensions]'  # extensions includes LiteLlm

Reference: https://google.github.io/adk-docs/
"""

from __future__ import annotations

import logging
import os
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

# Default reasoning model (Claude Sonnet 4.6 via LiteLlm)
DEFAULT_REASONING_MODEL = "claude-sonnet-4-6"
# Fallback model when LiteLlm extension is unavailable
FALLBACK_GEMINI_MODEL = "gemini-2.0-flash"

# Check for Google ADK availability
try:
    from google.adk.agents import Agent as ADKAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    GOOGLE_ADK_AVAILABLE = True
    logger.info("Google ADK loaded successfully")
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    ADKAgent = None
    Runner = None
    InMemorySessionService = None
    genai_types = None
    logger.warning("Google ADK not installed. Install with: pip install google-adk")

# LiteLlm is the bridge for non-Gemini models (Claude, GPT). Optional
# because google-adk[extensions] is a separate install and some
# deployments only need Gemini.
try:
    from google.adk.models.lite_llm import LiteLlm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    LiteLlm = None
    logger.info(
        "google-adk[extensions] not installed; non-Gemini models will fall back to %s. "
        "Install with: pip install 'google-adk[extensions]'",
        FALLBACK_GEMINI_MODEL,
    )


# =============================================================================
# Model resolution
# =============================================================================


def _canonical_model_id(raw: str | None) -> str:
    """Normalise a config model string into a canonical model ID.

    Empty / None → reasoning default (Claude Sonnet).
    Legacy GPT-4o aliases → reasoning default. Everything else passes
    through unchanged so callers stay in control of explicit choices.
    """
    model = (raw or "").strip()
    if not model:
        return DEFAULT_REASONING_MODEL
    lower = model.lower()
    if lower.startswith(("gpt-4o-mini", "gpt-4o")):
        return DEFAULT_REASONING_MODEL
    return model


# Module-level guard so the LiteLlm-missing warning only fires once per
# process instead of on every agent construction. Multi-agent workflows
# can build dozens of sub-agents per request — this prevents log spam.
_litellm_fallback_warned = False


def _resolve_adk_model(model_id: str) -> Any:
    """Return an ADK-compatible model object for `model_id`.

    Native Gemini IDs return as plain strings; everything else is wrapped
    in `LiteLlm`. If the LiteLlm extension is not installed, fall back
    to Gemini Flash so the agent still functions.
    """
    global _litellm_fallback_warned
    lower = model_id.lower()
    if "gemini" in lower:
        return model_id

    if not LITELLM_AVAILABLE:
        if not _litellm_fallback_warned:
            logger.warning(
                "Non-Gemini model %r requested but google-adk[extensions] is not "
                "installed; falling back to %s. Install with: "
                "pip install 'google-adk[extensions]'",
                model_id,
                FALLBACK_GEMINI_MODEL,
            )
            _litellm_fallback_warned = True
        return FALLBACK_GEMINI_MODEL

    if lower.startswith(("anthropic/", "openai/")):
        return LiteLlm(model=model_id)
    if lower.startswith("claude"):
        return LiteLlm(model=f"anthropic/{model_id}")
    if lower.startswith("gpt"):
        return LiteLlm(model=f"openai/{model_id}")
    return LiteLlm(model=model_id)


def _resolve_model_for_config(config: AgentConfig) -> Any:
    """Resolve `config.model` into the right ADK model object."""
    return _resolve_adk_model(_canonical_model_id(config.model))


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
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK not installed. Install with: pip install google-adk")

        # Ensure environment variable is set for the underlying google-genai SDK
        from adk.base import get_api_key

        key = get_api_key(ADKProvider.GOOGLE)
        if key and not os.getenv("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = key

        try:
            # Build tools list
            tools = []
            for tool_def in self.config.tools:
                # Convert to ADK tool format
                tools.append(self._create_adk_tool(tool_def))

            # Create agent using ADKAgent (LlmAgent). For Claude/GPT we
            # wrap the model name in LiteLlm so ADK routes through the
            # right provider; Gemini names pass through as plain strings.
            self._adk_agent = ADKAgent(
                name=self.config.name,
                model=_resolve_model_for_config(self.config),
                instruction=self.config.system_prompt or self._default_instruction(),
                description=self.config.description,
                tools=tools if tools else [],
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

            self._initialized = True
            logger.info(f"Google ADK agent initialized: {self.name}")

        except Exception as e:
            logger.error(f"Failed to initialize Google ADK agent: {e}")
            raise

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
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK not available")

        start_time = datetime.now(UTC)
        tool_calls = []

        try:
            # Create content using genai_types
            content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)],
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
                    _canonical_model_id(self.config.model),
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
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK not available. Install with: pip install google-adk")

        try:
            # Create sub-agents first. Each sub-agent's model is resolved
            # the same way as a top-level agent — Claude for reasoning by
            # default, Gemini Flash when explicitly requested or when
            # LiteLlm is unavailable.
            sub_agent_instances = []
            for sub_config in self.sub_agent_configs:
                sub_agent = ADKAgent(
                    name=sub_config.name,
                    model=_resolve_model_for_config(sub_config),
                    instruction=sub_config.system_prompt,
                    description=sub_config.description,
                )
                self._sub_agents[sub_config.name] = sub_agent
                sub_agent_instances.append(sub_agent)

            # Create coordinator with sub-agents
            self._coordinator = ADKAgent(
                name=self.config.name,
                model=_resolve_model_for_config(self.config),
                instruction=self.config.system_prompt or self._coordinator_instruction(),
                description="Coordinator agent for SkyyRose operations",
                sub_agents=sub_agent_instances if sub_agent_instances else [],
            )

            self._initialized = True
            logger.info(
                f"Google Multi-Agent initialized: {self.name} with {len(self._sub_agents)} sub-agents"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Google Multi-Agent: {e}")
            raise

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
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK not available")

        start_time = datetime.now(UTC)

        try:
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
            content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)],
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
            logger.error(f"Google Multi-Agent execution failed: {e}")
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
    model: str = DEFAULT_REASONING_MODEL,
    tools: list = None,
    **kwargs,
) -> GoogleADKAgent:
    """
    Create a Google ADK agent.

    Args:
        name: Agent name
        system_prompt: System instructions
        model: Model to use. Defaults to Claude Sonnet via LiteLlm. Pass
            a Gemini ID (e.g. "gemini-2.0-flash") for vision or
            high-throughput tasks.
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
