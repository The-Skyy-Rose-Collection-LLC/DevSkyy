"""Unit tests for mcp_tools.http_mount: tool_count + BearerAuthMiddleware.

tool_count: not a hard-asserted exact count (brittle) — only a positive int.
BearerAuthMiddleware: the fail-closed auth on the internet-facing /mcp mount —
a revert to fail-open (missing token silently allowed in prod) or to a plain
`!=` compare must make one of these tests fail.
"""

import asyncio

from mcp_tools.http_mount import BearerAuthMiddleware, tool_count


def test_tool_count_is_positive_int():
    n = asyncio.run(tool_count())
    assert isinstance(n, int)
    assert n > 0


class _DummyApp:
    """Inner ASGI app that records whether the middleware let a request through."""

    def __init__(self) -> None:
        self.called = False

    async def __call__(self, scope, receive, send) -> None:
        self.called = True


async def _drive(mw, headers=None):
    scope = {"type": "http", "headers": headers or []}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        sent.append(message)

    await mw(scope, receive, send)
    return sent


def _status(sent):
    for message in sent:
        if message.get("type") == "http.response.start":
            return message["status"]
    return None


def test_missing_token_in_production_is_rejected(monkeypatch):
    # Fail-closed: no MCP_SERVICE_TOKEN outside dev must NOT open /mcp.
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("MCP_SERVICE_TOKEN", raising=False)
    inner = _DummyApp()
    sent = asyncio.run(_drive(BearerAuthMiddleware(inner)))
    assert inner.called is False
    assert _status(sent) == 401


def test_missing_token_in_development_passes_through(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("MCP_SERVICE_TOKEN", raising=False)
    inner = _DummyApp()
    asyncio.run(_drive(BearerAuthMiddleware(inner)))
    assert inner.called is True


def test_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("MCP_SERVICE_TOKEN", "s3cret")
    inner = _DummyApp()
    sent = asyncio.run(
        _drive(BearerAuthMiddleware(inner), headers=[(b"authorization", b"Bearer wrong")])
    )
    assert inner.called is False
    assert _status(sent) == 401


def test_correct_token_passes_through(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("MCP_SERVICE_TOKEN", "s3cret")
    inner = _DummyApp()
    asyncio.run(_drive(BearerAuthMiddleware(inner), headers=[(b"authorization", b"Bearer s3cret")]))
    assert inner.called is True
