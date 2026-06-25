"""Tests for ADK model resolution.

Verifies that Claude is the default reasoning model, that explicit
model IDs pass through, that GPT-4o aliases redirect to the reasoning
default, and that LiteLlm wrapping kicks in for Anthropic / OpenAI.
"""

from __future__ import annotations

from adk import google_adk
from adk.google_adk import (
    DEFAULT_REASONING_MODEL,
    FALLBACK_GEMINI_MODEL,
    _canonical_model_id,
)


class TestCanonicalModelId:
    def test_empty_returns_default(self):
        assert _canonical_model_id("") == DEFAULT_REASONING_MODEL
        assert _canonical_model_id(None) == DEFAULT_REASONING_MODEL
        assert _canonical_model_id("   ") == DEFAULT_REASONING_MODEL

    def test_default_is_claude_sonnet(self):
        assert DEFAULT_REASONING_MODEL == "claude-sonnet-4-6"

    def test_gpt4o_aliases_promoted_to_claude(self):
        assert _canonical_model_id("gpt-4o") == DEFAULT_REASONING_MODEL
        assert _canonical_model_id("gpt-4o-mini") == DEFAULT_REASONING_MODEL

    def test_explicit_gemini_passes_through(self):
        assert _canonical_model_id("gemini-2.0-flash") == "gemini-2.0-flash"
        assert _canonical_model_id("gemini-1.5-pro") == "gemini-1.5-pro"

    def test_explicit_claude_passes_through(self):
        assert _canonical_model_id("claude-haiku-4-5") == "claude-haiku-4-5"
        assert _canonical_model_id("claude-opus-4-7") == "claude-opus-4-7"

    def test_explicit_unknown_passes_through(self):
        # The resolver shouldn't second-guess unknown model strings.
        assert _canonical_model_id("custom-model-x") == "custom-model-x"


class TestResolveAdkModel:
    def test_gemini_returns_plain_string(self):
        # Gemini is native to ADK — no wrapping needed.
        result = google_adk._resolve_adk_model("gemini-2.0-flash")
        assert result == "gemini-2.0-flash"
        assert isinstance(result, str)

    def test_non_gemini_falls_back_when_litellm_missing(self, monkeypatch):
        monkeypatch.setattr(google_adk, "LITELLM_AVAILABLE", False)
        result = google_adk._resolve_adk_model("claude-sonnet-4-6")
        assert result == FALLBACK_GEMINI_MODEL

    def test_claude_wraps_in_litellm_when_available(self, monkeypatch):
        # Mock LiteLlm so the test runs without the extension
        captured = {}

        class FakeLiteLlm:
            def __init__(self, model: str):
                captured["model"] = model
                self.model = model

        monkeypatch.setattr(google_adk, "LITELLM_AVAILABLE", True)
        monkeypatch.setattr(google_adk, "LiteLlm", FakeLiteLlm)

        result = google_adk._resolve_adk_model("claude-sonnet-4-6")
        assert isinstance(result, FakeLiteLlm)
        # Bare "claude-..." gets the anthropic/ provider prefix.
        assert captured["model"] == "anthropic/claude-sonnet-4-6"

    def test_anthropic_prefix_passes_through(self, monkeypatch):
        captured = {}

        class FakeLiteLlm:
            def __init__(self, model: str):
                captured["model"] = model

        monkeypatch.setattr(google_adk, "LITELLM_AVAILABLE", True)
        monkeypatch.setattr(google_adk, "LiteLlm", FakeLiteLlm)

        google_adk._resolve_adk_model("anthropic/claude-sonnet-4-6")
        # Already namespaced — don't double-prefix.
        assert captured["model"] == "anthropic/claude-sonnet-4-6"

    def test_gpt_wraps_with_openai_prefix(self, monkeypatch):
        captured = {}

        class FakeLiteLlm:
            def __init__(self, model: str):
                captured["model"] = model

        monkeypatch.setattr(google_adk, "LITELLM_AVAILABLE", True)
        monkeypatch.setattr(google_adk, "LiteLlm", FakeLiteLlm)

        google_adk._resolve_adk_model("gpt-5")
        assert captured["model"] == "openai/gpt-5"


class TestResolveModelForConfig:
    def test_uses_canonical_id(self, monkeypatch):
        from adk.base import ADKProvider, AgentConfig

        # Mock LiteLlm so this test doesn't depend on the extension
        class FakeLiteLlm:
            def __init__(self, model: str):
                self.model = model

        monkeypatch.setattr(google_adk, "LITELLM_AVAILABLE", True)
        monkeypatch.setattr(google_adk, "LiteLlm", FakeLiteLlm)

        # gpt-4o alias → promoted to Claude → wrapped in LiteLlm
        cfg = AgentConfig(name="t", model="gpt-4o", provider=ADKProvider.GOOGLE)
        resolved = google_adk._resolve_model_for_config(cfg)
        assert isinstance(resolved, FakeLiteLlm)
        assert resolved.model == f"anthropic/{DEFAULT_REASONING_MODEL}"
