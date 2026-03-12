"""
Claude SDK Base Agent
=====================

Wraps ClaudeSDKClient for DevSkyy integration with structured logging,
telemetry hooks, and output directory management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog
from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
)

from agents.claude_sdk.utils.tracker import DevSkyySubagentTracker

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SDKAgentConfig:
    """Configuration for a Claude SDK-based agent."""

    model: str = "haiku"
    permission_mode: str = "bypassPermissions"
    max_turns: int = 50
    output_dir: Path = field(default_factory=lambda: Path("data"))


class ClaudeSDKBaseAgent:
    """Base class wrapping ClaudeSDKClient with DevSkyy telemetry and logging.

    Subclasses define ``_build_agents()`` and ``_build_system_prompt()`` to
    configure the multi-agent topology. The base handles client lifecycle,
    hook wiring, and structured output capture.
    """

    def __init__(self, config: SDKAgentConfig | None = None) -> None:
        self.config = config or SDKAgentConfig()
        self._tracker: DevSkyySubagentTracker | None = None
        self._client: ClaudeSDKClient | None = None

    # ------------------------------------------------------------------
    # Subclass hooks
    # ------------------------------------------------------------------

    def _build_agents(self) -> dict[str, AgentDefinition]:
        """Return the subagent definitions. Override in subclass."""
        return {}

    def _build_system_prompt(self) -> str:
        """Return the lead agent system prompt. Override in subclass."""
        return "You are a DevSkyy AI agent."

    def _build_allowed_tools(self) -> list[str]:
        """Return the tools available to the lead agent."""
        return ["Task"]

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    def _build_options(self, session_dir: Path) -> ClaudeAgentOptions:
        """Construct ClaudeAgentOptions with DevSkyy telemetry hooks."""
        self._tracker = DevSkyySubagentTracker(session_dir=session_dir)

        hooks = {
            "PreToolUse": [
                HookMatcher(
                    matcher=None,
                    hooks=[self._tracker.pre_tool_use_hook],
                )
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher=None,
                    hooks=[self._tracker.post_tool_use_hook],
                )
            ],
        }

        return ClaudeAgentOptions(
            permission_mode=self.config.permission_mode,
            system_prompt=self._build_system_prompt(),
            allowed_tools=self._build_allowed_tools(),
            agents=self._build_agents(),
            hooks=hooks,
            model=self.config.model,
        )

    async def run(self, prompt: str, session_dir: Path | None = None) -> str:
        """Execute a single query and return the assistant's final text.

        Args:
            prompt: The user query to send to the agent.
            session_dir: Directory for session logs. Auto-created if None.

        Returns:
            The concatenated text of the assistant's response.
        """
        if session_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = self.config.output_dir / f"session_{ts}"
        session_dir.mkdir(parents=True, exist_ok=True)

        options = self._build_options(session_dir)
        response_parts: list[str] = []

        try:
            async with ClaudeSDKClient(options=options) as client:
                self._client = client
                await client.query(prompt=prompt)

                async for msg in client.receive_response():
                    msg_type = type(msg).__name__
                    if msg_type == "AssistantMessage":
                        for block in getattr(msg, "message", msg).content:
                            if getattr(block, "type", None) == "text":
                                response_parts.append(block.text)

                logger.info(
                    "sdk_agent_complete",
                    session_dir=str(session_dir),
                    response_length=sum(len(p) for p in response_parts),
                )
        finally:
            self._client = None
            if self._tracker:
                self._tracker.close()

        return "\n".join(response_parts)
