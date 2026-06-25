"""Kernel-side circuit breaker — prevents cascading failures per agent_type."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Tracks consecutive failures per agent_type and trips open when threshold is exceeded.

    Injecting `time_fn` enables deterministic unit testing without real sleeps.
    """

    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    time_fn: Callable[[], float] | None = None

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _consecutive_failures: int = field(default=0, init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)
    _time_fn: Callable[[], float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._time_fn = self.time_fn if self.time_fn is not None else time.monotonic

    @property
    def state(self) -> CircuitState:
        return self._state

    def allow_request(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            if self._time_fn() - self._opened_at >= self.recovery_timeout_seconds:
                self._state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: allow one probe request

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        self._opened_at = self._time_fn()
        if (
            self._state == CircuitState.HALF_OPEN
            or self._consecutive_failures >= self.failure_threshold
        ):
            self._state = CircuitState.OPEN
