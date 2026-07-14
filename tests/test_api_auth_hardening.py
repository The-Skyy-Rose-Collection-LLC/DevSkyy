"""Security regression tests for the auth-hardening pass (bug-252 sibling class).

Proves that endpoints which were unauthenticated (and in claude_sdk's case,
anonymous-RCE) now reject callers without valid credentials, and that the
WooCommerce webhook verifier fails closed when the secret is unset.

These are behavioral tests: mount each router on a minimal app and assert the
HTTP status a credential-less caller sees.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_UNAUTH = (401, 403)  # missing/invalid creds → Unauthorized or Forbidden


def _client(router, prefix: str = "") -> TestClient:
    app = FastAPI()
    if prefix:
        app.include_router(router, prefix=prefix)
    else:
        app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


class TestClaudeSdkNoAnonymousRce:
    """claude_sdk routes gave anonymous Bash-capable agents — now ADMIN-only."""

    def test_session_requires_auth(self):
        from api.v1.claude_sdk import router

        c = _client(router, prefix="/api/v1")
        r = c.post("/api/v1/claude-sdk/session", params={"action": "create"})
        assert r.status_code in _UNAUTH, r.status_code

    def test_excel_requires_auth(self):
        from api.v1.claude_sdk import router

        c = _client(router, prefix="/api/v1")
        r = c.post("/api/v1/claude-sdk/excel", params={"operation": "create", "description": "x"})
        assert r.status_code in _UNAUTH, r.status_code

    def test_dashboard_health_requires_auth(self):
        from api.v1.claude_sdk import router

        c = _client(router, prefix="/api/v1")
        r = c.get("/api/v1/claude-sdk/dashboard/health")
        assert r.status_code in _UNAUTH, r.status_code


class TestWordPressWritesRequireAuth:
    def test_content_sync_requires_auth(self):
        from api.v1.wordpress import router

        c = _client(router, prefix="/api/v1")
        r = c.post("/api/v1/wordpress/sync", json={"title": "x", "content": "y"})
        assert r.status_code in _UNAUTH, r.status_code

    def test_product_sync_requires_auth(self, monkeypatch):
        # Configure the site URL so the settings gate passes and auth becomes
        # the effective gate (else get_settings 503s before auth resolves).
        monkeypatch.setenv("WORDPRESS_SITE_URL", "https://skyyrose.co")

        from api.v1.wordpress_integration import router

        c = _client(router, prefix="/api/v1")
        # Send a plausible product body; auth must reject before any live write.
        r = c.post(
            "/api/v1/wordpress/products/sync",
            json={"sku": "test-001", "name": "Test", "price": 10, "collection": "signature"},
        )
        assert r.status_code in _UNAUTH, r.status_code


class TestFeatureFlagsAdminOnly:
    def test_upsert_flag_requires_auth(self):
        from api.v1.feature_flags import router

        c = _client(router)  # router already carries /api/v1/flags prefix
        r = c.put("/api/v1/flags/test-flag", json={"name": "test-flag", "enabled": True})
        assert r.status_code in _UNAUTH, r.status_code

    def test_delete_flag_requires_auth(self):
        from api.v1.feature_flags import router

        c = _client(router)
        r = c.delete("/api/v1/flags/test-flag")
        assert r.status_code in _UNAUTH, r.status_code


class TestWebhookFailsClosed:
    """An unset WC_WEBHOOK_SECRET must reject webhooks, not trust empty-key HMAC."""

    def test_empty_secret_rejects_webhook(self, monkeypatch):
        monkeypatch.delenv("WC_WEBHOOK_SECRET", raising=False)
        monkeypatch.setenv("WORDPRESS_SITE_URL", "https://skyyrose.co")

        from api.v1.woocommerce_webhooks import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)

        body = b'{"id": 1, "price": "1.00"}'
        # Forge the signature the way an attacker would with an empty key.
        forged = base64.b64encode(hmac.new(b"", body, hashlib.sha256).digest()).decode()
        r = client.post(
            "/woocommerce/webhooks/product",
            content=body,
            headers={"X-WC-Webhook-Signature": forged, "Content-Type": "application/json"},
        )
        assert r.status_code == 401, r.status_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
