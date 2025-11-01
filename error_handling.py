from datetime import datetime
from logging_config import error_logger, get_correlation_id

from fastapi import HTTPException, status

from collections import defaultdict, deque
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import logging
import random

"""
Enterprise Error Handling & Recovery System for DevSkyy Platform
Circuit breakers, exponential backoff, retry mechanisms, and centralized error management
"""

# ============================================================================
# ERROR TYPES AND CODES
# ============================================================================

class ErrorCode(str, Enum):
    """Standardized error codes"""

    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTH_001"
    AUTHORIZATION_DENIED = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    TOKEN_INVALID = "AUTH_004"
    ACCOUNT_LOCKED = "AUTH_005"

    # Validation
    VALIDATION_ERROR = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_REQUIRED_FIELD = "VAL_003"
    INVALID_FORMAT = "VAL_004"

    # Database
    DATABASE_CONNECTION_ERROR = "DB_001"
    DATABASE_QUERY_ERROR = "DB_002"
    DATABASE_CONSTRAINT_ERROR = "DB_003"
    DATABASE_TIMEOUT = "DB_004"

    # External Services
    EXTERNAL_SERVICE_UNAVAILABLE = "EXT_001"
    EXTERNAL_SERVICE_TIMEOUT = "EXT_002"
    EXTERNAL_SERVICE_ERROR = "EXT_003"
    API_RATE_LIMIT_EXCEEDED = "EXT_004"

    # Business Logic
    RESOURCE_NOT_FOUND = "BIZ_001"
    RESOURCE_ALREADY_EXISTS = "BIZ_002"
    OPERATION_NOT_ALLOWED = "BIZ_003"
    INSUFFICIENT_PERMISSIONS = "BIZ_004"

    # System
    INTERNAL_SERVER_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    CONFIGURATION_ERROR = "SYS_003"
    RESOURCE_EXHAUSTED = "SYS_004"

    # Security
    SECURITY_VIOLATION = "SEC_001"
    SUSPICIOUS_ACTIVITY = "SEC_002"
    RATE_LIMIT_EXCEEDED = "SEC_003"
    BLOCKED_REQUEST = "SEC_004"

class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DevSkyError(Exception):
    """Base exception class for DevSkyy platform"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.correlation_id = correlation_id or get_correlation_id()
        self.timestamp = datetime.utcnow()

# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0

        self.logger = logging.getLogger(f"circuit_breaker.{name}")

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_requests += 1

        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info(
                    f"🔄 Circuit breaker {self.name} transitioning to HALF_OPEN"
                )
            else:
                raise DevSkyError(
                    f"Circuit breaker {self.name} is OPEN",
                    ErrorCode.SERVICE_UNAVAILABLE,
                    ErrorSeverity.HIGH,
                    {"circuit_breaker": self.name, "state": self.state},
                )

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count
            self._on_success()
            return result

        except self.expected_exception as e:
            # Expected failure - increment failure count
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return (
            datetime.utcnow() - self.last_failure_time
        ).total_seconds() >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        self.total_successes += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info(
                    f"✅ Circuit breaker {self.name} CLOSED - service recovered"
                )
        else:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(
                f"🚨 Circuit breaker {self.name} OPENED - service failing"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(self.total_requests, 1),
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
        }

# ============================================================================
# RETRY MECHANISM WITH EXPONENTIAL BACKOFF
# ============================================================================

class RetryConfig:
    """Configuration for retry mechanism"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: List[Type[Exception]] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]

async def retry_with_backoff(
    func: Callable, config: RetryConfig, *args, **kwargs
) -> Any:
    """Execute function with exponential backoff retry"""
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            # Check if exception is retryable
            if not any(
                isinstance(e, exc_type) for exc_type in config.retryable_exceptions
            ):
                raise e

            # Don't retry on last attempt
            if attempt == config.max_attempts - 1:
                break

            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base**attempt), config.max_delay
            )

            # Add jitter to prevent thundering herd
            if config.jitter:
                delay *= 0.5 + secrets.SystemRandom().random() * 0.5

            error_logger.logger.warning(
                f"Retry attempt {attempt + 1}/{config.max_attempts} failed, retrying in {delay:.2f}s",
                extra={
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "max_attempts": config.max_attempts,
                    "delay": delay,
                    "error": str(e),
                },
            )

            await asyncio.sleep(delay)

    # All attempts failed
    raise last_exception

def retry(config: RetryConfig = None):
    """Decorator for retry with exponential backoff"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)

        return wrapper

    return decorator

# ============================================================================
# CENTRALIZED ERROR HANDLER
# ============================================================================

class ErrorHandler:
    """Centralized error handling and recovery system"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_stats = defaultdict(int)
        self.recent_errors = deque(maxlen=1000)
        self.error_patterns = defaultdict(list)

    def register_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Register a new circuit breaker"""
        circuit_breaker = CircuitBreaker(name, **kwargs)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        user_id: str = None,
        request_id: str = None,
    ) -> HTTPException:
        """Handle and convert errors to HTTP exceptions"""

        # Record error statistics
        error_type = type(error).__name__
        self.error_stats[error_type] += 1

        # Record error details
        error_record = {
            "timestamp": datetime.utcnow(),
            "error_type": error_type,
            "message": str(error),
            "context": context or {},
            "user_id": user_id,
            "request_id": request_id or get_correlation_id(),
        }
        self.recent_errors.append(error_record)

        # Log error
        error_logger.log_application_error(error, context)

        # Convert to appropriate HTTP exception
        if isinstance(error, DevSkyError):
            return self._handle_devskyy_error(error)
        elif isinstance(error, ValueError):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": ErrorCode.VALIDATION_ERROR,
                    "message": str(error),
                    "correlation_id": get_correlation_id(),
                },
            )
        elif isinstance(error, PermissionError):
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": ErrorCode.AUTHORIZATION_DENIED,
                    "message": "Access denied",
                    "correlation_id": get_correlation_id(),
                },
            )
        else:
            # Generic internal server error
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                    "message": "An internal error occurred",
                    "correlation_id": get_correlation_id(),
                },
            )

    def _handle_devskyy_error(self, error: DevSkyError) -> HTTPException:
        """Handle DevSkyy-specific errors"""

        # Map error codes to HTTP status codes
        status_code_map = {
            ErrorCode.AUTHENTICATION_FAILED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTHORIZATION_DENIED: status.HTTP_403_FORBIDDEN,
            ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.ACCOUNT_LOCKED: status.HTTP_423_LOCKED,
            ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
            ErrorCode.MISSING_REQUIRED_FIELD: status.HTTP_400_BAD_REQUEST,
            ErrorCode.INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
            ErrorCode.DATABASE_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.DATABASE_QUERY_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.DATABASE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,
            ErrorCode.DATABASE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            ErrorCode.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
            ErrorCode.API_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.RESOURCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.RESOURCE_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
            ErrorCode.OPERATION_NOT_ALLOWED: status.HTTP_405_METHOD_NOT_ALLOWED,
            ErrorCode.INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
            ErrorCode.INTERNAL_SERVER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.RESOURCE_EXHAUSTED: status.HTTP_507_INSUFFICIENT_STORAGE,
            ErrorCode.SECURITY_VIOLATION: status.HTTP_403_FORBIDDEN,
            ErrorCode.SUSPICIOUS_ACTIVITY: status.HTTP_403_FORBIDDEN,
            ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.BLOCKED_REQUEST: status.HTTP_403_FORBIDDEN,
        }

        http_status = status_code_map.get(
            error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        return HTTPException(
            status_code=http_status,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "severity": error.severity,
                "details": error.details,
                "correlation_id": error.correlation_id,
                "timestamp": error.timestamp.isoformat(),
            },
        )

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": sum(self.error_stats.values()),
            "error_types": dict(self.error_stats),
            "recent_error_count": len(self.recent_errors),
            "circuit_breaker_stats": {
                name: cb.get_stats() for name, cb in self.circuit_breakers.items()
            },
        }

# ============================================================================
# GLOBAL ERROR HANDLER INSTANCE
# ============================================================================

# Global error handler instance
error_handler = ErrorHandler()

# Register common circuit breakers
database_circuit_breaker = error_handler.register_circuit_breaker(
    "database",
    failure_threshold=3,
    recovery_timeout=30,
)

openai_circuit_breaker = error_handler.register_circuit_breaker(
    "openai_api",
    failure_threshold=5,
    recovery_timeout=60,
)

external_api_circuit_breaker = error_handler.register_circuit_breaker(
    "external_api",
    failure_threshold=3,
    recovery_timeout=45,
)
