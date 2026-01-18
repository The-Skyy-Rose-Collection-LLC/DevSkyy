"""
Cohere Client
=============

Client for Cohere API.

Reference: https://docs.cohere.com/reference/chat
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
    from config import COHERE_API_KEY
except ImportError:
    COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

from ..base import BaseLLMClient, CompletionResponse, Message, MessageRole, StreamChunk, ToolCall

logger = logging.getLogger(__name__)


class CohereClient(BaseLLMClient):
    """
    Cohere API Client.

    Supports: Command R+, Command R, Command

    Usage:
        client = CohereClient()
        response = await client.complete(
            messages=[Message.user("Hello!")],
            model="command-r"
        )
        print(response.content)
    """

    provider = "cohere"
    default_model = "command-r-08-2024"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.cohere.ai/v1",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key or COHERE_API_KEY or os.getenv("COHERE_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _messages_to_cohere(self, messages: list[Message]) -> tuple[str, list[dict[str, str]], str]:
        """Convert to Cohere format."""
        preamble = ""
        chat_history = []
        current_message = ""

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                preamble = m.content
            elif m.role == MessageRole.USER:
                if current_message:
                    chat_history.append({"role": "USER", "message": current_message})
                current_message = m.content
            else:
                chat_history.append({"role": "CHATBOT", "message": m.content})

        return preamble, chat_history, current_message

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion using Cohere API."""
        model = model or self.default_model
        start_time = datetime.now(UTC)

        preamble, chat_history, message = self._messages_to_cohere(messages)

        data: dict[str, Any] = {
            "model": model,
            "message": message,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if preamble:
            data["preamble"] = preamble
        if chat_history:
            data["chat_history"] = chat_history

        if tools:
            data["tools"] = [
                {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameter_definitions": {
                        k: {
                            "type": v.get("type", "string"),
                            "description": v.get("description", ""),
                        }
                        for k, v in t.get("parameters", {}).get("properties", {}).items()
                    },
                }
                for t in tools
            ]

        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat",
            json=data,
        )

        result = response.json()
        meta = result.get("meta", {})
        tokens = meta.get("tokens", {})

        # Parse tool calls
        tool_calls = []
        if result.get("tool_calls"):
            for i, tc in enumerate(result["tool_calls"]):
                tool_calls.append(
                    ToolCall(
                        id=f"call_{i}",
                        type="function",
                        function={
                            "name": tc.get("name", ""),
                            "arguments": tc.get("parameters", {}),
                        },
                    )
                )

        return CompletionResponse(
            content=result.get("text", ""),
            model=model,
            provider=self.provider,
            input_tokens=tokens.get("input_tokens", 0),
            output_tokens=tokens.get("output_tokens", 0),
            total_tokens=tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0),
            finish_reason=result.get("finish_reason", ""),
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
        """Stream completion using Cohere API."""
        model = model or self.default_model
        await self.connect()

        preamble, chat_history, message = self._messages_to_cohere(messages)

        data: dict[str, Any] = {
            "model": model,
            "message": message,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if preamble:
            data["preamble"] = preamble
        if chat_history:
            data["chat_history"] = chat_history

        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat",
            json=data,
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    chunk_data = json.loads(line)

                    if chunk_data.get("event_type") == "text-generation":
                        yield StreamChunk(
                            content=chunk_data.get("text", ""),
                            delta_content=chunk_data.get("text", ""),
                        )
                    elif chunk_data.get("event_type") == "stream-end":
                        yield StreamChunk(finish_reason=chunk_data.get("finish_reason", ""))


__all__ = ["CohereClient"]
