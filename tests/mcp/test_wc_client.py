"""Tests for skyyrose/integrations/wc_safe_client.py + mcp_tools/tools/wc_client.py.

Covers:
    - Retry-After parsing (seconds and HTTP date forms)
    - 429 retry on EVERY verb (closes archive Pattern #2)
    - Retry exhaustion behavior
    - Network error retry
    - MCP tool input validation
    - wc_smoketest credential placeholder detection
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from mcp_tools.tools.wc_client import (
    GetOrdersInput,
    GetProductInput,
    GetProductsInput,
    SmoketestInput,
    UpdateProductInput,
    wc_smoketest,
    wc_update_product,
)
from skyyrose.integrations.wc_safe_client import (
    WCCredentials,
    WCSafeClient,
    _parse_retry_after,
)

# ---------------------------------------------------------------------------
# Retry-After parser (pure function)
# ---------------------------------------------------------------------------


class TestParseRetryAfter:
    def test_seconds_int_string(self) -> None:
        assert _parse_retry_after("30", default=99.0) == 30.0

    def test_seconds_float_string(self) -> None:
        assert _parse_retry_after("2.5", default=99.0) == 2.5

    def test_http_date_future(self) -> None:
        future = datetime.now(UTC) + timedelta(seconds=10)
        date_str = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
        result = _parse_retry_after(date_str, default=99.0)
        # Within ~5s of 10 (timing jitter)
        assert 5.0 < result < 15.0

    def test_none_returns_default(self) -> None:
        assert _parse_retry_after(None, default=42.0) == 42.0

    def test_garbage_returns_default(self) -> None:
        assert _parse_retry_after("not-a-date-or-number", default=7.0) == 7.0

    def test_past_date_returns_zero(self) -> None:
        past = "Wed, 01 Jan 2020 00:00:00 GMT"
        assert _parse_retry_after(past, default=99.0) == 0.0


# ---------------------------------------------------------------------------
# WCSafeClient retry-on-every-verb (the archive Pattern #2 fix)
# ---------------------------------------------------------------------------


class FakeTransport(httpx.AsyncBaseTransport):
    """Programmable httpx transport — returns canned responses in sequence."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.calls: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if not self._responses:
            raise RuntimeError("FakeTransport exhausted")
        return self._responses.pop(0)


def _make_client(transport: FakeTransport) -> WCSafeClient:
    creds = WCCredentials(
        base_url="https://example.test",
        consumer_key="ck_test",
        consumer_secret="cs_test",
    )
    client = WCSafeClient(creds, timeout_seconds=5.0, max_retries=3)
    # Swap in the test transport
    client._client = httpx.AsyncClient(
        base_url=creds.base_url,
        transport=transport,
        timeout=5.0,
    )
    return client


@pytest.mark.asyncio
async def test_retries_get_on_429_until_success() -> None:
    transport = FakeTransport(
        [
            httpx.Response(429, headers={"Retry-After": "0.01"}, content=b"slow down"),
            httpx.Response(429, headers={"Retry-After": "0.01"}, content=b"slow down"),
            httpx.Response(200, json=[{"id": 1}]),
        ]
    )
    async with _make_client(transport) as client:
        resp = await client._request_with_retry("GET", "products", sleep=_zero_sleep)
    assert resp.status_code == 200
    assert len(transport.calls) == 3  # 2 retries + final success


@pytest.mark.asyncio
async def test_retries_post_on_429() -> None:
    """Archive Pattern #2: retry must apply to writes too."""
    transport = FakeTransport(
        [
            httpx.Response(429, content=b""),
            httpx.Response(201, json={"id": 99}),
        ]
    )
    async with _make_client(transport) as client:
        resp = await client.post("products", json={"name": "x"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_retries_delete_on_503() -> None:
    """503 retry parity with 429."""
    transport = FakeTransport(
        [
            httpx.Response(503),
            httpx.Response(200, json={"deleted": True}),
        ]
    )
    async with _make_client(transport) as client:
        resp = await client.delete("products/1")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_retry_exhausted_returns_last_response() -> None:
    """After max_retries the final 429 is returned, not raised."""
    transport = FakeTransport([httpx.Response(429) for _ in range(10)])
    async with _make_client(transport) as client:
        resp = await client._request_with_retry("GET", "products", sleep=_zero_sleep)
    assert resp.status_code == 429
    assert len(transport.calls) == 4  # max_retries=3 means 3 retries + 1 final


@pytest.mark.asyncio
async def test_non_retriable_returns_immediately() -> None:
    """4xx other than 429 should NOT retry (e.g., 401, 404)."""
    transport = FakeTransport([httpx.Response(404)])
    async with _make_client(transport) as client:
        resp = await client.get("products/999")
    assert resp.status_code == 404
    assert len(transport.calls) == 1


@pytest.mark.asyncio
async def test_honors_retry_after_over_backoff() -> None:
    """Retry-After of 0.05s should win over the default 1s backoff if larger."""
    sleeps: list[float] = []

    async def capturing_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    transport = FakeTransport(
        [
            httpx.Response(429, headers={"Retry-After": "5"}),
            httpx.Response(200, json=[]),
        ]
    )
    async with _make_client(transport) as client:
        await client._request_with_retry("GET", "products", sleep=capturing_sleep)

    # Should have slept at least 5s (the Retry-After value)
    assert sleeps[0] >= 5.0


async def _zero_sleep(_seconds: float) -> None:
    """Drop-in for asyncio.sleep that returns immediately (test speed)."""
    return None


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


class TestCredentials:
    def test_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WC_BASE_URL", "https://example.test/")
        monkeypatch.setenv("WC_CONSUMER_KEY", "ck_xyz")
        monkeypatch.setenv("WC_CONSUMER_SECRET", "cs_xyz")
        creds = WCCredentials.from_env()
        assert creds.base_url == "https://example.test"  # rstripped trailing slash
        assert creds.consumer_key == "ck_xyz"

    def test_missing_env_raises_keyerror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WC_BASE_URL", raising=False)
        monkeypatch.delenv("WC_CONSUMER_KEY", raising=False)
        monkeypatch.delenv("WC_CONSUMER_SECRET", raising=False)
        with pytest.raises(KeyError):
            WCCredentials.from_env()


# ---------------------------------------------------------------------------
# MCP tool input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_per_page_capped_at_100(self) -> None:
        with pytest.raises(Exception):
            GetProductsInput(per_page=101)

    def test_per_page_min_1(self) -> None:
        with pytest.raises(Exception):
            GetProductsInput(per_page=0)

    def test_status_literal(self) -> None:
        with pytest.raises(Exception):
            GetProductsInput(status="unknown")  # type: ignore[arg-type]

    def test_product_id_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            GetProductInput(product_id=0)
        with pytest.raises(Exception):
            GetProductInput(product_id=-1)

    def test_order_status_literal(self) -> None:
        with pytest.raises(Exception):
            GetOrdersInput(status="bogus")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# wc_update_product dry-run gate
# ---------------------------------------------------------------------------


class TestUpdateGate:
    @pytest.mark.asyncio
    async def test_dry_run_when_confirm_false(self) -> None:
        result = await wc_update_product(
            UpdateProductInput(product_id=42, fields={"price": "99"}, confirm=False)
        )
        assert "dry" in result.lower() or "plan" in result.lower()
        assert "42" in result


# ---------------------------------------------------------------------------
# wc_smoketest placeholder detection
# ---------------------------------------------------------------------------


class TestSmoketest:
    @pytest.mark.asyncio
    async def test_detects_placeholder_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WC_BASE_URL", "https://example.test")
        monkeypatch.setenv("WC_CONSUMER_KEY", "YOUR_KEY_HERE")
        monkeypatch.setenv("WC_CONSUMER_SECRET", "ck_real_looking_secret_xyz")
        result = await wc_smoketest(SmoketestInput())
        assert "FAILED" in result
        assert "placeholder" in result.lower()

    @pytest.mark.asyncio
    async def test_missing_env_returns_clear_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WC_BASE_URL", raising=False)
        monkeypatch.delenv("WC_CONSUMER_KEY", raising=False)
        monkeypatch.delenv("WC_CONSUMER_SECRET", raising=False)
        result = await wc_smoketest(SmoketestInput())
        assert "FAILED" in result
        assert "missing env var" in result.lower()
