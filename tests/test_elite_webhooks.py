"""
Tests for Elite Studio Webhook Manager (api/v1/elite_studio_webhooks.py).

All Redis and httpx calls are mocked — no live services required.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(redis_mock=None):
    from api.v1.elite_studio_webhooks import WebhookManager

    mgr = WebhookManager(redis_url="redis://localhost:6379/0")
    if redis_mock is not None:
        mgr._redis = redis_mock
    return mgr


def _sign(secret: str, body: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


class TestWebhookRegister:
    def test_register_returns_webhook_id(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        wid = mgr.register("https://example.com/hook", ["job.completed"], "secret")
        assert isinstance(wid, str)
        assert len(wid) == 32  # uuid4().hex

    def test_register_persists_to_redis(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        mgr.register("https://example.com/hook", ["job.completed"], "s3cr3t")
        mock_redis.hset.assert_called_once()
        call_kwargs = mock_redis.hset.call_args
        # The mapping should contain 'url' and 'events'
        mapping = call_kwargs[1]["mapping"]
        assert mapping["url"] == "https://example.com/hook"
        assert "job.completed" in json.loads(mapping["events"])

    def test_register_multiple_events(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        mgr.register(
            "https://example.com/hook",
            ["job.completed", "job.failed"],
            "s",
        )
        call_kwargs = mock_redis.hset.call_args[1]["mapping"]
        events = json.loads(call_kwargs["events"])
        assert set(events) == {"job.completed", "job.failed"}

    def test_register_invalid_event_raises(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        with pytest.raises(ValueError, match="Unknown events"):
            mgr.register("https://example.com/hook", ["job.unknown"], "s")

    def test_register_without_redis_returns_id(self):
        mgr = _make_manager()
        with patch.object(mgr, "_get_redis", return_value=None):
            wid = mgr.register("https://example.com/hook", ["job.completed"], "s")
        assert isinstance(wid, str)


# ---------------------------------------------------------------------------
# fire()
# ---------------------------------------------------------------------------


class TestWebhookFire:
    def _make_registration(self, event: str, url: str = "https://example.com/hook") -> dict:
        return {
            "webhook_id": "abc123",
            "url": url,
            "events": json.dumps([event]),
            "secret": "mysecret",
            "registered_at": "2026-01-01T00:00:00+00:00",
        }

    def test_fire_calls_deliver(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        reg = self._make_registration("job.completed")

        async def _noop(*args, **kwargs):
            pass

        with (
            patch.object(mgr, "_get_registrations_for_event", return_value=[reg]),
            patch("api.v1.elite_studio_webhooks._fire_all", side_effect=_noop) as mock_fire_all,
        ):
            mgr.fire("job.completed", {"job_id": "elite:br-001:xx", "status": "success"})
            mock_fire_all.assert_called_once()

    def test_fire_unknown_event_skips(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        with patch.object(mgr, "_get_registrations_for_event") as mock_get:
            mgr.fire("job.unknown_event", {})
            mock_get.assert_not_called()

    def test_fire_no_registrations_skips(self):
        mock_redis = MagicMock()
        mgr = _make_manager(mock_redis)
        with (
            patch.object(mgr, "_get_registrations_for_event", return_value=[]),
            patch("api.v1.elite_studio_webhooks._fire_all") as mock_fire_all,
        ):
            mgr.fire("job.completed", {})
            mock_fire_all.assert_not_called()


# ---------------------------------------------------------------------------
# HMAC signature verification
# ---------------------------------------------------------------------------


class TestHmacSignature:
    def test_signature_matches(self):
        from api.v1.elite_studio_webhooks import _sign

        secret = "supersecret"
        body = '{"event":"job.completed"}'
        sig = _sign(secret, body)
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        assert sig == expected

    def test_different_secrets_produce_different_signatures(self):
        from api.v1.elite_studio_webhooks import _sign

        body = '{"event":"job.completed"}'
        assert _sign("secret1", body) != _sign("secret2", body)

    def test_different_bodies_produce_different_signatures(self):
        from api.v1.elite_studio_webhooks import _sign

        secret = "mysecret"
        assert _sign(secret, '{"a":1}') != _sign(secret, '{"a":2}')


# ---------------------------------------------------------------------------
# _deliver() — async delivery with HMAC header
# ---------------------------------------------------------------------------


class TestDeliver:
    @pytest.mark.asyncio
    async def test_deliver_sends_correct_headers(self):
        from api.v1.elite_studio_webhooks import _deliver

        registration = {
            "url": "https://example.com/hook",
            "secret": "topsecret",
        }
        payload = {"job_id": "elite:br-001:xx", "status": "success"}

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        # httpx is a top-level import in the module — patch AsyncClient directly
        with patch("api.v1.elite_studio_webhooks.httpx.AsyncClient", return_value=mock_client):
            await _deliver(registration, "job.completed", payload)

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        headers = call_kwargs["headers"]
        assert "X-SkyyRose-Signature" in headers
        assert headers["X-SkyyRose-Event"] == "job.completed"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_deliver_never_raises_on_http_error(self):
        from api.v1.elite_studio_webhooks import _deliver

        registration = {"url": "https://example.com/hook", "secret": "s"}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("api.v1.elite_studio_webhooks.httpx.AsyncClient", return_value=mock_client):
            # Must not raise
            await _deliver(registration, "job.failed", {"job_id": "x"})

    @pytest.mark.asyncio
    async def test_deliver_skips_empty_url(self):
        from api.v1.elite_studio_webhooks import _deliver

        registration = {"url": "", "secret": "s"}
        # Should return immediately without touching httpx
        with patch("api.v1.elite_studio_webhooks.httpx.AsyncClient") as mock_cls:
            await _deliver(registration, "job.completed", {})
            mock_cls.assert_not_called()
