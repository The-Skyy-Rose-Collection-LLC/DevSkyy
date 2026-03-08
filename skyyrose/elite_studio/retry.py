"""
Retry logic for transient API failures.

Shared by all agents — DRY replacement for copy-pasted retry loops.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from .config import MAX_RETRIES, RETRY_DELAY_SECONDS

T = TypeVar("T")

# Keywords that indicate transient (retryable) errors
TRANSIENT_KEYWORDS = frozenset(
    ("timeout", "timed out", "deadline", "429", "502", "503", "overloaded")
)


def is_transient_error(error_msg: str) -> bool:
    """Check if an error message indicates a transient failure."""
    lower = error_msg.lower()
    return any(kw in lower for kw in TRANSIENT_KEYWORDS)


def retry_on_transient(
    fn: Callable[[], T],
    *,
    label: str = "",
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY_SECONDS,
) -> T:
    """Execute fn() with retry on transient errors.

    Args:
        fn: Zero-arg callable to execute.
        label: Log prefix for retry messages (e.g., "[Gemini]").
        max_retries: Maximum number of attempts.
        delay: Seconds to wait between retries.

    Returns:
        The result of fn() on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if is_transient_error(str(exc)) and attempt < max_retries - 1:
                if label:
                    print(f"   {label} Retry after: {exc}")
                time.sleep(delay)
                continue
            raise

    # Should not reach here, but satisfy type checker
    raise last_exc  # type: ignore[misc]
