"""
Tests for Elite Studio REST API (api/v1/elite_studio.py).

All external services (Redis, queue producer) are mocked so tests run
without a live Redis instance or real queue.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Minimal FastAPI app fixture — avoids importing the full main_enterprise app
# (which requires database, sentry, etc.)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _dev_auth_env(monkeypatch):
    """Pin ENVIRONMENT so the elite-studio auth guard doesn't depend on ambient
    env. The guard raises 503 'API_KEY not configured' when API_KEY is unset AND
    ENVIRONMENT is not a dev value; these tests set API_KEY per-test but never
    ENVIRONMENT (bug-231 — never rely on ambient env). Auth-active tests set
    API_KEY to a real value, taking the header-validation branch, unaffected here.
    """
    monkeypatch.setenv("ENVIRONMENT", "test")


@pytest.fixture(scope="module")
def client():
    from fastapi import FastAPI

    from api.v1.elite_studio import router

    app = FastAPI()
    # The router already has prefix="/elite-studio"; mount at "/api/v1" so
    # endpoints land at "/api/v1/elite-studio/*" as expected by the tests.
    app.include_router(router, prefix="/api/v1")
    return TestClient(app, raise_server_exceptions=False)


# Helper: build a fake EliteStudioJobResult JSON string
def _make_result(
    job_id: str = "elite:br-001:abcd1234",
    sku: str = "br-001",
    status: str = "success",
) -> str:
    return json.dumps(
        {
            "job_id": job_id,
            "sku": sku,
            "status": status,
            "output_path": f"assets/images/products/{sku}-render-front.webp",
            "error": "",
            "completed_at": datetime.now(UTC).isoformat(),
            "stage_timings": {"vision": 1.2, "generation": 3.4},
            "cost_usd": 0.005,
        }
    )


# ---------------------------------------------------------------------------
# POST /produce
# ---------------------------------------------------------------------------


class TestProduce:
    def test_enqueue_success(self, client):
        with (
            patch("api.v1.elite_studio.aenqueue_produce", return_value="elite:br-001:abcd1234"),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "br-001", "view": "front", "priority": 5},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["job_id"] == "elite:br-001:abcd1234"
        assert data["sku"] == "br-001"
        assert data["status"] == "queued"
        assert "queued_at" in data

    def test_enqueue_invalid_view(self, client):
        with patch.dict("os.environ", {"API_KEY": ""}, clear=False):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "br-001", "view": "sideways"},
            )
        assert resp.status_code == 422

    def test_enqueue_empty_sku(self, client):
        with patch.dict("os.environ", {"API_KEY": ""}, clear=False):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "  ", "view": "front"},
            )
        assert resp.status_code == 422

    def test_enqueue_redis_failure_returns_503(self, client):
        with (
            patch(
                "api.v1.elite_studio.aenqueue_produce",
                side_effect=ConnectionError("Redis down"),
            ),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "br-001"},
            )
        assert resp.status_code == 503

    def test_api_key_required(self, client):
        with patch.dict("os.environ", {"API_KEY": "secret123"}, clear=False):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "br-001"},
                headers={"X-API-Key": "wrong"},
            )
        assert resp.status_code == 401

    def test_api_key_accepted(self, client):
        with (
            patch("api.v1.elite_studio.aenqueue_produce", return_value="elite:br-001:zz"),
            patch.dict("os.environ", {"API_KEY": "secret123"}, clear=False),
        ):
            resp = client.post(
                "/api/v1/elite-studio/produce",
                json={"sku": "br-001"},
                headers={"X-API-Key": "secret123"},
            )
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# POST /produce-batch
# ---------------------------------------------------------------------------


class TestProduceBatch:
    def test_batch_enqueue(self, client):
        job_ids = ["elite:br-001:aa", "elite:br-002:bb"]
        with (
            patch("api.v1.elite_studio.aenqueue_batch", return_value=job_ids),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.post(
                "/api/v1/elite-studio/produce-batch",
                json={"skus": ["br-001", "br-002"]},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["job_ids"] == job_ids
        assert data["total"] == 2

    def test_batch_empty_skus_rejected(self, client):
        with patch.dict("os.environ", {"API_KEY": ""}, clear=False):
            resp = client.post(
                "/api/v1/elite-studio/produce-batch",
                json={"skus": []},
            )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------


class TestGetJobStatus:
    def test_found(self, client):
        mock_redis = MagicMock()
        mock_redis.get.return_value = _make_result()
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs/elite:br-001:abcd1234")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_not_found(self, client):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs/nonexistent")
        assert resp.status_code == 404

    def test_redis_unavailable(self, client):
        with (
            patch("api.v1.elite_studio._get_redis", return_value=None),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs/any-id")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/result
# ---------------------------------------------------------------------------


class TestGetJobResult:
    def test_full_result_returned(self, client):
        mock_redis = MagicMock()
        mock_redis.get.return_value = _make_result()
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs/elite:br-001:abcd1234/result")
        assert resp.status_code == 200
        data = resp.json()
        assert "stage_timings" in data
        assert "cost_usd" in data

    def test_not_found(self, client):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs/ghost/result")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id}
# ---------------------------------------------------------------------------


class TestCancelJob:
    def test_cancel_queued_job(self, client):
        mock_redis = MagicMock()
        mock_redis.zrem.return_value = 1
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.delete("/api/v1/elite-studio/jobs/elite:br-001:abcd1234")
        assert resp.status_code == 204

    def test_cancel_completed_job_returns_204(self, client):
        mock_redis = MagicMock()
        mock_redis.zrem.return_value = 0
        mock_redis.exists.return_value = 1
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.delete("/api/v1/elite-studio/jobs/elite:br-001:done")
        assert resp.status_code == 204

    def test_cancel_nonexistent_returns_404(self, client):
        mock_redis = MagicMock()
        mock_redis.zrem.return_value = 0
        mock_redis.exists.return_value = 0
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.delete("/api/v1/elite-studio/jobs/ghost")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    def _build_redis_mock(self, results: list[str]) -> MagicMock:
        mock_redis = MagicMock()
        mock_redis.keys.return_value = [f"elite_studio:result:job{i}" for i in range(len(results))]
        mock_redis.get.side_effect = results
        return mock_redis

    def test_list_returns_paginated(self, client):
        raw = [_make_result(f"elite:br-00{i}:xx", f"br-00{i}") for i in range(3)]
        mock_redis = self._build_redis_mock(raw)
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    def test_status_filter(self, client):
        raw = [
            _make_result("elite:br-001:a", "br-001", "success"),
            _make_result("elite:br-002:b", "br-002", "error"),
        ]
        mock_redis = self._build_redis_mock(raw)
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs?status=error")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["jobs"][0]["status"] == "error"

    def test_sku_filter(self, client):
        raw = [
            _make_result("elite:br-001:a", "br-001"),
            _make_result("elite:lh-002:b", "lh-002"),
        ]
        mock_redis = self._build_redis_mock(raw)
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/jobs?sku=lh-002")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


# ---------------------------------------------------------------------------
# GET /skus
# ---------------------------------------------------------------------------


class TestListSkus:
    def test_returns_unique_skus(self, client):
        raw = [
            _make_result("elite:br-001:a", "br-001"),
            _make_result("elite:br-001:b", "br-001"),
            _make_result("elite:lh-002:c", "lh-002"),
        ]
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ["k1", "k2", "k3"]
        mock_redis.get.side_effect = raw
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/skus")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["skus"]) == {"br-001", "lh-002"}
        assert data["total"] == 2


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_healthy(self, client):
        mock_redis = MagicMock()
        mock_redis.zcard.return_value = 7
        with (
            patch("api.v1.elite_studio._get_redis", return_value=mock_redis),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["queue_depth"] == 7

    def test_unavailable_when_redis_down(self, client):
        with (
            patch("api.v1.elite_studio._get_redis", return_value=None),
            patch.dict("os.environ", {"API_KEY": ""}, clear=False),
        ):
            resp = client.get("/api/v1/elite-studio/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unavailable"
        assert data["redis"] == "unavailable"
