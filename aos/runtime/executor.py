"""Executor — kernel.execute() end-to-end runner.

The executor is a thin coordinator that runs in 5 phases:
    1. Spawn (policy + approval gates fire)
    2. Resolve agent factory + build adapter
    3. Transition READY → RUNNING + run inside AgentContainer
    4. Capture heal journal → audit each retry
    5. Record learning trace + finalize (COMPLETED or FAILED)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from aos.adapters.superagent_adapter import AdapterRun, HealJournalEntry
from aos.runtime.types import ExecutionResult


class ExecutionOutcome(BaseModel):
    """The result of kernel.execute() — combines container metrics + agent telemetry."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    pid: int
    success: bool
    agent_run: AdapterRun
    container_result: ExecutionResult
    heal_entries: tuple[HealJournalEntry, ...] = ()
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NoFactoryError(KeyError):
    """Raised when kernel.execute() is called for an unregistered agent_type."""
