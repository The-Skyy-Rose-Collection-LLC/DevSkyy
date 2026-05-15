"""Tests for AuditTrail."""

from __future__ import annotations

import pytest

from aos.governance.audit import AuditTrail
from aos.governance.types import AuditEntry, AuditEventType


@pytest.fixture
async def audit(tmp_path) -> AuditTrail:
    db_path = tmp_path / "audit.db"
    trail = AuditTrail(db_path=str(db_path))
    await trail.initialize()
    return trail


class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_log_and_query(self, audit: AuditTrail):
        entry = AuditEntry(
            event_type=AuditEventType.PROCESS_SPAWN,
            actor_pid=0,
            target_pid=1,
            details={"agent_type": "commerce"},
        )
        await audit.log(entry)
        rows = await audit.query()
        assert len(rows) == 1
        assert rows[0].event_type == AuditEventType.PROCESS_SPAWN
        assert rows[0].details == {"agent_type": "commerce"}

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self, audit: AuditTrail):
        await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=1))
        await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_KILL, target_pid=1))
        await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=2))

        spawns = await audit.query(event_type=AuditEventType.PROCESS_SPAWN)
        assert len(spawns) == 2
        kills = await audit.query(event_type=AuditEventType.PROCESS_KILL)
        assert len(kills) == 1

    @pytest.mark.asyncio
    async def test_filter_by_target_pid(self, audit: AuditTrail):
        await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=1))
        await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=2))

        only_one = await audit.query(target_pid=1)
        assert len(only_one) == 1
        assert only_one[0].target_pid == 1

    @pytest.mark.asyncio
    async def test_filter_by_correlation_id(self, audit: AuditTrail):
        await audit.log(
            AuditEntry(
                event_type=AuditEventType.PROCESS_SPAWN,
                target_pid=1,
                correlation_id="abc",
            )
        )
        await audit.log(
            AuditEntry(
                event_type=AuditEventType.MESSAGE_SENT,
                actor_pid=1,
                correlation_id="abc",
            )
        )
        await audit.log(
            AuditEntry(
                event_type=AuditEventType.PROCESS_SPAWN,
                target_pid=2,
                correlation_id="xyz",
            )
        )

        rows = await audit.query(correlation_id="abc")
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_limit(self, audit: AuditTrail):
        for i in range(10):
            await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=i))
        rows = await audit.query(limit=5)
        assert len(rows) == 5

    @pytest.mark.asyncio
    async def test_count(self, audit: AuditTrail):
        for i in range(7):
            await audit.log(AuditEntry(event_type=AuditEventType.PROCESS_SPAWN, target_pid=i))
        assert await audit.count() == 7
        assert await audit.count(event_type=AuditEventType.PROCESS_SPAWN) == 7
        assert await audit.count(event_type=AuditEventType.PROCESS_KILL) == 0
