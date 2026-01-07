"""
Ralph-Wiggums Error Loop: Try all possible solutions until success or exhaustion.

Philosophy: "I'm in danger!" → Try everything → "I'm helping!"

This module provides comprehensive error handling utilities including:
- Retry with exponential backoff
- Circuit breaker pattern
- Fallback chains
- Error categorization
- Timeout handling
- Graceful degradation

Named after Ralph Wiggums because we try every possible approach until something works.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCategory(Enum):
    """Error categories for determining retry strategy."""
    NETWORK = "network"  # Network failures, connection issues
    AUTHENTICATION = "authentication"  # 401, 403, invalid credentials
    TIMEOUT = "timeout"  # Operation timeout
    RATE_LIMIT = "rate_limit"  # 429, quota exceeded
    VALIDATION = "validation"  # 400, invalid input
    SERVER_ERROR = "server_error"  # 500, 502, 503
    FATAL = "fatal"  # Non-recoverable errors


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class AllAttemptsFailedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"All {attempts} attempts failed. Last error: {type(last_error).__name__}: {last_error}"
        )


def categorize_error(error: Exception) -> ErrorCategory:
    """
    Categorize an error to determine retry strategy.

    Args:
        error: The exception to categorize

    Returns:
        ErrorCategory enum value
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Network errors
    if any(term in error_str or term in error_type for term in [
        "connection", "network", "timeout", "unreachable", "refused"
    ]):
        if "timeout" in error_str or "timeout" in error_type:
            return ErrorCategory.TIMEOUT
        return ErrorCategory.NETWORK

    # Authentication errors
    if any(term in error_str for term in ["401", "403", "unauthorized", "forbidden", "authentication"]):
        return ErrorCategory.AUTHENTICATION

    # Rate limiting
    if any(term in error_str for term in ["429", "rate limit", "quota", "throttle"]):
        return ErrorCategory.RATE_LIMIT

    # Validation errors
    if any(term in error_str for term in ["400", "validation", "invalid", "bad request"]):
        return ErrorCategory.VALIDATION

    # Server errors
    if any(term in error_str for term in ["500", "502", "503", "504", "server error", "internal error"]):
        return ErrorCategory.SERVER_ERROR

    # Default to fatal
    return ErrorCategory.FATAL


async def ralph_wiggums_execute(
    operation: Callable[[], T],
    fallbacks: list[Callable[[], T]] | None = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_categories: list[ErrorCategory] | None = None,
) -> tuple[bool, T | None, Exception | None]:
    """
    Ralph-Wiggums loop: Try operation, then fallbacks, with exponential backoff.

    Args:
        operation: Primary operation to execute (async function)
        fallbacks: List of fallback operations (async functions)
        max_attempts: Maximum retry attempts per operation
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential calculation (default 2.0)
        jitter: Add random jitter to avoid thundering herd
        retry_categories: Error categories to retry (default: NETWORK, TIMEOUT, RATE_LIMIT, SERVER_ERROR)

    Returns:
        Tuple of (success: bool, result: Optional[T], error: Optional[Exception])

    Example:
        >>> async def primary():
        ...     return await api_call()
        >>> async def backup():
        ...     return await backup_api_call()
        >>> success, result, error = await ralph_wiggums_execute(primary, [backup])
    """
    if retry_categories is None:
        retry_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.SERVER_ERROR,
        ]

    attempts_list = [operation] + (fallbacks or [])

    for op_index, attempt in enumerate(attempts_list):
        op_name = f"operation_{op_index}" if op_index > 0 else "primary"

        for retry_count in range(max_attempts):
            try:
                logger.debug(f"Ralph-Wiggums: Executing {op_name} (attempt {retry_count + 1}/{max_attempts})")

                # Execute the operation
                if asyncio.iscoroutinefunction(attempt):
                    result = await attempt()
                else:
                    result = attempt()

                logger.info(f"Ralph-Wiggums: Success with {op_name} on attempt {retry_count + 1}")
                return (True, result, None)

            except Exception as e:
                category = categorize_error(e)
                logger.warning(
                    f"Ralph-Wiggums: {op_name} failed (attempt {retry_count + 1}/{max_attempts}): "
                    f"{type(e).__name__}: {e} [Category: {category.value}]"
                )

                # Check if we should retry this error
                if category not in retry_categories:
                    logger.error(f"Ralph-Wiggums: Error category {category.value} not retryable, moving to next operation")
                    break

                # Last attempt for this operation?
                if retry_count == max_attempts - 1:
                    logger.error(f"Ralph-Wiggums: {op_name} exhausted all {max_attempts} attempts")
                    break

                # Calculate backoff delay
                delay = min(base_delay * (exponential_base ** retry_count), max_delay)

                # Add jitter to avoid thundering herd
                if jitter:
                    import random
                    delay = delay * (0.5 + random.random())

                # Special handling for rate limits
                if category == ErrorCategory.RATE_LIMIT:
                    delay = min(delay * 2, max_delay)  # Double the delay for rate limits

                logger.debug(f"Ralph-Wiggums: Waiting {delay:.2f}s before retry")
                await asyncio.sleep(delay)

    # All operations and attempts failed
    logger.error("Ralph-Wiggums: All operations and attempts exhausted")
    return (False, None, AllAttemptsFailedError(len(attempts_list) * max_attempts, e))


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    States:
    - CLOSED: Normal operation, tracking failures
    - OPEN: Too many failures, rejecting calls immediately
    - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>> result = await breaker.call(my_async_function)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_attempts: int = 1,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting half-open
            half_open_attempts: Number of successful calls needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED

        self._lock = asyncio.Lock()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)

    async def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt reset
            if self.state == CircuitState.OPEN and self._should_attempt_reset():
                logger.info("Circuit breaker: Attempting reset (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}. "
                f"Retry after {self.timeout}s."
            )

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success!
            await self._on_success()
            return result

        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.debug(f"Circuit breaker: HALF_OPEN success {self.success_count}/{self.half_open_attempts}")

                if self.success_count >= self.half_open_attempts:
                    logger.info("Circuit breaker: Closing circuit (recovered)")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            logger.warning(f"Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}")

            if self.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker: HALF_OPEN test failed, reopening")
                self.state = CircuitState.OPEN

            elif self.failure_count >= self.failure_threshold:
                logger.error("Circuit breaker: Threshold exceeded, opening circuit")
                self.state = CircuitState.OPEN


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_categories: list[ErrorCategory] | None = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        retry_categories: Error categories to retry

    Example:
        >>> @with_retry(max_attempts=3, base_delay=2.0)
        ... async def fetch_data():
        ...     return await api.get("/data")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            success, result, error = await ralph_wiggums_execute(
                lambda: func(*args, **kwargs),
                fallbacks=None,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                retry_categories=retry_categories,
            )

            if success:
                return result
            else:
                raise error

        return wrapper
    return decorator


async def with_fallbacks(
    operations: list[Callable[[], T]],
    max_attempts_per_op: int = 2,
    base_delay: float = 1.0,
) -> T:
    """
    Try multiple operations in sequence with retries.

    Args:
        operations: List of async functions to try (in order)
        max_attempts_per_op: Max retries per operation
        base_delay: Base delay for exponential backoff

    Returns:
        Result from first successful operation

    Raises:
        AllAttemptsFailedError: If all operations fail

    Example:
        >>> result = await with_fallbacks([
        ...     lambda: primary_api.call(),
        ...     lambda: backup_api.call(),
        ...     lambda: cache.get(),
        ... ])
    """
    if not operations:
        raise ValueError("Must provide at least one operation")

    primary = operations[0]
    fallbacks = operations[1:] if len(operations) > 1 else None

    success, result, error = await ralph_wiggums_execute(
        primary,
        fallbacks=fallbacks,
        max_attempts=max_attempts_per_op,
        base_delay=base_delay,
    )

    if success:
        return result
    else:
        raise error


# Example usage and tests
if __name__ == "__main__":
    # Example 1: Basic retry with exponential backoff
    async def flaky_operation():
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("Network temporarily unavailable")
        return "Success!"

    async def example_basic_retry():
        print("\n=== Example 1: Basic Retry ===")
        success, result, error = await ralph_wiggums_execute(
            flaky_operation,
            max_attempts=5,
            base_delay=0.5,
        )
        print(f"Result: success={success}, result={result}, error={error}")

    # Example 2: With fallbacks
    async def example_with_fallbacks():
        print("\n=== Example 2: With Fallbacks ===")

        async def primary():
            raise ConnectionError("Primary API down")

        async def backup():
            raise TimeoutError("Backup API slow")

        async def cache():
            return "Cached data"

        success, result, error = await ralph_wiggums_execute(
            primary,
            fallbacks=[backup, cache],
            max_attempts=2,
        )
        print(f"Result: success={success}, result={result}")

    # Example 3: Circuit breaker
    async def example_circuit_breaker():
        print("\n=== Example 3: Circuit Breaker ===")
        breaker = CircuitBreaker(failure_threshold=3, timeout=5)

        async def failing_service():
            raise Exception("Service down")

        # Trigger failures
        for i in range(5):
            try:
                await breaker.call(failing_service)
            except Exception as e:
                print(f"Attempt {i + 1}: {type(e).__name__}")

    # Run examples
    async def main():
        await example_basic_retry()
        await example_with_fallbacks()
        await example_circuit_breaker()

    asyncio.run(main())
