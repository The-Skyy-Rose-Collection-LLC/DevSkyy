"""
DevSkyy SubAgent Base Class
=============================

Base for all sub-agents within core agent domains.

Sub-agents:
- Handle specific tasks within a domain
- Self-heal independently (3 attempts)
- Escalate to their parent core agent on failure
- Report health back to the core agent
- Call LLMs via _llm_execute() (routes through UnifiedLLMClient)

Example:
    class SocialMediaSubAgent(SubAgent):
        name = "social_media"
        parent_type = CoreAgentType.MARKETING

        async def execute(self, task, **kwargs):
            return await self._llm_execute(task, system_prompt="You are a social media expert.")
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any

from agents.errors import AgentError, ErrorCategory

from .base import CoreAgentType, SelfHealingMixin

logger = logging.getLogger(__name__)

# Lazy-initialized singleton
_llm_client: Any = None


def _get_llm_client():
    """Lazy-initialize UnifiedLLMClient singleton."""
    global _llm_client
    if _llm_client is None:
        from llm.unified_llm_client import UnifiedLLMClient

        _llm_client = UnifiedLLMClient()
    return _llm_client


class SubAgent(SelfHealingMixin):
    """
    Base class for sub-agents within core agent domains.

    Each sub-agent:
    - Belongs to a core agent (parent)
    - Has a specific capability within the domain
    - Self-heals independently before escalating
    - Can be swapped out by the parent if circuit breaker opens
    - Calls LLMs via _llm_execute() with automatic routing

    Subclasses must implement:
    - execute(task, **kwargs) → dict[str, Any]

    Convention:
    - name: snake_case identifier (e.g., "social_media")
    - parent_type: CoreAgentType of the parent core agent
    - capabilities: list of what this sub-agent can do
    """

    name: str = "unnamed_sub_agent"
    parent_type: CoreAgentType = CoreAgentType.ORCHESTRATOR
    capabilities: list[str] = []
    description: str = ""

    # Override in subclass to set a default system prompt for LLM calls
    system_prompt: str = ""

    def __init__(
        self,
        *,
        parent: Any | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.parent = parent
        self.correlation_id = correlation_id
        self.__init_healing__()

    # -------------------------------------------------------------------------
    # LLM Execution (available to all sub-agents)
    # -------------------------------------------------------------------------

    async def _llm_execute(
        self,
        task: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        execution_mode: str = "balanced",
        preferred_provider: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute an LLM call via UnifiedLLMClient.

        All sub-agents can use this to make real LLM calls with:
        - Automatic provider routing (Anthropic → OpenAI → Google fallback)
        - Task classification & prompt technique selection
        - Circuit breaker per provider
        - Cost optimization

        Args:
            task: The user-facing task/prompt.
            system_prompt: Override the class-level system_prompt.
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Max output tokens.
            execution_mode: "fast", "balanced", or "round_table".
            preferred_provider: Force a specific provider.

        Returns:
            {"success": True, "result": "...", "provider": "...", "model": "...", ...}
        """
        from llm.base import Message, ModelProvider
        from llm.unified_llm_client import ExecutionMode, LLMRequest

        client = _get_llm_client()

        sys = system_prompt or self.system_prompt
        messages = []
        if sys:
            messages.append(Message.system(sys))
        messages.append(Message.user(task))

        # Map string to enum
        mode_map = {
            "fast": ExecutionMode.FAST,
            "balanced": ExecutionMode.BALANCED,
            "round_table": ExecutionMode.ROUND_TABLE,
        }

        provider = None
        if preferred_provider:
            try:
                provider = ModelProvider(preferred_provider)
            except ValueError:
                pass

        request = LLMRequest(
            messages=messages,
            task_description=task,
            execution_mode=mode_map.get(execution_mode, ExecutionMode.BALANCED),
            preferred_provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            correlation_id=self.correlation_id,
        )

        response = await client.complete(request)

        return {
            "success": True,
            "result": response.content,
            "provider": response.provider_used.value,
            "model": response.model_used,
            "technique": response.technique_used.value if response.technique_used else None,
            "latency_ms": response.total_latency_ms,
            "agent": self.name,
        }

    @abstractmethod
    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute sub-agent task. Implement in each sub-agent."""
        ...

    async def execute_safe(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute with self-healing wrapper.

        On failure:
        1. Self-heal (3 attempts)
        2. If still failing, escalate to parent core agent
        """
        if not self.circuit_breaker_allows():
            return {
                "success": False,
                "error": f"Circuit breaker OPEN for {self.name}",
                "escalation_needed": True,
                "parent_type": self.parent_type.value,
            }

        try:
            result = await self.execute(task, **kwargs)
            self._record_success()
            return result

        except Exception as exc:
            logger.error("[%s] Execution failed: %s", self.name, exc)

            # Self-heal
            diagnosis = self.diagnose(exc)
            heal_result = await self.heal(diagnosis)

            if heal_result.success:
                try:
                    result = await self.execute(task, **kwargs)
                    self._record_success()
                    return result
                except Exception as retry_exc:
                    self._record_failure()
                    return self._escalation_response(retry_exc)

            self._record_failure()
            return self._escalation_response(exc)

    def _escalation_response(self, error: Exception) -> dict[str, Any]:
        """Build escalation response for parent core agent."""
        return {
            "success": False,
            "error": str(error),
            "escalation_needed": True,
            "sub_agent": self.name,
            "parent_type": self.parent_type.value,
            "diagnosis": self.diagnose(error).failure_category.value,
        }

    async def escalate_to_parent(
        self, task: str, error: Exception, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Explicitly escalate a task to the parent core agent.

        The parent will try alternative sub-agents or its own strategy.
        """
        if self.parent is None:
            raise AgentError(
                f"Sub-agent '{self.name}' has no parent to escalate to",
                category=ErrorCategory.CONFIGURATION,
            )

        logger.warning(
            "[%s] Escalating to parent %s: %s",
            self.name,
            self.parent_type.value,
            str(error)[:100],
        )

        if hasattr(self.parent, "execute_safe"):
            return await self.parent.execute_safe(task, **kwargs)

        raise AgentError(
            f"Parent agent for '{self.name}' does not support execute_safe",
            category=ErrorCategory.EXECUTION,
        )

    def to_portal_node(self) -> dict[str, Any]:
        """Serialize for 3D portal sub-agent display."""
        health = self.health_check()
        return {
            "id": self.name,
            "parent": self.parent_type.value,
            "label": self.name.replace("_", " ").title(),
            "description": self.description,
            "capabilities": self.capabilities,
            "healthy": health.healthy,
            "circuit_breaker": health.circuit_breaker,
        }


__all__ = ["SubAgent"]
