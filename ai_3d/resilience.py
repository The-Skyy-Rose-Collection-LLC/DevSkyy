"""
Resilience utilities for 3D pipeline.

Provides retry logic, exponential backoff, circuit breaker pattern,
and graceful degradation for external API calls.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes before closing circuit
    timeout: float = 60.0  # Seconds to wait before half-open
    half_open_max_calls: int = 1  # Max concurrent calls in half-open


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, service_name: str, timeout: float):
        self.service_name = service_name
        self.timeout = timeout
        super().__init__(f"Circuit breaker is OPEN for {service_name}. Retry after {timeout:.1f}s")


class MaxRetriesExceededError(Exception):
    """Raised when max retries are exceeded."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Max retries ({attempts}) exceeded. Last error: {last_error}")


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by monitoring external service health
    and temporarily blocking requests when service is failing.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state_data = CircuitBreakerState()

    def _should_attempt(self) -> bool:
        """Check if request should be attempted."""
        current_time = time.time()

        if self.state_data.state == CircuitState.CLOSED:
            return True

        if self.state_data.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            time_since_failure = current_time - self.state_data.last_failure_time
            if time_since_failure >= self.config.timeout:
                logger.info(f"Circuit breaker {self.name}: OPEN → HALF_OPEN")
                self.state_data.state = CircuitState.HALF_OPEN
                self.state_data.half_open_calls = 0
                return True
            return False

        if self.state_data.state == CircuitState.HALF_OPEN:
            # Allow limited concurrent calls
            if self.state_data.half_open_calls < self.config.half_open_max_calls:
                self.state_data.half_open_calls += 1
                return True
            return False

        return False

    def record_success(self) -> None:
        """Record successful call."""
        if self.state_data.state == CircuitState.HALF_OPEN:
            self.state_data.success_count += 1
            if self.state_data.success_count >= self.config.success_threshold:
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN → CLOSED")
                self.state_data.state = CircuitState.CLOSED
                self.state_data.failure_count = 0
                self.state_data.success_count = 0
        elif self.state_data.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.state_data.failure_count = 0

    def record_failure(self) -> None:
        """Record failed call."""
        current_time = time.time()
        self.state_data.last_failure_time = current_time

        if self.state_data.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker {self.name}: HALF_OPEN → OPEN")
            self.state_data.state = CircuitState.OPEN
            self.state_data.success_count = 0

        elif self.state_data.state == CircuitState.CLOSED:
            self.state_data.failure_count += 1
            if self.state_data.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker {self.name}: CLOSED → OPEN "
                    f"({self.state_data.failure_count} failures)"
                )
                self.state_data.state = CircuitState.OPEN

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        if not self._should_attempt():
            raise CircuitBreakerError(self.name, self.config.timeout)

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state_data.state.value,
            "failure_count": self.state_data.failure_count,
            "success_count": self.state_data.success_count,
            "last_failure_time": self.state_data.last_failure_time,
        }


class RetryStrategy:
    """
    Exponential backoff retry strategy with jitter.

    Implements industry-standard retry logic for resilient API calls.
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        import random

        # Exponential backoff: delay = initial_delay * (base ^ attempt)
        delay = self.config.initial_delay * (self.config.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1  # ±10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.1, delay)  # Minimum 100ms

    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        **kwargs: Any,
    ) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exception types to retry on
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful function call

        Raises:
            MaxRetriesExceededError: If all retries exhausted
        """
        last_exception: Exception | None = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.config.max_attempts}")
                result = await func(*args, **kwargs)

                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")

                return result

            except retryable_exceptions as e:
                last_exception = e

                if attempt == self.config.max_attempts:
                    logger.error(f"All {self.config.max_attempts} attempts failed. Last error: {e}")
                    break

                delay = self.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)

        # All retries exhausted
        raise MaxRetriesExceededError(
            attempts=self.config.max_attempts,
            last_error=last_exception or Exception("Unknown error"),
        )


@dataclass
class FallbackConfig:
    """Configuration for graceful degradation."""

    enable_cache: bool = True
    cache_stale_threshold: float = 3600.0  # 1 hour in seconds
    fallback_value: Any = None
    log_fallback: bool = True


class GracefulDegradation:
    """
    Graceful degradation with caching and fallback values.

    Provides resilience when external services are unavailable.
    """

    def __init__(self, config: FallbackConfig | None = None):
        self.config = config or FallbackConfig()
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, timestamp)

    def _get_cache_key(self, func: Callable, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from function and arguments."""
        import hashlib
        import json

        # Simple key generation (can be enhanced for complex types)
        key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
        key_str = json.dumps(key_parts, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _get_cached_value(self, cache_key: str) -> Any | None:
        """Get cached value if available and not stale."""
        if not self.config.enable_cache:
            return None

        if cache_key not in self._cache:
            return None

        value, timestamp = self._cache[cache_key]
        age = time.time() - timestamp

        if age > self.config.cache_stale_threshold:
            logger.warning(f"Cache hit but stale ({age:.0f}s old)")
            return None

        logger.info(f"Cache hit ({age:.0f}s old)")
        return value

    def _store_cached_value(self, cache_key: str, value: Any) -> None:
        """Store value in cache."""
        if self.config.enable_cache:
            self._cache[cache_key] = (value, time.time())

    async def execute_with_fallback(
        self,
        func: Callable[..., T],
        *args: Any,
        fallback_value: Any = None,
        **kwargs: Any,
    ) -> T:
        """
        Execute function with graceful degradation.

        Returns cached value or fallback value if function fails.
        """
        cache_key = self._get_cache_key(func, *args, **kwargs)

        try:
            result = await func(*args, **kwargs)
            self._store_cached_value(cache_key, result)
            return result

        except Exception as e:
            if self.config.log_fallback:
                logger.error(f"Function failed: {e}. Attempting fallback...")

            # Try cache first
            cached = self._get_cached_value(cache_key)
            if cached is not None:
                logger.warning("Using cached value (service unavailable)")
                return cached

            # Use fallback value
            fb_value = fallback_value or self.config.fallback_value
            if fb_value is not None:
                logger.warning("Using fallback value (service unavailable)")
                return fb_value

            # No fallback available, re-raise
            logger.error("No fallback available, re-raising exception")
            raise


class ResilientAPIClient:
    """
    Resilient API client wrapper combining all patterns.

    Combines retry, circuit breaker, and graceful degradation.
    """

    def __init__(
        self,
        service_name: str,
        retry_config: RetryConfig | None = None,
        circuit_config: CircuitBreakerConfig | None = None,
        fallback_config: FallbackConfig | None = None,
    ):
        self.service_name = service_name
        self.retry_strategy = RetryStrategy(retry_config)
        self.circuit_breaker = CircuitBreaker(service_name, circuit_config)
        self.degradation = GracefulDegradation(fallback_config)

    async def call(
        self,
        func: Callable[..., T],
        *args: Any,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        fallback_value: Any = None,
        **kwargs: Any,
    ) -> T:
        """
        Execute API call with full resilience stack.

        Order:
        1. Circuit breaker check
        2. Retry with exponential backoff
        3. Graceful degradation (cache/fallback)
        """

        async def wrapped_call() -> T:
            return await self.retry_strategy.execute(
                func,
                *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        try:
            # Circuit breaker wraps retry strategy
            result = await self.circuit_breaker.call(wrapped_call)
            return result

        except (CircuitBreakerError, MaxRetriesExceededError) as e:
            # Circuit is open or retries exhausted - try graceful degradation
            logger.warning(f"Resilient call failed: {e}. Trying fallback...")
            return await self.degradation.execute_with_fallback(
                func,
                *args,
                fallback_value=fallback_value,
                **kwargs,
            )

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of resilient client."""
        return {
            "service_name": self.service_name,
            "circuit_breaker": self.circuit_breaker.get_state(),
            "cache_size": len(self.degradation._cache),
        }
