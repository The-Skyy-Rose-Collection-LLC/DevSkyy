"""
Session persistence for cli-anything-skyyrose-theme.

Sessions store: name, timestamps, command history, and arbitrary metadata.
All writes are atomic via _locked_save_json (temp file + fcntl.flock + fsync
+ os.replace — same pattern as cli-anything-elementor).

SESSIONS_DIR: ~/.cli_anything/skyyrose_theme/sessions/
SCHEMA: cli-anything-skyyrose-theme/session/v1
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "cli-anything-skyyrose-theme/session/v1"
MAX_HISTORY = 50
SESSIONS_DIR = Path.home() / ".cli_anything" / "skyyrose_theme" / "sessions"


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class SessionError(RuntimeError):
    """Base class for session errors."""


class SessionNotFoundError(SessionError):
    """Raised when a session file cannot be found."""


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default"
    schema: str = SCHEMA
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    history: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def add_history(self, command: str) -> None:
        """Append *command* to history, trimming to MAX_HISTORY."""
        self.history = [*self.history, command][-MAX_HISTORY:]
        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "default"),
            schema=data.get("schema", SCHEMA),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            history=data.get("history", []),
            meta=data.get("meta", {}),
        )


# ---------------------------------------------------------------------------
# Atomic file writer
# ---------------------------------------------------------------------------


def _locked_save_json(path: Path, data: dict[str, Any]) -> None:
    """
    Write *data* as JSON to *path* atomically.

    Uses a sibling lock file + fcntl.flock to prevent concurrent writers,
    then writes to a temp file in the same directory, fsyncs, and
    os.replaces into the final path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")

    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
        try:
            dir_ = path.parent
            fd, tmp_path_str = tempfile.mkstemp(dir=dir_, prefix=".session-")
            tmp_path = Path(tmp_path_str)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2)
                    fh.write("\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_path, path)
            except Exception:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
                raise
        finally:
            fcntl.flock(lock_fh, fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def _session_path(session_id: str, sessions_dir: Path | None = None) -> Path:
    d = sessions_dir or SESSIONS_DIR
    return d / f"{session_id}.json"


def save_session(session: Session, sessions_dir: Path | None = None) -> Path:
    """Persist *session* and return its file path."""
    path = _session_path(session.id, sessions_dir)
    session.updated_at = time.time()
    _locked_save_json(path, session.to_dict())
    return path


def load_session(session_id: str, sessions_dir: Path | None = None) -> Session:
    """Load session by ID. Raises SessionNotFoundError if missing."""
    path = _session_path(session_id, sessions_dir)
    if not path.exists():
        raise SessionNotFoundError(f"Session not found: {session_id} ({path})")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Session.from_dict(data)


def list_sessions(sessions_dir: Path | None = None) -> list[Session]:
    """Return all sessions sorted by updated_at descending."""
    d = sessions_dir or SESSIONS_DIR
    if not d.exists():
        return []
    sessions = []
    for p in d.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append(Session.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(sessions, key=lambda s: s.updated_at, reverse=True)


def delete_session(session_id: str, sessions_dir: Path | None = None) -> bool:
    """Delete session file. Returns True if deleted, False if not found."""
    path = _session_path(session_id, sessions_dir)
    if not path.exists():
        return False
    path.unlink()
    lock_path = path.with_suffix(".lock")
    if lock_path.exists():
        lock_path.unlink()
    return True


def get_or_create_session(name: str = "default", sessions_dir: Path | None = None) -> Session:
    """
    Return the most-recently-updated session with *name*, creating one if
    none exists.
    """
    existing = [s for s in list_sessions(sessions_dir) if s.name == name]
    if existing:
        return existing[0]
    session = Session(name=name)
    save_session(session, sessions_dir)
    return session
