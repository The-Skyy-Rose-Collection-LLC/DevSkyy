"""
Session management for cli-anything-hf-spaces.

Sessions track recent Space interactions for context within a CLI session.
Token is NEVER stored in session JSON — it is in-memory only.

Uses _locked_save_json for atomic writes (POSIX flock + tempfile + os.replace).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Session storage root
_SESSIONS_DIR = Path.home() / ".cli_anything" / "hf_spaces" / "sessions"

SCHEMA = "1"
MAX_HISTORY = 50


# ---------------------------------------------------------------------------
# Atomic write helper (verbatim pattern from elementor harness)
# ---------------------------------------------------------------------------


def _locked_save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".session-", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            try:
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------


@dataclass
class Session:
    session_id: str
    created_at: float
    updated_at: float
    space_id: Optional[str] = None  # last active space (owner/name)
    history: List[Dict[str, Any]] = field(default_factory=list)

    # NOTE: token is intentionally absent — never serialised.

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def new(cls, space_id: Optional[str] = None) -> "Session":
        now = time.time()
        return cls(
            session_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            space_id=space_id,
        )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def push_history(self, entry: Dict[str, Any]) -> None:
        """Append an entry to history, capping at MAX_HISTORY."""
        entry = dict(entry)
        entry.setdefault("ts", time.time())
        self.history.append(entry)
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        self.updated_at = time.time()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "space_id": self.space_id,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            space_id=data.get("space_id"),
            history=data.get("history", []),
        )


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def sessions_dir() -> Path:
    return _SESSIONS_DIR


def session_path(session_id: str) -> Path:
    return _SESSIONS_DIR / f"{session_id}.json"


def save(session: Session) -> None:
    """Atomically persist a session to disk."""
    _locked_save_json(session_path(session.session_id), session.to_dict())


def load(session_id: str) -> Session:
    """
    Load a session by ID.

    Raises:
        FileNotFoundError: if the session does not exist.
        ValueError: if the JSON is malformed.
    """
    path = session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session '{session_id}' not found at {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Session.from_dict(data)
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"Malformed session file {path}: {exc}") from exc


def delete(session_id: str) -> bool:
    """
    Delete a session file.

    Returns True if deleted, False if not found.
    """
    path = session_path(session_id)
    if path.exists():
        path.unlink()
        return True
    return False


def list_sessions() -> List[Session]:
    """
    Return all stored sessions, sorted newest-first by updated_at.

    Silently skips malformed files.
    """
    if not _SESSIONS_DIR.exists():
        return []
    sessions: List[Session] = []
    for p in _SESSIONS_DIR.glob("*.json"):
        try:
            with p.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            sessions.append(Session.from_dict(data))
        except Exception:
            continue
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    return sessions
