"""Unit tests for WCCredentials.from_env() — single-source WC credential resolution.

WCSafeClient appends the REST route itself, so from_env must return the SITE ROOT
under any of the repo's URL conventions, and accept the WC_/WOOCOMMERCE_ key names.
_ensure_wordpress_env_loaded is stubbed so the real .env.wordpress never leaks in.
"""

import pytest

import skyyrose.integrations.wc_safe_client as wc


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Never touch the real .env.wordpress during unit tests.
    monkeypatch.setattr(wc, "_ensure_wordpress_env_loaded", lambda: None)
    for var in (
        "WC_BASE_URL",
        "WORDPRESS_URL",
        "WP_SITE_URL",
        "WC_CONSUMER_KEY",
        "WOOCOMMERCE_KEY",
        "WC_CONSUMER_SECRET",
        "WOOCOMMERCE_SECRET",
    ):
        monkeypatch.delenv(var, raising=False)


def test_wordpress_url_resolves_to_site_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORDPRESS_URL", "https://skyyrose.co/")
    monkeypatch.setenv("WOOCOMMERCE_KEY", "ck_x")
    monkeypatch.setenv("WOOCOMMERCE_SECRET", "cs_x")
    creds = wc.WCCredentials.from_env()
    assert creds.base_url == "https://skyyrose.co"  # site root, REST suffix not appended
    assert creds.consumer_key == "ck_x"
    assert creds.consumer_secret == "cs_x"


def test_wc_base_url_full_rest_is_stripped_to_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WC_BASE_URL", "https://x.example/wp-json/wc/v3")
    monkeypatch.setenv("WC_CONSUMER_KEY", "ck_y")
    monkeypatch.setenv("WC_CONSUMER_SECRET", "cs_y")
    creds = wc.WCCredentials.from_env()
    assert creds.base_url == "https://x.example"


def test_missing_creds_raise_keyerror() -> None:
    with pytest.raises(KeyError):
        wc.WCCredentials.from_env()
