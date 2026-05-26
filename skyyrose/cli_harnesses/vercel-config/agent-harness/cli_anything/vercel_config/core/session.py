"""Session management for cli-anything-vercel-config.

Sessions persist the active project reference (id_or_name + optional teamId)
across REPL invocations so users don't have to re-type ``--project`` each time.

Storage layout::

    ~/.cli_anything/vercel_config/sessions/<name>.json

Each session file schema (SCHEMA constant)::

    {
      "schema": "cli-anything-vercel-config/session/v1",
      "name": "my-session",
      "project": "my-project",
      "teamId": null,
      "history": ["project show", "env list"],
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:01:00Z"
    }
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────

SCHEMA = "cli-anything-vercel-config/session/v1"
SESSIONS_DIR = Path.home() / ".cli_anything" / "vercel_config" / "sessions"
MAX_HISTORY = 200


# ── Dataclass ─────────────────────────────────────────────────────────


@dataclass
class Session:
    """Persisted REPL session for the vercel-config CLI.

    Attributes:
        name:       Session label (used as filename stem).
        project:    Project id_or_name.
        team_id:    Optional Vercel team ID.
        history:    List of recent commands (capped at MAX_HISTORY).
        created_at: ISO-8601 creation timestamp.
        updated_at: ISO-8601 last-modified timestamp.
    """

    name: str
    project: str
    team_id: Optional[str] = field(default=None)
    history: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Session.name must not be empty.")
        if not self.project or not self.project.strip():
            raise ValueError("Session.project must not be empty.")

    def push_history(self, command: str) -> None:
        """Append a command to history, evicting oldest if over MAX_HISTORY."""
        if command and command.strip():
            self.history.append(command.strip())
            if len(self.history) > MAX_HISTORY:
                self.history = self.history[-MAX_HISTORY:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA,
            "name": self.name,
            "project": self.project,
            "teamId": self.team_id,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            name=data["name"],
            project=data["project"],
            team_id=data.get("teamId"),
            history=data.get("history", []),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
        )


# ── Persistence helpers ───────────────────────────────────────────────


def _session_path(name: str, sessions_dir: Path = SESSIONS_DIR) -> Path:
    return sessions_dir / f"{name}.json"


def save(session: Session, sessions_dir: Path = SESSIONS_DIR) -> Path:
    """Atomically persist a session to disk.

    Args:
        session:      Session to save.
        sessions_dir: Override default sessions directory (used in tests).

    Returns:
        Path to the written session file.
    """
    session.updated_at = _now_iso()
    path = _session_path(session.name, sessions_dir)
    _locked_save_json(path, session.to_dict())
    return path


def load(name: str, sessions_dir: Path = SESSIONS_DIR) -> Session:
    """Load a session by name.

    Args:
        name:         Session name (file stem).
        sessions_dir: Override default sessions directory.

    Returns:
        Parsed ``Session`` instance.

    Raises:
        FileNotFoundError: If the session file does not exist.
        ValueError:         If the JSON is malformed or missing required fields.
    """
    path = _session_path(name, sessions_dir)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Session not found: {name!r} (looked at {path})")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Session file corrupt: {path}: {exc}") from exc

    return Session.from_dict(data)


def delete(name: str, sessions_dir: Path = SESSIONS_DIR) -> bool:
    """Delete a session file.

    Returns:
        True if deleted, False if file did not exist.
    """
    path = _session_path(name, sessions_dir)
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def list_sessions(sessions_dir: Path = SESSIONS_DIR) -> List[Session]:
    """Return all saved sessions, sorted by updated_at descending.

    Args:
        sessions_dir: Override default sessions directory.

    Returns:
        List of ``Session`` instances (may be empty).
    """
    sessions_dir.mkdir(parents=True, exist_ok=True)
    results: List[Session] = []
    for p in sessions_dir.glob("*.json"):
        try:
            raw = p.read_text(encoding="utf-8")
            data = json.loads(raw)
            results.append(Session.from_dict(data))
        except Exception:
            continue  # skip corrupt files silently
    results.sort(key=lambda s: s.updated_at, reverse=True)
    return results


# ── Atomic write ──────────────────────────────────────────────────────


def _locked_save_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON to path atomically using temp file + fcntl.flock + os.replace.

    This is the canonical _locked_save_json pattern for cli-anything harnesses.
    Uses best-effort locking (POSIX only); silently skips on Windows/ImportError.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".session-", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass  # Best-effort — POSIX-only.
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


# ── Timestamp helper ──────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
