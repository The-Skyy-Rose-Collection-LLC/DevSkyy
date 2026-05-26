"""Session persistence for cli-anything-comfyui.

Each session is a JSON file in ``~/.cli_anything/comfyui/sessions/``.
History is capped at MAX_HISTORY entries; oldest entries are dropped.

Atomic writes use tempfile + fcntl.flock + os.replace (same pattern as
manifest.py) so a crash mid-write never corrupts a session.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_HISTORY = 50

_SESSIONS_DIR = Path.home() / ".cli_anything" / "comfyui" / "sessions"


@dataclass
class Session:
    """Persistent session tracking ComfyUI interactions."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    host: str = "http://127.0.0.1:8188"
    history: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # history
    # ------------------------------------------------------------------

    def push_history(self, entry: dict[str, Any]) -> None:
        """Append *entry* to history, dropping oldest if cap exceeded."""
        self.history.append(entry)
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        self.updated_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "host": self.host,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            host=data.get("host", "http://127.0.0.1:8188"),
            history=data.get("history", []),
        )


# ---------------------------------------------------------------------------
# Atomic I/O helpers (same lock pattern as manifest.py)
# ---------------------------------------------------------------------------


def _locked_save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".session_")
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


def _session_path(session_id: str, sessions_dir: Path | None = None) -> Path:
    base = sessions_dir or _SESSIONS_DIR
    return base / f"{session_id}.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def save_session(session: Session, sessions_dir: Path | None = None) -> Path:
    """Persist *session* atomically.  Returns the path written."""
    path = _session_path(session.session_id, sessions_dir)
    _locked_save_json(path, session.to_dict())
    return path


def load_session(session_id: str, sessions_dir: Path | None = None) -> Session:
    """Load a session by ID.  Raises :exc:`FileNotFoundError` if missing."""
    path = _session_path(session_id, sessions_dir)
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Session.from_dict(data)


def delete_session(session_id: str, sessions_dir: Path | None = None) -> bool:
    """Delete a session file.  Returns True if deleted, False if not found."""
    path = _session_path(session_id, sessions_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def list_sessions(sessions_dir: Path | None = None) -> list[dict[str, str]]:
    """Return summary dicts for all persisted sessions (sorted by updated_at desc)."""
    base = sessions_dir or _SESSIONS_DIR
    if not base.exists():
        return []
    summaries: list[dict[str, str]] = []
    for p in base.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            summaries.append(
                {
                    "session_id": data.get("session_id", p.stem),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "host": data.get("host", ""),
                }
            )
        except (json.JSONDecodeError, KeyError):
            pass
    summaries.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return summaries
