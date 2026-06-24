"""Session edge-case and concurrency tests — pure-Python, no MD required.

Covers malformed-JSON behaviour, schema mismatch on load, and concurrent
writes from multiple threads.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import cli_anything.marvelous.core.session as session_mod
import pytest
from cli_anything.marvelous.core.session import (Session, delete_session,
                                                 list_sessions, load_session,
                                                 new_session, save_session)

# ── Shared fixture ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def patch_sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(session_mod, "SESSIONS_DIR", tmp_path / "sessions")


# ── Malformed / schema-mismatch behaviour ─────────────────────────────────


class TestSessionSchemaEdgeCases:
    def test_malformed_json_raises_value_error(self, tmp_path):
        """load_session with corrupt JSON must raise ValueError with 'Malformed'."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        (session_dir / "corrupt.json").write_text("{bad json{{", encoding="utf-8")
        session_mod.SESSIONS_DIR = session_dir
        with pytest.raises(ValueError, match="Malformed"):
            load_session("corrupt")

    def test_schema_mismatch_unknown_fields_ignored(self):
        """Session.from_dict silently drops unknown keys — no KeyError."""
        data = {
            "session_id": "schema-test",
            "project_path": "/tmp/x.zpac",
            "unknown_future_field": "some_value",
            "another_unknown": 999,
        }
        s = Session.from_dict(data)
        assert s.session_id == "schema-test"
        assert s.project_path == "/tmp/x.zpac"

    def test_schema_mismatch_missing_optional_fields_uses_defaults(self):
        """A JSON with only session_id fills other fields with defaults."""
        s = Session.from_dict({"session_id": "minimal"})
        assert s.garment_name == ""
        assert s.simulation_frames == 100
        assert s.last_export_path == ""
        assert s.notes == ""

    def test_list_sessions_skips_corrupt_entries(self, tmp_path):
        """list_sessions must skip unreadable JSON rather than crashing."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        session_mod.SESSIONS_DIR = session_dir

        # Write one valid and one corrupt session
        good = Session(session_id="good-one", project_path="/tmp/ok.zpac")
        save_session(good)
        (session_dir / "bad.json").write_text("{{corrupt", encoding="utf-8")

        result = list_sessions()
        assert len(result) == 1
        assert result[0].session_id == "good-one"

    def test_empty_json_object_missing_required_field_raises(self):
        """Session.from_dict({}) must raise TypeError because session_id is required."""
        with pytest.raises(TypeError):
            Session.from_dict({})

    def test_session_updated_at_changes_on_save(self):
        """save_session must bump updated_at each time it is called."""
        import time

        s = Session(session_id="time-test", updated_at=0.0)
        save_session(s)
        loaded = load_session("time-test")
        assert loaded.updated_at > 0.0
        assert loaded.updated_at == pytest.approx(time.time(), abs=5.0)


# ── Concurrent writes ─────────────────────────────────────────────────────


class TestSessionConcurrentWrites:
    def test_concurrent_saves_produce_valid_json(self, tmp_path):
        """8 threads each saving the same session must leave valid JSON on disk."""
        session_dir = tmp_path / "sessions"
        session_mod.SESSIONS_DIR = session_dir

        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                s = Session(
                    session_id="shared-session",
                    project_path=f"/tmp/project_{i}.zpac",
                    notes=f"worker-{i}",
                )
                save_session(s)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Threads raised errors: {errors}"

        # The file must be valid JSON after all concurrent writes
        session_file = session_dir / "shared-session.json"
        assert session_file.exists()
        with session_file.open(encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["session_id"] == "shared-session"

    def test_concurrent_different_sessions_all_written(self, tmp_path):
        """8 threads writing 8 distinct session IDs must all succeed."""
        session_dir = tmp_path / "sessions"
        session_mod.SESSIONS_DIR = session_dir

        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                s = Session(session_id=f"session-{i}", project_path=f"/tmp/{i}.zpac")
                save_session(s)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        sessions = list_sessions()
        assert len(sessions) == 8

    def test_concurrent_new_sessions_all_distinct_ids(self, tmp_path):
        """new_session() from concurrent threads must produce distinct IDs."""
        session_dir = tmp_path / "sessions"
        session_mod.SESSIONS_DIR = session_dir

        created_ids: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            s = new_session(project_path="/tmp/x.zpac")
            with lock:
                created_ids.append(s.session_id)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(created_ids) == len(set(created_ids)), "Duplicate session IDs generated"
