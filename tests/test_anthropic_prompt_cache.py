"""Tests for Anthropic prompt caching.

Verifies that the AnthropicClient sends `cache_control: ephemeral` on the
system prompt by default, and that opt-out via `cache_system=False`
works. Cache metrics from the response should land in `metadata`.
"""

from __future__ import annotations

import pytest

from llm.providers.anthropic import AnthropicClient


class TestFormatSystem:
    def test_cache_disabled_returns_bare_string(self):
        out = AnthropicClient._format_system("hello", with_cache_control=False)
        assert out == "hello"

    def test_cache_enabled_returns_array_with_cache_control(self):
        out = AnthropicClient._format_system("hello", with_cache_control=True)
        assert isinstance(out, list)
        assert len(out) == 1
        block = out[0]
        assert block["type"] == "text"
        assert block["text"] == "hello"
        assert block["cache_control"] == {"type": "ephemeral"}

    def test_cache_enabled_preserves_long_brand_dna(self):
        brand_dna = "\n".join(
            f"Line {i}: SkyyRose brand context line for caching." for i in range(50)
        )
        out = AnthropicClient._format_system(brand_dna, with_cache_control=True)
        assert out[0]["text"] == brand_dna
        assert out[0]["cache_control"]["type"] == "ephemeral"


@pytest.mark.asyncio
class TestCompleteRequestPayload:
    """Verify that the request payload sent to Anthropic includes cache_control.

    We don't actually hit the API — we patch `_make_request` and inspect
    the JSON body the client constructed.
    """

    async def _run_complete(self, monkeypatch, cache_system: bool | None = None):
        from llm.base import Message

        client = AnthropicClient(api_key="test-key")
        captured: dict[str, dict] = {}

        class FakeResponse:
            def json(self):
                return {
                    "content": [{"type": "text", "text": "ok"}],
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 10,
                        "cache_creation_input_tokens": 80,
                        "cache_read_input_tokens": 0,
                    },
                    "stop_reason": "end_turn",
                }

        async def fake_make_request(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = kwargs.get("json")
            return FakeResponse()

        monkeypatch.setattr(client, "_make_request", fake_make_request)

        kwargs = {} if cache_system is None else {"cache_system": cache_system}
        response = await client.complete(
            messages=[
                Message.system("Brand DNA context goes here."),
                Message.user("Generate a hero shot."),
            ],
            **kwargs,
        )
        return captured, response

    async def test_default_payload_uses_cache_control(self, monkeypatch):
        captured, _ = await self._run_complete(monkeypatch)
        body = captured["json"]
        assert isinstance(body["system"], list)
        assert body["system"][0]["cache_control"] == {"type": "ephemeral"}
        assert body["system"][0]["text"] == "Brand DNA context goes here."

    async def test_opt_out_payload_uses_bare_string(self, monkeypatch):
        captured, _ = await self._run_complete(monkeypatch, cache_system=False)
        body = captured["json"]
        assert body["system"] == "Brand DNA context goes here."

    async def test_response_metadata_carries_cache_metrics(self, monkeypatch):
        _, response = await self._run_complete(monkeypatch)
        assert response.metadata["cache_creation_input_tokens"] == 80
        assert response.metadata["cache_read_input_tokens"] == 0
