"""
LLM Exceptions
==============

Custom exception hierarchy for LLM operations.
"""

from typing import Any


class LLMError(Exception):
    """Base exception for all LLM errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.model = model
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "provider": self.provider,
            "model": self.model,
            "details": self.details,
        }


class AuthenticationError(LLMError):
    """Raised when API authentication fails."""

    pass


class RateLimitError(LLMError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class QuotaExceededError(LLMError):
    """Raised when API quota is exceeded."""

    pass


class InvalidRequestError(LLMError):
    """Raised when request is invalid."""

    pass


class ModelNotFoundError(LLMError):
    """Raised when requested model is not available."""

    pass


class ContentFilterError(LLMError):
    """Raised when content is filtered by safety systems."""

    pass


class ContextLengthError(LLMError):
    """Raised when context length exceeds model limit."""

    def __init__(
        self,
        message: str,
        max_tokens: int | None = None,
        requested_tokens: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


class TimeoutError(LLMError):
    """Raised when request times out."""

    pass


class ServiceUnavailableError(LLMError):
    """Raised when service is temporarily unavailable."""

    pass


class StreamError(LLMError):
    """Raised when streaming fails."""

    pass


class ToolCallError(LLMError):
    """Raised when tool/function call fails."""

    def __init__(
        self,
        message: str,
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.tool_name = tool_name


__all__ = [
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "QuotaExceededError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ContentFilterError",
    "ContextLengthError",
    "TimeoutError",
    "ServiceUnavailableError",
    "StreamError",
    "ToolCallError",
]
