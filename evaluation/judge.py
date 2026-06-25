"""Claude judge — vision or text — via forced tool-use (Anthropic structured output).

Anthropic has no OpenAI-style json_schema response_format; the reliable structured
path is tools + tool_choice={"type":"tool", name, disable_parallel_tool_use:True},
then read the single tool_use block's `.input`. Verified against anthropic 0.83.0.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# USD per 1M tokens (input, output). Keep in sync with model-routing doc.
_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (15.0, 75.0),
}


_VALID_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/gif", "image/webp"})


def anthropic_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in _PRICING:
        logger.warning("anthropic_cost_usd: unknown model %r — using Sonnet pricing", model)
    pin, pout = _PRICING.get(model, (3.0, 15.0))
    return input_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout


def make_client() -> Any:
    """Construct an Anthropic client from config.settings.ANTHROPIC_API_KEY.

    Note: `.strip()` is applied so a whitespace-only key is treated as empty.
    """
    from anthropic import Anthropic
    from config.settings import settings  # Pydantic settings; key field exists at line 63

    key = (settings.ANTHROPIC_API_KEY or "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is empty — set it before running the judge.")
    return Anthropic(api_key=key)


def image_block(b64_data: str, media_type: str = "image/png") -> dict[str, Any]:
    if media_type not in _VALID_MEDIA_TYPES:
        raise ValueError(f"image_block: unsupported media_type {media_type!r}")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": b64_data},
    }


class ClaudeJudge:
    def __init__(
        self,
        client: Any,
        model: str,
        max_tokens: int = 1500,  # generous for a verdict JSON; bump if adapters request large free-text fields
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def run(self, *, messages: list[dict], tool: dict) -> tuple[dict, float]:
        """Force one call to `tool` and return (tool_input, cost_usd)."""
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"], "disable_parallel_tool_use": True},
        )
        blocks = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not blocks:
            raise RuntimeError(f"judge returned no tool_use block (stop={resp.stop_reason})")
        cost = anthropic_cost_usd(self._model, resp.usage.input_tokens, resp.usage.output_tokens)
        return dict(blocks[0].input), cost
