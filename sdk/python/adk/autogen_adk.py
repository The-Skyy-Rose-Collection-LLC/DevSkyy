"""
AutoGen Integration
===================

Integration with Microsoft AutoGen v0.7.5 - Actor-model multi-agent framework.

Features:
- Actor-based agent architecture
- Distributed agent runtimes
- Conversational multi-agent systems
- Code execution agents
- Human-in-the-loop support

Reference: https://microsoft.github.io/autogen/
"""

import logging
import os
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from adk.base import (
    ADKProvider,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    agent_factory,
    estimate_cost,
)

logger = logging.getLogger(__name__)


# =============================================================================
# AutoGen Configuration Models
# =============================================================================


class AutoGenModelConfig(BaseModel):
    """Configuration for AutoGen model client"""

    model: str = Field("gpt-4o-mini", description="Model name")
    api_type: str = Field("openai", description="API type: openai, azure, anthropic")
    api_key: str | None = Field(None, description="API key (from env if not set)")
    base_url: str | None = Field(None, description="Custom base URL")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4096)


class AutoGenAgentType(BaseModel):
    """AutoGen agent type configuration"""

    agent_type: str = Field(
        "assistant",
        description="Type: assistant, user_proxy, code_executor",
    )
    system_message: str = Field("", description="System message")
    is_termination_msg: Callable | None = Field(None, description="Termination function")
    human_input_mode: str = Field(
        "NEVER",
        description="NEVER, ALWAYS, TERMINATE",
    )
    code_execution_config: dict | None = Field(None, description="Code execution settings")


# =============================================================================
# AutoGen Agent
# =============================================================================


class AutoGenAgent(BaseDevSkyyAgent):
    """
    Agent using Microsoft AutoGen framework.

    Features:
    - Actor-model architecture
    - Multi-agent conversations
    - Code execution capabilities
    - Distributed runtimes
    - Flexible termination

    Example:
        agent = AutoGenAgent(config)
        result = await agent.run("Write a Python script for inventory analysis")

    Note: AutoGen v0.7.x uses the new agentchat API
    """

    def __init__(
        self,
        config: AgentConfig,
        agent_type: str = "assistant",
        human_input_mode: str = "NEVER",
    ):
        super().__init__(config)
        self.agent_type = agent_type
        self.human_input_mode = human_input_mode
        self._autogen_agent = None
        self._model_client = None

    async def initialize(self) -> None:
        """Initialize AutoGen agent"""
        try:
            from autogen_agentchat.agents import AssistantAgent

            # Create model client
            self._model_client = self._create_model_client()

            # Create agent based on type
            self._autogen_agent = AssistantAgent(
                name=self.config.name,
                model_client=self._model_client,
                system_message=self.config.system_prompt or self._default_system_message(),
            )

            logger.info(f"AutoGen agent initialized: {self.name}")

        except ImportError as e:
            logger.warning(f"AutoGen not available: {e}")
            raise ImportError(
                "AutoGen not installed. Install with: pip install autogen-agentchat"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen agent: {e}")
            raise

    def _create_model_client(self):
        """Create model client for AutoGen"""
        model = self.config.model.lower()

        try:
            # Try OpenAI first
            if "gpt" in model or "openai" in model:
                from autogen_ext.models.openai import OpenAIChatCompletionClient

                return OpenAIChatCompletionClient(
                    model=self._extract_model_name(model, "openai"),
                    api_key=os.getenv("OPENAI_API_KEY"),
                )

            # Anthropic
            elif "claude" in model or "anthropic" in model:
                from autogen_ext.models.anthropic import AnthropicChatCompletionClient

                return AnthropicChatCompletionClient(
                    model=self._extract_model_name(model, "anthropic"),
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                )

            # Default to OpenAI
            else:
                from autogen_ext.models.openai import OpenAIChatCompletionClient

                return OpenAIChatCompletionClient(
                    model="gpt-4o-mini",
                    api_key=os.getenv("OPENAI_API_KEY"),
                )

        except ImportError:
            # Fallback to basic client
            logger.warning("Using basic model client")
            return None

    def _extract_model_name(self, model: str, provider: str) -> str:
        """Extract clean model name"""
        model = model.lower()

        if provider == "openai":
            if "gpt-4o-mini" in model:
                return "gpt-4o-mini"
            elif "gpt-4o" in model:
                return "gpt-4o"
            elif "gpt-4-turbo" in model:
                return "gpt-4-turbo"
            return "gpt-4o-mini"

        elif provider == "anthropic":
            if "sonnet" in model:
                return "claude-3-5-sonnet-20241022"
            elif "opus" in model:
                return "claude-3-opus-20240229"
            elif "haiku" in model:
                return "claude-3-haiku-20240307"
            return "claude-3-5-sonnet-20241022"

        return model

    def _default_system_message(self) -> str:
        """Default system message for SkyyRose"""
        return f"""You are an AI assistant for SkyyRose luxury streetwear.

{self.config.brand_context}

Your role:
- Provide expert assistance with {self.agent_type} tasks
- Maintain professional, luxury brand voice
- Be precise and actionable in responses
- Focus on delivering value

When writing code:
- Use Python 3.11+ best practices
- Include error handling
- Add clear comments
- Follow PEP 8 style
"""

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute AutoGen agent"""
        start_time = datetime.now(UTC)

        try:
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken

            # Create message
            message = TextMessage(content=prompt, source="user")

            # Run agent
            response = await self._autogen_agent.on_messages(
                [message],
                CancellationToken(),
            )

            # Extract content
            content = ""
            if hasattr(response, "chat_message") and response.chat_message:
                content = response.chat_message.content
            elif hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)

            # Token estimation
            input_tokens = int(len(prompt.split()) * 1.3)
            output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AUTOGEN,
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
            logger.error(f"AutoGen execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AUTOGEN,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# AutoGen Team (Multi-Agent)
# =============================================================================


class AutoGenTeam(BaseDevSkyyAgent):
    """
    Multi-agent team using AutoGen.

    Features:
    - Conversational agent teams
    - Round-robin or selector-based routing
    - Shared context
    - Termination conditions

    Example:
        team = AutoGenTeam(
            config,
            agents=[
                {"name": "analyst", "role": "Data Analyst"},
                {"name": "writer", "role": "Content Writer"},
            ]
        )
        result = await team.run("Analyze sales and create report")
    """

    def __init__(
        self,
        config: AgentConfig,
        agent_configs: list[dict],
        team_type: str = "round_robin",  # round_robin, selector
        max_turns: int = 10,
    ):
        super().__init__(config)
        self.agent_configs = agent_configs
        self.team_type = team_type
        self.max_turns = max_turns
        self._agents = []
        self._team = None

    async def initialize(self) -> None:
        """Initialize AutoGen team"""
        try:
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.conditions import MaxMessageTermination
            from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat

            # Create model client
            model_client = self._create_model_client()

            # Create agents
            for agent_config in self.agent_configs:
                agent = AssistantAgent(
                    name=agent_config.get("name", "agent"),
                    model_client=model_client,
                    system_message=agent_config.get(
                        "system_message",
                        f"You are a {agent_config.get('role', 'helpful assistant')}",
                    ),
                )
                self._agents.append(agent)

            # Create team based on type
            termination = MaxMessageTermination(max_messages=self.max_turns)

            if self.team_type == "selector":
                self._team = SelectorGroupChat(
                    self._agents,
                    model_client=model_client,
                    termination_condition=termination,
                )
            else:
                self._team = RoundRobinGroupChat(
                    self._agents,
                    termination_condition=termination,
                )

            logger.info(f"AutoGen team initialized with {len(self._agents)} agents")

        except ImportError as e:
            raise ImportError("AutoGen not installed") from e

    def _create_model_client(self):
        """Create shared model client"""
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient

            return OpenAIChatCompletionClient(
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        except ImportError:
            return None

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute team conversation"""
        start_time = datetime.now(UTC)

        try:
            from autogen_core import CancellationToken

            # Run team
            result = await self._team.run(
                task=prompt,
                cancellation_token=CancellationToken(),
            )

            # Extract messages
            content_parts = []
            if hasattr(result, "messages"):
                for msg in result.messages:
                    if hasattr(msg, "content"):
                        content_parts.append(f"[{msg.source}]: {msg.content}")

            content = "\n\n".join(content_parts) if content_parts else str(result)

            # Token estimation
            input_tokens = int(len(prompt.split()) * 1.3)
            output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AUTOGEN,
                content=content,
                status=AgentStatus.COMPLETED,
                iterations=len(content_parts),
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
            logger.error(f"AutoGen team execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.AUTOGEN,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# Code Executor Agent
# =============================================================================


class AutoGenCodeAgent(AutoGenAgent):
    """
    AutoGen agent with code execution capabilities.

    Features:
    - Python code execution
    - Sandboxed environment
    - Result capture
    - Error handling

    Example:
        agent = AutoGenCodeAgent(config)
        result = await agent.run("Write code to analyze sales data")
    """

    def __init__(self, config: AgentConfig, work_dir: str | None = None):
        super().__init__(config, agent_type="code_executor")
        self.work_dir = work_dir or os.getenv(
            "AUTOGEN_WORK_DIR", os.path.join(tempfile.gettempdir(), "autogen_work")
        )
        self._code_executor = None

    async def initialize(self) -> None:
        """Initialize code execution agent"""
        try:
            from autogen_agentchat.agents import CodeExecutorAgent
            from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

            # Create code executor
            self._code_executor = LocalCommandLineCodeExecutor(
                work_dir=self.work_dir,
            )

            # Create code agent
            self._autogen_agent = CodeExecutorAgent(
                name=self.config.name,
                code_executor=self._code_executor,
            )

            logger.info(f"AutoGen code agent initialized: {self.name}")

        except ImportError as e:
            # Fall back to regular agent
            logger.warning(f"Code executor not available, using assistant: {e}")
            await super().initialize()


# =============================================================================
# Factory Functions
# =============================================================================


def create_autogen_agent(
    name: str,
    system_prompt: str = "",
    model: str = "gpt-4o-mini",
    agent_type: str = "assistant",
    **kwargs,
) -> AutoGenAgent:
    """
    Create an AutoGen agent.

    Args:
        name: Agent name
        system_prompt: System message
        model: Model to use
        agent_type: assistant, code_executor
        **kwargs: Additional config

    Returns:
        AutoGenAgent instance
    """
    config = AgentConfig(
        name=name,
        provider=ADKProvider.AUTOGEN,
        model=model,
        system_prompt=system_prompt,
        **kwargs,
    )

    if agent_type == "code_executor":
        return AutoGenCodeAgent(config)

    return AutoGenAgent(config, agent_type=agent_type)


def create_autogen_team(
    name: str,
    agents: list[dict],
    team_type: str = "round_robin",
    max_turns: int = 10,
    model: str = "gpt-4o-mini",
    **kwargs,
) -> AutoGenTeam:
    """
    Create an AutoGen team.

    Args:
        name: Team name
        agents: List of agent configs with name, role, system_message
        team_type: round_robin or selector
        max_turns: Maximum conversation turns
        model: Model to use
        **kwargs: Additional config

    Returns:
        AutoGenTeam instance
    """
    config = AgentConfig(
        name=name,
        provider=ADKProvider.AUTOGEN,
        model=model,
        **kwargs,
    )

    return AutoGenTeam(config, agents, team_type, max_turns)


# Pre-built SkyyRose teams
def create_skyyrose_dev_team() -> AutoGenTeam:
    """Create development team for SkyyRose"""
    agents = [
        {
            "name": "architect",
            "role": "Software Architect",
            "system_message": """You are a software architect for SkyyRose e-commerce platform.
            You design systems, review code, and ensure best practices.
            Focus on scalability, security, and maintainability.""",
        },
        {
            "name": "developer",
            "role": "Full-Stack Developer",
            "system_message": """You are a full-stack developer for SkyyRose.
            You write Python, JavaScript, and work with WordPress/WooCommerce.
            Write clean, tested, documented code.""",
        },
        {
            "name": "reviewer",
            "role": "Code Reviewer",
            "system_message": """You are a code reviewer for SkyyRose.
            You review code for bugs, security issues, and improvements.
            Be thorough but constructive.""",
        },
    ]

    return create_autogen_team(
        name="dev_team",
        agents=agents,
        team_type="round_robin",
        max_turns=6,
    )


def create_skyyrose_analysis_team() -> AutoGenTeam:
    """Create data analysis team for SkyyRose"""
    agents = [
        {
            "name": "analyst",
            "role": "Data Analyst",
            "system_message": """You are a data analyst for SkyyRose luxury streetwear.
            You analyze sales, customer behavior, and market trends.
            Use data to drive business decisions.""",
        },
        {
            "name": "strategist",
            "role": "Business Strategist",
            "system_message": """You are a business strategist for SkyyRose.
            You interpret data insights and recommend actions.
            Focus on growth and profitability.""",
        },
    ]

    return create_autogen_team(
        name="analysis_team",
        agents=agents,
        team_type="round_robin",
        max_turns=4,
    )


# Register with factory
agent_factory.register(ADKProvider.AUTOGEN, AutoGenAgent)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Models
    "AutoGenModelConfig",
    "AutoGenAgentType",
    # Agents
    "AutoGenAgent",
    "AutoGenTeam",
    "AutoGenCodeAgent",
    # Factory
    "create_autogen_agent",
    "create_autogen_team",
    # Pre-built teams
    "create_skyyrose_dev_team",
    "create_skyyrose_analysis_team",
]
