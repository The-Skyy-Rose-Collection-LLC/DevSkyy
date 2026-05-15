"""Smoke test: kernel.execute() with a real EnhancedSuperAgent instance.

Validates that:
  - SuperAgentAdapter's duck-typed surface matches the real agent class
  - Real AgentResult flows through kernel.execute() into the audit log
  - No LLM is actually called (execute is monkey-patched)

If EnhancedSuperAgent can't be imported (deps missing), the test is skipped.
"""

from __future__ import annotations

import pytest

from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from aos.kernel.types import ProcessStatus, SpawnRequest

pytest_plugins: list[str] = []


def _import_real_agent():
    try:
        from adk.base import ADKProvider, AgentConfig, AgentResult, AgentStatus
        from agents.base_super_agent import EnhancedSuperAgent
    except Exception as exc:  # noqa: BLE001 — graceful skip when deps incomplete
        pytest.skip(f"EnhancedSuperAgent unavailable in this env: {exc}")
    return EnhancedSuperAgent, AgentConfig, AgentResult, AgentStatus, ADKProvider


@pytest.fixture
async def kernel(tmp_path) -> Kernel:
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=10.0)
    await k.boot()
    return k


@pytest.mark.asyncio
async def test_real_agent_class_runs_through_kernel(kernel: Kernel):
    EnhancedSuperAgent, AgentConfig, AgentResult, AgentStatus, ADKProvider = _import_real_agent()

    # EnhancedSuperAgent.execute is @abstractmethod; create a minimal concrete subclass.
    # The method is immediately monkey-patched below so this impl never runs.
    class _ConcreteSmoke(EnhancedSuperAgent):
        async def execute(self, prompt: str, **kwargs) -> AgentResult:  # type: ignore[override]
            raise NotImplementedError

    config = AgentConfig(
        name="smoke_commerce",
        description="smoke test agent",
        system_prompt="You are a commerce agent.",
        temperature=0.2,
        max_tokens=128,
    )
    agent = _ConcreteSmoke(config)
    # Bypass full initialize() — it spins up RAG / ML / router with real env deps
    agent._initialized = True
    agent.agent_type = "commerce"

    fake_result = AgentResult(
        agent_name="smoke_commerce",
        agent_provider=ADKProvider.PYDANTIC,
        content="ok from real agent class",
        status=AgentStatus.COMPLETED,
        cost_usd=0.0,
        latency_ms=12.5,
        input_tokens=10,
        output_tokens=5,
    )

    async def fake_execute(prompt: str, **_kwargs):  # noqa: ARG001
        return fake_result

    agent.execute = fake_execute  # type: ignore[method-assign]

    await kernel.register_agent_factory("commerce", lambda: _async(agent))
    outcome = await kernel.execute(
        SpawnRequest(agent_type="commerce", prompt="update br-001 price")
    )

    assert outcome.success
    assert outcome.agent_run.agent_type == "commerce"
    assert outcome.agent_run.raw_result.content == "ok from real agent class"
    assert outcome.agent_run.metadata["cost_usd"] == 0.0
    assert outcome.agent_run.metadata["latency_ms"] == 12.5

    final = await kernel.processes.get(outcome.pid)
    assert final.status == ProcessStatus.COMPLETED

    spawns = await kernel.audit.query(event_type=AuditEventType.PROCESS_SPAWN)
    completes = await kernel.audit.query(event_type=AuditEventType.PROCESS_COMPLETE)
    assert any(e.target_pid == outcome.pid for e in spawns)
    assert any(e.target_pid == outcome.pid for e in completes)


async def _async(value):
    return value
