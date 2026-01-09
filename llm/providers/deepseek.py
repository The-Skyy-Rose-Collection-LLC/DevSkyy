"""
DeepSeek Client
===============

Client for DeepSeek API (V3 and R1 reasoning models).

DeepSeek-V3: Cost-effective code generation ($0.14/1M tokens, 100x cheaper than GPT-4)
DeepSeek-R1: Reasoning model matching OpenAI o1 ($0.14/1M tokens)

Reference: https://platform.deepseek.com/api-docs
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from ..base import BaseLLMClient, CompletionResponse, Message, StreamChunk, ToolCall

logger = logging.getLogger(__name__)


class DeepSeekClient(BaseLLMClient):
    """
    DeepSeek API Client.

    Supports:
    - deepseek-chat (V3): General-purpose, code-optimized
    - deepseek-reasoner (R1): Advanced reasoning mode

    Usage:
        client = DeepSeekClient()
        response = await client.complete(
            messages=[Message.user("Write a Python function")],
            model="deepseek-chat"
        )
        print(response.content)
    """

    provider = "deepseek"
    default_model = "deepseek-chat"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com/v1",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _messages_to_openai_format(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert to OpenAI-compatible format (DeepSeek uses OpenAI API structure)."""
        formatted = []
        for m in messages:
            formatted.append(
                {
                    "role": m.role.value,
                    "content": m.content,
                }
            )
        return formatted

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion using DeepSeek API."""
        model = model or self.default_model
        start_time = datetime.now(UTC)

        data: dict[str, Any] = {
            "model": model,
            "messages": self._messages_to_openai_format(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add tools if provided (function calling)
        if tools:
            data["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.get("name", ""),
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {}),
                    },
                }
                for t in tools
            ]

        # Add reasoning mode for deepseek-reasoner
        if model == "deepseek-reasoner":
            # R1 model uses different parameter
            data.pop("temperature", None)  # R1 doesn't support temperature

        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=data,
        )

        result = response.json()
        choice = result["choices"][0]
        message_content = choice["message"]
        usage = result.get("usage", {})

        # Parse tool calls
        tool_calls = []
        if message_content.get("tool_calls"):
            for tc in message_content["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", ""),
                        type="function",
                        function={
                            "name": tc["function"]["name"],
                            "arguments": (
                                json.loads(tc["function"]["arguments"])
                                if isinstance(tc["function"]["arguments"], str)
                                else tc["function"]["arguments"]
                            ),
                        },
                    )
                )

        # Extract reasoning content for R1 model
        reasoning_content = None
        if model == "deepseek-reasoner" and message_content.get("reasoning_content"):
            reasoning_content = message_content["reasoning_content"]

        response_obj = CompletionResponse(
            content=message_content.get("content", ""),
            model=model,
            provider=self.provider,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason"),
            tool_calls=tool_calls if tool_calls else None,
            latency_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
        )

        # Add reasoning content to metadata for R1
        if reasoning_content:
            response_obj.metadata = response_obj.metadata or {}
            response_obj.metadata["reasoning_content"] = reasoning_content

        return response_obj

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using DeepSeek API."""
        model = model or self.default_model

        data: dict[str, Any] = {
            "model": model,
            "messages": self._messages_to_openai_format(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # R1 doesn't support temperature
        if model == "deepseek-reasoner":
            data.pop("temperature", None)

        response = await self._make_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=data,
            stream=True,
        )

        async for line in response.aiter_lines():
            if not line or line == "data: [DONE]":
                continue

            if line.startswith("data: "):
                line = line[6:]

            try:
                chunk_data = json.loads(line)
                delta = chunk_data["choices"][0].get("delta", {})
                content = delta.get("content", "")

                if content:
                    yield StreamChunk(
                        content=content,
                        model=model,
                        provider=self.provider,
                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                    )

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to parse stream chunk: {e}")
                continue

    def get_model_info(self, model: str | None = None) -> dict[str, Any]:
        """Get information about DeepSeek models."""
        model = model or self.default_model

        model_info = {
            "deepseek-chat": {
                "context_length": 128000,
                "cost_per_1m_input": 0.14,
                "cost_per_1m_output": 0.28,
                "strengths": ["code", "technical", "cost-effective"],
                "description": "V3 model - 671B parameters, MoE architecture, excellent for code generation",
            },
            "deepseek-reasoner": {
                "context_length": 128000,
                "cost_per_1m_input": 0.14,
                "cost_per_1m_output": 0.55,
                "strengths": ["reasoning", "math", "logic"],
                "description": "R1 reasoning model - matches OpenAI o1 performance at 1/95th the cost",
            },
        }

        return model_info.get(model, {})
