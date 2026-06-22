"""Tests for the fleet-telemetry emitter — record_llm_usage() + LLMRouter wiring.

The observability gap had two halves: no consumer (FleetObserver, tested separately) AND a
dead emit path (get_token_tracker had zero callers). These tests cover the emit half:
record_llm_usage attributes a call to the current agent (via ContextVar), records failures,
never raises, and LLMRouter.complete() actually calls it on both success and failure.
"""

from __future__ import annotations

import pytest

from core.token_tracker import current_agent_id, get_token_tracker, record_llm_usage
from llm import ModelProvider
from llm.base import CompletionResponse, Message
from llm.router import LLMRouter


@pytest.fixture(autouse=True)
def _reset_tracker_and_ctx():
    import core.token_tracker as _tt

    _tt._global_tracker = None
    _tt.current_agent_id.set(None)
    yield
    _tt.get_token_tracker().clear()
    _tt.current_agent_id.set(None)


# --- record_llm_usage helper ---------------------------------------------------


def test_record_llm_usage_attributes_to_contextvar():
    current_agent_id.set("agentX")
    record_llm_usage(provider="openai", model="gpt-4o", input_tokens=10, output_tokens=5)
    by_agent = get_token_tracker().get_usage_by_agent()
    assert by_agent["agentX"]["requests"] == 1
    assert by_agent["agentX"]["total_tokens"] == 15  # auto-filled by record()


def test_record_llm_usage_explicit_agent_id_overrides_contextvar():
    current_agent_id.set("ctxAgent")
    record_llm_usage(provider="openai", model="gpt-4o", agent_id="explicit", input_tokens=1)
    by_agent = get_token_tracker().get_usage_by_agent()
    assert "explicit" in by_agent
    assert "ctxAgent" not in by_agent


def test_record_llm_usage_unknown_when_no_contextvar():
    record_llm_usage(provider="openai", model="gpt-4o", input_tokens=1)
    assert "unknown" in get_token_tracker().get_usage_by_agent()


def test_record_llm_usage_records_failure():
    record_llm_usage(provider="openai", model="gpt-4o", success=False, error="boom")
    recs = get_token_tracker().records()
    assert len(recs) == 1
    assert recs[0].success is False
    assert recs[0].error == "boom"


def test_record_llm_usage_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("tracker exploded")

    monkeypatch.setattr("core.token_tracker.get_token_tracker", boom)
    record_llm_usage(provider="openai", model="gpt-4o", input_tokens=1)  # must not raise


# --- LLMRouter.complete() wiring ----------------------------------------------


async def test_router_complete_records_success(monkeypatch):
    router = LLMRouter()
    resp = CompletionResponse(
        content="hi",
        model="gpt-4o",
        provider="openai",
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        latency_ms=120.0,
    )

    class _FakeClient:
        async def complete(self, messages, model=None, **kwargs):
            return resp

    monkeypatch.setattr(router, "_get_client", lambda provider: _FakeClient())
    current_agent_id.set("router_agent")

    out = await router.complete([Message.user("hi")], provider=ModelProvider.OPENAI)

    assert out is resp
    by_agent = get_token_tracker().get_usage_by_agent()
    assert by_agent["router_agent"]["requests"] == 1
    assert by_agent["router_agent"]["total_tokens"] == 15


async def test_router_complete_records_failure(monkeypatch):
    router = LLMRouter()

    class _BoomClient:
        async def complete(self, messages, model=None, **kwargs):
            raise RuntimeError("provider down")

    monkeypatch.setattr(router, "_get_client", lambda provider: _BoomClient())
    current_agent_id.set("boom_agent")

    with pytest.raises(Exception):
        await router.complete([Message.user("hi")], provider=ModelProvider.OPENAI)

    recs = get_token_tracker().records()
    assert any((not r.success) and r.agent_id == "boom_agent" for r in recs)


async def test_router_circuit_breaker_open_records_failure(monkeypatch):
    """A circuit-breaker-blocked call still emits a failure record (no silent telemetry gap)."""
    router = LLMRouter()
    monkeypatch.setattr(router.circuit_breaker, "is_available", lambda provider: False)
    current_agent_id.set("cb_agent")

    with pytest.raises(Exception):
        await router.complete([Message.user("hi")], provider=ModelProvider.OPENAI)

    recs = get_token_tracker().records()
    assert any(
        (not r.success) and r.agent_id == "cb_agent" and "circuit_breaker" in (r.error or "")
        for r in recs
    )
