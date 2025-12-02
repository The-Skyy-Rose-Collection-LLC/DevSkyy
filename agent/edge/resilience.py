"""
Resilience Layer - Circuit Breaker, Timeout, Retry, and Bulkhead Patterns

Production-grade resilience for edge-backend communication with:
- Circuit Breaker: Prevent cascading failures
- Timeout: Enforce operation time limits
- Retry: Exponential backoff with jitter
- Bulkhead: Isolate failures per component
- Graceful Degradation: Fallback strategies

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                      Resilience Layer                            │
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │  Circuit    │   │  Timeout    │   │   Retry     │           │
│  │  Breaker    │──▶│  Enforcer   │──▶│   Handler   │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│         │                                    │                   │
│         ▼                                    ▼                   │
│  ┌─────────────┐                     ┌─────────────┐           │
│  │  Bulkhead   │                     │  Fallback   │           │
│  │  Isolation  │                     │  Strategy   │           │
│  └─────────────┘                     └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘

Circuit Breaker States:
┌─────────┐  failures >= threshold  ┌────────┐
│ CLOSED  │ ───────────────────────▶│  OPEN  │
│(normal) │                         │(reject)│
└────┬────┘                         └───┬────┘
     │                                  │
     │◀─────────── success ─────────────┤
     │                                  │
     │         ┌───────────┐   timeout  │
     └────────▶│HALF-OPEN  │◀───────────┘
               │ (probe)   │
               └───────────┘

Per CLAUDE.md Truth Protocol:
- Rule #10: Log errors, continue processing
- Rule #12: P95 < 200ms maintained under failure
- Rule #14: All failures logged to error ledger
"""

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import logging
import random
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

T = TypeVar("T")


# === Circuit Breaker ===


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failure threshold exceeded, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    def __init__(self, name: str, state: CircuitState, retry_after: float):
        self.name = name
        self.state = state
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{name}' is {state.value}. "
            f"Retry after {retry_after:.1f}s"
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""

    # Failure thresholds
    failure_threshold: int = 5  # Failures before opening
    failure_rate_threshold: float = 0.5  # 50% failure rate threshold
    minimum_calls: int = 10  # Minimum calls before rate-based evaluation

    # Timing
    recovery_timeout: float = 30.0  # Seconds before attempting recovery
    half_open_max_calls: int = 3  # Test calls in half-open state

    # Sliding window
    window_size: int = 100  # Number of calls to track
    window_time_seconds: float = 60.0  # Time window for rate calculation

    # Slow call handling
    slow_call_threshold_ms: float = 5000.0  # Calls slower than this are "slow"
    slow_call_rate_threshold: float = 0.8  # 80% slow calls triggers open


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    slow_calls: int = 0
    state_transitions: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    time_in_open_state_seconds: float = 0.0
    consecutive_successes: int = 0
    consecutive_failures: int = 0


@dataclass
class CallResult:
    """Result of a single call through circuit breaker"""

    success: bool
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    error: Exception | None = None


class CircuitBreaker:
    """
    Circuit Breaker implementation with sliding window metrics.

    Prevents cascading failures by:
    1. Tracking call success/failure rates
    2. Opening circuit when threshold exceeded
    3. Periodically testing recovery
    4. Automatically closing on recovery

    Usage:
        breaker = CircuitBreaker("backend_api")

        async with breaker:
            result = await call_backend()

        # Or decorator style
        @breaker.protect
        async def call_backend():
            ...
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[CircuitState, CircuitState], None] | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._metrics = CircuitBreakerMetrics()

        # Sliding window of recent calls
        self._call_history: deque[CallResult] = deque(
            maxlen=self.config.window_size
        )

        # State timing
        self._last_state_change = datetime.now()
        self._open_started_at: datetime | None = None

        # Half-open state tracking
        self._half_open_calls = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state"""
        return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Current metrics"""
        return self._metrics

    @property
    def is_closed(self) -> bool:
        """Check if circuit allows requests"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is rejecting requests"""
        return self._state == CircuitState.OPEN

    async def __aenter__(self):
        """Context manager entry - check if call allowed"""
        await self._before_call()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - record result"""
        success = exc_type is None
        await self._after_call(success, exc_val)
        return False  # Don't suppress exceptions

    async def _before_call(self) -> None:
        """Check circuit state before allowing call"""
        async with self._lock:
            await self._check_state_timeout()

            if self._state == CircuitState.OPEN:
                self._metrics.rejected_calls += 1
                retry_after = self._get_retry_after()
                raise CircuitBreakerError(self.name, self._state, retry_after)

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics.rejected_calls += 1
                    raise CircuitBreakerError(self.name, self._state, 1.0)
                self._half_open_calls += 1

    async def _after_call(
        self, success: bool, error: Exception | None = None, duration_ms: float = 0.0
    ) -> None:
        """Record call result and update state"""
        async with self._lock:
            result = CallResult(
                success=success,
                duration_ms=duration_ms,
                error=error,
            )
            self._call_history.append(result)
            self._metrics.total_calls += 1

            if success:
                self._record_success()
            else:
                self._record_failure(error)

            await self._evaluate_state()

    def _record_success(self) -> None:
        """Record successful call"""
        self._metrics.successful_calls += 1
        self._metrics.last_success_time = datetime.now()
        self._metrics.consecutive_successes += 1
        self._metrics.consecutive_failures = 0

    def _record_failure(self, error: Exception | None) -> None:
        """Record failed call"""
        self._metrics.failed_calls += 1
        self._metrics.last_failure_time = datetime.now()
        self._metrics.consecutive_failures += 1
        self._metrics.consecutive_successes = 0

        logger.warning(
            f"Circuit breaker '{self.name}' recorded failure: {error}"
        )

    async def _evaluate_state(self) -> None:
        """Evaluate if state should change based on metrics"""
        if self._state == CircuitState.CLOSED:
            if self._should_open():
                await self._transition_to(CircuitState.OPEN)

        elif self._state == CircuitState.HALF_OPEN:
            if self._metrics.consecutive_successes >= self.config.half_open_max_calls:
                await self._transition_to(CircuitState.CLOSED)
            elif self._metrics.consecutive_failures > 0:
                await self._transition_to(CircuitState.OPEN)

    def _should_open(self) -> bool:
        """Determine if circuit should open"""
        # Check consecutive failures
        if self._metrics.consecutive_failures >= self.config.failure_threshold:
            logger.warning(
                f"Circuit '{self.name}' opening: "
                f"{self._metrics.consecutive_failures} consecutive failures"
            )
            return True

        # Check failure rate (need minimum calls)
        if len(self._call_history) >= self.config.minimum_calls:
            recent_calls = self._get_recent_calls()
            if len(recent_calls) >= self.config.minimum_calls:
                failure_rate = sum(1 for c in recent_calls if not c.success) / len(
                    recent_calls
                )
                if failure_rate >= self.config.failure_rate_threshold:
                    logger.warning(
                        f"Circuit '{self.name}' opening: "
                        f"{failure_rate:.1%} failure rate"
                    )
                    return True

        return False

    def _get_recent_calls(self) -> list[CallResult]:
        """Get calls within the time window"""
        cutoff = datetime.now() - timedelta(
            seconds=self.config.window_time_seconds
        )
        return [c for c in self._call_history if c.timestamp > cutoff]

    async def _check_state_timeout(self) -> None:
        """Check if state should transition due to timeout"""
        if self._state == CircuitState.OPEN:
            if self._open_started_at:
                elapsed = (datetime.now() - self._open_started_at).total_seconds()
                if elapsed >= self.config.recovery_timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)

    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state"""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.now()
        self._metrics.state_transitions += 1

        if new_state == CircuitState.OPEN:
            self._open_started_at = datetime.now()
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        elif new_state == CircuitState.CLOSED:
            if self._open_started_at:
                self._metrics.time_in_open_state_seconds += (
                    datetime.now() - self._open_started_at
                ).total_seconds()
            self._open_started_at = None

        logger.info(
            f"Circuit breaker '{self.name}' transitioned: "
            f"{old_state.value} → {new_state.value}"
        )

        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    def _get_retry_after(self) -> float:
        """Calculate seconds until retry is allowed"""
        if self._open_started_at:
            elapsed = (datetime.now() - self._open_started_at).total_seconds()
            return max(0, self.config.recovery_timeout - elapsed)
        return self.config.recovery_timeout

    def protect(self, func: Callable) -> Callable:
        """Decorator to protect a function with circuit breaker"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                await self._before_call()
                result = await func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                await self._after_call(True, None, duration_ms)
                return result
            except CircuitBreakerError:
                raise
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                await self._after_call(False, e, duration_ms)
                raise

        return wrapper

    async def force_open(self) -> None:
        """Manually open the circuit"""
        async with self._lock:
            await self._transition_to(CircuitState.OPEN)

    async def force_close(self) -> None:
        """Manually close the circuit"""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)

    async def reset(self) -> None:
        """Reset circuit breaker to initial state"""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._metrics = CircuitBreakerMetrics()
            self._call_history.clear()
            self._open_started_at = None
            self._half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' reset")

    def get_health(self) -> dict[str, Any]:
        """Get circuit breaker health status"""
        recent_calls = self._get_recent_calls()
        failure_rate = (
            sum(1 for c in recent_calls if not c.success) / len(recent_calls)
            if recent_calls
            else 0.0
        )

        return {
            "name": self.name,
            "state": self._state.value,
            "metrics": {
                "total_calls": self._metrics.total_calls,
                "successful_calls": self._metrics.successful_calls,
                "failed_calls": self._metrics.failed_calls,
                "rejected_calls": self._metrics.rejected_calls,
                "state_transitions": self._metrics.state_transitions,
                "consecutive_failures": self._metrics.consecutive_failures,
                "consecutive_successes": self._metrics.consecutive_successes,
            },
            "failure_rate": round(failure_rate * 100, 2),
            "time_in_open_seconds": round(
                self._metrics.time_in_open_state_seconds, 2
            ),
            "last_failure": (
                self._metrics.last_failure_time.isoformat()
                if self._metrics.last_failure_time
                else None
            ),
        }


# === Retry Handler ===


class RetryStrategy(Enum):
    """Retry backoff strategies"""

    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    EXPONENTIAL_JITTER = "exponential_jitter"  # Exponential with random jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_retries: int = 3
    initial_delay_ms: float = 100.0
    max_delay_ms: float = 10000.0
    multiplier: float = 2.0
    jitter_factor: float = 0.1  # 10% jitter
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER

    # Retry conditions
    retryable_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        OSError,
    )


class RetryHandler:
    """
    Handles retry logic with configurable backoff strategies.

    Usage:
        retry = RetryHandler(RetryConfig(max_retries=3))

        result = await retry.execute(async_function, arg1, arg2)
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self._attempt_count = 0

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay_ms

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay_ms * (
                self.config.multiplier ** attempt
            )

        else:  # EXPONENTIAL_JITTER
            base_delay = self.config.initial_delay_ms * (
                self.config.multiplier ** attempt
            )
            jitter = base_delay * self.config.jitter_factor * random.random()
            delay = base_delay + jitter

        return min(delay, self.config.max_delay_ms)

    def _is_retryable(self, error: Exception) -> bool:
        """Check if exception is retryable"""
        return isinstance(error, self.config.retryable_exceptions)

    async def execute(
        self,
        func: Callable,
        *args,
        on_retry: Callable[[int, Exception], None] | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            on_retry: Callback on each retry (attempt, exception)
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                self._attempt_count = attempt
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if not self._is_retryable(e):
                    logger.debug(f"Non-retryable exception: {type(e).__name__}")
                    raise

                if attempt >= self.config.max_retries:
                    logger.warning(
                        f"All {self.config.max_retries} retries exhausted"
                    )
                    raise

                delay_ms = self._calculate_delay(attempt)
                logger.info(
                    f"Retry {attempt + 1}/{self.config.max_retries} "
                    f"after {delay_ms:.0f}ms: {e}"
                )

                if on_retry:
                    on_retry(attempt + 1, e)

                await asyncio.sleep(delay_ms / 1000)

        raise last_exception  # type: ignore


# === Timeout Handler ===


class TimeoutError(Exception):
    """Raised when operation exceeds timeout"""

    def __init__(self, operation: str, timeout_ms: float):
        self.operation = operation
        self.timeout_ms = timeout_ms
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_ms:.0f}ms"
        )


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior"""

    default_timeout_ms: float = 5000.0
    operation_timeouts: dict[str, float] = field(default_factory=dict)


class TimeoutHandler:
    """
    Enforces timeout on async operations.

    Usage:
        timeout = TimeoutHandler(TimeoutConfig(default_timeout_ms=5000))

        result = await timeout.execute(
            async_function,
            timeout_ms=3000,
            operation_name="fetch_data"
        )
    """

    def __init__(self, config: TimeoutConfig | None = None):
        self.config = config or TimeoutConfig()

    def get_timeout(self, operation: str | None = None) -> float:
        """Get timeout for operation"""
        if operation and operation in self.config.operation_timeouts:
            return self.config.operation_timeouts[operation]
        return self.config.default_timeout_ms

    async def execute(
        self,
        func: Callable,
        *args,
        timeout_ms: float | None = None,
        operation_name: str = "unknown",
        **kwargs,
    ) -> Any:
        """
        Execute function with timeout.

        Args:
            func: Async function to execute
            *args: Function arguments
            timeout_ms: Timeout in milliseconds (overrides config)
            operation_name: Name for error messages
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            TimeoutError: If operation exceeds timeout
        """
        effective_timeout = timeout_ms or self.get_timeout(operation_name)
        timeout_seconds = effective_timeout / 1000

        try:
            return await asyncio.wait_for(
                func(*args, **kwargs), timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            raise TimeoutError(operation_name, effective_timeout)


# === Bulkhead Pattern ===


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead isolation"""

    max_concurrent: int = 10  # Max concurrent calls
    max_queue_size: int = 100  # Max queued calls
    queue_timeout_ms: float = 5000.0  # Timeout waiting for slot


class BulkheadFullError(Exception):
    """Raised when bulkhead is full"""

    def __init__(self, name: str, concurrent: int, queued: int):
        self.name = name
        self.concurrent = concurrent
        self.queued = queued
        super().__init__(
            f"Bulkhead '{name}' full: {concurrent} concurrent, {queued} queued"
        )


class Bulkhead:
    """
    Bulkhead pattern for isolating components.

    Limits concurrent calls to prevent resource exhaustion.

    Usage:
        bulkhead = Bulkhead("database", BulkheadConfig(max_concurrent=10))

        async with bulkhead:
            result = await database_call()
    """

    def __init__(self, name: str, config: BulkheadConfig | None = None):
        self.name = name
        self.config = config or BulkheadConfig()

        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._queue_count = 0
        self._active_count = 0
        self._lock = asyncio.Lock()

        # Metrics
        self._total_calls = 0
        self._rejected_calls = 0

    async def __aenter__(self):
        """Acquire slot in bulkhead"""
        async with self._lock:
            if self._queue_count >= self.config.max_queue_size:
                self._rejected_calls += 1
                raise BulkheadFullError(
                    self.name, self._active_count, self._queue_count
                )
            self._queue_count += 1

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.config.queue_timeout_ms / 1000,
            )
        except asyncio.TimeoutError:
            async with self._lock:
                self._queue_count -= 1
                self._rejected_calls += 1
            raise BulkheadFullError(
                self.name, self._active_count, self._queue_count
            )

        async with self._lock:
            self._queue_count -= 1
            self._active_count += 1
            self._total_calls += 1

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release slot in bulkhead"""
        self._semaphore.release()
        async with self._lock:
            self._active_count -= 1
        return False

    def get_metrics(self) -> dict[str, Any]:
        """Get bulkhead metrics"""
        return {
            "name": self.name,
            "active": self._active_count,
            "queued": self._queue_count,
            "max_concurrent": self.config.max_concurrent,
            "max_queue": self.config.max_queue_size,
            "total_calls": self._total_calls,
            "rejected_calls": self._rejected_calls,
            "utilization": round(
                self._active_count / self.config.max_concurrent * 100, 2
            ),
        }


# === Fallback Strategies ===


class FallbackStrategy(ABC):
    """Base class for fallback strategies"""

    @abstractmethod
    async def execute(
        self, operation: str, error: Exception, context: dict[str, Any]
    ) -> Any:
        """Execute fallback logic"""


class CachedFallback(FallbackStrategy):
    """Return cached value on failure"""

    def __init__(self, cache: dict[str, Any] | None = None):
        self._cache = cache or {}

    async def execute(
        self, operation: str, error: Exception, context: dict[str, Any]
    ) -> Any:
        cache_key = context.get("cache_key", operation)
        if cache_key in self._cache:
            logger.info(f"Fallback: returning cached value for '{cache_key}'")
            return self._cache[cache_key]
        raise error

    def set_cache(self, key: str, value: Any) -> None:
        """Store fallback value"""
        self._cache[key] = value


class DefaultValueFallback(FallbackStrategy):
    """Return default value on failure"""

    def __init__(self, defaults: dict[str, Any] | None = None):
        self._defaults = defaults or {}

    async def execute(
        self, operation: str, error: Exception, context: dict[str, Any]
    ) -> Any:
        if operation in self._defaults:
            logger.info(f"Fallback: returning default for '{operation}'")
            return self._defaults[operation]
        raise error

    def set_default(self, operation: str, value: Any) -> None:
        """Set default value for operation"""
        self._defaults[operation] = value


class GracefulDegradationFallback(FallbackStrategy):
    """Execute degraded version of operation"""

    def __init__(self):
        self._degraded_handlers: dict[str, Callable] = {}

    def register_degraded(self, operation: str, handler: Callable) -> None:
        """Register degraded handler for operation"""
        self._degraded_handlers[operation] = handler

    async def execute(
        self, operation: str, error: Exception, context: dict[str, Any]
    ) -> Any:
        if operation in self._degraded_handlers:
            logger.info(f"Fallback: executing degraded handler for '{operation}'")
            handler = self._degraded_handlers[operation]
            if asyncio.iscoroutinefunction(handler):
                return await handler(context)
            return handler(context)
        raise error


# === Unified Resilience Layer ===


@dataclass
class ResilienceConfig:
    """Unified configuration for resilience layer"""

    circuit_breaker: CircuitBreakerConfig = field(
        default_factory=CircuitBreakerConfig
    )
    retry: RetryConfig = field(default_factory=RetryConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    bulkhead: BulkheadConfig = field(default_factory=BulkheadConfig)

    # Feature flags
    enable_circuit_breaker: bool = True
    enable_retry: bool = True
    enable_timeout: bool = True
    enable_bulkhead: bool = True
    enable_fallback: bool = True


class ResilienceLayer:
    """
    Unified resilience layer combining all patterns.

    Wraps operations with circuit breaker, timeout, retry,
    bulkhead, and fallback strategies.

    Usage:
        resilience = ResilienceLayer("backend_api")

        result = await resilience.execute(
            async_function,
            operation="fetch_user",
            timeout_ms=3000,
        )

        # Or decorator
        @resilience.protect(timeout_ms=5000)
        async def fetch_data():
            ...
    """

    def __init__(
        self,
        name: str,
        config: ResilienceConfig | None = None,
        fallback: FallbackStrategy | None = None,
    ):
        self.name = name
        self.config = config or ResilienceConfig()

        # Initialize components
        self.circuit_breaker = CircuitBreaker(
            f"{name}_circuit",
            self.config.circuit_breaker,
            on_state_change=self._on_circuit_state_change,
        )

        self.retry_handler = RetryHandler(self.config.retry)
        self.timeout_handler = TimeoutHandler(self.config.timeout)
        self.bulkhead = Bulkhead(f"{name}_bulkhead", self.config.bulkhead)

        self.fallback = fallback

        # Metrics
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._fallback_executions = 0

    def _on_circuit_state_change(
        self, old_state: CircuitState, new_state: CircuitState
    ) -> None:
        """Handle circuit state changes"""
        logger.warning(
            f"Resilience layer '{self.name}' circuit state: "
            f"{old_state.value} → {new_state.value}"
        )

    async def execute(
        self,
        func: Callable,
        *args,
        operation: str = "unknown",
        timeout_ms: float | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with full resilience protection.

        Order of protection:
        1. Bulkhead (limit concurrency)
        2. Circuit Breaker (prevent cascading failures)
        3. Timeout (enforce time limits)
        4. Retry (handle transient failures)
        5. Fallback (graceful degradation)

        Args:
            func: Async function to execute
            *args: Function arguments
            operation: Operation name for logging
            timeout_ms: Operation timeout
            context: Context for fallback strategies
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback value
        """
        self._total_executions += 1
        context = context or {}

        async def protected_call():
            # Layer 1: Timeout
            if self.config.enable_timeout:
                return await self.timeout_handler.execute(
                    func,
                    *args,
                    timeout_ms=timeout_ms,
                    operation_name=operation,
                    **kwargs,
                )
            return await func(*args, **kwargs)

        async def retried_call():
            # Layer 2: Retry
            if self.config.enable_retry:
                return await self.retry_handler.execute(protected_call)
            return await protected_call()

        async def circuit_protected_call():
            # Layer 3: Circuit Breaker
            if self.config.enable_circuit_breaker:
                start_time = datetime.now()
                try:
                    await self.circuit_breaker._before_call()
                    result = await retried_call()
                    duration_ms = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000
                    await self.circuit_breaker._after_call(True, None, duration_ms)
                    return result
                except CircuitBreakerError:
                    raise
                except Exception as e:
                    duration_ms = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000
                    await self.circuit_breaker._after_call(False, e, duration_ms)
                    raise
            return await retried_call()

        try:
            # Layer 4: Bulkhead
            if self.config.enable_bulkhead:
                async with self.bulkhead:
                    result = await circuit_protected_call()
            else:
                result = await circuit_protected_call()

            self._successful_executions += 1
            return result

        except Exception as e:
            self._failed_executions += 1

            # Layer 5: Fallback
            if self.config.enable_fallback and self.fallback:
                try:
                    result = await self.fallback.execute(operation, e, context)
                    self._fallback_executions += 1
                    return result
                except Exception:
                    pass  # Fallback failed, raise original

            raise

    def protect(
        self,
        operation: str | None = None,
        timeout_ms: float | None = None,
    ) -> Callable:
        """
        Decorator to protect a function with resilience.

        Args:
            operation: Operation name (defaults to function name)
            timeout_ms: Timeout for this operation
        """

        def decorator(func: Callable) -> Callable:
            op_name = operation or func.__name__

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute(
                    func,
                    *args,
                    operation=op_name,
                    timeout_ms=timeout_ms,
                    **kwargs,
                )

            return wrapper

        return decorator

    def get_health(self) -> dict[str, Any]:
        """Get resilience layer health status"""
        return {
            "name": self.name,
            "circuit_breaker": self.circuit_breaker.get_health(),
            "bulkhead": self.bulkhead.get_metrics(),
            "executions": {
                "total": self._total_executions,
                "successful": self._successful_executions,
                "failed": self._failed_executions,
                "fallback": self._fallback_executions,
                "success_rate": round(
                    self._successful_executions
                    / max(1, self._total_executions)
                    * 100,
                    2,
                ),
            },
        }

    async def reset(self) -> None:
        """Reset all resilience components"""
        await self.circuit_breaker.reset()
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._fallback_executions = 0


# === Resilience Registry ===


class ResilienceRegistry:
    """
    Registry for managing multiple resilience layers.

    Provides per-agent and per-operation resilience configuration.
    """

    def __init__(self):
        self._layers: dict[str, ResilienceLayer] = {}
        self._default_config = ResilienceConfig()

    def get_or_create(
        self,
        name: str,
        config: ResilienceConfig | None = None,
        fallback: FallbackStrategy | None = None,
    ) -> ResilienceLayer:
        """Get existing or create new resilience layer"""
        if name not in self._layers:
            self._layers[name] = ResilienceLayer(
                name, config or self._default_config, fallback
            )
        return self._layers[name]

    def get(self, name: str) -> ResilienceLayer | None:
        """Get resilience layer by name"""
        return self._layers.get(name)

    def set_default_config(self, config: ResilienceConfig) -> None:
        """Set default configuration for new layers"""
        self._default_config = config

    def get_all_health(self) -> dict[str, Any]:
        """Get health status of all layers"""
        return {name: layer.get_health() for name, layer in self._layers.items()}

    async def reset_all(self) -> None:
        """Reset all resilience layers"""
        for layer in self._layers.values():
            await layer.reset()


# Global registry instance
resilience_registry = ResilienceRegistry()
