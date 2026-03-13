"""
SDK-Powered SubAgent
=====================

SubAgent that uses the Claude Agent SDK as its execution engine
instead of raw LLM calls via UnifiedLLMClient.

This gives sub-agents full tool-use capabilities:
- File I/O (Read, Write, Edit)
- Shell execution (Bash)
- Web search and fetch
- Multi-agent delegation (Task tool)
- MCP server access

Use this when a sub-agent needs to DO things (run code, search,
write files) rather than just generate text.

Example:
    class DeploySubAgent(SDKSubAgent):
        name = "deploy_runner"
        parent_type = CoreAgentType.OPERATIONS
        sdk_tools = ["Bash", "Read", "Write"]
        capabilities = ["deploy", "rollback", "health_check"]

        def _sdk_default_prompt(self):
            return "You are a deployment specialist. Run deploy scripts safely."

        async def execute(self, task, **kwargs):
            result = await self._sdk_execute(task)
            return result.to_dict()
"""

from __future__ import annotations

from typing import Any

import structlog
from claude_agent_sdk import AgentDefinition

from agents.claude_sdk.mixin import SDKCapabilityMixin
from agents.core.sub_agent import SubAgent

logger = structlog.get_logger(__name__)


class SDKSubAgent(SubAgent, SDKCapabilityMixin):
    """SubAgent with Claude Agent SDK execution capabilities.

    Inherits from both SubAgent (self-healing, escalation, health)
    and SDKCapabilityMixin (SDK execution, delegation, sessions).

    The execute() method routes through _sdk_execute() by default,
    giving the agent full tool-use capabilities. Subclasses can
    override execute() for custom routing logic.

    Class attributes (override in subclass):
        sdk_tools:      Tools available to this agent
        sdk_model:      Claude model to use
        sdk_agents:     Subagent definitions for delegation
        capabilities:   Human-readable capability list
    """

    # Default SDK config — override per subclass
    sdk_tools: list[str] = ["Read", "Write", "Bash"]
    sdk_model: str = "sonnet"
    sdk_agents: dict[str, AgentDefinition] = {}

    def __init__(
        self,
        *,
        parent: Any | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            parent=parent,
            correlation_id=correlation_id,
            **kwargs,
        )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute task via Claude Agent SDK.

        The SDK agent gets full tool access and can read files,
        run commands, search the web, and delegate to subagents.

        Falls back to _llm_execute() if SDK execution fails and
        the task is simple enough for a text-only response.

        Args:
            task: The task description/prompt.
            **kwargs: Additional context passed to the prompt.

        Returns:
            Dict with success, result, agent, and SDK metrics.
        """
        # Build context-enriched prompt
        prompt = self._build_task_prompt(task, **kwargs)

        # Try SDK execution first
        sdk_result = await self._sdk_execute(
            prompt,
            tools=self.sdk_tools,
            agents=self.sdk_agents or {},
            label=self.name,
        )

        if sdk_result.success:
            return {
                "success": True,
                "result": sdk_result.response,
                "agent": self.name,
                "execution_mode": "sdk",
                "metrics": sdk_result.metrics,
                "session_dir": sdk_result.session_dir,
            }

        # SDK failed — try LLM fallback for text-only tasks
        logger.warning(
            "sdk_execution_failed_trying_llm",
            agent=self.name,
            error=sdk_result.error,
        )

        try:
            llm_result = await self._llm_execute(
                task,
                system_prompt=self._sdk_default_prompt(),
            )
            llm_result["execution_mode"] = "llm_fallback"
            return llm_result
        except Exception as llm_exc:
            return {
                "success": False,
                "result": "",
                "agent": self.name,
                "error": (f"SDK: {sdk_result.error}; LLM fallback: {llm_exc}"),
                "execution_mode": "failed",
            }

    def _build_task_prompt(self, task: str, **kwargs: Any) -> str:
        """Build an enriched prompt with task context.

        Subclasses can override to inject domain-specific context
        (product catalogs, brand guidelines, etc.).
        """
        parts = [task]

        if kwargs:
            context_lines = [f"- {k}: {v}" for k, v in kwargs.items() if v is not None]
            if context_lines:
                parts.append("\nAdditional context:\n" + "\n".join(context_lines))

        return "\n".join(parts)

    async def execute_with_delegation(
        self,
        task: str,
        agents: dict[str, AgentDefinition],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute by delegating to SDK subagents.

        Use when the task benefits from parallel work by specialized
        subagents (e.g., research + analysis + report).

        Args:
            task: Coordination task for the lead agent.
            agents: Subagent definitions to spawn.
            **kwargs: Additional context.

        Returns:
            Dict with delegated results and metrics.
        """
        prompt = self._build_task_prompt(task, **kwargs)

        sdk_result = await self._sdk_delegate(
            prompt,
            agents=agents,
            label=f"{self.name}_delegate",
        )

        return {
            "success": sdk_result.success,
            "result": sdk_result.response,
            "agent": self.name,
            "execution_mode": "sdk_delegation",
            "metrics": sdk_result.metrics,
            "error": sdk_result.error,
        }

    def to_portal_node(self) -> dict[str, Any]:
        """Serialize for 3D portal with SDK metadata."""
        base = super().to_portal_node()
        base["sdk_enabled"] = True
        base["sdk_tools"] = self.sdk_tools
        base["sdk_model"] = self.sdk_model
        return base
