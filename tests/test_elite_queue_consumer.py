"""
Tests for EliteStudioWorker (consumer).

Mocks run_single() and Redis to avoid live dependencies.
"""

from __future__ import annotations

import json
import signal
from datetime import UTC, datetime
from unittest.mock import patch

import fakeredis
import pytest

from skyyrose.elite_studio.queue.consumer import (
    EliteStudioWorker,
    _EVENT_CHANNEL,
    _RESULT_KEY_PREFIX,
)
from skyyrose.elite_studio.queue.job_types import EliteStudioJobData, EliteStudioJobResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis_server():
    """Shared fakeredis server for the test session."""
    return fakeredis.FakeServer()


@pytest.fixture()
def fake_redis(fake_redis_server):
    """Per-test fakeredis client connected to the shared server."""
    return fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture()
def worker(fake_redis):
    """EliteStudioWorker with its Redis client replaced by fakeredis."""
    w = EliteStudioWorker(concurrency=1)
    w._redis = fake_redis
    return w


@pytest.fixture()
def job_data():
    return EliteStudioJobData(sku="br-001", view="front", priority=5)


# ---------------------------------------------------------------------------
# _store_result
# ---------------------------------------------------------------------------


def test_store_result_writes_to_redis(worker, fake_redis):
    result = EliteStudioJobResult(
        job_id="elite:br-001:abc12345",
        sku="br-001",
        status="success",
        output_path="/some/path.jpg",
        completed_at=datetime.now(UTC).isoformat(),
    )
    worker._store_result(result)

    raw = fake_redis.get(f"{_RESULT_KEY_PREFIX}elite:br-001:abc12345")
    assert raw is not None
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["output_path"] == "/some/path.jpg"


def test_store_result_sets_ttl(worker, fake_redis):
    result = EliteStudioJobResult(
        job_id="elite:br-001:ttltest",
        sku="br-001",
        status="success",
    )
    worker._store_result(result)

    ttl = fake_redis.ttl(f"{_RESULT_KEY_PREFIX}elite:br-001:ttltest")
    assert ttl > 0, "Result key must have a TTL"


def test_store_result_publishes_event(worker, fake_redis):
    pubsub = fake_redis.pubsub()
    pubsub.subscribe(_EVENT_CHANNEL)

    result = EliteStudioJobResult(
        job_id="elite:br-001:pub123",
        sku="br-001",
        status="success",
    )
    worker._store_result(result)

    # Drain subscribe message then get our event
    messages = []
    for _ in range(5):
        msg = pubsub.get_message()
        if msg and msg["type"] == "message":
            messages.append(json.loads(msg["data"]))

    assert any(m.get("job_id") == "elite:br-001:pub123" for m in messages)


def test_store_result_degrades_when_redis_unavailable(job_data):
    """_store_result must not raise even when Redis is down."""
    w = EliteStudioWorker(concurrency=1)
    w._redis = None  # force no connection

    result = EliteStudioJobResult(
        job_id="elite:br-001:noredis",
        sku="br-001",
        status="success",
    )
    # Should log a warning but not raise
    w._store_result(result)


# ---------------------------------------------------------------------------
# process_job — success path
# ---------------------------------------------------------------------------


def _make_production_result(status: str = "success", output_path: str = "/out/img.jpg"):
    from skyyrose.elite_studio.models import ProductionResult

    return ProductionResult(
        sku="br-001",
        view="front",
        status=status,
        output_path=output_path,
        error="",
        step="",
    )


def test_process_job_success_stores_result(worker, fake_redis, job_data):
    prod_result = _make_production_result("success", "/out/br-001.jpg")

    stored = []
    worker._store_result = lambda r: stored.append(r)

    with patch("skyyrose.elite_studio.queue.consumer.run_single", return_value=prod_result):
        worker.process_job("elite:br-001:aabbccdd", job_data)

    assert len(stored) == 1
    assert stored[0].status == "success"
    assert stored[0].output_path == "/out/br-001.jpg"


def test_process_job_skipped_maps_to_skipped_status(worker, fake_redis, job_data):
    prod_result = _make_production_result("skipped", "")

    stored = []
    worker._store_result = lambda r: stored.append(r)

    with patch("skyyrose.elite_studio.queue.consumer.run_single", return_value=prod_result):
        worker.process_job("elite:br-001:skip1234", job_data)

    assert stored[0].status == "skipped"


def test_process_job_error_maps_to_error_status(worker, fake_redis, job_data):
    prod_result = _make_production_result("error", "")

    stored = []
    worker._store_result = lambda r: stored.append(r)

    with patch("skyyrose.elite_studio.queue.consumer.run_single", return_value=prod_result):
        worker.process_job("elite:br-001:err12345", job_data)

    assert stored[0].status == "error"


# ---------------------------------------------------------------------------
# process_job — exception path (DLQ)
# ---------------------------------------------------------------------------


def test_process_job_exception_moves_to_dlq(worker, job_data):
    dlq_entries = []

    with patch(
        "skyyrose.elite_studio.queue.consumer.run_single",
        side_effect=RuntimeError("pipeline exploded"),
    ):
        with patch.object(worker._dlq, "move_to_dlq", side_effect=lambda **kw: dlq_entries.append(kw)):
            stored = []
            worker._store_result = lambda r: stored.append(r)

            worker.process_job("elite:br-001:dlqtest1", job_data)

    assert len(dlq_entries) == 1
    assert dlq_entries[0]["job_id"] == "elite:br-001:dlqtest1"
    assert "pipeline exploded" in dlq_entries[0]["error"]


def test_process_job_exception_stores_error_result(worker, job_data):
    stored = []
    worker._store_result = lambda r: stored.append(r)

    with patch(
        "skyyrose.elite_studio.queue.consumer.run_single",
        side_effect=ValueError("bad input"),
    ):
        with patch.object(worker._dlq, "move_to_dlq"):
            worker.process_job("elite:br-001:errstore", job_data)

    assert stored[-1].status == "error"
    assert "bad input" in stored[-1].error


# ---------------------------------------------------------------------------
# SIGTERM handling
# ---------------------------------------------------------------------------


def test_sigterm_sets_shutdown_flag(worker):
    """SIGTERM handler must set _shutdown_requested without raising."""
    worker._register_signal_handlers()
    # Simulate the signal handler directly
    handler = signal.getsignal(signal.SIGTERM)
    handler(signal.SIGTERM, None)
    assert worker._shutdown_requested is True
