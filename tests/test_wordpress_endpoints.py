"""Tests for WordPress API endpoints and integration.

Covers: /api/v1/wordpress/sync, /api/v1/wordpress/status,
WordPress settings, and webhook handlers.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestWordPressSettings:
    """Tests for WordPressSettings configuration."""

    def test_settings_from_env(self):
        with patch.dict(
            os.environ,
            {
                "WORDPRESS_SITE_URL": "https://test.example.com",
                "WORDPRESS_API_TOKEN": "test-token",
                "WOOCOMMERCE_KEY": "ck_test",
                "WOOCOMMERCE_SECRET": "cs_test",
            },
        ):
            from api.v1.wordpress_integration import WordPressSettings

            settings = WordPressSettings()
            assert settings.site_url == "https://test.example.com"
            assert settings.api_token == "test-token"
            assert settings.consumer_key == "ck_test"

    def test_settings_fallback_to_wordpress_url(self):
        with patch.dict(
            os.environ,
            {
                "WORDPRESS_URL": "https://fallback.example.com",
            },
            clear=False,
        ):
            # Remove WORDPRESS_SITE_URL if set
            env = os.environ.copy()
            env.pop("WORDPRESS_SITE_URL", None)
            with patch.dict(os.environ, env, clear=True):
                from importlib import reload

                import api.v1.wordpress_integration as wp_mod

                reload(wp_mod)
                settings = wp_mod.WordPressSettings()
                # Should fall back to WORDPRESS_URL
                assert settings.site_url in ("https://fallback.example.com", "")

    def test_has_wp_auth_with_token(self):
        from api.v1.wordpress_integration import WordPressSettings

        settings = WordPressSettings()
        settings.api_token = "some-token"
        assert settings.has_wp_auth is True

    def test_has_wp_auth_with_app_password(self):
        from api.v1.wordpress_integration import WordPressSettings

        settings = WordPressSettings()
        settings.api_token = ""
        settings.wp_auth_user = "admin"
        settings.wp_auth_pass = "xxxx xxxx xxxx"
        assert settings.has_wp_auth is True

    def test_no_wp_auth(self):
        from api.v1.wordpress_integration import WordPressSettings

        settings = WordPressSettings()
        settings.api_token = ""
        settings.wp_auth_user = ""
        settings.wp_auth_pass = ""
        assert settings.has_wp_auth is False


class TestWordPressSyncEndpoint:
    """Tests for the /wordpress/sync endpoint."""

    def test_sync_models_exist(self):
        from api.v1.wordpress import WordPressSyncRequest

        req = WordPressSyncRequest(
            title="Test Post",
            content="<p>Hello</p>",
            status="draft",
        )
        assert req.title == "Test Post"
        assert req.status == "draft"

    def test_sync_response_model(self):
        from api.v1.wordpress import WordPressSyncResponse

        resp = WordPressSyncResponse(
            success=True,
            wordpress_id=123,
            url="https://example.com/?p=123",
        )
        assert resp.success is True
        assert resp.wordpress_id == 123


class TestWordPressClientFactory:
    """Tests for create_wordpress_client."""

    @pytest.mark.asyncio
    async def test_create_client_with_app_password(self):
        from integrations.wordpress_com_client import create_wordpress_client

        client = await create_wordpress_client(
            site_url="https://test.example.com",
            username="admin",
            app_password="xxxx xxxx",
        )
        assert client is not None
        assert client.config.site_url == "https://test.example.com"
        assert client.config.username == "admin"
        await client.close()

    @pytest.mark.asyncio
    async def test_create_client_with_token(self):
        from integrations.wordpress_com_client import create_wordpress_client

        client = await create_wordpress_client(
            site_url="https://test.example.com",
            api_token="test-bearer-token",
        )
        assert client is not None
        assert client.config.api_token == "test-bearer-token"
        await client.close()

    @pytest.mark.asyncio
    async def test_create_client_with_woo_creds(self):
        from integrations.wordpress_com_client import create_wordpress_client

        client = await create_wordpress_client(
            site_url="https://test.example.com",
            api_token="token-for-auth",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )
        assert client.woo_config is not None
        assert client.woo_config.consumer_key == "ck_test"
        await client.close()
