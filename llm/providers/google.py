"""
Google Gemini Client
====================

Client for Google Gemini API.

Reference: https://ai.google.dev/api/rest
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from ..base import (
    BaseLLMClient,
    CompletionResponse,
    Message,
    MessageRole,
    StreamChunk,
    ToolCall,
)

logger = logging.getLogger(__name__)


class GoogleClient(BaseLLMClient):
    """
    Google Gemini API Client.

    Supports: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash

    Usage:
        client = GoogleClient()
        response = await client.complete(
            messages=[Message.user("Hello!")],
            model="gemini-1.5-flash"
        )
        print(response.content)
    """

    provider = "google"
    default_model = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key or os.getenv("GOOGLE_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    def _messages_to_gemini(self, messages: list[Message]) -> tuple:
        """Convert to Gemini format."""
        system_instruction = None
        contents = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == MessageRole.USER else "model"
                contents.append(
                    {
                        "role": role,
                        "parts": [{"text": m.content}],
                    }
                )

        return system_instruction, contents

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion using Google Gemini API."""
        model = model or self.default_model
        start_time = datetime.now(UTC)

        system_instruction, contents = self._messages_to_gemini(messages)

        data: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            data["systemInstruction"] = system_instruction

        if tools:
            data["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": t.get("name", ""),
                            "description": t.get("description", ""),
                            "parameters": t.get("parameters", {}),
                        }
                        for t in tools
                    ]
                }
            ]

        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        response = await self._make_request("POST", url, json=data)

        result = response.json()

        # Extract content
        content = ""
        tool_calls = []

        candidates = result.get("candidates", [])
        if candidates:
            candidate = candidates[0]
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    content += part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{len(tool_calls)}",
                            type="function",
                            function={
                                "name": fc["name"],
                                "arguments": fc.get("args", {}),
                            },
                        )
                    )

        # Extract usage
        usage = result.get("usageMetadata", {})

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.provider,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidates[0].get("finishReason", "") if candidates else "",
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
        """Stream completion using Google Gemini API."""
        model = model or self.default_model
        await self.connect()

        system_instruction, contents = self._messages_to_gemini(messages)

        data: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            data["systemInstruction"] = system_instruction

        url = f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse"

        async with self._client.stream("POST", url, json=data) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_data = json.loads(line[6:])

                    for candidate in chunk_data.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if "text" in part:
                                yield StreamChunk(
                                    content=part["text"],
                                    delta_content=part["text"],
                                )


__all__ = ["GoogleClient"]
