"""ComfyUI queue data model and prompt payload builder."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueueStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """A single item in the ComfyUI queue."""

    prompt_id: str
    number: int
    node_errors: dict[str, Any] = field(default_factory=dict)
    status: QueueStatus = QueueStatus.PENDING

    @classmethod
    def from_running_tuple(cls, entry: list[Any]) -> "QueueItem":
        """Parse a running-queue entry: [number, prompt_id, prompt, extra, node_errors]."""
        if len(entry) < 2:
            raise ValueError(f"Running entry too short: {entry!r}")
        number = int(entry[0])
        prompt_id = str(entry[1])
        node_errors = entry[4] if len(entry) > 4 and isinstance(entry[4], dict) else {}
        return cls(
            prompt_id=prompt_id,
            number=number,
            node_errors=node_errors,
            status=QueueStatus.RUNNING,
        )

    @classmethod
    def from_pending_tuple(cls, entry: list[Any]) -> "QueueItem":
        """Parse a pending-queue entry: [number, prompt_id, prompt, extra]."""
        if len(entry) < 2:
            raise ValueError(f"Pending entry too short: {entry!r}")
        number = int(entry[0])
        prompt_id = str(entry[1])
        return cls(
            prompt_id=prompt_id,
            number=number,
            status=QueueStatus.PENDING,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "number": self.number,
            "status": self.status.value,
            "node_errors": self.node_errors,
        }


def build_prompt_payload(
    workflow: dict[str, Any],
    client_id: str | None = None,
    extra_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the POST body for /prompt.

    Args:
        workflow: Raw workflow dict (node_id -> node_spec).
        client_id: Optional client identifier for tracking.  A fresh UUID4
            is generated when *None*.
        extra_data: Optional additional data merged into the payload.

    Returns:
        Dict suitable for ``json=`` in an httpx POST to /prompt.
    """
    payload: dict[str, Any] = {
        "prompt": workflow,
        "client_id": client_id or str(uuid.uuid4()),
    }
    if extra_data:
        payload["extra_data"] = extra_data
    return payload


def parse_queue_response(data: dict[str, Any]) -> dict[str, list[QueueItem]]:
    """Parse the /queue GET response into running + pending lists.

    Returns:
        Dict with keys ``"running"`` and ``"pending"`` containing
        :class:`QueueItem` lists.
    """
    running: list[QueueItem] = []
    pending: list[QueueItem] = []

    for entry in data.get("queue_running", []):
        try:
            running.append(QueueItem.from_running_tuple(entry))
        except (ValueError, TypeError, IndexError):
            pass

    for entry in data.get("queue_pending", []):
        try:
            pending.append(QueueItem.from_pending_tuple(entry))
        except (ValueError, TypeError, IndexError):
            pass

    return {"running": running, "pending": pending}
