"""Session management for cli-anything-marvelous.

Sessions persist CLI state across invocations: open project path,
active garment, simulation settings. Written atomically via
_locked_save_json so concurrent CLI processes don't corrupt state.
"""

from __future__ import annotations

import itertools
import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Thread-safe monotonic counter to ensure unique session IDs even when
# multiple threads call new_session() within the same millisecond.
_session_counter = itertools.count()
_session_counter_lock = threading.Lock()

# Default location; tests monkeypatch this to tmp_path or set MARVELOUS_SESSIONS_DIR
SESSIONS_DIR = Path(
    os.environ.get("MARVELOUS_SESSIONS_DIR", "")
    or str(Path.home() / ".cli-anything-marvelous" / "sessions")
)


# ── Atomic write ─────────────────────────────────────────────────────────


def _locked_save_json(path: Path, payload: dict[str, Any]) -> None:
    """Write *payload* to *path* atomically with an exclusive lock.

    Uses tempfile + os.replace so a crashed write never leaves a
    half-written JSON.  The fcntl lock is best-effort (skipped on
    Windows or if the OS refuses it).
    """
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


# ── Session model ────────────────────────────────────────────────────────


@dataclass
class Session:
    """Represents a single CLI work session for Marvelous Designer."""

    session_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    project_path: str = ""
    garment_name: str = ""
    simulation_frames: int = 100
    last_export_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        valid = {k for k in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


# ── CRUD ─────────────────────────────────────────────────────────────────


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def save_session(session: Session) -> Path:
    """Persist *session* to disk.  Returns the path written."""
    session.updated_at = time.time()
    path = _session_path(session.session_id)
    _locked_save_json(path, session.to_dict())
    return path


def load_session(session_id: str) -> Session:
    """Load session by ID.

    Raises:
        FileNotFoundError: Session does not exist.
        ValueError: JSON is malformed.
    """
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session '{session_id}' not found at {path}")
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed session JSON at {path}: {exc}") from exc
    return Session.from_dict(data)


def list_sessions() -> list[Session]:
    """Return all sessions, sorted newest-first."""
    if not SESSIONS_DIR.exists():
        return []
    sessions: list[Session] = []
    for p in SESSIONS_DIR.glob("*.json"):
        try:
            with p.open(encoding="utf-8") as fh:
                sessions.append(Session.from_dict(json.load(fh)))
        except (json.JSONDecodeError, TypeError):
            continue
    return sorted(sessions, key=lambda s: s.updated_at, reverse=True)


def delete_session(session_id: str) -> bool:
    """Delete session by ID.  Returns True if deleted, False if not found."""
    path = _session_path(session_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def new_session(project_path: str = "", garment_name: str = "") -> Session:
    """Create and save a new session with a unique timestamp+counter ID."""
    with _session_counter_lock:
        seq = next(_session_counter)
    session_id = f"md-{int(time.time() * 1000)}-{seq}"
    s = Session(
        session_id=session_id,
        project_path=project_path,
        garment_name=garment_name,
    )
    save_session(s)
    return s
