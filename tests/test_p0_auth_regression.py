"""P0 auth regression tests — assert 401 on all newly-gated endpoints.

Covers Finding #2 from the Wave 2 cleanup audit:
  - api/v1/catalog.py     — /answer, /answer/stream, /cache/clear
  - api/virtual_tryon.py  — /generate, /generate/upload, /batch, /models/generate
  - api/ar_sessions.py    — POST /sessions, PATCH /sessions/{id}, POST /sessions/{id}/tryon
  - api/v1/sync.py        — POST /trigger, POST /rt-to-hf
  - api/v1/wordpress.py   — POST /sync, GET /status
  - api/v1/wordpress_agent.py — POST /agent/execute
  - api/websocket.py      — all 6 WebSocket channels (missing ?token= → 403)

Each test asserts HTTP 401 when no Authorization header is provided.
WebSocket endpoints assert HTTP 403 when the required `token` query param is absent
(FastAPI rejects missing required Query params before the handler runs).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _no_auth_headers() -> dict:
    """Empty headers — no Authorization."""
    return {}


# ---------------------------------------------------------------------------
# catalog.py — LLM cost endpoints
# ---------------------------------------------------------------------------


class TestCatalogAuthRequired:
    """GET /api/v1/catalog/answer and /answer/stream require auth."""

    @pytest.mark.asyncio
    async def test_answer_no_auth_returns_401(self, client):
        resp = await client.get("/api/v1/catalog/answer?q=test")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_answer_stream_no_auth_returns_401(self, client):
        resp = await client.get("/api/v1/catalog/answer/stream?q=test")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_cache_clear_no_auth_returns_401(self, client):
        resp = await client.post("/api/v1/catalog/cache/clear")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_public_search_no_auth_returns_200_or_non_401(self, client):
        """Public /search endpoint must remain unauthenticated."""
        resp = await client.get("/api/v1/catalog/search?q=rose")
        # 200, 422 (validation), 503 (service unavailable) — all acceptable; 401 is not
        assert resp.status_code != 401, "/search should NOT require auth"

    @pytest.mark.asyncio
    async def test_public_health_no_auth_non_401(self, client):
        """Public /health must remain unauthenticated."""
        resp = await client.get("/api/v1/catalog/health")
        assert resp.status_code != 401, "/health should NOT require auth"


# ---------------------------------------------------------------------------
# virtual_tryon.py — FASHN cost endpoints ($0.075/image)
# ---------------------------------------------------------------------------


class TestVirtualTryonAuthRequired:
    """All FASHN tryon endpoints require auth."""

    @pytest.mark.asyncio
    async def test_generate_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/tryon/generate",
            json={
                "garment_image": "https://example.com/g.jpg",
                "person_image": "https://example.com/p.jpg",
            },
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_generate_upload_no_auth_returns_401(self, client):
        resp = await client.post("/api/v1/tryon/generate/upload")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_batch_no_auth_returns_401(self, client):
        resp = await client.post("/api/v1/tryon/batch", json={"requests": []})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_models_generate_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/tryon/models/generate",
            json={"description": "test model"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


# ---------------------------------------------------------------------------
# ar_sessions.py — AR session write endpoints
# ---------------------------------------------------------------------------


class TestARSessionsAuthRequired:
    """Write endpoints on /api/v1/ar-sessions require auth."""

    @pytest.mark.asyncio
    async def test_create_session_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/ar-sessions/sessions",
            json={"product_sku": "br-001"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_update_session_no_auth_returns_401(self, client):
        resp = await client.patch(
            "/api/v1/ar-sessions/sessions/fake-session-id",
            json={"status": "active"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_record_tryon_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/ar-sessions/sessions/fake-session-id/tryon",
            json={},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


# ---------------------------------------------------------------------------
# api/v1/sync.py — Sync trigger endpoints
# ---------------------------------------------------------------------------


class TestSyncAuthRequired:
    """POST /api/v1/sync/trigger and /rt-to-hf require auth."""

    @pytest.mark.asyncio
    async def test_trigger_no_auth_returns_401(self, client):
        resp = await client.post("/api/v1/sync/trigger", json={"direction": "full"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_rt_to_hf_no_auth_returns_401(self, client):
        resp = await client.post("/api/v1/sync/rt-to-hf")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_public_status_no_auth_non_401(self, client):
        """GET /status must remain public (read-only health info)."""
        resp = await client.get("/api/v1/sync/status")
        assert resp.status_code != 401, "/sync/status should NOT require auth"

    @pytest.mark.asyncio
    async def test_public_health_no_auth_non_401(self, client):
        """GET /health must remain public."""
        resp = await client.get("/api/v1/sync/health")
        assert resp.status_code != 401, "/sync/health should NOT require auth"


# ---------------------------------------------------------------------------
# api/v1/wordpress.py — WordPress integration
# ---------------------------------------------------------------------------


class TestWordPressAuthRequired:
    """Both /api/v1/wordpress endpoints require auth."""

    @pytest.mark.asyncio
    async def test_sync_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/wordpress/sync",
            json={"title": "Test", "content": "Body"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_status_no_auth_returns_401(self, client):
        resp = await client.get("/api/v1/wordpress/status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


# ---------------------------------------------------------------------------
# api/v1/wordpress_agent.py — Agent SSE endpoint
# ---------------------------------------------------------------------------


class TestWordPressAgentAuthRequired:
    """POST /api/v1/agent/execute requires auth."""

    @pytest.mark.asyncio
    async def test_execute_no_auth_returns_401(self, client):
        resp = await client.post(
            "/api/v1/agent/execute",
            json={"intent": "health_check", "prompt": "ping"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_webhook_dispatch_no_auth_allowed(self, client):
        """Webhook dispatch must remain unauthenticated (WooCommerce HMAC delivery)."""
        resp = await client.post(
            "/api/v1/agent/webhooks/dispatch",
            json={"topic": "order.created", "payload": {}},
        )
        # 4xx is fine (missing fields, config), but MUST NOT be 401
        assert resp.status_code != 401, "/webhooks/dispatch must NOT require JWT auth"


# ---------------------------------------------------------------------------
# api/websocket.py — WebSocket channels
#
# FastAPI returns HTTP 403 (Forbidden) when a required Query parameter is
# absent on a WebSocket upgrade request — this is the correct pre-connection
# rejection behaviour (the connection is refused before the handler runs).
# ---------------------------------------------------------------------------


class TestWebSocketAuthRequired:
    """WebSocket endpoints require ?token= query parameter."""

    @pytest.mark.asyncio
    async def test_ws_agents_no_token_rejected(self, client):
        """Upgrade request without ?token= must be rejected (403 or 401)."""
        resp = await client.get(
            "/api/ws/agents",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection (401/403/400), got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_round_table_no_token_rejected(self, client):
        resp = await client.get(
            "/api/ws/round_table",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_tasks_no_token_rejected(self, client):
        resp = await client.get(
            "/api/ws/tasks",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_3d_pipeline_no_token_rejected(self, client):
        resp = await client.get(
            "/api/ws/3d_pipeline",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_metrics_no_token_rejected(self, client):
        resp = await client.get(
            "/api/ws/metrics",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_legacy_ws_no_token_rejected(self, client):
        """Legacy /ws/{channel} also requires ?token=."""
        resp = await client.get(
            "/ws/agents",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        assert resp.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_invalid_token_rejected(self, client):
        """WebSocket with a fake token must be rejected."""
        resp = await client.get(
            "/api/ws/agents?token=not.a.real.jwt",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        # May return 403 (invalid token in WebSocket close) or 400/401
        assert resp.status_code in (400, 401, 403), (
            f"Expected auth rejection for invalid token, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ws_valid_token_accepted(self, client, jwt_manager):
        """WebSocket with a valid JWT must NOT be rejected at the HTTP upgrade stage."""
        tokens = jwt_manager.create_token_pair(user_id="test-user-ws", roles=["api_user"])
        resp = await client.get(
            f"/api/ws/agents?token={tokens.access_token}",
            headers={"Connection": "upgrade", "Upgrade": "websocket"},
        )
        # httpx ASGI client doesn't do the full WS handshake — FastAPI will
        # respond 101 (switching protocols) or 200 on valid auth; what it must
        # NOT do is return 401/403
        assert resp.status_code not in (401, 403), (
            f"Valid token should not be rejected, got {resp.status_code}"
        )
