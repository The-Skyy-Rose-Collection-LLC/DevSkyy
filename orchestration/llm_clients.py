"""
LLM Provider Clients
====================

Unified clients for all major LLM providers.

Providers:
- OpenAI (GPT-4, o1)
- Anthropic (Claude)
- Google (Gemini)
- Mistral
- Cohere (Command)
- Groq (Llama, Mixtral)

Features:
- Async support
- Streaming
- Function calling
- Error handling with retries
- Token counting
"""

import logging
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


# =============================================================================
# Common Models
# =============================================================================


class MessageRole(str, Enum):
    """Message roles"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Chat message"""

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


class ToolCall(BaseModel):
    """Tool call request"""

    id: str
    type: str = "function"
    function: dict[str, Any]


class CompletionResponse(BaseModel):
    """Unified completion response"""

    content: str
    model: str
    provider: str

    # Usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Metadata
    finish_reason: str = ""
    tool_calls: list[ToolCall] = []
    latency_ms: float = 0

    # Raw response
    raw: dict[str, Any] = {}


class StreamChunk(BaseModel):
    """Streaming chunk"""

    content: str = ""
    finish_reason: str | None = None
    tool_calls: list[dict] = []


# =============================================================================
# Base Client
# =============================================================================


class BaseLLMClient(ABC):
    """
    Base LLM Client

    Abstract base class for all provider clients.
    """

    provider: str = "base"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        """Generate completion"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion"""
        pass

    def _messages_to_list(self, messages: list[Message]) -> list[dict]:
        """Convert Message objects to dict list"""
        return [{"role": m.role.value, "content": m.content} for m in messages]


# =============================================================================
# OpenAI Client
# =============================================================================


class OpenAIClient(BaseLLMClient):
    """
    OpenAI API Client

    Supports: GPT-4o, GPT-4o-mini, o1-preview, o1-mini

    Usage:
        client = OpenAIClient()
        response = await client.complete(
            messages=[Message(role=MessageRole.USER, content="Hello")],
            model="gpt-4o-mini"
        )
    """

    provider = "openai"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        response_format: dict = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        data = {
            "model": model,
            "messages": self._messages_to_list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            data["tools"] = tools
        if response_format:
            data["response_format"] = response_format

        start_time = datetime.now()

        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=data,
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"OpenAI error: {error}")

        result = response.json()
        choice = result["choices"][0]
        usage = result.get("usage", {})

        # Extract tool calls
        tool_calls = []
        if choice.get("message", {}).get("tool_calls"):
            for tc in choice["message"]["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tc["id"],
                        type=tc["type"],
                        function=tc["function"],
                    )
                )

        return CompletionResponse(
            content=choice.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            tool_calls=tool_calls,
            latency_ms=latency,
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
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

                    import json

                    chunk_data = json.loads(data_str)
                    delta = chunk_data["choices"][0].get("delta", {})

                    yield StreamChunk(
                        content=delta.get("content", ""),
                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                    )


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseLLMClient):
    """
    Anthropic API Client

    Supports: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku

    Usage:
        client = AnthropicClient()
        response = await client.complete(
            messages=[Message(role=MessageRole.USER, content="Hello")],
            model="claude-3-5-sonnet-20241022"
        )
    """

    provider = "anthropic"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.anthropic.com",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

    def _messages_to_anthropic(self, messages: list[Message]) -> tuple:
        """Convert to Anthropic format (separate system)"""
        system = ""
        msgs = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system = m.content
            else:
                msgs.append(
                    {
                        "role": "user" if m.role == MessageRole.USER else "assistant",
                        "content": m.content,
                    }
                )

        return system, msgs

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        system, msgs = self._messages_to_anthropic(messages)

        data = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            data["system"] = system

        if tools:
            data["tools"] = tools

        start_time = datetime.now()

        response = await self._client.post(
            f"{self.base_url}/v1/messages",
            json=data,
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"Anthropic error: {error}")

        result = response.json()
        usage = result.get("usage", {})

        # Extract content
        content = ""
        tool_calls = []

        for block in result.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        type="function",
                        function={
                            "name": block["name"],
                            "arguments": block["input"],
                        },
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
            latency_ms=latency,
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        await self.connect()

        system, msgs = self._messages_to_anthropic(messages)

        data = {
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
                    import json

                    chunk_data = json.loads(line[6:])

                    if chunk_data["type"] == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        yield StreamChunk(
                            content=delta.get("text", ""),
                        )
                    elif chunk_data["type"] == "message_stop":
                        yield StreamChunk(finish_reason="stop")


# =============================================================================
# Google Client
# =============================================================================


class GoogleClient(BaseLLMClient):
    """
    Google Gemini API Client

    Supports: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash

    Usage:
        client = GoogleClient()
        response = await client.complete(
            messages=[Message(role=MessageRole.USER, content="Hello")],
            model="gemini-1.5-flash"
        )
    """

    provider = "google"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        **kwargs,
    ):
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
        """Convert to Gemini format"""
        system = ""
        contents = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system = m.content
            else:
                contents.append(
                    {
                        "role": "user" if m.role == MessageRole.USER else "model",
                        "parts": [{"text": m.content}],
                    }
                )

        return system, contents

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        system, contents = self._messages_to_gemini(messages)

        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system:
            data["systemInstruction"] = {"parts": [{"text": system}]}

        if tools:
            data["tools"] = [{"functionDeclarations": tools}]

        start_time = datetime.now()

        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        response = await self._client.post(url, json=data)

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"Google error: {error}")

        result = response.json()
        candidate = result.get("candidates", [{}])[0]
        usage = result.get("usageMetadata", {})

        # Extract content
        content = ""
        tool_calls = []

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

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.provider,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidate.get("finishReason", ""),
            tool_calls=tool_calls,
            latency_ms=latency,
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        await self.connect()

        system, contents = self._messages_to_gemini(messages)

        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system:
            data["systemInstruction"] = {"parts": [{"text": system}]}

        url = f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}"

        async with self._client.stream("POST", url, json=data) as response:
            async for line in response.aiter_lines():
                if line:
                    import json

                    chunk_data = json.loads(line)

                    for candidate in chunk_data.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if "text" in part:
                                yield StreamChunk(content=part["text"])


# =============================================================================
# Mistral Client
# =============================================================================


class MistralClient(BaseLLMClient):
    """
    Mistral API Client

    Supports: Mistral Large, Mistral Medium, Mistral Small, Codestral
    """

    provider = "mistral"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.mistral.ai/v1",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or os.getenv("MISTRAL_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "mistral-small-latest",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        data = {
            "model": model,
            "messages": self._messages_to_list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            data["tools"] = tools

        start_time = datetime.now()

        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=data,
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"Mistral error: {error}")

        result = response.json()
        choice = result["choices"][0]
        usage = result.get("usage", {})

        return CompletionResponse(
            content=choice.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            latency_ms=latency,
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "mistral-small-latest",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
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

                    import json

                    chunk_data = json.loads(data_str)
                    delta = chunk_data["choices"][0].get("delta", {})

                    yield StreamChunk(
                        content=delta.get("content", ""),
                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                    )


# =============================================================================
# Cohere Client
# =============================================================================


class CohereClient(BaseLLMClient):
    """
    Cohere API Client

    Supports: Command R+, Command R
    """

    provider = "cohere"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.cohere.ai/v1",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or os.getenv("COHERE_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _messages_to_cohere(self, messages: list[Message]) -> tuple:
        """Convert to Cohere format"""
        preamble = ""
        chat_history = []
        message = ""

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                preamble = m.content
            elif m.role == MessageRole.USER:
                if message:
                    chat_history.append({"role": "USER", "message": message})
                message = m.content
            else:
                chat_history.append({"role": "CHATBOT", "message": m.content})

        return preamble, chat_history, message

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "command-r",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        preamble, chat_history, message = self._messages_to_cohere(messages)

        data = {
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
            data["tools"] = tools

        start_time = datetime.now()

        response = await self._client.post(
            f"{self.base_url}/chat",
            json=data,
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"Cohere error: {error}")

        result = response.json()
        meta = result.get("meta", {})
        tokens = meta.get("tokens", {})

        return CompletionResponse(
            content=result.get("text", ""),
            model=model,
            provider=self.provider,
            input_tokens=tokens.get("input_tokens", 0),
            output_tokens=tokens.get("output_tokens", 0),
            total_tokens=tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0),
            finish_reason=result.get("finish_reason", ""),
            latency_ms=latency,
            raw=result,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "command-r",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        await self.connect()

        preamble, chat_history, message = self._messages_to_cohere(messages)

        data = {
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
                    import json

                    chunk_data = json.loads(line)

                    if chunk_data.get("event_type") == "text-generation":
                        yield StreamChunk(content=chunk_data.get("text", ""))
                    elif chunk_data.get("event_type") == "stream-end":
                        yield StreamChunk(finish_reason=chunk_data.get("finish_reason", ""))


# =============================================================================
# Groq Client
# =============================================================================


class GroqClient(BaseLLMClient):
    """
    Groq API Client (Fast Inference)

    Supports: Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B

    Note: Groq uses OpenAI-compatible API
    """

    provider = "groq"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.groq.com/openai/v1",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or os.getenv("GROQ_API_KEY", ""),
            base_url=base_url,
            **kwargs,
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        messages: list[Message],
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict] = None,
        **kwargs,
    ) -> CompletionResponse:
        await self.connect()

        data = {
            "model": model,
            "messages": self._messages_to_list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            data["tools"] = tools

        start_time = datetime.now()

        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=data,
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        if response.status_code >= 400:
            error = response.json()
            raise Exception(f"Groq error: {error}")

        result = response.json()
        choice = result["choices"][0]
        usage = result.get("usage", {})

        # Groq reports speed metrics
        x_groq = result.get("x_groq", {})

        return CompletionResponse(
            content=choice.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            latency_ms=latency,
            raw={**result, "speed_metrics": x_groq},
        )

    async def stream(
        self,
        messages: list[Message],
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
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

                    import json

                    chunk_data = json.loads(data_str)
                    delta = chunk_data["choices"][0].get("delta", {})

                    yield StreamChunk(
                        content=delta.get("content", ""),
                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                    )
