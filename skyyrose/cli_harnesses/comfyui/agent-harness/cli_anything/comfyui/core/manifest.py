"""Action manifest — plan/apply pattern for ComfyUI CLI operations.

The manifest records a pending set of changes (a *plan*) that the user
reviews before execution.  Once approved, ``apply`` runs each change.

Atomic persistence uses tempfile + fcntl.flock + os.replace so a crash
mid-write never leaves a partial manifest on disk.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

_DEFAULT_MANIFEST_PATH = Path.home() / ".cli_anything" / "comfyui" / "manifest.json"


class ChangeKind(str, Enum):
    QUEUE_SUBMIT = "queue_submit"
    QUEUE_CLEAR = "queue_clear"
    QUEUE_INTERRUPT = "queue_interrupt"
    WORKFLOW_SAVE = "workflow_save"
    SESSION_DELETE = "session_delete"
    HISTORY_CLEAR = "history_clear"


# Kinds that are destructive and require --confirm before apply.
DESTRUCTIVE_KINDS: frozenset[ChangeKind] = frozenset(
    {
        ChangeKind.QUEUE_CLEAR,
        ChangeKind.QUEUE_INTERRUPT,
        ChangeKind.HISTORY_CLEAR,
        ChangeKind.SESSION_DELETE,
    }
)


@dataclass
class ChangeItem:
    """A single planned change within an :class:`ActionManifest`."""

    kind: ChangeKind
    description: str
    params: dict[str, Any] = field(default_factory=dict)

    def is_destructive(self) -> bool:
        return self.kind in DESTRUCTIVE_KINDS

    def summary(self) -> str:
        tag = "[DESTRUCTIVE] " if self.is_destructive() else ""
        return f"{tag}{self.kind.value}: {self.description}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "description": self.description,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangeItem":
        return cls(
            kind=ChangeKind(data["kind"]),
            description=data["description"],
            params=data.get("params", {}),
        )


@dataclass
class ActionManifest:
    """Ordered list of planned changes with metadata."""

    changes: list[ChangeItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    applied: bool = False

    def add(self, item: ChangeItem) -> None:
        self.changes.append(item)

    def has_destructive(self) -> bool:
        return any(c.is_destructive() for c in self.changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "applied": self.applied,
            "changes": [c.to_dict() for c in self.changes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionManifest":
        return cls(
            changes=[ChangeItem.from_dict(c) for c in data.get("changes", [])],
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            applied=data.get("applied", False),
        )


# ---------------------------------------------------------------------------
# Atomic I/O
# ---------------------------------------------------------------------------


def _locked_save_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write *data* as JSON to *path* using flock + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".manifest_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            json.dump(data, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
            fcntl.flock(fh, fcntl.LOCK_UN)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def save_manifest(
    manifest: ActionManifest,
    path: Path | str | None = None,
) -> Path:
    """Persist *manifest* atomically.  Returns the path written."""
    dest = Path(path) if path else _DEFAULT_MANIFEST_PATH
    _locked_save_json(dest, manifest.to_dict())
    return dest


def load_manifest(path: Path | str | None = None) -> ActionManifest:
    """Load an :class:`ActionManifest` from *path* (default location if None)."""
    src = Path(path) if path else _DEFAULT_MANIFEST_PATH
    if not src.exists():
        return ActionManifest()
    text = src.read_text(encoding="utf-8")
    data = json.loads(text)
    return ActionManifest.from_dict(data)


# ---------------------------------------------------------------------------
# Plan builder helpers
# ---------------------------------------------------------------------------


def build_plan(changes: list[ChangeItem]) -> ActionManifest:
    """Create a new :class:`ActionManifest` from *changes*."""
    m = ActionManifest()
    for c in changes:
        m.add(c)
    return m


def plan_queue_submit(workflow_path: str) -> ChangeItem:
    return ChangeItem(
        kind=ChangeKind.QUEUE_SUBMIT,
        description=f"Submit workflow from {workflow_path}",
        params={"workflow_path": workflow_path},
    )


def plan_queue_clear() -> ChangeItem:
    return ChangeItem(
        kind=ChangeKind.QUEUE_CLEAR,
        description="Clear the ComfyUI pending queue",
        params={},
    )


def plan_queue_interrupt() -> ChangeItem:
    return ChangeItem(
        kind=ChangeKind.QUEUE_INTERRUPT,
        description="Interrupt the currently running prompt",
        params={},
    )


def plan_workflow_save(source: str, destination: str) -> ChangeItem:
    return ChangeItem(
        kind=ChangeKind.WORKFLOW_SAVE,
        description=f"Save workflow {source} -> {destination}",
        params={"source": source, "destination": destination},
    )


def plan_history_clear(prompt_id: str | None = None) -> ChangeItem:
    desc = f"Clear history for prompt {prompt_id}" if prompt_id else "Clear all history"
    return ChangeItem(
        kind=ChangeKind.HISTORY_CLEAR,
        description=desc,
        params={"prompt_id": prompt_id},
    )
