"""
Anthropic Client
================

Client for Anthropic Claude API.

Reference: https://docs.anthropic.com/en/api/messages
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
    CallerInfo,
    CallerType,
    CompletionResponse,
    ContainerInfo,
    Message,
    MessageRole,
    StreamChunk,
    ToolCall,
)

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """
    Anthropic Claude API Client.

    Supports: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, Claude 3.5 Haiku

    Usage:
        client = AnthropicClient()
        response = await client.complete(
            messages=[Message.user("Hello!")],
            model="claude-sonnet-4-20250514"
        )
        print(response.content)
    """

    provider = "anthropic"
    default_model = "claude-sonnet-4-20250514"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.anthropic.com",
        enable_ptc: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: API base URL
            enable_ptc: Enable Programmatic Tool Calling (default True)
            **kwargs: Additional arguments passed to BaseLLMClient
        """
        super().__init__(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )
        self.enable_ptc = enable_ptc

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with optional PTC beta header."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Add beta header for Programmatic Tool Calling
        if self.enable_ptc:
            headers["anthropic-beta"] = "advanced-tool-use-2025-11-20"

        return headers

    def _messages_to_anthropic(self, messages: list[Message]) -> tuple[str, list[dict[str, Any]]]:
        """Convert to Anthropic format (separate system message)."""
        system = ""
        msgs = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system = m.content
            else:
                role = "user" if m.role == MessageRole.USER else "assistant"
                msgs.append({"role": role, "content": m.content})

        return system, msgs

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,  # Increased default for PTC
        tools: list[dict[str, Any]] | None = None,
        container_id: str | None = None,  # For container reuse
        **kwargs: Any,
    ) -> CompletionResponse:
        """
        Generate completion using Anthropic API.

        Args:
            messages: Conversation messages
            model: Model to use (defaults to claude-sonnet-4-20250514)
            temperature: Sampling temperature
            max_tokens: Maximum tokens (increased to 4096 for PTC)
            tools: Tool definitions (supports PTC with allowed_callers)
            container_id: Existing container ID to reuse
            **kwargs: Additional arguments

        Returns:
            CompletionResponse with content, tool calls, and optional container info
        """
        model = model or self.default_model
        start_time = datetime.now(UTC)

        system, msgs = self._messages_to_anthropic(messages)

        data: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            data["system"] = system

        # Container reuse for PTC
        if container_id:
            data["container"] = container_id

        if tools:
            # Pass tools as-is (already in Anthropic format from ToolSpec or direct dict)
            data["tools"] = tools

        response = await self._make_request(
            "POST",
            f"{self.base_url}/v1/messages",
            json=data,
        )

        result = response.json()
        usage = result.get("usage", {})

        # Extract container info (PTC)
        container_info = None
        if "container" in result:
            container_data = result["container"]
            # Parse ISO 8601 timestamp
            expires_str = container_data["expires_at"]
            # Handle both Z and +00:00 timezone formats
            expires_str = expires_str.replace("Z", "+00:00")
            expires_at = datetime.fromisoformat(expires_str)

            container_info = ContainerInfo(
                id=container_data["id"],
                expires_at=expires_at,
            )

        # Extract content and tool calls
        content = ""
        tool_calls = []

        for block in result.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                # Parse caller info (PTC)
                caller_info = None
                if "caller" in block:
                    caller_data = block["caller"]
                    caller_info = CallerInfo(
                        type=CallerType(caller_data["type"]),
                        tool_id=caller_data.get("tool_id"),
                    )

                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        type="function",
                        function={
                            "name": block["name"],
                            "arguments": block["input"],
                        },
                        caller=caller_info,
                    )
                )

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.provider,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            finish_reason=result.get("stop_reason", ""),
            tool_calls=tool_calls,
            latency_ms=self._calculate_latency(start_time),
            raw=result,
            container=container_info,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using Anthropic API."""
        model = model or self.default_model
        await self.connect()

        system, msgs = self._messages_to_anthropic(messages)

        data: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if system:
            data["system"] = system

        async with self._client.stream(
            "POST",
            f"{self.base_url}/v1/messages",
            json=data,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_data = json.loads(line[6:])

                    if chunk_data["type"] == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        yield StreamChunk(
                            content=delta.get("text", ""),
                            delta_content=delta.get("text", ""),
                        )
                    elif chunk_data["type"] == "message_stop":
                        yield StreamChunk(finish_reason="stop")


__all__ = ["AnthropicClient"]
