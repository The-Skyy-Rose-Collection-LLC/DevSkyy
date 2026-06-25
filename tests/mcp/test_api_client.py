"""Regression tests for mcp_tools/api_client.py request construction.

Covers (bug-135):
  - An empty DEVSKYY_API_KEY must NOT emit an "Authorization: Bearer " header.
    The trailing-space-only value is rejected by httpx with LocalProtocolError
    before the request is sent, which silently broke every backend tool call.
  - A configured key IS sent as a Bearer token.
  - The endpoint string maps to /api/v1/<endpoint> (the list_agents tool now
    calls "agents", not the 422-returning "agents/list").
"""

from __future__ import annotations

import pytest

import mcp_tools.api_client as ac


class _FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict[str, str]]:
        return [{"id": "agent-1"}]


class _CapturingClient:
    """Stand-in for httpx.AsyncClient that records the request kwargs."""

    captured: dict = {}

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> _CapturingClient:
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def request(self, *, method, url, headers, json=None, params=None) -> _FakeResponse:
        _CapturingClient.captured = {"method": method, "url": url, "headers": dict(headers)}
        return _FakeResponse()


@pytest.mark.asyncio
async def test_empty_api_key_omits_authorization_header(monkeypatch):
    monkeypatch.setattr(ac, "API_KEY", "")
    monkeypatch.setattr(ac.httpx, "AsyncClient", _CapturingClient)
    _CapturingClient.captured = {}

    await ac._make_api_request("agents", method="GET")

    cap = _CapturingClient.captured
    assert cap["url"].endswith("/api/v1/agents")
    assert "Authorization" not in cap["headers"], "empty key must not produce 'Bearer '"


@pytest.mark.asyncio
async def test_configured_api_key_sends_bearer(monkeypatch):
    monkeypatch.setattr(ac, "API_KEY", "test-key-123")
    monkeypatch.setattr(ac.httpx, "AsyncClient", _CapturingClient)
    _CapturingClient.captured = {}

    await ac._make_api_request("health", method="GET")

    assert _CapturingClient.captured["headers"]["Authorization"] == "Bearer test-key-123"
