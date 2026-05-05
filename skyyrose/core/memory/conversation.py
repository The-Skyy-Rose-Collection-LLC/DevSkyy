"""ConversationStore — SQLite-backed chronological turn buffer.

Per-thread isolation, per-agent indexing, append-only. Designed to answer
"what did we say in the last N turns?" — the question vector stores can't
answer cheaply.

For semantic recall ("when did we discuss X?"), use ``AgentMemory`` and the
shared vector store. For close-of-conversation summarization that promotes
chronological turns into durable semantic memories, use
``skyyrose.core.memory.consolidator.consolidate_thread``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default location: <project_root>/data/memory/conversations.db
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "memory" / "conversations.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_thread_time
    ON conversation_turns(thread_id, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_time
    ON conversation_turns(agent_id, created_at);
"""


@dataclass(frozen=True)
class ConversationTurn:
    """A single chronological turn in a conversation thread."""

    id: int
    thread_id: str
    agent_id: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ConversationStore:
    """SQLite-backed chronological conversation log.

    Async by wrapping sync sqlite3 calls in ``asyncio.to_thread()``. Avoids
    the aiosqlite dependency for code that mostly does small append + recent-N
    queries. If you ever need long-running streaming reads, swap in aiosqlite.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._initialized = False

    async def initialize(self) -> None:
        """Create the parent directory + run schema migration."""
        await asyncio.to_thread(self._sync_init)
        self._initialized = True
        logger.info("ConversationStore initialized at %s", self.db_path)

    def _sync_init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def append_turn(
        self,
        thread_id: str,
        agent_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Append a turn to the thread; returns the new turn ID."""
        self._require_init()
        return await asyncio.to_thread(
            self._sync_append, thread_id, agent_id, role, content, metadata
        )

    def _sync_append(
        self,
        thread_id: str,
        agent_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO conversation_turns
                    (thread_id, agent_id, role, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    agent_id,
                    role,
                    content,
                    json.dumps(metadata) if metadata else None,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    async def recent(self, thread_id: str, n: int = 10) -> list[ConversationTurn]:
        """Last n turns of a thread, oldest-first (chronological)."""
        self._require_init()
        return await asyncio.to_thread(self._sync_recent, thread_id, n)

    def _sync_recent(self, thread_id: str, n: int) -> list[ConversationTurn]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, thread_id, agent_id, role, content, metadata_json, created_at
                FROM conversation_turns
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (thread_id, n),
            ).fetchall()
        # Reverse so oldest-first
        return [self._row_to_turn(r) for r in reversed(rows)]

    async def thread_log(self, thread_id: str) -> list[ConversationTurn]:
        """Full chronological log of a thread (oldest first)."""
        self._require_init()
        return await asyncio.to_thread(self._sync_thread_log, thread_id)

    def _sync_thread_log(self, thread_id: str) -> list[ConversationTurn]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, thread_id, agent_id, role, content, metadata_json, created_at
                FROM conversation_turns
                WHERE thread_id = ?
                ORDER BY created_at ASC
                """,
                (thread_id,),
            ).fetchall()
        return [self._row_to_turn(r) for r in rows]

    async def list_threads(self, agent_id: str | None = None) -> list[str]:
        """Distinct thread_ids, optionally filtered by agent."""
        self._require_init()
        return await asyncio.to_thread(self._sync_list_threads, agent_id)

    def _sync_list_threads(self, agent_id: str | None) -> list[str]:
        with self._connect() as conn:
            if agent_id is not None:
                rows = conn.execute(
                    "SELECT DISTINCT thread_id FROM conversation_turns WHERE agent_id = ?",
                    (agent_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT DISTINCT thread_id FROM conversation_turns").fetchall()
        return [r["thread_id"] for r in rows]

    async def delete_thread(self, thread_id: str) -> int:
        """Delete all turns of a thread; returns rows deleted."""
        self._require_init()
        return await asyncio.to_thread(self._sync_delete_thread, thread_id)

    def _sync_delete_thread(self, thread_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM conversation_turns WHERE thread_id = ?", (thread_id,))
            conn.commit()
            return cur.rowcount

    @staticmethod
    def _row_to_turn(row: sqlite3.Row) -> ConversationTurn:
        return ConversationTurn(
            id=row["id"],
            thread_id=row["thread_id"],
            agent_id=row["agent_id"],
            role=row["role"],
            content=row["content"],
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _require_init(self) -> None:
        if not self._initialized:
            raise RuntimeError("ConversationStore not initialized — await initialize() first.")


__all__ = ["ConversationStore", "ConversationTurn", "DEFAULT_DB_PATH"]
