"""Governance types — audit entries and policy decisions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
    """Categories of auditable events."""

    PROCESS_SPAWN = "process_spawn"
    PROCESS_START = "process_start"
    PROCESS_KILL = "process_kill"
    PROCESS_PAUSE = "process_pause"
    PROCESS_RESUME = "process_resume"
    PROCESS_COMPLETE = "process_complete"
    PROCESS_FAIL = "process_fail"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    POLICY_VIOLATION = "policy_violation"
    SYSTEM_BOOT = "system_boot"
    SYSTEM_SHUTDOWN = "system_shutdown"
    MODULE_LOADED = "module_loaded"
    MODULE_UNLOADED = "module_unloaded"
    AGENT_REGISTERED = "agent_registered"
    PROCESS_RETRY = "process_retry"
    PROCESS_HEAL_SUCCESS = "process_heal_success"
    PROCESS_HEAL_FAILED = "process_heal_failed"
    LEARNING_RECORDED = "learning_recorded"
    LEARNING_FLUSHED = "learning_flushed"
    PLAN_STARTED = "plan_started"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"
    REFLECTION_RECORDED = "reflection_recorded"
    FINETUNE_QUEUED = "finetune_queued"


class AuditEntry(BaseModel):
    """Immutable audit log entry. Written to SQLite for persistence."""

    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: AuditEventType
    actor_pid: int | None = None
    target_pid: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None

    def to_row(self) -> tuple[str, str, str, int | None, int | None, str, str | None]:
        """Convert to a flat tuple for SQLite insertion."""
        import json

        return (
            self.id,
            self.timestamp.isoformat(),
            self.event_type.value,
            self.actor_pid,
            self.target_pid,
            json.dumps(self.details),
            self.correlation_id,
        )
