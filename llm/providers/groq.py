"""
Groq Client
===========

Client for Groq API (fast inference).

Reference: https://console.groq.com/docs/api-reference
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

# Import config for API keys (loads .env.hf)
try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

from ..base import BaseLLMClient, CompletionResponse, Message, StreamChunk, ToolCall

logger = logging.getLogger(__name__)


class GroqClient(BaseLLMClient):
    """
    Groq API Client (Fast Inference).

    Supports: Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma 2

    Note: Groq uses OpenAI-compatible API format.

    Usage:
        client = GroqClient()
        response = await client.complete(
            messages=[Message.user("Hello!")],
            model="llama-3.1-70b-versatile"
        )
        print(response.content)
    """

    provider = "groq"
    default_model = "llama-3.3-70b-versatile"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key or GROQ_API_KEY or os.getenv("GROQ_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion using Groq API."""
        model = model or self.default_model
        start_time = datetime.now(UTC)

        data: dict[str, Any] = {
            "model": model,
            "messages": self._messages_to_list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            data["tools"] = [{"type": "function", "function": t} for t in tools]
            data["tool_choice"] = kwargs.get("tool_choice", "auto")

        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=data,
        )

        result = response.json()
        choice = result["choices"][0]
        message = choice.get("message", {})
        usage = result.get("usage", {})

        # Parse tool calls
        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tc["id"],
                        type=tc["type"],
                        function={
                            "name": tc["function"]["name"],
                            "arguments": json.loads(tc["function"]["arguments"]),
                        },
                    )
                )

        return CompletionResponse(
            content=message.get("content", "") or "",
            model=model,
            provider=self.provider,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            tool_calls=tool_calls,
            latency_ms=self._calculate_latency(start_time),
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using Groq API."""
        model = model or self.default_model
        await self.connect()

        data = {
            "model": model,
            "messages": self._messages_to_list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=data,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    chunk_data = json.loads(data_str)
                    delta = chunk_data["choices"][0].get("delta", {})

                    yield StreamChunk(
                        content=delta.get("content", ""),
                        delta_content=delta.get("content", ""),
                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                    )


__all__ = ["GroqClient"]
