"""Regression tests for AgentResult construction in EnhancedSuperAgent.

Locks the fix for the field-name bug (claude-mem obs 17791): the base agent
constructed ``AgentResult(output=..., usage=...)`` — both are non-fields — while
omitting the required ``content`` / ``agent_name`` / ``agent_provider``. That
raised ``ValidationError`` at runtime, which was swallowed by a surrounding
``try/except`` and silently fell back to basic ``execute()``. As a result the
router and round-table optimization paths computed a result and then threw it
away on every call. These tests prove the router-internal path now returns a
valid, content-bearing :class:`AgentResult`.
"""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from adk.base import ADKProvider, AgentResult, AgentStatus
from agents.base_super_agent.types import TaskCategory
from agents.marketing_agent import MarketingAgent


def test_agentresult_contract_requires_content_not_output() -> None:
    """The corrected kwargs build a valid result; the old buggy kwargs cannot."""
    result = AgentResult(
        agent_name="marketing_agent",
        agent_provider=ADKProvider.PYDANTIC,
        content="hello",
        status=AgentStatus.COMPLETED,
    )
    assert result.content == "hello"

    # The pre-fix construction: ``output=`` is not a field, and the required
    # ``content`` / ``agent_name`` / ``agent_provider`` are missing.
    with pytest.raises(ValidationError):
        AgentResult(status=AgentStatus.COMPLETED, output="hello")


@pytest.mark.asyncio
async def test_router_internal_returns_content_bearing_result(monkeypatch) -> None:
    """The router path returns a real content-bearing result, not a fallback."""
    agent = MarketingAgent()

    async def fake_route(prompt, task_category=None, **kwargs):
        return {
            "text": "ROUTED_OUTPUT",
            "provider": "openai",
            "model": "gpt-x",
            "usage": {"total_tokens": 5},
        }

    monkeypatch.setattr(agent, "_route_to_provider", fake_route)

    # If AgentResult construction still raised, the except clause would fall back
    # to execute(); make that failure mode loud instead of silent.
    async def fail_if_fallback(*args, **kwargs):
        raise AssertionError("fell back to execute() — AgentResult construction still broken")

    monkeypatch.setattr(agent, "execute", fail_if_fallback)

    enhanced = SimpleNamespace(enhanced_prompt="launch the drop")
    result = await agent._execute_with_router_internal(
        enhanced,
        task_type="campaign",
        task_category=TaskCategory.GENERATION,
        correlation_id="corr-1",
    )

    assert isinstance(result, AgentResult)
    assert result.content == "ROUTED_OUTPUT"
    assert result.agent_name == agent.name
    assert result.agent_provider == agent._active_provider
    assert result.status == AgentStatus.COMPLETED
    # usage data is preserved (folded into metadata, not dropped).
    assert result.metadata["usage"] == {"total_tokens": 5}
