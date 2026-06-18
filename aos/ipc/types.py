"""IPC message types for the AOS message bus.

All messages are immutable. Correlation IDs link request/response pairs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(StrEnum):
    """Types of messages on the bus."""

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"
    SIGNAL = "signal"


class SignalType(StrEnum):
    """System-level signals that bypass normal queuing."""

    BUDGET_EXCEEDED = "budget_exceeded"
    KILL = "kill"
    PAUSE = "pause"
    RESUME = "resume"
    HEALTH_CHECK = "health_check"


class Message(BaseModel):
    """Immutable message envelope for IPC.

    Signals (BUDGET_EXCEEDED, KILL) bypass queue ordering.
    """

    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    type: MessageType
    topic: str
    sender_pid: int
    recipient_pid: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: float | None = None
    priority: int = 0

    def make_reply(self, sender_pid: int, payload: dict[str, Any]) -> Message:
        """Create a response message linked to this request."""
        return Message(
            type=MessageType.RESPONSE,
            topic=self.topic,
            sender_pid=sender_pid,
            recipient_pid=self.sender_pid,
            payload=payload,
            correlation_id=self.correlation_id or self.id,
        )

    @property
    def is_signal(self) -> bool:
        """Check if this message is a system signal."""
        return self.type == MessageType.SIGNAL

    @property
    def is_expired(self) -> bool:
        """Check if this message has exceeded its TTL."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(UTC) - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds


class Subscription(BaseModel):
    """A subscription to a topic on the message bus."""

    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str
    subscriber_pid: int
