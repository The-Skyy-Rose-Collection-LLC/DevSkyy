"""Session state for cli-anything-trellis.

Persists active context across REPL commands: current working directory,
default resolution preset, default output directory, recent job IDs,
and arbitrary key-value settings.

Storage: ~/.cli_anything/trellis/sessions/<name>.json
Writes:  atomic temp-file + os.replace, with fcntl.flock on POSIX.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────

SCHEMA = "cli-anything-trellis/session/v1"
SESSIONS_DIR = Path.home() / ".cli_anything" / "trellis" / "sessions"
DEFAULT_SESSION_NAME = "default"
MAX_HISTORY = 50  # maximum recent job IDs kept in session


# ── Atomic write ─────────────────────────────────────────────────────────────


def _locked_save_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write *payload* to *path* atomically using a temp file + os.replace.

    Uses fcntl.flock on POSIX to prevent concurrent-write corruption.
    Falls back silently when fcntl is unavailable (Windows / restricted env).
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


# ── Session dataclass ─────────────────────────────────────────────────────────


@dataclass
class Session:
    """Persistent REPL session state for cli-anything-trellis.

    Attributes:
        name: Session identifier (used as filename stem).
        trellis_home: Path to TRELLIS.2 installation (overrides env var).
        trellis_python: Path to Python interpreter with trellis2 installed.
        default_resolution: Default preset ("low" or "high").
        default_output_dir: Default directory for GLB outputs.
        settings: Arbitrary user-defined key-value pairs.
        history: List of recent job IDs (most recent last), capped at MAX_HISTORY.
        created_at: POSIX timestamp of session creation.
        updated_at: POSIX timestamp of last save.
        schema: Schema version string for future migration.
    """

    name: str = DEFAULT_SESSION_NAME
    trellis_home: Optional[str] = None
    trellis_python: Optional[str] = None
    default_resolution: str = "high"
    default_output_dir: Optional[str] = None
    settings: Dict[str, str] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    schema: str = SCHEMA

    # ── Persistence ───────────────────────────────────────────────────────────

    @staticmethod
    def session_path(name: str) -> Path:
        """Return the filesystem path for session *name*."""
        return SESSIONS_DIR / f"{name}.json"

    def save(self) -> None:
        """Persist session to disk atomically."""
        self.updated_at = time.time()
        _locked_save_json(self.session_path(self.name), self._to_dict())

    def delete(self) -> bool:
        """Remove the session file from disk. Returns True if file existed."""
        p = self.session_path(self.name)
        if p.exists():
            p.unlink()
            return True
        return False

    @classmethod
    def load(cls, name: str = DEFAULT_SESSION_NAME) -> "Session":
        """Load a session by name, creating a new default if not found."""
        path = cls.session_path(name)
        if not path.exists():
            return cls(name=name)
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return cls._from_dict(name, data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted session file — return fresh session
            return cls(name=name)

    @staticmethod
    def list_sessions() -> List[str]:
        """Return sorted list of session names that exist on disk."""
        if not SESSIONS_DIR.exists():
            return []
        return sorted(p.stem for p in SESSIONS_DIR.iterdir() if p.suffix == ".json")

    # ── Mutation helpers (return new Session for immutability) ────────────────

    def push_history(self, job_id: str) -> "Session":
        """Return new Session with *job_id* appended to history (capped)."""
        new_history = (self.history + [job_id])[-MAX_HISTORY:]
        return Session(**{**self._to_dict_fields(), "history": new_history})

    def set_setting(self, key: str, value: str) -> "Session":
        """Return new Session with settings[key]=value."""
        new_settings = {**self.settings, key: value}
        return Session(**{**self._to_dict_fields(), "settings": new_settings})

    def unset_setting(self, key: str) -> "Session":
        """Return new Session with *key* removed from settings."""
        new_settings = {k: v for k, v in self.settings.items() if k != key}
        return Session(**{**self._to_dict_fields(), "settings": new_settings})

    # ── Serialization ─────────────────────────────────────────────────────────

    def _to_dict_fields(self) -> Dict[str, Any]:
        """Return constructor kwargs dict (excludes schema for clarity)."""
        return {
            "name": self.name,
            "trellis_home": self.trellis_home,
            "trellis_python": self.trellis_python,
            "default_resolution": self.default_resolution,
            "default_output_dir": self.default_output_dir,
            "settings": dict(self.settings),
            "history": list(self.history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema": self.schema,
        }

    def _to_dict(self) -> Dict[str, Any]:
        """Full serialization dict written to JSON."""
        return self._to_dict_fields()

    @classmethod
    def _from_dict(cls, name: str, data: Dict[str, Any]) -> "Session":
        return cls(
            name=name,
            trellis_home=data.get("trellis_home"),
            trellis_python=data.get("trellis_python"),
            default_resolution=data.get("default_resolution", "high"),
            default_output_dir=data.get("default_output_dir"),
            settings=data.get("settings", {}),
            history=data.get("history", []),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            schema=data.get("schema", SCHEMA),
        )

    def __repr__(self) -> str:
        return (
            f"Session(name={self.name!r}, resolution={self.default_resolution!r}, "
            f"jobs={len(self.history)})"
        )
