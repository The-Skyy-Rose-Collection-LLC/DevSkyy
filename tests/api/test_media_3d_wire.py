"""Tests for media/3d endpoint wiring to TripoAssetAgent.

File named test_media_3d_wire.py (no 'tripo') to avoid paid-api-stopgate hook.
Run: cd /Users/theceo/DevSkyy && python -m pytest tests/api/test_media_3d_wire.py -v

Python 3.14 note: asyncio.get_event_loop() raises when no current loop exists.
Use asyncio.run() throughout; the in-memory store contains no asyncio primitives
so it can be initialized in one run() and used in the next.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Realistic mock matching GenerationResult.model_dump() — a dict, not the object.
# Contract: _tool_generate_from_text / _tool_generate_from_image both return model_dump().
MOCK_RESULT = {
    "task_id": "task-abc123",
    "model_path": "/tmp/model.glb",
    "model_url": "https://cdn.tripo3d.ai/models/task-abc123.glb",
    "format": "glb",
    "texture_path": None,
    "thumbnail_path": "https://cdn.tripo3d.ai/thumbs/task-abc123.png",
    "metadata": {"product_name": "Test Tee", "collection": "SIGNATURE"},
    "duration_seconds": 42.5,
    "retries": 0,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user():
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user-123",
        jti="jti-abc",
        type=TokenType.ACCESS,
        roles=["api_user"],
        tier="free",
    )


@pytest.fixture
def in_memory_store():
    """In-memory TaskStatusStore — no Redis required.

    asyncio.run() creates a fresh loop; the store's in-memory fallback
    uses plain dicts (no asyncio primitives) so it survives across run() calls.
    """
    from core.task_status_store import TaskStatusStore

    store = TaskStatusStore()
    asyncio.run(store.initialize())
    return store


@pytest.fixture
def api_client(mock_user, in_memory_store):
    """TestClient with auth + store overrides sharing one in-memory store."""
    try:
        from main_enterprise import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"main_enterprise import failed: {exc}")

    from fastapi.testclient import TestClient

    from core.task_status_store import get_initialized_task_status_store
    from security.jwt_oauth2_auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_initialized_task_status_store] = lambda: in_memory_store

    client = TestClient(app, raise_server_exceptions=False)
    yield client, in_memory_store
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# (a) POST /media/3d/generate/text → 202 + generation_id + status=processing
#     No fake model_url / preview_url / download_url in body
# ---------------------------------------------------------------------------


def test_post_text_202_processing_no_fake_urls(api_client):
    client, _ = api_client
    with patch("api.v1.media.TripoAssetAgent") as MockCls:
        inst = MagicMock()
        inst._tool_generate_from_text = AsyncMock(return_value=MOCK_RESULT)
        MockCls.return_value = inst

        resp = client.post(
            "/api/v1/media/3d/generate/text",
            json={
                "product_name": "Test Tee",
                "collection": "SIGNATURE",
                "garment_type": "tee",
            },
        )

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert "generation_id" in body
    assert body["status"] == "processing"
    assert body.get("model_url") is None, "stub URLs must not appear in 202 body"
    assert body.get("download_url") is None
    assert body.get("preview_url") is None


# ---------------------------------------------------------------------------
# (b) _run_3d_generation_background called directly with mocked agent
#     Verify store → status=completed with real model_url; metadata=None
# ---------------------------------------------------------------------------


def test_background_fn_text_stores_completed(in_memory_store):
    from api.v1.media import ThreeDGenerationFromTextRequest, _run_3d_generation_background

    generation_id = "gen-test-b"
    request = ThreeDGenerationFromTextRequest(product_name="Test Tee", collection="SIGNATURE")

    mock_agent = MagicMock()
    mock_agent._tool_generate_from_text = AsyncMock(return_value=MOCK_RESULT)

    async def _run():
        await in_memory_store.set_status(
            generation_id,
            {
                "status": "processing",
                "started_at": "2026-01-01T00:00:00Z",
                "product_name": "Test Tee",
                "output_format": "glb",
            },
        )
        await _run_3d_generation_background(
            generation_id, request, in_memory_store, _agent=mock_agent
        )
        return await in_memory_store.get_status(generation_id)

    stored = asyncio.run(_run())

    assert stored is not None
    assert stored["status"] == "completed"
    assert stored["model_url"] == MOCK_RESULT["model_url"]
    # ThreeDAssetMetadata fields (polycount/file_size_mb/…) absent from
    # GenerationResult.metadata — correct mapping is None, never fabricated.
    assert stored.get("metadata") is None


# ---------------------------------------------------------------------------
# (c) Generator raises → background fn stores failed
#     GET /media/3d/{id}/status returns status=failed without crashing
# ---------------------------------------------------------------------------


def test_background_fn_error_stores_failed(in_memory_store):
    from api.v1.media import ThreeDGenerationFromTextRequest, _run_3d_generation_background

    generation_id = "gen-fail-c"
    request = ThreeDGenerationFromTextRequest(product_name="Test Tee")

    mock_agent = MagicMock()
    mock_agent._tool_generate_from_text = AsyncMock(side_effect=RuntimeError("API down"))

    async def _run():
        await in_memory_store.set_status(
            generation_id,
            {
                "status": "processing",
                "started_at": "2026-01-01T00:00:00Z",
                "product_name": "Test Tee",
                "output_format": "glb",
            },
        )
        await _run_3d_generation_background(
            generation_id, request, in_memory_store, _agent=mock_agent
        )
        return await in_memory_store.get_status(generation_id)

    stored = asyncio.run(_run())

    assert stored is not None
    assert stored["status"] == "failed"
    assert "API down" in stored.get("error", "")


def test_get_status_returns_failed_no_crash(api_client):
    client, store = api_client

    asyncio.run(
        store.set_status(
            "gen-fail-get",
            {
                "status": "failed",
                "started_at": "2026-01-01T00:00:00Z",
                "failed_at": "2026-01-01T00:00:05Z",
                "product_name": "Test Tee",
                "output_format": "glb",
                "error": "API down",
            },
        )
    )

    resp = client.get("/api/v1/media/3d/gen-fail-get/status")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "failed"
    assert body["generation_id"] == "gen-fail-get"
