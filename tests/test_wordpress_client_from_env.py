"""Unit tests for WordPressClient.from_env() credential + URL resolution.

Covers the bug-165 hardening: the site URL may arrive under three conventions
(WORDPRESS_URL / WP_SITE_URL / WC_BASE_URL) and WC_BASE_URL is a full REST base
that must be normalized back to the site root. No network, no real .env —
environment is monkeypatched.
"""

import asyncio

import pytest

from integrations.wordpress_client import WordPressClient, WordPressWooCommerceClient

_WC_VARS = (
    "WORDPRESS_URL",
    "WP_SITE_URL",
    "WC_BASE_URL",
    "WC_CONSUMER_KEY",
    "WOOCOMMERCE_KEY",
    "WC_CONSUMER_SECRET",
    "WOOCOMMERCE_SECRET",
)


def _clear(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _WC_VARS:
        monkeypatch.delenv(var, raising=False)


def _close(client: WordPressClient) -> None:
    # __post_init__ opens an httpx.AsyncClient — close it to avoid ResourceWarning.
    asyncio.run(client.close())


def test_alias_resolves_to_real_client() -> None:
    assert WordPressWooCommerceClient is WordPressClient


def test_wc_base_url_is_normalized_to_site_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """WC_BASE_URL (full REST base) → stripped to the site root the client expects."""
    _clear(monkeypatch)
    monkeypatch.setenv("WC_BASE_URL", "https://skyyrose.com/wp-json/wc/v3")
    monkeypatch.setenv("WC_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WC_CONSUMER_SECRET", "cs_test")

    client = WordPressClient.from_env()
    try:
        assert client.site_url == "https://skyyrose.com"
        assert client.consumer_key == "ck_test"
        # Property re-appends the REST path exactly once (no doubled suffix).
        assert client.wc_base_url == "https://skyyrose.com/wp-json/wc/v3"
    finally:
        _close(client)


def test_site_root_url_and_woocommerce_key_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """WORDPRESS_URL (already a root) + the WOOCOMMERCE_* key/secret names."""
    _clear(monkeypatch)
    monkeypatch.setenv("WORDPRESS_URL", "https://skyyrose.com/")
    monkeypatch.setenv("WOOCOMMERCE_KEY", "ck_y")
    monkeypatch.setenv("WOOCOMMERCE_SECRET", "cs_y")

    client = WordPressClient.from_env()
    try:
        assert client.site_url == "https://skyyrose.com"  # trailing slash stripped
        assert client.consumer_key == "ck_y"
        assert client.consumer_secret == "cs_y"
    finally:
        _close(client)


def test_missing_credentials_raises_valueerror(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    with pytest.raises(ValueError):
        WordPressClient.from_env()
