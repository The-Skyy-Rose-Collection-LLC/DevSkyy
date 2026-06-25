"""WooCommerce REST client with correct 429 handling on EVERY HTTP verb.

Closes archive Pattern #2 (May 13 obs #4479..#4540): the existing scripts
built retry into write paths but not read paths. smoketest, fetch_live, diff
verification, and trash all crashed on first GET 429 before any write ran.

This client wraps httpx.AsyncClient with:
    - Honors `Retry-After` header (in seconds OR HTTP date)
    - Falls back to exponential backoff (1s, 2s, 4s, 8s, 16s, 32s) on 429/503
    - Per-retry Retry-After capped at 60s; total elapsed capped at 120s
      (defends against a hostile server pinning us at minutes-per-retry)
    - Applies to every verb: GET, POST, PUT, PATCH, DELETE

Existing infrastructure NOT replaced: `sync/woocommerce_sync.py::WooCommerceSyncClient`
remains the canonical sync path. This module is the SAFE base for new code
(MCP tools, scripts) that must survive 429 bursts. Migrating the existing
client is out of scope.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

# 429/503 retry policy. Per-retry backoff is exponential (1s..32s) but a
# server-provided Retry-After can extend each individual wait up to 60s.
# A hard total-time deadline (_TOTAL_DEADLINE_SECONDS) caps the whole loop
# to prevent a hostile or misconfigured server from pinning us for minutes.
_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
_RETRIABLE_STATUSES = frozenset({429, 503})
_RETRIABLE_NETWORK_ERRORS = (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)
_TOTAL_DEADLINE_SECONDS = 120.0  # Hard ceiling across all retries combined.


@dataclass(frozen=True)
class WCCredentials:
    """WooCommerce REST credentials. Loaded from env at construction time.

    `consumer_key` and `consumer_secret` are excluded from the default repr so
    that accidental `logger.debug(creds)` or traceback inclusion does not leak
    plaintext secrets to logs (CR finding 2026-05-22).
    """

    base_url: str
    consumer_key: str = field(repr=False)
    consumer_secret: str = field(repr=False)

    @classmethod
    def from_env(cls) -> WCCredentials:
        """Load credentials from env. Raises KeyError if any are missing."""
        return cls(
            base_url=os.environ["WC_BASE_URL"].rstrip("/"),
            consumer_key=os.environ["WC_CONSUMER_KEY"],
            consumer_secret=os.environ["WC_CONSUMER_SECRET"],
        )

    def __str__(self) -> str:
        # Belt-and-braces: also redact in str() in case anything bypasses repr.
        return f"WCCredentials(base_url={self.base_url!r}, consumer_key=<redacted>, consumer_secret=<redacted>)"


def _parse_retry_after(value: str | None, default: float) -> float:
    """Parse Retry-After (seconds or HTTP date). Falls back to `default` on parse failure."""
    if not value:
        return default
    value = value.strip()
    try:
        return float(value)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        delta = (when - datetime.now(UTC)).total_seconds()
        return max(delta, 0.0)
    except (TypeError, ValueError):
        return default


class WCSafeClient:
    """Async WooCommerce REST client with retry-on-every-verb.

    Usage:
        async with WCSafeClient.from_env() as client:
            products = await client.get("products", params={"per_page": 100})
    """

    def __init__(
        self,
        credentials: WCCredentials,
        timeout_seconds: float = 30.0,
        max_retries: int = 6,
    ) -> None:
        self._creds = credentials
        self._max_retries = min(max_retries, len(_RETRY_DELAYS_SECONDS))
        self._client = httpx.AsyncClient(
            base_url=credentials.base_url,
            auth=(credentials.consumer_key, credentials.consumer_secret),
            timeout=timeout_seconds,
            follow_redirects=True,
        )

    @classmethod
    def from_env(cls, **kwargs: Any) -> WCSafeClient:
        return cls(WCCredentials.from_env(), **kwargs)

    async def __aenter__(self) -> WCSafeClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        sleep: Any = asyncio.sleep,
    ) -> httpx.Response:
        """Execute one request, retrying on 429/503/network errors.

        Total time budget: bounded by `_TOTAL_DEADLINE_SECONDS` (default 120s).
        The previous "~63s worst case" claim was wrong — Retry-After per-retry
        cap of 60s × 6 retries = 360s in the worst case. We now track elapsed
        time and abort early when the deadline is exceeded.

        `sleep` is injectable so tests can substitute a mock that returns
        immediately rather than actually waiting on real backoff.
        """
        # WordPress.com hosting disables pretty permalinks — must use the
        # index.php?rest_route= form per CLAUDE.md WordPress rules
        # (CR finding 2026-05-22).
        url = path if path.startswith("/") else f"/index.php?rest_route=/wc/v3/{path}"

        deadline = time.monotonic() + _TOTAL_DEADLINE_SECONDS
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.request(method, url, params=params, json=json)
            except _RETRIABLE_NETWORK_ERRORS as exc:
                last_exc = exc
                if attempt >= self._max_retries or time.monotonic() >= deadline:
                    raise
                await sleep(_RETRY_DELAYS_SECONDS[attempt])
                continue

            if response.status_code not in _RETRIABLE_STATUSES:
                return response

            # 429 / 503 — honor Retry-After if present.
            if attempt >= self._max_retries:
                return response  # Caller sees the final 429/503.

            backoff = _RETRY_DELAYS_SECONDS[attempt]
            retry_after = _parse_retry_after(response.headers.get("Retry-After"), backoff)
            # Cap Retry-After at 60s to defend against a hostile server pinning
            # us at minutes-per-retry. Honor the larger of (our backoff,
            # server's ask capped at 60s) so we don't out-spam an explicit ask.
            wait = max(backoff, min(retry_after, 60.0))
            # Hard deadline: if waiting would exceed the total budget, return
            # the 429/503 response now instead of one more cycle.
            if time.monotonic() + wait >= deadline:
                return response
            await sleep(wait)

        if last_exc:
            raise last_exc
        raise RuntimeError("unreachable: retry loop exited without response or exception")

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        return await self._request_with_retry("GET", path, params=params)

    async def post(self, path: str, json: dict) -> httpx.Response:
        return await self._request_with_retry("POST", path, json=json)

    async def put(self, path: str, json: dict) -> httpx.Response:
        return await self._request_with_retry("PUT", path, json=json)

    async def patch(self, path: str, json: dict) -> httpx.Response:
        return await self._request_with_retry("PATCH", path, json=json)

    async def delete(self, path: str, params: dict | None = None) -> httpx.Response:
        return await self._request_with_retry("DELETE", path, params=params)
