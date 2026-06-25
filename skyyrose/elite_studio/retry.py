"""
Retry logic for transient API failures.

Shared by all agents — DRY replacement for copy-pasted retry loops.

Backoff policy: exponential with full-range jitter. The base ``delay`` doubles
each attempt and a small random offset prevents synchronized retry waves when
many workers see the same transient (the "thundering herd" pattern that turns
a recoverable 5xx blip into a sustained outage). Delay is capped to keep the
worst-case total wait predictable.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

from .config import MAX_RETRIES, RETRY_DELAY_SECONDS

T = TypeVar("T")

# Keywords that indicate transient (retryable) errors
TRANSIENT_KEYWORDS = frozenset(
    ("timeout", "timed out", "deadline", "429", "502", "503", "overloaded")
)

# Cap the per-attempt sleep so a pathological backoff cannot wedge the worker
# for minutes. With base=1s, max_retries=5 → caps at 1, 2, 4, 8, 16 (sum=31s).
_MAX_BACKOFF_SECONDS = 30.0
_MAX_JITTER_SECONDS = 0.5


def is_transient_error(error_msg: str) -> bool:
    """Check if an error message indicates a transient failure."""
    lower = error_msg.lower()
    return any(kw in lower for kw in TRANSIENT_KEYWORDS)


def _backoff_seconds(base: float, attempt: int) -> float:
    """Exponential backoff with jitter, capped at ``_MAX_BACKOFF_SECONDS``."""
    exp = base * (2**attempt)
    return min(exp, _MAX_BACKOFF_SECONDS) + random.uniform(0, _MAX_JITTER_SECONDS)


def retry_on_transient[T](
    fn: Callable[[], T],
    *,
    label: str = "",
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY_SECONDS,
) -> T:
    """Execute fn() with retry on transient errors.

    Uses exponential backoff with jitter: attempt N sleeps for
    ``min(delay * 2^N, _MAX_BACKOFF_SECONDS) + uniform(0, _MAX_JITTER_SECONDS)``.

    Args:
        fn: Zero-arg callable to execute.
        label: Log prefix for retry messages (e.g., "[Gemini]").
        max_retries: Maximum number of attempts.
        delay: Base delay in seconds; doubles per attempt.

    Returns:
        The result of fn() on success.

    Raises:
        The last exception if all retries are exhausted, or any non-transient
        exception immediately.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            if is_transient_error(str(exc)) and attempt < max_retries - 1:
                wait = _backoff_seconds(delay, attempt)
                if label:
                    logger.warning(
                        "%s retry %d/%d after %.2fs (transient: %s)",
                        label,
                        attempt + 1,
                        max_retries,
                        wait,
                        exc,
                    )
                time.sleep(wait)
                continue
            raise

    # Unreachable — the loop always returns or raises. ``raise`` without an
    # active exception would be a TypeError, so the previous ``raise last_exc``
    # was dead code. Use ``RuntimeError`` to assert the invariant explicitly.
    raise RuntimeError(  # pragma: no cover
        f"retry_on_transient: exhausted {max_retries} attempts without return/raise"
    )
