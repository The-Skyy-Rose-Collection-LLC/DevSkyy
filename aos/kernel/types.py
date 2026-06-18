"""Shared domain types for the AOS kernel.

All types are frozen Pydantic models — state transitions produce new instances.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class ProcessStatus(IntEnum):
    """Lifecycle states for an agent process.

    State machine::

        PENDING -> READY -> RUNNING -> COMPLETED
                                    -> FAILED
                           RUNNING <-> PAUSED
                           RUNNING <-> WAITING
        Any terminal state -> ZOMBIE (if parent hasn't reaped)
    """

    PENDING = 0
    READY = 1
    RUNNING = 2
    PAUSED = 3
    WAITING = 4
    COMPLETED = 5
    FAILED = 6
    ZOMBIE = 7


class ProcessPriority(IntEnum):
    """Scheduling priority levels. Higher value = higher priority."""

    IDLE = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


# Valid state transitions: from_status -> set of valid to_statuses
VALID_TRANSITIONS: dict[ProcessStatus, frozenset[ProcessStatus]] = {
    ProcessStatus.PENDING: frozenset({ProcessStatus.READY, ProcessStatus.FAILED}),
    ProcessStatus.READY: frozenset({ProcessStatus.RUNNING, ProcessStatus.FAILED}),
    ProcessStatus.RUNNING: frozenset(
        {
            ProcessStatus.PAUSED,
            ProcessStatus.WAITING,
            ProcessStatus.COMPLETED,
            ProcessStatus.FAILED,
        }
    ),
    ProcessStatus.PAUSED: frozenset({ProcessStatus.RUNNING, ProcessStatus.FAILED}),
    ProcessStatus.WAITING: frozenset({ProcessStatus.RUNNING, ProcessStatus.FAILED}),
    ProcessStatus.COMPLETED: frozenset({ProcessStatus.ZOMBIE}),
    ProcessStatus.FAILED: frozenset({ProcessStatus.ZOMBIE}),
    ProcessStatus.ZOMBIE: frozenset(),
}


def is_terminal(status: ProcessStatus) -> bool:
    """Check if a process status is terminal (COMPLETED, FAILED, or ZOMBIE)."""
    return status in {ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.ZOMBIE}


def can_transition(from_status: ProcessStatus, to_status: ProcessStatus) -> bool:
    """Check if a state transition is valid."""
    return to_status in VALID_TRANSITIONS.get(from_status, frozenset())


class AgentProcess(BaseModel):
    """Process control block for an agent instance.

    Immutable — state transitions produce new instances via .model_copy(update={...}).
    """

    model_config = {"frozen": True}

    pid: int
    parent_pid: int | None = None
    agent_type: str
    prompt: str
    status: ProcessStatus = ProcessStatus.PENDING
    priority: ProcessPriority = ProcessPriority.NORMAL
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any | None = None
    error: str | None = None
    children: tuple[int, ...] = ()
    budget_usd: float = 1.0
    spent_usd: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])

    def with_status(self, new_status: ProcessStatus, **kwargs: Any) -> AgentProcess:
        """Create a new process with updated status + optional field overrides.

        Raises ValueError if the transition is invalid.
        """
        if not can_transition(self.status, new_status):
            msg = f"Invalid transition: {self.status.name} -> {new_status.name}"
            raise ValueError(msg)
        updates: dict[str, Any] = {"status": new_status, **kwargs}
        if new_status == ProcessStatus.RUNNING and self.started_at is None:
            updates.setdefault("started_at", datetime.now(UTC))
        if is_terminal(new_status) and self.completed_at is None:
            updates.setdefault("completed_at", datetime.now(UTC))
        return self.model_copy(update=updates)

    def add_child(self, child_pid: int) -> AgentProcess:
        """Return a new process with a child PID appended."""
        return self.model_copy(update={"children": (*self.children, child_pid)})

    def add_spend(self, amount: float) -> AgentProcess:
        """Return a new process with accumulated spend."""
        return self.model_copy(update={"spent_usd": self.spent_usd + amount})

    @property
    def is_over_budget(self) -> bool:
        """Check if the process has exceeded its budget."""
        return self.spent_usd >= self.budget_usd

    @property
    def is_alive(self) -> bool:
        """Check if the process is in a non-terminal state."""
        return not is_terminal(self.status)


class SpawnRequest(BaseModel):
    """Request to spawn a new agent process."""

    model_config = {"frozen": True}

    agent_type: str
    prompt: str
    priority: ProcessPriority = ProcessPriority.NORMAL
    parent_pid: int | None = None
    budget_usd: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
