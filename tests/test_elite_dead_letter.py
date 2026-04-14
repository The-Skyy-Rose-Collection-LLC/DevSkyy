"""
Tests for DeadLetterQueue.

Uses fakeredis to avoid requiring a live Redis instance.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import fakeredis
import pytest

from skyyrose.elite_studio.queue.dead_letter import (
    DeadLetterQueue,
    _DLQ_KEY,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis_server():
    return fakeredis.FakeServer()


@pytest.fixture()
def fake_redis(fake_redis_server):
    return fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture()
def dlq(fake_redis):
    d = DeadLetterQueue()
    d._redis = fake_redis
    return d


def _make_original_data(sku: str = "br-001") -> dict:
    return {
        "sku": sku,
        "view": "front",
        "priority": 5,
        "enable_compositor": False,
        "max_retries": 2,
    }


# ---------------------------------------------------------------------------
# move_to_dlq()
# ---------------------------------------------------------------------------


def test_move_to_dlq_adds_entry(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:aabb1234", "pipeline failed", _make_original_data())
    assert fake_redis.llen(_DLQ_KEY) == 1


def test_move_to_dlq_stores_correct_job_id(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:aabb1234", "some error", _make_original_data())
    raw = fake_redis.lindex(_DLQ_KEY, 0)
    entry = json.loads(raw)
    assert entry["job_id"] == "elite:br-001:aabb1234"


def test_move_to_dlq_stores_error_message(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:errmsg", "timeout exceeded", _make_original_data())
    raw = fake_redis.lindex(_DLQ_KEY, 0)
    entry = json.loads(raw)
    assert "timeout exceeded" in entry["error"]


def test_move_to_dlq_stores_sku(dlq, fake_redis):
    dlq.move_to_dlq("elite:sg-005:xyz", "error", _make_original_data("sg-005"))
    raw = fake_redis.lindex(_DLQ_KEY, 0)
    entry = json.loads(raw)
    assert entry["sku"] == "sg-005"


def test_move_to_dlq_stores_failed_at_timestamp(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:ts", "error", _make_original_data())
    raw = fake_redis.lindex(_DLQ_KEY, 0)
    entry = json.loads(raw)
    assert "failed_at" in entry
    # Must be a parseable ISO datetime
    datetime.fromisoformat(entry["failed_at"])


def test_move_to_dlq_stores_original_data(dlq, fake_redis):
    orig = _make_original_data("lh-002")
    dlq.move_to_dlq("elite:lh-002:orig", "error", orig)
    raw = fake_redis.lindex(_DLQ_KEY, 0)
    entry = json.loads(raw)
    assert entry["original_data"]["sku"] == "lh-002"


def test_move_to_dlq_degrades_when_redis_unavailable():
    d = DeadLetterQueue()
    d._redis = None
    # Must not raise
    d.move_to_dlq("elite:br-001:noredis", "error", _make_original_data())


def test_move_to_dlq_works_without_original_data(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:nodata", "error")
    assert fake_redis.llen(_DLQ_KEY) == 1


# ---------------------------------------------------------------------------
# list_failed()
# ---------------------------------------------------------------------------


def test_list_failed_returns_all_entries(dlq):
    dlq.move_to_dlq("elite:br-001:a", "err1", _make_original_data())
    dlq.move_to_dlq("elite:br-002:b", "err2", _make_original_data("br-002"))
    dlq.move_to_dlq("elite:sg-001:c", "err3", _make_original_data("sg-001"))

    entries = dlq.list_failed()
    assert len(entries) == 3


def test_list_failed_returns_empty_when_dlq_empty(dlq):
    assert dlq.list_failed() == []


def test_list_failed_returns_empty_when_redis_unavailable():
    d = DeadLetterQueue()
    d._redis = None
    assert d.list_failed() == []


def test_list_failed_entries_are_dicts(dlq):
    dlq.move_to_dlq("elite:br-001:dict", "error", _make_original_data())
    entries = dlq.list_failed()
    assert all(isinstance(e, dict) for e in entries)


# ---------------------------------------------------------------------------
# retry()
# ---------------------------------------------------------------------------


def test_retry_removes_entry_from_dlq(dlq, fake_redis):
    dlq.move_to_dlq("elite:br-001:retry1", "error", _make_original_data())
    assert fake_redis.llen(_DLQ_KEY) == 1

    new_job_id_holder = []
    with patch(
        "skyyrose.elite_studio.queue.producer.enqueue_produce", return_value="elite:br-001:newjob"
    ) as mock_enqueue:
        new_id = dlq.retry("elite:br-001:retry1")
        new_job_id_holder.append(new_id)

    assert fake_redis.llen(_DLQ_KEY) == 0
    assert new_job_id_holder[0] == "elite:br-001:newjob"


def test_retry_calls_enqueue_produce_with_correct_sku(dlq):
    dlq.move_to_dlq("elite:sg-005:rtry", "error", _make_original_data("sg-005"))

    with patch(
        "skyyrose.elite_studio.queue.producer.enqueue_produce", return_value="elite:sg-005:new"
    ) as mock_enqueue:
        dlq.retry("elite:sg-005:rtry")

    mock_enqueue.assert_called_once()
    assert (
        mock_enqueue.call_args.kwargs.get("sku") == "sg-005"
        or mock_enqueue.call_args.args[0] == "sg-005"
    )


def test_retry_raises_key_error_for_unknown_job(dlq):
    with pytest.raises(KeyError, match="not found in DLQ"):
        dlq.retry("elite:nonexistent:000")


def test_retry_raises_runtime_error_when_redis_unavailable():
    d = DeadLetterQueue()
    d._redis = None
    with pytest.raises(RuntimeError, match="Redis unavailable"):
        d.retry("elite:br-001:any")


def test_retry_preserves_other_entries(dlq):
    dlq.move_to_dlq("elite:br-001:keep", "err", _make_original_data())
    dlq.move_to_dlq("elite:br-002:gone", "err", _make_original_data("br-002"))

    with patch(
        "skyyrose.elite_studio.queue.producer.enqueue_produce", return_value="elite:br-002:new"
    ):
        dlq.retry("elite:br-002:gone")

    remaining = dlq.list_failed()
    job_ids = [e["job_id"] for e in remaining]
    assert "elite:br-001:keep" in job_ids
    assert "elite:br-002:gone" not in job_ids


# ---------------------------------------------------------------------------
# purge()
# ---------------------------------------------------------------------------


def test_purge_removes_old_entries(dlq, fake_redis):
    # Insert an entry with an old failed_at
    old_entry = {
        "job_id": "elite:br-001:oldentry",
        "sku": "br-001",
        "error": "old error",
        "failed_at": (datetime.now(UTC) - timedelta(hours=100)).isoformat(),
        "original_data": _make_original_data(),
    }
    fake_redis.lpush(_DLQ_KEY, json.dumps(old_entry))

    count = dlq.purge(older_than_hours=72)
    assert count == 1
    assert fake_redis.llen(_DLQ_KEY) == 0


def test_purge_keeps_recent_entries(dlq, fake_redis):
    # Insert a recent entry
    recent_entry = {
        "job_id": "elite:br-001:recent",
        "sku": "br-001",
        "error": "recent error",
        "failed_at": datetime.now(UTC).isoformat(),
        "original_data": _make_original_data(),
    }
    fake_redis.lpush(_DLQ_KEY, json.dumps(recent_entry))

    count = dlq.purge(older_than_hours=72)
    assert count == 0
    assert fake_redis.llen(_DLQ_KEY) == 1


def test_purge_returns_zero_when_dlq_empty(dlq):
    assert dlq.purge() == 0


def test_purge_returns_zero_when_redis_unavailable():
    d = DeadLetterQueue()
    d._redis = None
    assert d.purge() == 0


def test_purge_mixed_entries(dlq, fake_redis):
    now = datetime.now(UTC)
    for i in range(3):
        old_entry = {
            "job_id": f"elite:br-00{i}:old",
            "sku": f"br-00{i}",
            "error": "old",
            "failed_at": (now - timedelta(hours=80)).isoformat(),
            "original_data": {},
        }
        fake_redis.lpush(_DLQ_KEY, json.dumps(old_entry))

    for i in range(2):
        recent_entry = {
            "job_id": f"elite:sg-00{i}:recent",
            "sku": f"sg-00{i}",
            "error": "recent",
            "failed_at": now.isoformat(),
            "original_data": {},
        }
        fake_redis.lpush(_DLQ_KEY, json.dumps(recent_entry))

    purged = dlq.purge(older_than_hours=72)
    assert purged == 3
    assert fake_redis.llen(_DLQ_KEY) == 2
