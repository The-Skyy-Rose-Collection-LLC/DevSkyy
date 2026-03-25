"""
LiteLLM Universal Provider
===========================

Wraps litellm.acompletion() to support 100+ LLM providers through a single
interface. Used as a universal fallback when dedicated provider clients fail
or aren't configured.

Benefits:
- Any new model works instantly without a new provider class
- Automatic retry, fallback, cost tracking built into LiteLLM
- Consistent interface across all providers
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from llm.base import (
    BaseLLMClient,
    CompletionResponse,
    Message,
    ModelProvider,
    StreamChunk,
)
from llm.exceptions import (
    AuthenticationError,
    LLMError,
    RateLimitError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

# Map ModelProvider enum to LiteLLM model string format
_PROVIDER_MODEL_MAP: dict[ModelProvider, str] = {
    ModelProvider.ANTHROPIC: "anthropic/claude-sonnet-4-20250514",
    ModelProvider.OPENAI: "openai/gpt-4o-mini",
    ModelProvider.GOOGLE: "gemini/gemini-2.0-flash",
    ModelProvider.MISTRAL: "mistral/mistral-small-latest",
    ModelProvider.GROQ: "groq/llama-3.3-70b-versatile",
    ModelProvider.COHERE: "cohere/command-r-08-2024",
    ModelProvider.DEEPSEEK: "deepseek/deepseek-chat",
}


class LiteLLMClient(BaseLLMClient):
    """
    Universal LLM client using LiteLLM.

    Supports 100+ providers through litellm.acompletion().
    Used as fallback when dedicated provider clients are unavailable.
    """

    provider = "litellm"
    default_model = "anthropic/claude-sonnet-4-20250514"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key=api_key or "", **kwargs)
        self._default_model = model or self.default_model
        self._litellm: Any = None

    def _ensure_litellm(self) -> Any:
        """Lazy import litellm to avoid import cost when not used."""
        if self._litellm is None:
            try:
                import litellm

                # Suppress litellm's verbose logging
                litellm.suppress_debug_info = True
                litellm.set_verbose = False
                self._litellm = litellm
            except ImportError:
                raise LLMError(
                    "litellm is not installed. Install with: pip install litellm",
                    provider=self.provider,
                )
        return self._litellm

    def _get_headers(self) -> dict[str, str]:
        """Not used -- LiteLLM handles auth internally via env vars."""
        return {}

    @staticmethod
    def get_model_string(provider: ModelProvider, model: str | None = None) -> str:
        """
        Convert ModelProvider + optional model name to LiteLLM model string.

        Args:
            provider: The ModelProvider enum value
            model: Optional specific model name (overrides default)

        Returns:
            LiteLLM-compatible model string like "anthropic/claude-sonnet-4-20250514"
        """
        if model:
            # If model already has provider prefix, use as-is
            if "/" in model:
                return model
            # Otherwise prepend provider name
            return f"{provider.value}/{model}"
        return _PROVIDER_MODEL_MAP.get(provider, f"{provider.value}/default")

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """
        Generate completion via LiteLLM.

        Args:
            messages: Conversation messages
            model: LiteLLM model string (e.g. "anthropic/claude-sonnet-4-20250514")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Tool/function definitions
            **kwargs: Additional LiteLLM options

        Returns:
            CompletionResponse
        """
        litellm = self._ensure_litellm()
        model = model or self._default_model
        start = datetime.now(UTC)

        msg_list = self._messages_to_list(messages)

        call_kwargs: dict[str, Any] = {
            "model": model,
            "messages": msg_list,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            call_kwargs["tools"] = tools

        # Pass through extra kwargs (e.g. top_p, stop, etc.)
        call_kwargs.update(kwargs)

        try:
            response = await litellm.acompletion(**call_kwargs)

            # Extract usage
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

            # Extract content
            content = ""
            if response.choices:
                choice = response.choices[0]
                content = getattr(choice.message, "content", "") or ""

            # Extract cost from LiteLLM's built-in cost tracking
            cost = None
            try:
                cost = litellm.completion_cost(completion_response=response)
            except Exception:
                pass

            return CompletionResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=(
                    getattr(response.choices[0], "finish_reason", "") if response.choices else ""
                ),
                latency_ms=self._calculate_latency(start),
                cost_usd=cost,
            )

        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"LiteLLM auth failed for {model}: {e}",
                    provider=self.provider,
                )
            elif "rate limit" in error_str or "429" in error_str:
                raise RateLimitError(
                    f"LiteLLM rate limited for {model}: {e}",
                    provider=self.provider,
                )
            elif "500" in error_str or "503" in error_str or "unavailable" in error_str:
                raise ServiceUnavailableError(
                    f"LiteLLM service error for {model}: {e}",
                    provider=self.provider,
                )
            raise LLMError(
                f"LiteLLM completion failed for {model}: {e}",
                provider=self.provider,
                details={"model": model},
            )

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream completion via LiteLLM.

        Args:
            messages: Conversation messages
            model: LiteLLM model string
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamChunk objects
        """
        litellm = self._ensure_litellm()
        model = model or self._default_model
        msg_list = self._messages_to_list(messages)

        try:
            response = await litellm.acompletion(
                model=model,
                messages=msg_list,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            index = 0
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", "") or ""
                    finish = getattr(chunk.choices[0], "finish_reason", None)

                    yield StreamChunk(
                        content=content,
                        delta_content=content,
                        finish_reason=finish,
                        index=index,
                    )
                    index += 1

        except Exception as e:
            raise LLMError(
                f"LiteLLM stream failed for {model}: {e}",
                provider=self.provider,
            )


__all__ = ["LiteLLMClient"]
