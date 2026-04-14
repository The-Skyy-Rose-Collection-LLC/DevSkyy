"""
Tests for Elite Studio queue producer.

Uses fakeredis to avoid requiring a live Redis instance.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.queue.job_types import EliteStudioJobData
from skyyrose.elite_studio.queue.producer import (
    ELITE_TASK_TYPE,
    _make_job_id,
    enqueue_batch,
    enqueue_produce,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_queue(enqueue_return: str = "task-id-123") -> MagicMock:
    """Return a mock TaskQueue whose enqueue coroutine returns enqueue_return."""
    mock_queue = MagicMock()
    mock_queue.enqueue = AsyncMock(return_value=enqueue_return)
    mock_queue.disconnect = AsyncMock()
    return mock_queue


# ---------------------------------------------------------------------------
# _make_job_id
# ---------------------------------------------------------------------------


def test_make_job_id_format():
    job_id = _make_job_id("br-001")
    parts = job_id.split(":")
    assert parts[0] == "elite"
    assert parts[1] == "br-001"
    assert len(parts[2]) == 8  # 8 hex chars


def test_make_job_id_unique():
    ids = {_make_job_id("br-001") for _ in range(20)}
    assert len(ids) == 20, "Job IDs must be unique"


# ---------------------------------------------------------------------------
# enqueue_produce
# ---------------------------------------------------------------------------


def test_enqueue_produce_returns_job_id():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        job_id = enqueue_produce("br-001")

    assert job_id.startswith("elite:br-001:")
    assert len(job_id.split(":")[-1]) == 8


def test_enqueue_produce_calls_enqueue_with_correct_task_type():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_produce("br-001", view="back", priority=8)

    mock_queue.enqueue.assert_called_once()
    call_kwargs = mock_queue.enqueue.call_args
    assert call_kwargs.kwargs["task_type"] == ELITE_TASK_TYPE
    assert call_kwargs.kwargs["priority"] == 8


def test_enqueue_produce_payload_contains_sku_and_view():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_produce("sg-005", view="back")

    task_data = mock_queue.enqueue.call_args.kwargs["task_data"]
    assert task_data["sku"] == "sg-005"
    assert task_data["view"] == "back"


def test_enqueue_produce_payload_contains_job_id():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        job_id = enqueue_produce("br-002")

    task_data = mock_queue.enqueue.call_args.kwargs["task_data"]
    assert task_data["job_id"] == job_id


def test_enqueue_produce_enable_compositor_flag():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_produce("br-003", enable_compositor=True)

    task_data = mock_queue.enqueue.call_args.kwargs["task_data"]
    assert task_data["enable_compositor"] is True


def test_enqueue_produce_calls_disconnect():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_produce("br-001")

    mock_queue.disconnect.assert_called_once()


def test_enqueue_produce_default_priority_is_5():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_produce("br-001")

    assert mock_queue.enqueue.call_args.kwargs["priority"] == 5


# ---------------------------------------------------------------------------
# enqueue_batch
# ---------------------------------------------------------------------------


def test_enqueue_batch_returns_correct_count():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        job_ids = enqueue_batch(["br-001", "br-002", "br-003"])

    assert len(job_ids) == 3


def test_enqueue_batch_job_ids_are_unique():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        job_ids = enqueue_batch(["br-001", "br-002", "br-003"])

    assert len(set(job_ids)) == 3, "All batch job IDs must be unique"


def test_enqueue_batch_each_sku_prefixed_correctly():
    mock_queue = _make_mock_queue()
    skus = ["br-001", "sg-005", "lh-002"]
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        job_ids = enqueue_batch(skus)

    for job_id, sku in zip(job_ids, skus, strict=False):
        assert job_id.startswith(f"elite:{sku}:")


def test_enqueue_batch_calls_enqueue_once_per_sku():
    mock_queue = _make_mock_queue()
    skus = ["br-001", "br-002"]
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_batch(skus)

    assert mock_queue.enqueue.call_count == 2


def test_enqueue_batch_shared_connection_disconnects_once():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        enqueue_batch(["br-001", "br-002", "br-003"])

    mock_queue.disconnect.assert_called_once()


def test_enqueue_batch_empty_list_returns_empty():
    mock_queue = _make_mock_queue()
    with patch("skyyrose.elite_studio.queue.producer._get_queue", return_value=mock_queue):
        result = enqueue_batch([])

    assert result == []
    mock_queue.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# EliteStudioJobData validation
# ---------------------------------------------------------------------------


def test_job_data_normalizes_sku_to_lowercase():
    jd = EliteStudioJobData(sku="  BR-001  ")
    assert jd.sku == "br-001"


def test_job_data_rejects_invalid_view():
    with pytest.raises(Exception):
        EliteStudioJobData(sku="br-001", view="side")


def test_job_data_rejects_empty_sku():
    with pytest.raises(Exception):
        EliteStudioJobData(sku="   ")


def test_job_data_priority_bounds():
    with pytest.raises(Exception):
        EliteStudioJobData(sku="br-001", priority=0)
    with pytest.raises(Exception):
        EliteStudioJobData(sku="br-001", priority=11)
