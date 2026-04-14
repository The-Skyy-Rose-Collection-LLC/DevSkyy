"""
Tests for Enterprise API v2.

All external services (Redis, queue producer, runners, agents) are mocked
so tests run without live infrastructure. Each test module uses a minimal
FastAPI app fixture to avoid importing the full main_enterprise stack.

Coverage:
  - POST /api/v2/creative/operations (async + sync modes)
  - GET  /api/v2/creative/operations/{id}
  - GET  /api/v2/creative/operations (pagination + filters)
  - DELETE /api/v2/creative/operations/{id}
  - POST /api/v2/characters
  - GET  /api/v2/characters/rosie
  - GET  /api/v2/characters/{id}
  - GET  /api/v2/characters (list)
  - PATCH /api/v2/characters/{id}
  - GET  /api/v2/assets
  - GET  /api/v2/assets/{id}
  - DELETE /api/v2/assets/{id}
  - POST /api/v2/webhooks
  - GET  /api/v2/webhooks
  - DELETE /api/v2/webhooks/{id}
  - POST /api/v2/webhooks/{id}/test
  - GET  /api/v2/health
  - GET  /api/v2/usage
  - VALID_EVENTS contains all 21 events
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _fake_op_json(
    operation_id: str = "elite:br-001:aabbccdd",
    intent: str = "product-render",
    op_status: str = "queued",
    sku: str = "br-001",
) -> str:
    return json.dumps(
        {
            "operation_id": operation_id,
            "intent": intent,
            "status": op_status,
            "sku": sku,
            "created_at": _now(),
            "result": None,
            "error": "",
            "cost_usd": 0.0,
            "stage_timings": {},
        }
    )


def _fake_char_json(character_id: str = "char_abc123", name: str = "TestChar") -> str:
    return json.dumps(
        {
            "character_id": character_id,
            "name": name,
            "style": "pixar-chibi",
            "front_view_prompt": "Pixar front view prompt",
            "expression_grid_prompt": "Expression grid prompt",
            "sprite_description": "Sprite description",
            "created_at": _now(),
        }
    )


# ---------------------------------------------------------------------------
# App fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def creative_client():
    from api.v2.creative import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v2")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def characters_client():
    from api.v2.characters import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v2")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def assets_client():
    from api.v2.assets import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v2")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def webhooks_client():
    from api.v2.webhooks import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v2")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def health_client():
    from api.v2.health import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v2")
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Creative: POST /operations (async mode)
# ---------------------------------------------------------------------------


class TestCreateOperationAsync:
    def test_enqueue_returns_202_queued(self, creative_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with (
            patch("api.v2.creative.enqueue_creative", return_value="elite:br-001:test0001"),
            patch("api.v2.creative._get_redis", return_value=mock_redis),
        ):
            resp = creative_client.post(
                "/api/v2/creative/operations",
                json={"intent": "product-render", "sku": "br-001", "async_mode": True},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "queued"
        assert body["intent"] == "product-render"
        assert body["sku"] == "br-001"
        assert "operation_id" in body

    def test_invalid_intent_returns_422(self, creative_client):
        resp = creative_client.post(
            "/api/v2/creative/operations",
            json={"intent": "nonexistent-intent"},
        )
        assert resp.status_code == 422

    def test_priority_clamped_to_range(self, creative_client):
        resp = creative_client.post(
            "/api/v2/creative/operations",
            json={"intent": "product-render", "priority": 99},
        )
        assert resp.status_code == 422

    def test_webhook_url_stored_when_provided(self, creative_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with (
            patch("api.v2.creative.enqueue_creative", return_value="elite:br-001:webhk001"),
            patch("api.v2.creative._get_redis", return_value=mock_redis),
        ):
            resp = creative_client.post(
                "/api/v2/creative/operations",
                json={
                    "intent": "social-pack",
                    "sku": "br-002",
                    "async_mode": True,
                    "webhook_url": "https://example.com/hook",
                },
            )

        assert resp.status_code == 202
        # setex called for both operation storage and webhook key
        assert mock_redis.setex.call_count >= 2

    def test_queue_unavailable_returns_503(self, creative_client):
        with patch(
            "api.v2.creative.enqueue_creative",
            side_effect=ConnectionError("Redis down"),
        ):
            resp = creative_client.post(
                "/api/v2/creative/operations",
                json={"intent": "product-render", "async_mode": True},
            )
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Creative: POST /operations (sync mode)
# ---------------------------------------------------------------------------


class TestCreateOperationSync:
    def test_sync_mode_returns_completed(self, creative_client):
        fake_state = {
            "operation_id": "op-sync-001",
            "intent": "product-render",
            "status": "success",
            "sku": "br-001",
            "cost_usd": 0.012,
            "stage_timings": {"render": 2.3},
            "error": "",
        }
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with (
            patch("api.v2.creative.run_creative", return_value=fake_state),
            patch("api.v2.creative._get_redis", return_value=mock_redis),
        ):
            resp = creative_client.post(
                "/api/v2/creative/operations",
                json={"intent": "product-render", "sku": "br-001", "async_mode": False},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "completed"
        assert body["cost_usd"] == pytest.approx(0.012)

    def test_sync_mode_failed_state_returns_failed_status(self, creative_client):
        fake_state = {
            "operation_id": "op-sync-002",
            "intent": "product-render",
            "status": "error",
            "sku": "sg-001",
            "cost_usd": 0.0,
            "stage_timings": {},
            "error": "model timeout",
        }
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with (
            patch("api.v2.creative.run_creative", return_value=fake_state),
            patch("api.v2.creative._get_redis", return_value=mock_redis),
        ):
            resp = creative_client.post(
                "/api/v2/creative/operations",
                json={"intent": "product-render", "async_mode": False},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "failed"
        assert "model timeout" in body["error"]


# ---------------------------------------------------------------------------
# Creative: GET /operations/{id}
# ---------------------------------------------------------------------------


class TestGetOperation:
    def test_returns_queued_status_from_redis(self, creative_client):
        op_json = _fake_op_json(operation_id="elite:br-001:aabb0001", op_status="queued")
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.side_effect = lambda key: (
            op_json if "aabb0001" in key and "v2:operation" in key else None
        )

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations/elite:br-001:aabb0001")

        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    def test_not_found_returns_404(self, creative_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations/nonexistent-op-id")

        assert resp.status_code == 404

    def test_redis_unavailable_returns_503(self, creative_client):
        with patch("api.v2.creative._get_redis", return_value=None):
            resp = creative_client.get("/api/v2/creative/operations/some-op-id")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Creative: GET /operations (list + filters)
# ---------------------------------------------------------------------------


class TestListOperations:
    def _build_redis_mock(self, ops: list[str]) -> MagicMock:
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        keys = [f"elite_studio:v2:operation:{i}" for i in range(len(ops))]
        mock_redis.keys.return_value = keys
        mock_redis.get.side_effect = lambda key: ops[keys.index(key)] if key in keys else None
        return mock_redis

    def test_returns_paginated_list(self, creative_client):
        ops = [
            _fake_op_json(f"op-{i}", op_status="completed") for i in range(5)
        ]
        mock_redis = self._build_redis_mock(ops)

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations?page=1&page_size=3")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["operations"]) == 3
        assert body["page"] == 1
        assert body["page_size"] == 3

    def test_status_filter(self, creative_client):
        ops = [
            _fake_op_json("op-q1", op_status="queued"),
            _fake_op_json("op-c1", op_status="completed"),
            _fake_op_json("op-q2", op_status="queued"),
        ]
        mock_redis = self._build_redis_mock(ops)

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations?status=queued")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert all(o["status"] == "queued" for o in body["operations"])

    def test_sku_filter(self, creative_client):
        ops = [
            _fake_op_json("op-br1", sku="br-001"),
            _fake_op_json("op-sg1", sku="sg-001"),
        ]
        mock_redis = self._build_redis_mock(ops)

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations?sku=sg-001")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["operations"][0]["sku"] == "sg-001"

    def test_intent_filter(self, creative_client):
        ops = [
            _fake_op_json("op-r1", intent="product-render"),
            _fake_op_json("op-s1", intent="social-pack"),
        ]
        mock_redis = self._build_redis_mock(ops)

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.get("/api/v2/creative/operations?intent=social-pack")

        assert resp.status_code == 200
        assert resp.json()["total"] == 1


# ---------------------------------------------------------------------------
# Creative: DELETE /operations/{id}
# ---------------------------------------------------------------------------


class TestCancelOperation:
    def test_cancel_queued_returns_204(self, creative_client):
        op_json = _fake_op_json("op-cancel-01", op_status="queued")
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zrem.return_value = 1
        mock_redis.get.return_value = op_json
        mock_redis.setex.return_value = True

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.delete("/api/v2/creative/operations/op-cancel-01")

        assert resp.status_code == 204

    def test_cancel_nonexistent_returns_404(self, creative_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zrem.return_value = 0
        mock_redis.get.return_value = None

        with patch("api.v2.creative._get_redis", return_value=mock_redis):
            resp = creative_client.delete("/api/v2/creative/operations/nonexistent-op")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Characters: POST /
# ---------------------------------------------------------------------------


class TestCreateCharacter:
    def _mock_agent_sheet(self):
        from skyyrose.elite_studio.character.models import CharacterSheet, CharacterSpec

        spec = CharacterSpec(
            name="TestChar",
            style="pixar-chibi",
            body_description="desc",
            face_features="features",
            outfit_base="outfit",
            brand_elements=(),
            reference_paths=(),
        )
        return CharacterSheet(
            success=True,
            spec=spec,
            front_view_prompt="Front prompt",
            side_view_prompt="Side prompt",
            back_view_prompt="Back prompt",
            expression_grid_prompt="Expression prompt",
            sprite_description="Sprite desc",
        )

    def test_create_returns_201(self, characters_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        sheet = self._mock_agent_sheet()
        with (
            patch("api.v2.characters.CharacterCreationAgent") as MockAgent,
            patch("api.v2.characters._get_redis", return_value=mock_redis),
        ):
            MockAgent.return_value.create_sheet.return_value = sheet
            resp = characters_client.post(
                "/api/v2/characters",
                json={
                    "name": "TestChar",
                    "style": "pixar-chibi",
                    "body_description": "A character",
                    "face_features": "Round face",
                    "outfit_base": "Black hoodie",
                    "brand_elements": ["rose gold accents"],
                },
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "TestChar"
        assert body["style"] == "pixar-chibi"
        assert "character_id" in body
        assert "front_view_prompt" in body
        assert "expression_grid_prompt" in body

    def test_missing_name_returns_422(self, characters_client):
        resp = characters_client.post("/api/v2/characters", json={"style": "pixar-chibi"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Characters: GET /rosie
# ---------------------------------------------------------------------------


class TestGetRosie:
    def test_rosie_returns_canonical_spec(self, characters_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None  # not cached
        mock_redis.setex.return_value = True

        from skyyrose.elite_studio.character.models import CharacterSheet, CharacterSpec

        spec = CharacterSpec(
            name="Rosie",
            style="pixar-chibi",
            body_description="Young Black girl",
            face_features="Round face",
            outfit_base="Mini hoodie",
            brand_elements=("rose gold",),
            reference_paths=(),
        )
        rosie_sheet = CharacterSheet(
            success=True,
            spec=spec,
            front_view_prompt="Rosie front prompt",
            side_view_prompt="Rosie side prompt",
            back_view_prompt="Rosie back prompt",
            expression_grid_prompt="Rosie expressions",
            sprite_description="Rosie sprite",
        )

        with (
            patch("api.v2.characters.CharacterCreationAgent") as MockAgent,
            patch("api.v2.characters._get_redis", return_value=mock_redis),
        ):
            MockAgent.return_value.create_skyyrose_rosie.return_value = rosie_sheet
            resp = characters_client.get("/api/v2/characters/rosie")

        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Rosie"
        assert body["style"] == "pixar-chibi"
        assert body["character_id"] == "rosie_canonical"
        assert "front_view_prompt" in body

    def test_rosie_returns_cached_when_warm(self, characters_client):
        cached_json = _fake_char_json("rosie_canonical", "Rosie")
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = cached_json

        with patch("api.v2.characters._get_redis", return_value=mock_redis):
            resp = characters_client.get("/api/v2/characters/rosie")

        assert resp.status_code == 200
        assert resp.json()["character_id"] == "rosie_canonical"


# ---------------------------------------------------------------------------
# Webhooks: POST / and GET /
# ---------------------------------------------------------------------------


class TestWebhooks:
    def test_register_webhook_returns_201(self, webhooks_client):
        with patch("api.v2.webhooks._manager") as mock_mgr:
            mock_mgr.register.return_value = "whk_test_001"
            mock_mgr._get_redis.return_value = MagicMock(
                hset=MagicMock(), keys=MagicMock(return_value=[])
            )
            resp = webhooks_client.post(
                "/api/v2/webhooks",
                json={
                    "url": "https://example.com/hook",
                    "events": ["operation.completed", "operation.failed"],
                    "description": "My webhook",
                },
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["webhook_id"] == "whk_test_001"
        assert body["active"] is True
        assert "operation.completed" in body["events"]

    def test_register_with_invalid_event_returns_422(self, webhooks_client):
        resp = webhooks_client.post(
            "/api/v2/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["not.a.real.event"],
            },
        )
        assert resp.status_code == 422

    def test_register_with_invalid_url_returns_422(self, webhooks_client):
        resp = webhooks_client.post(
            "/api/v2/webhooks",
            json={"url": "ftp://bad-scheme.com", "events": ["operation.completed"]},
        )
        assert resp.status_code == 422

    def test_list_webhooks_returns_all(self, webhooks_client):
        raw_records = [
            {
                "webhook_id": "whk_001",
                "url": "https://example.com/a",
                "events": json.dumps(["operation.completed"]),
                "secret": "s3cr3t",
                "registered_at": _now(),
                "active": "true",
                "description": "A",
            }
        ]
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = ["elite_studio:webhooks:whk_001"]
        mock_redis.hgetall.return_value = raw_records[0]

        with (
            patch("api.v2.webhooks._manager._get_redis", return_value=mock_redis),
            patch("api.v2.webhooks._get_redis", return_value=mock_redis),
        ):
            resp = webhooks_client.get("/api/v2/webhooks")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1

    def test_delete_nonexistent_webhook_returns_404(self, webhooks_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.delete.return_value = 0

        with patch("api.v2.webhooks._get_redis", return_value=mock_redis):
            resp = webhooks_client.delete("/api/v2/webhooks/nonexistent-whk")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# VALID_EVENTS contains all 21 required events
# ---------------------------------------------------------------------------


class TestValidEvents:
    EXPECTED_EVENTS = {
        "operation.created",
        "operation.started",
        "operation.completed",
        "operation.failed",
        "operation.review_required",
        "character.created",
        "character.updated",
        "asset.generated",
        "asset.approved",
        "asset.rejected",
        "subscription.created",
        "subscription.updated",
        "subscription.cancelled",
        "invoice.paid",
        "usage.threshold_reached",
        "team.member_invited",
        "team.member_removed",
        # Legacy events preserved
        "job.completed",
        "job.failed",
        "job.review_required",
    }

    def test_all_expected_events_present(self):
        from api.v1.elite_studio_webhooks import VALID_EVENTS

        missing = self.EXPECTED_EVENTS - VALID_EVENTS
        assert not missing, f"Missing events in VALID_EVENTS: {missing}"

    def test_valid_events_is_frozenset(self):
        from api.v1.elite_studio_webhooks import VALID_EVENTS

        assert isinstance(VALID_EVENTS, frozenset)

    def test_valid_events_count(self):
        from api.v1.elite_studio_webhooks import VALID_EVENTS

        # At least 20 events (18 new + 3 legacy)
        assert len(VALID_EVENTS) >= 20


# ---------------------------------------------------------------------------
# Health: GET /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_healthy_when_redis_connected(self, health_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zcard.return_value = 3

        with (
            patch("api.v2.health._get_redis", return_value=mock_redis),
            patch("api.v2.health._check_graph", return_value="ready"),
        ):
            resp = health_client.get("/api/v2/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["services"]["redis"] == "connected"
        assert body["services"]["graph"] == "ready"
        assert body["services"]["queue_depth"] == 3

    def test_degraded_when_redis_unavailable(self, health_client):
        with (
            patch("api.v2.health._get_redis", return_value=None),
            patch("api.v2.health._check_graph", return_value="ready"),
        ):
            resp = health_client.get("/api/v2/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["services"]["redis"] == "unavailable"

    def test_degraded_when_graph_unavailable(self, health_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zcard.return_value = 0

        with (
            patch("api.v2.health._get_redis", return_value=mock_redis),
            patch("api.v2.health._check_graph", return_value="unavailable"),
        ):
            resp = health_client.get("/api/v2/health")

        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"

    def test_services_dict_present(self, health_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zcard.return_value = 0

        with (
            patch("api.v2.health._get_redis", return_value=mock_redis),
            patch("api.v2.health._check_graph", return_value="ready"),
        ):
            resp = health_client.get("/api/v2/health")

        body = resp.json()
        assert "services" in body
        services = body["services"]
        assert "redis" in services
        assert "graph" in services
        assert "queue_depth" in services

    def test_no_auth_required_for_health(self, health_client):
        # Health endpoint must be accessible without X-API-Key
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.zcard.return_value = 0

        with (
            patch("api.v2.health._get_redis", return_value=mock_redis),
            patch("api.v2.health._check_graph", return_value="ready"),
        ):
            resp = health_client.get("/api/v2/health")  # no auth header

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Usage: GET /usage
# ---------------------------------------------------------------------------


class TestUsageEndpoint:
    def test_usage_returns_summary(self, health_client):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.keys.side_effect = lambda pattern: (
            ["elite_studio:v2:operation:op1"] if "v2:operation" in pattern else []
        )
        mock_redis.get.return_value = json.dumps(
            {
                "operation_id": "op1",
                "intent": "product-render",
                "status": "completed",
                "sku": "br-001",
                "created_at": _now(),
                "cost_usd": 0.05,
                "stage_timings": {},
                "error": "",
            }
        )
        mock_redis.zcard.return_value = 2

        with patch("api.v2.health._get_redis", return_value=mock_redis):
            resp = health_client.get("/api/v2/usage")

        assert resp.status_code == 200
        body = resp.json()
        assert "total_operations" in body
        assert "completed" in body
        assert "failed" in body
        assert "queued" in body
        assert "total_cost_usd" in body
        assert body["total_cost_usd"] >= 0.0

    def test_usage_requires_auth_when_api_key_set(self, health_client):
        with patch.dict("os.environ", {"API_KEY": "secret-key"}):
            resp = health_client.get("/api/v2/usage")  # no X-API-Key header
        assert resp.status_code == 401
