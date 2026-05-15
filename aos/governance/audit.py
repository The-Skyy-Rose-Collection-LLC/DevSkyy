"""AuditTrail — immutable append-only audit log backed by SQLite.

Every kernel action (spawn, kill, message-sent, budget-exceeded, etc.) is
logged here. Queryable by event_type, actor/target PID, correlation_id, time range.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import aiosqlite

from aos.governance.types import AuditEntry, AuditEventType

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_pid INTEGER,
    target_pid INTEGER,
    details TEXT NOT NULL,
    correlation_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_pid ON audit_log(actor_pid);
CREATE INDEX IF NOT EXISTS idx_audit_target_pid ON audit_log(target_pid);
CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
"""


class AuditTrail:
    """Append-only audit log persisted to SQLite.

    Call initialize() once after construction to create the schema.
    All write operations are atomic. Reads are non-blocking.
    """

    def __init__(self, db_path: str | Path = "aos_audit.db") -> None:
        self._db_path = str(db_path)
        self._initialized = False
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Open the persistent connection and create the schema. Idempotent."""
        if self._initialized:
            return
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()
        self._initialized = True

    async def close(self) -> None:
        """Close the persistent connection. Safe to call multiple times."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
        self._initialized = False

    def _require_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            msg = "AuditTrail not initialized — call await audit.initialize() first"
            raise RuntimeError(msg)
        return self._conn

    async def log(self, entry: AuditEntry) -> None:
        """Append an audit entry to the log."""
        conn = self._require_conn()
        async with self._lock:
            await conn.execute(
                """
                INSERT INTO audit_log (
                    id, timestamp, event_type, actor_pid, target_pid, details, correlation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entry.to_row(),
            )
            await conn.commit()

    async def query(
        self,
        *,
        event_type: AuditEventType | None = None,
        actor_pid: int | None = None,
        target_pid: int | None = None,
        correlation_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query the audit log with optional filters. Results ordered newest-first."""
        clauses: list[str] = []
        params: list[object] = []

        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type.value)
        if actor_pid is not None:
            clauses.append("actor_pid = ?")
            params.append(actor_pid)
        if target_pid is not None:
            clauses.append("target_pid = ?")
            params.append(target_pid)
        if correlation_id is not None:
            clauses.append("correlation_id = ?")
            params.append(correlation_id)
        if since is not None:
            clauses.append("timestamp >= ?")
            params.append(since.isoformat())
        if until is not None:
            clauses.append("timestamp <= ?")
            params.append(until.isoformat())

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT id, timestamp, event_type, actor_pid, target_pid, details, correlation_id "
            f"FROM audit_log{where} ORDER BY timestamp DESC LIMIT ?"
        )
        params.append(limit)

        rows: list[AuditEntry] = []
        conn = self._require_conn()
        async with conn.execute(sql, params) as cursor:
            async for row in cursor:
                rows.append(_row_to_entry(row))
        return rows

    async def count(
        self,
        *,
        event_type: AuditEventType | None = None,
        actor_pid: int | None = None,
        target_pid: int | None = None,
    ) -> int:
        """Count entries matching the filters."""
        clauses: list[str] = []
        params: list[object] = []
        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type.value)
        if actor_pid is not None:
            clauses.append("actor_pid = ?")
            params.append(actor_pid)
        if target_pid is not None:
            clauses.append("target_pid = ?")
            params.append(target_pid)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT COUNT(*) FROM audit_log{where}"
        conn = self._require_conn()
        async with conn.execute(sql, params) as cursor:
            row = await cursor.fetchone()
        return int(row[0]) if row else 0


def _row_to_entry(row: tuple) -> AuditEntry:
    """Convert a SQLite row into an AuditEntry."""
    id_, ts_str, event_type, actor_pid, target_pid, details_json, correlation_id = row
    return AuditEntry(
        id=id_,
        timestamp=datetime.fromisoformat(ts_str),
        event_type=AuditEventType(event_type),
        actor_pid=actor_pid,
        target_pid=target_pid,
        details=json.loads(details_json) if details_json else {},
        correlation_id=correlation_id,
    )
